from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable


FetchRun = Callable[[Any], dict[str, Any]]
EXTRA_COLUMNS = [
    "maintainer",
    "maintainer_rerun_url",
    "maintainer_rerun_repository",
    "maintainer_rerun_sha",
]


def load_github_verifier() -> Any:
    module_path = Path(__file__).with_name("verify_github_runs.py")
    spec = importlib.util.spec_from_file_location("verify_github_runs", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_maintainer_reruns(
    *,
    leaderboard_json: Path,
    reruns_dir: Path,
    fetch_run: FetchRun,
) -> list[str]:
    if not reruns_dir.exists():
        return []

    verifier = load_github_verifier()
    index = _read_json_object(leaderboard_json)
    rows_by_submission = _rows_by_submission(index)
    errors: list[str] = []

    for path in sorted(reruns_dir.glob("*.json")):
        attestation = _read_json_object(path)
        errors.extend(
            _validate_attestation(
                path=path,
                attestation=attestation,
                rows_by_submission=rows_by_submission,
                verifier=verifier,
                fetch_run=fetch_run,
            )
        )
    return errors


def apply_maintainer_reruns(
    *,
    leaderboard_json: Path,
    leaderboard_csv: Path,
    reruns_dir: Path,
    fetch_run: FetchRun,
) -> int:
    errors = validate_maintainer_reruns(
        leaderboard_json=leaderboard_json,
        reruns_dir=reruns_dir,
        fetch_run=fetch_run,
    )
    if errors:
        raise ValueError("\n".join(errors))
    if not reruns_dir.exists():
        return 0

    index = _read_json_object(leaderboard_json)
    rows_by_submission = _rows_by_submission(index)
    applied = 0

    for path in sorted(reruns_dir.glob("*.json")):
        attestation = _read_json_object(path)
        submission_path = str(attestation["submission_path"])
        row = rows_by_submission[submission_path]
        rerun = attestation["rerun"]
        row["trust_level"] = "maintainer_rerun"
        row["maintainer"] = str(attestation["maintainer"])
        row["maintainer_rerun_url"] = str(rerun["github_run_url"])
        row["maintainer_rerun_repository"] = str(rerun["github_repository"])
        row["maintainer_rerun_sha"] = str(rerun["github_sha"])
        applied += 1

    _write_json(leaderboard_json, index)
    _apply_csv_overlay(leaderboard_csv=leaderboard_csv, rows_by_submission=rows_by_submission)
    return applied


def _validate_attestation(
    *,
    path: Path,
    attestation: dict[str, Any],
    rows_by_submission: dict[str, dict[str, Any]],
    verifier: Any,
    fetch_run: FetchRun,
) -> list[str]:
    errors: list[str] = []
    if attestation.get("schema_version") != "agent-anvil.maintainer-rerun.v1":
        errors.append(f"{path}: schema_version must be agent-anvil.maintainer-rerun.v1")

    submission_path = str(attestation.get("submission_path") or "")
    if not submission_path:
        errors.append(f"{path}: submission_path is required")
        return errors
    row = rows_by_submission.get(submission_path)
    if row is None:
        errors.append(f"{path}: submission_path {submission_path!r} not found in leaderboard")
        return errors

    expected_evidence = str(attestation.get("submission_evidence_sha256") or "")
    row_evidence = str(row.get("evidence_sha256") or "")
    if not expected_evidence:
        errors.append(f"{path}: submission_evidence_sha256 is required")
    elif expected_evidence != row_evidence:
        errors.append(
            f"{path}: submission_evidence_sha256 does not match leaderboard evidence_sha256"
        )

    maintainer = str(attestation.get("maintainer") or "").strip()
    if not maintainer:
        errors.append(f"{path}: maintainer is required")

    rerun = attestation.get("rerun")
    if not isinstance(rerun, dict):
        errors.append(f"{path}: rerun object is required")
        return errors

    errors.extend(
        verifier.verify_submission(
            path=path,
            submission={
                "verification": {
                    "trust_level": "github_actions",
                    "github_run_url": rerun.get("github_run_url", ""),
                    "github_repository": rerun.get("github_repository", ""),
                    "github_sha": rerun.get("github_sha", ""),
                }
            },
            fetch_run=fetch_run,
        )
    )
    return errors


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected JSON object")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _rows_by_submission(index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = index.get("rows")
    if not isinstance(rows, list):
        raise ValueError("leaderboard JSON must contain a rows array")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("submission_path"), str):
            result[row["submission_path"]] = row
    return result


def _apply_csv_overlay(
    *,
    leaderboard_csv: Path,
    rows_by_submission: dict[str, dict[str, Any]],
) -> None:
    with leaderboard_csv.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        csv_rows = list(reader)

    for column in EXTRA_COLUMNS:
        if column not in fieldnames:
            fieldnames.append(column)

    for csv_row in csv_rows:
        submission_path = csv_row.get("submission_path", "")
        overlay = rows_by_submission.get(submission_path)
        if overlay is None:
            continue
        csv_row.update({key: _csv_value(overlay.get(key, "")) for key in fieldnames})

    with leaderboard_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)


def _csv_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return "" if value is None else str(value)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply maintainer rerun attestations to Agent Anvil leaderboard indexes."
    )
    parser.add_argument("--leaderboard-json", type=Path, default=Path("leaderboard.json"))
    parser.add_argument("--leaderboard-csv", type=Path, default=Path("leaderboard.csv"))
    parser.add_argument("--reruns-dir", type=Path, default=Path("maintainer_reruns"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    verifier = load_github_verifier()
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")

    try:
        applied = apply_maintainer_reruns(
            leaderboard_json=args.leaderboard_json,
            leaderboard_csv=args.leaderboard_csv,
            reruns_dir=args.reruns_dir,
            fetch_run=lambda parsed: verifier.fetch_github_run(parsed, token=token),
        )
    except ValueError as exc:
        for line in str(exc).splitlines():
            print(f"::error::{line}", file=sys.stderr)
        return 1

    print(f"Applied maintainer reruns: {applied}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
