from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENT_ANVIL_RELEASE_REF = "git+https://github.com/agent-axiom/agent-anvil@v0.2.19"


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
    workflow = (ROOT / ".github" / "workflows" / "maintainer-rerun.yml").read_text(
        encoding="utf-8"
    )

    assert "agent-anvil.maintainer-rerun.v1" in text
    assert "submission_evidence_sha256" in text
    assert "rerun.github_run_url" in text
    assert "successful GitHub Actions run" in text
    assert "workflow_dispatch" in workflow
    assert "submission_path" in workflow
    assert "scripts/write_maintainer_rerun.py" in workflow
    assert "actions/upload-artifact@v7" in workflow
    assert "maintainer-rerun-attestation" in workflow


def test_github_actions_submission_example_is_copy_pasteable() -> None:
    workflow = (ROOT / "examples" / "github-actions-submission.yml").read_text(
        encoding="utf-8"
    )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "examples/github-actions-submission.yml" in readme
    assert "uvx --from git+https://github.com/agent-axiom/agent-anvil" in workflow
    assert "--require-trust github_actions" in workflow
    assert "PYTHONPATH: ${{ github.workspace }}" in workflow
    assert "GITHUB_STEP_SUMMARY" in workflow
    assert "actions/upload-artifact@v7" in workflow
    assert "submission/" in workflow
    assert "uv sync --group dev" not in workflow


def test_public_workflows_pin_agent_anvil_release() -> None:
    paths = (
        ROOT / ".github" / "workflows" / "leaderboard.yml",
        ROOT / "README.md",
        ROOT / "examples" / "github-actions-submission.yml",
    )

    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert AGENT_ANVIL_RELEASE_REF in text
        assert "git+https://github.com/agent-axiom/agent-anvil \\" not in text


def test_readme_links_verified_end_to_end_demo() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

    for text in (readme, contributing):
        assert "https://github.com/agent-axiom/agent-anvil-demo-agent" in text
        assert (
            "https://github.com/agent-axiom/agent-anvil-demo-agent/actions/runs/26336840349"
            in text
        )
        assert "https://github.com/agent-axiom/agent-anvil-leaderboard/pull/5" in text


def test_space_invites_verified_submissions() -> None:
    app = (ROOT / "space" / "app.py").read_text(encoding="utf-8")
    readme = (ROOT / "space" / "README.md").read_text(encoding="utf-8")

    for text in (app, readme):
        assert "Submit your agent" in text
        assert "agent-axiom/agent-anvil-demo-agent" in text
        assert "agent-anvil-leaderboard/pull/5" in text
        assert "self_reported" in text
        assert "github_actions" in text
        assert "maintainer_rerun" in text
        assert "filter" in text.lower()
        assert "sort" in text.lower()
