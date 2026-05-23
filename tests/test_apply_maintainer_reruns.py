from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from typing import Any


def load_apply_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "apply_maintainer_reruns.py"
    spec = importlib.util.spec_from_file_location("apply_maintainer_reruns", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_index(root: Path) -> tuple[Path, Path]:
    json_path = root / "leaderboard.json"
    csv_path = root / "leaderboard.csv"
    row = {
        "rank": 1,
        "submission_path": "submissions/demo.json",
        "agent_name": "Demo Agent",
        "trust_level": "github_actions",
        "evidence_sha256": "evidence-123",
        "github_run_url": "https://github.com/acme/agent/actions/runs/1",
    }
    json_path.write_text(
        json.dumps(
            {
                "schema_version": "agent-anvil.leaderboard.index.v1",
                "rows": [row],
            }
        ),
        encoding="utf-8",
    )
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    return json_path, csv_path


def write_attestation(root: Path, **overrides: Any) -> Path:
    attestations = root / "maintainer_reruns"
    attestations.mkdir()
    payload = {
        "schema_version": "agent-anvil.maintainer-rerun.v1",
        "submission_path": "submissions/demo.json",
        "submission_evidence_sha256": "evidence-123",
        "maintainer": "agent-axiom",
        "rerun": {
            "github_run_url": "https://github.com/agent-axiom/agent-anvil/actions/runs/99",
            "github_repository": "agent-axiom/agent-anvil",
            "github_sha": "abc123",
        },
    }
    payload.update(overrides)
    path = attestations / "demo.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def successful_run(parsed: Any) -> dict[str, Any]:
    return {
        "status": "completed",
        "conclusion": "success",
        "head_sha": "abc123def",
        "repository": {"full_name": "agent-axiom/agent-anvil"},
    }


def test_apply_maintainer_rerun_promotes_json_and_csv_rows(tmp_path: Path) -> None:
    module = load_apply_module()
    leaderboard_json, leaderboard_csv = write_index(tmp_path)
    write_attestation(tmp_path)

    applied = module.apply_maintainer_reruns(
        leaderboard_json=leaderboard_json,
        leaderboard_csv=leaderboard_csv,
        reruns_dir=tmp_path / "maintainer_reruns",
        fetch_run=successful_run,
    )

    assert applied == 1
    payload = json.loads(leaderboard_json.read_text(encoding="utf-8"))
    row = payload["rows"][0]
    assert row["trust_level"] == "maintainer_rerun"
    assert row["maintainer"] == "agent-axiom"
    assert row["maintainer_rerun_url"].endswith("/actions/runs/99")
    assert row["maintainer_rerun_sha"] == "abc123"

    with leaderboard_csv.open(encoding="utf-8", newline="") as handle:
        csv_row = next(csv.DictReader(handle))
    assert csv_row["trust_level"] == "maintainer_rerun"
    assert csv_row["maintainer"] == "agent-axiom"
    assert csv_row["maintainer_rerun_sha"] == "abc123"


def test_apply_maintainer_rerun_rejects_evidence_mismatch(tmp_path: Path) -> None:
    module = load_apply_module()
    leaderboard_json, leaderboard_csv = write_index(tmp_path)
    write_attestation(tmp_path, submission_evidence_sha256="different")

    errors = module.validate_maintainer_reruns(
        leaderboard_json=leaderboard_json,
        reruns_dir=tmp_path / "maintainer_reruns",
        fetch_run=successful_run,
    )

    assert "does not match leaderboard evidence_sha256" in errors[0]


def test_apply_maintainer_rerun_noops_without_rerun_dir(tmp_path: Path) -> None:
    module = load_apply_module()
    leaderboard_json, leaderboard_csv = write_index(tmp_path)

    applied = module.apply_maintainer_reruns(
        leaderboard_json=leaderboard_json,
        leaderboard_csv=leaderboard_csv,
        reruns_dir=tmp_path / "maintainer_reruns",
        fetch_run=successful_run,
    )

    assert applied == 0
