from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any


def load_verify_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "verify_attestations.py"
    spec = importlib.util.spec_from_file_location("verify_attestations", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def github_actions_submission(**verification_overrides: Any) -> dict[str, Any]:
    verification = {
        "trust_level": "github_actions",
        "github_repository": "agent-axiom/agent-anvil-demo-agent",
        "github_sha": "abc123",
        "github_run_url": (
            "https://github.com/agent-axiom/agent-anvil-demo-agent/actions/runs/12345"
        ),
    }
    verification.update(verification_overrides)
    return {
        "schema_version": "agent-anvil.leaderboard.v1",
        "submitter": {"agent_name": "Demo", "commit_sha": "abc123"},
        "verification": verification,
    }


def write_submission(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def completed(returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["gh", "attestation", "verify"], returncode=returncode, stdout="", stderr="boom"
    )


def test_verify_all_submissions_ignores_self_reported_rows(tmp_path: Path) -> None:
    module = load_verify_module()
    submissions = tmp_path / "submissions"
    submissions.mkdir()
    write_submission(
        submissions / "self.json",
        {"verification": {"trust_level": "self_reported"}},
    )

    reports = module.verify_all_submissions(
        submissions_dir=submissions,
        run_command=lambda command: (_ for _ in ()).throw(AssertionError(command)),
    )

    assert reports == []


def test_verify_all_submissions_invokes_gh_for_github_actions_rows(tmp_path: Path) -> None:
    module = load_verify_module()
    submissions = tmp_path / "submissions"
    submissions.mkdir()
    submission_path = submissions / "demo.json"
    write_submission(submission_path, github_actions_submission())
    seen: list[list[str]] = []

    reports = module.verify_all_submissions(
        submissions_dir=submissions,
        run_command=lambda command: seen.append(command) or completed(),
    )

    assert reports == []
    assert seen == [
        [
            "gh",
            "attestation",
            "verify",
            str(submission_path),
            "-R",
            "agent-axiom/agent-anvil-demo-agent",
        ]
    ]


def test_main_warns_but_passes_by_default_when_attestation_is_missing(
    tmp_path: Path, capsys
) -> None:
    module = load_verify_module()
    submissions = tmp_path / "submissions"
    submissions.mkdir()
    write_submission(submissions / "demo.json", github_actions_submission())

    exit_code = module.main(
        ["--submissions-dir", str(submissions)],
        run_command=lambda command: completed(returncode=1),
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "::warning" in captured.err
    assert "gh attestation verify failed" in captured.err


def test_main_fails_in_strict_mode_when_attestation_is_missing(tmp_path: Path) -> None:
    module = load_verify_module()
    submissions = tmp_path / "submissions"
    submissions.mkdir()
    write_submission(submissions / "demo.json", github_actions_submission())

    exit_code = module.main(
        ["--submissions-dir", str(submissions), "--strict"],
        run_command=lambda command: completed(returncode=1),
    )

    assert exit_code == 1
