from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any


def load_verify_module():
    module_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "verify_attestations.py"
    )
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
        args=["gh", "attestation", "verify"],
        returncode=returncode,
        stdout="",
        stderr="boom",
    )


def test_verify_all_submissions_labels_self_reported_rows_without_network(
    tmp_path: Path,
) -> None:
    module = load_verify_module()
    submissions = tmp_path / "submissions"
    submissions.mkdir()
    write_submission(
        submissions / "self.json",
        {"verification": {"trust_level": "self_reported"}},
    )

    results = module.verify_all_submissions(
        submissions_dir=submissions,
        run_command=lambda command: (_ for _ in ()).throw(AssertionError(command)),
    )

    assert len(results) == 1
    assert results[0].status == "self_reported"
    assert results[0].warning == ""


def test_verify_all_submissions_invokes_gh_for_github_actions_rows(
    tmp_path: Path,
) -> None:
    module = load_verify_module()
    submissions = tmp_path / "submissions"
    submissions.mkdir()
    submission_path = submissions / "demo.json"
    write_submission(submission_path, github_actions_submission())
    seen: list[list[str]] = []

    results = module.verify_all_submissions(
        submissions_dir=submissions,
        run_command=lambda command: seen.append(command) or completed(),
    )

    assert len(results) == 1
    assert results[0].status == "attested"
    assert results[0].warning == ""
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


def test_main_updates_leaderboard_json_with_provenance_status(tmp_path: Path) -> None:
    module = load_verify_module()
    submissions = tmp_path / "submissions"
    submissions.mkdir()
    submission_path = submissions / "demo.json"
    write_submission(submission_path, github_actions_submission())
    leaderboard_json = tmp_path / "leaderboard.json"
    leaderboard_json.write_text(
        json.dumps(
            {
                "schema_version": "agent-anvil.leaderboard.index.v1",
                "rows": [
                    {
                        "submission_path": str(submission_path),
                        "trust_level": "github_actions",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    exit_code = module.main(
        [
            "--submissions-dir",
            str(submissions),
            "--leaderboard-json",
            str(leaderboard_json),
        ],
        run_command=lambda command: completed(),
    )

    assert exit_code == 0
    payload = json.loads(leaderboard_json.read_text(encoding="utf-8"))
    assert payload["rows"][0]["provenance_status"] == "attested"
    assert payload["rows"][0]["provenance_badge"] == "[attested]"


def test_main_updates_leaderboard_csv_with_provenance_status(tmp_path: Path) -> None:
    module = load_verify_module()
    submissions = tmp_path / "submissions"
    submissions.mkdir()
    submission_path = submissions / "demo.json"
    write_submission(submission_path, github_actions_submission())
    leaderboard_csv = tmp_path / "leaderboard.csv"
    leaderboard_csv.write_text(
        f"rank,submission_path,trust_level\n1,{submission_path},github_actions\n",
        encoding="utf-8",
    )

    exit_code = module.main(
        [
            "--submissions-dir",
            str(submissions),
            "--leaderboard-csv",
            str(leaderboard_csv),
        ],
        run_command=lambda command: completed(),
    )

    assert exit_code == 0
    csv_text = leaderboard_csv.read_text(encoding="utf-8")
    assert "provenance_status,provenance_badge,provenance_warning" in csv_text
    assert "attested,[attested]," in csv_text


def test_strict_new_submission_policy_only_fails_new_github_actions_rows(
    tmp_path: Path, capsys
) -> None:
    module = load_verify_module()
    submissions = tmp_path / "submissions"
    submissions.mkdir()
    old_path = submissions / "old.json"
    new_path = submissions / "new.json"
    write_submission(old_path, github_actions_submission())
    write_submission(
        new_path, github_actions_submission(github_repository="acme/new-agent")
    )

    exit_code = module.main(
        [
            "--submissions-dir",
            str(submissions),
            "--strict-new-submission",
            str(new_path),
        ],
        run_command=lambda command: completed(returncode=1),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"::error file={new_path}" in captured.err
    assert f"::error file={old_path}" not in captured.err
    assert f"::warning file={old_path}" in captured.err


def test_attestation_summary_lists_provenance_metadata() -> None:
    module = load_verify_module()
    report = module.AttestationReport(
        path=Path("submissions/demo.json"),
        repository="agent-axiom/agent-anvil-demo-agent",
        trust_level="github_actions",
        github_run_url="https://github.com/agent-axiom/agent-anvil-demo-agent/actions/runs/1",
        github_sha="abc123",
        status="attested",
        warning="",
    )

    summary = module.render_markdown_summary([report])

    assert "GitHub evidence is checked by `scripts/verify_github_runs.py`" in summary
    assert "agent-axiom/agent-anvil-demo-agent" in summary
    assert "abc123" in summary
    assert "[attested]" in summary
