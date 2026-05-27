from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


def load_health_module():
    module_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "check_submission_health.py"
    )
    spec = importlib.util.spec_from_file_location(
        "check_submission_health", module_path
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def healthy_submission(**overrides: Any) -> dict[str, Any]:
    submission: dict[str, Any] = {
        "schema_version": "agent-anvil.leaderboard.v1",
        "submitter": {"agent_name": "Safe Agent"},
        "benchmark": {
            "name": "agent_anvil_trace_eval_benchmark",
            "manifest_sha256": "a" * 64,
            "scenario_hashes": {"experiments/scenarios/refund_trace.yaml": "b" * 64},
        },
        "metrics": {"total_trials": 100},
        "verification": {
            "trust_level": "github_actions",
            "generated_at": "2026-05-23T15:41:36Z",
            "generated_by": "agent-anvil/0.2.22",
            "github_run_url": "https://github.com/acme/agent/actions/runs/123",
            "github_repository": "acme/agent",
            "github_sha": "abc123",
        },
    }
    submission.update(overrides)
    return submission


def test_check_submission_health_accepts_complete_submission() -> None:
    module = load_health_module()

    report = module.check_submission_health(
        Path("submissions/safe-agent.json"),
        healthy_submission(),
    )

    assert report.errors == []
    assert report.warnings == []


def test_check_submission_health_reports_structural_errors() -> None:
    module = load_health_module()
    submission = healthy_submission(
        schema_version="agent-anvil.leaderboard.v0",
        benchmark={
            "name": "agent_anvil_trace_eval_benchmark",
            "manifest_sha256": "short",
            "scenario_hashes": {},
        },
        metrics={"total_trials": 0},
    )

    report = module.check_submission_health(Path("submissions/bad.json"), submission)

    assert "schema_version must be agent-anvil.leaderboard.v1" in report.errors
    assert (
        "benchmark.manifest_sha256 must be a 64-character sha256 hex digest"
        in report.errors
    )
    assert "benchmark.scenario_hashes must not be empty" in report.errors
    assert "metrics.total_trials must be positive" in report.errors


def test_check_submission_health_warns_on_low_trials_and_self_reported() -> None:
    module = load_health_module()
    submission = healthy_submission(
        metrics={"total_trials": 10},
        verification={
            "trust_level": "self_reported",
            "generated_at": "2026-05-23T15:41:36Z",
            "generated_by": "agent-anvil/0.2.22",
        },
    )

    report = module.check_submission_health(Path("submissions/draft.json"), submission)

    assert report.errors == []
    assert (
        "self_reported rows are accepted but should be treated as unverified"
        in report.warnings
    )
    assert (
        "metrics.total_trials is below the recommended minimum of 100"
        in report.warnings
    )


def test_check_generated_index_requires_row_metadata(tmp_path: Path) -> None:
    module = load_health_module()
    index_path = tmp_path / "leaderboard.json"
    index_path.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "submission_path": "submissions/safe-agent.json",
                        "agent_name": "Safe Agent",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    errors = module.check_generated_index(index_path)

    assert "row 1: missing submission_schema_version" in errors
    assert "row 1: missing benchmark_manifest_sha256" in errors


def test_main_can_write_review_summary_file(tmp_path: Path) -> None:
    module = load_health_module()
    submissions_dir = tmp_path / "submissions"
    submissions_dir.mkdir()
    (submissions_dir / "safe-agent.json").write_text(
        json.dumps(healthy_submission()),
        encoding="utf-8",
    )
    leaderboard_json = tmp_path / "leaderboard.json"
    leaderboard_json.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "submission_schema_version": "agent-anvil.leaderboard.v1",
                        "submission_generated_by": "agent-anvil/0.2.22",
                        "benchmark_manifest_sha256": "a" * 64,
                        "benchmark_scenario_count": 1,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    summary_path = tmp_path / "submission-review.md"

    exit_code = module.main(
        [
            "--submissions-dir",
            str(submissions_dir),
            "--leaderboard-json",
            str(leaderboard_json),
            "--summary-out",
            str(summary_path),
        ]
    )

    assert exit_code == 0
    summary = summary_path.read_text(encoding="utf-8")
    assert "## Agent Anvil leaderboard health" in summary
    assert "Submissions checked: 1" in summary
    assert "Errors: 0" in summary
    assert "Warnings: 0" in summary
