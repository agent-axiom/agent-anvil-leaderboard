from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def load_writer_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "write_maintainer_rerun.py"
    spec = importlib.util.spec_from_file_location("write_maintainer_rerun", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_write_attestation_creates_reviewable_json(tmp_path: Path) -> None:
    module = load_writer_module()

    output = module.write_attestation(
        output_dir=tmp_path,
        submission_path="submissions/acme-agent.json",
        submission_evidence_sha256="abc123",
        maintainer="agent-axiom",
        rerun_github_run_url="https://github.com/acme/agent/actions/runs/42",
        rerun_github_repository="acme/agent",
        rerun_github_sha="deadbeef",
    )

    assert output == tmp_path / "acme-agent.json"
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload == {
        "schema_version": "agent-anvil.maintainer-rerun.v1",
        "submission_path": "submissions/acme-agent.json",
        "submission_evidence_sha256": "abc123",
        "maintainer": "agent-axiom",
        "rerun": {
            "github_run_url": "https://github.com/acme/agent/actions/runs/42",
            "github_repository": "acme/agent",
            "github_sha": "deadbeef",
        },
    }


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("submission_path", "other/acme-agent.json", "must be under submissions/"),
        ("submission_path", "submissions/../secret.json", "must not contain path traversal"),
        ("submission_evidence_sha256", "", "submission_evidence_sha256 is required"),
        ("maintainer", "", "maintainer is required"),
        ("rerun_github_run_url", "https://example.com/run/42", "expected a GitHub Actions run URL"),
        ("rerun_github_repository", "acme", "expected owner/repo"),
        ("rerun_github_sha", "", "rerun_github_sha is required"),
    ],
)
def test_write_attestation_rejects_invalid_inputs(
    tmp_path: Path,
    field: str,
    value: str,
    message: str,
) -> None:
    module = load_writer_module()
    kwargs = {
        "output_dir": tmp_path,
        "submission_path": "submissions/acme-agent.json",
        "submission_evidence_sha256": "abc123",
        "maintainer": "agent-axiom",
        "rerun_github_run_url": "https://github.com/acme/agent/actions/runs/42",
        "rerun_github_repository": "acme/agent",
        "rerun_github_sha": "deadbeef",
    }
    kwargs[field] = value

    with pytest.raises(ValueError, match=message):
        module.write_attestation(**kwargs)
