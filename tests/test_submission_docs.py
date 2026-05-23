from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pr_template_contains_submission_checklist() -> None:
    template = ROOT / ".github" / "pull_request_template.md"

    text = template.read_text(encoding="utf-8")

    assert "Leaderboard Submission Checklist" in text
    assert "anvil leaderboard validate" in text
    assert "raw traces" in text
    assert "github_actions" in text
    assert "HF Space" in text


def test_contributing_guide_explains_submission_flow() -> None:
    text = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

    assert "How To Submit" in text
    assert "leaderboard_submission.json" in text
    assert "submissions/<agent-name>.json" in text
    assert "No Raw Traces" in text
    assert "Trust Levels" in text
    assert "Maintainer Reruns" in text


def test_submissions_readme_documents_file_contract() -> None:
    text = (ROOT / "submissions" / "README.md").read_text(encoding="utf-8")

    assert "one JSON file per agent result" in text
    assert "Do not edit leaderboard.csv" in text
    assert "self_reported" in text
    assert "github_actions" in text
    assert "maintainer_rerun" in text


def test_maintainer_rerun_readme_documents_attestation_contract() -> None:
    text = (ROOT / "maintainer_reruns" / "README.md").read_text(encoding="utf-8")

    assert "agent-anvil.maintainer-rerun.v1" in text
    assert "submission_evidence_sha256" in text
    assert "rerun.github_run_url" in text
    assert "successful GitHub Actions run" in text
