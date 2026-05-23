from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest


def load_verify_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "verify_github_runs.py"
    spec = importlib.util.spec_from_file_location("verify_github_runs", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def github_actions_submission(**verification_overrides: Any) -> dict[str, Any]:
    verification = {
        "trust_level": "github_actions",
        "github_repository": "agent-axiom/agent-anvil",
        "github_sha": "abc123",
        "github_run_url": "https://github.com/agent-axiom/agent-anvil/actions/runs/12345",
    }
    verification.update(verification_overrides)
    return {
        "schema_version": "agent-anvil.leaderboard.v1",
        "submitter": {"agent_name": "Demo", "commit_sha": "abc123"},
        "verification": verification,
    }


def test_parse_github_run_url() -> None:
    module = load_verify_module()

    parsed = module.parse_github_run_url(
        "https://github.com/agent-axiom/agent-anvil/actions/runs/12345"
    )

    assert parsed.owner == "agent-axiom"
    assert parsed.repo == "agent-anvil"
    assert parsed.run_id == "12345"


def test_parse_github_run_url_rejects_non_run_url() -> None:
    module = load_verify_module()

    with pytest.raises(ValueError, match="GitHub Actions run URL"):
        module.parse_github_run_url("https://github.com/agent-axiom/agent-anvil")


def test_verify_submission_accepts_successful_matching_run() -> None:
    module = load_verify_module()
    submission = github_actions_submission()

    errors = module.verify_submission(
        path=Path("submissions/demo.json"),
        submission=submission,
        fetch_run=lambda parsed: {
            "status": "completed",
            "conclusion": "success",
            "head_sha": "abc123def456",
            "repository": {"full_name": "agent-axiom/agent-anvil"},
        },
    )

    assert errors == []


def test_verify_submission_rejects_failed_run() -> None:
    module = load_verify_module()
    submission = github_actions_submission()

    errors = module.verify_submission(
        path=Path("submissions/demo.json"),
        submission=submission,
        fetch_run=lambda parsed: {
            "status": "completed",
            "conclusion": "failure",
            "head_sha": "abc123def456",
            "repository": {"full_name": "agent-axiom/agent-anvil"},
        },
    )

    assert "run conclusion is failure" in errors[0]


def test_verify_submission_requires_repository_and_sha_metadata() -> None:
    module = load_verify_module()
    submission = github_actions_submission(github_repository="", github_sha="")

    errors = module.verify_submission(
        path=Path("submissions/demo.json"),
        submission=submission,
        fetch_run=lambda parsed: {
            "status": "completed",
            "conclusion": "success",
            "head_sha": "abc123def456",
            "repository": {"full_name": "agent-axiom/agent-anvil"},
        },
    )

    assert "requires verification.github_repository" in errors
    assert "requires verification.github_sha" in errors


def test_verify_submission_rejects_sha_mismatch() -> None:
    module = load_verify_module()
    submission = github_actions_submission(github_sha="abc123")

    errors = module.verify_submission(
        path=Path("submissions/demo.json"),
        submission=submission,
        fetch_run=lambda parsed: {
            "status": "completed",
            "conclusion": "success",
            "head_sha": "fffff",
            "repository": {"full_name": "agent-axiom/agent-anvil"},
        },
    )

    assert "github_sha does not match run head_sha" in errors[0]


def test_verify_all_submissions_ignores_self_reported_rows(tmp_path: Path) -> None:
    module = load_verify_module()
    submissions = tmp_path / "submissions"
    submissions.mkdir()
    (submissions / "README.md").write_text("# docs\n", encoding="utf-8")
    (submissions / "self.json").write_text(
        json.dumps({"verification": {"trust_level": "self_reported"}}),
        encoding="utf-8",
    )

    errors = module.verify_all_submissions(
        submissions_dir=submissions,
        fetch_run=lambda parsed: (_ for _ in ()).throw(AssertionError("network call")),
    )

    assert errors == []
