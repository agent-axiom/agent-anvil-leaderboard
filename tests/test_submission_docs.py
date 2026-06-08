from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENT_ANVIL_RELEASE_REF = "git+https://github.com/agent-axiom/agent-anvil@v0.2.40"


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
    assert "id-token: write" in workflow
    assert "attestations: write" in workflow
    assert "actions/attest@v4" in workflow
    assert "subject-path: leaderboard_submission.json" in workflow
    assert "actions/upload-artifact@v7" in workflow
    assert "submission/" in workflow
    assert "uv sync --group dev" not in workflow


def test_github_actions_auto_pr_example_is_copy_pasteable() -> None:
    workflow = (ROOT / "examples" / "github-actions-auto-pr.yml").read_text(
        encoding="utf-8"
    )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

    assert "examples/github-actions-auto-pr.yml" in readme
    assert "examples/github-actions-auto-pr.yml" in contributing
    assert AGENT_ANVIL_RELEASE_REF in workflow
    assert "LEADERBOARD_PR_TOKEN" in workflow
    assert "repository: agent-axiom/agent-anvil-leaderboard" in workflow
    assert "path: leaderboard-repo" in workflow
    assert "token: ${{ secrets.LEADERBOARD_PR_TOKEN }}" in workflow
    assert "anvil leaderboard pr leaderboard_submission.json" in workflow
    assert "--pr-body-out agent-anvil-leaderboard-pr.md" in workflow
    assert "git push --set-upstream origin" in workflow
    assert "gh pr create" in workflow
    assert "GH_TOKEN: ${{ secrets.LEADERBOARD_PR_TOKEN }}" in workflow
    assert "does not run arbitrary agents" in readme


def test_public_workflows_pin_agent_anvil_release() -> None:
    paths = (
        ROOT / ".github" / "workflows" / "leaderboard.yml",
        ROOT / ".github" / "workflows" / "maintainer-rerun.yml",
        ROOT / "README.md",
        ROOT / "examples" / "github-actions-submission.yml",
        ROOT / "examples" / "github-actions-auto-pr.yml",
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
            "https://github.com/agent-axiom/agent-anvil-demo-agent/actions/runs/26656805979"
            in text
        )
        assert "https://github.com/agent-axiom/agent-anvil-leaderboard/pull/18" in text


def test_space_invites_verified_submissions() -> None:
    app = (ROOT / "space" / "app.py").read_text(encoding="utf-8")
    readme = (ROOT / "space" / "README.md").read_text(encoding="utf-8")

    for text in (app, readme):
        assert "Submit your agent" in text
        assert "agent-axiom/agent-anvil-demo-agent" in text
        assert "agent-anvil-leaderboard/pull/18" in text
        assert "self_reported" in text
        assert "github_actions" in text
        assert "maintainer_rerun" in text
        assert "filter" in text.lower()
        assert "sort" in text.lower()
        assert "freshness" in text.lower()
        assert "stale" in text.lower()
        assert "health" in text.lower()
        assert "benchmark" in text.lower()


def test_leaderboard_workflow_runs_submission_health_checks() -> None:
    workflow = (ROOT / ".github" / "workflows" / "leaderboard.yml").read_text(
        encoding="utf-8"
    )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "scripts/check_submission_health.py" in workflow
    assert "Check submission health" in workflow
    assert "--summary-out agent-anvil-submission-review.md" in workflow
    assert "<!-- agent-anvil-leaderboard-review -->" in workflow
    assert "actions/github-script" in workflow
    assert "Fail on submission health errors" in workflow
    assert "Fail on GitHub Actions evidence errors" in workflow
    assert "python3 scripts/check_submission_health.py" in readme
    assert "sticky PR comment" in readme
    assert "scripts/verify_attestations.py" in workflow
    assert "Artifact attestation warnings" in readme
    assert "anvil leaderboard audit submissions" in workflow
    assert "--json-out leaderboard_audit.json" in workflow
    assert "--markdown-out agent-anvil-leaderboard-audit.md" in workflow
    assert "--fail-on reject" in workflow
    assert "--fail-on reject" in readme
    assert "agent-anvil-leaderboard-audit.md" in workflow
    assert "leaderboard_audit.json" in workflow
    assert "if: always()" in workflow
    assert "steps.leaderboard-audit.outputs.exit_code" in workflow
    assert "Leaderboard audit" in readme
    assert "gh attestation verify" in readme
    assert "--strict-new-submissions-from" in workflow
    assert "agent-anvil-attestation-review.md" in workflow
    assert "provenance_status" in readme
    assert "New `github_actions` rows without attestations fail CI" in readme


def test_docs_explain_reproduction_script_flow() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    template = (ROOT / ".github" / "pull_request_template.md").read_text(
        encoding="utf-8"
    )

    assert "anvil leaderboard reproduce submissions/<agent-name>.json" in readme
    assert "reproduce_leaderboard_submission.sh" in readme
    assert "maintainer rerun" in readme
    assert "leaderboard reproduce" in template
