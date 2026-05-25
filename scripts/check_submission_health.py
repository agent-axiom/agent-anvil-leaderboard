from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, NamedTuple


SCHEMA_VERSION = "agent-anvil.leaderboard.v1"
MIN_RECOMMENDED_TRIALS = 100
SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")


class HealthReport(NamedTuple):
    path: Path
    errors: list[str]
    warnings: list[str]


def check_submission_health(path: Path, submission: dict[str, Any]) -> HealthReport:
    errors: list[str] = []
    warnings: list[str] = []

    if submission.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")

    benchmark = _object(submission.get("benchmark"))
    manifest_hash = str(benchmark.get("manifest_sha256") or "")
    if not SHA256_RE.fullmatch(manifest_hash):
        errors.append(
            "benchmark.manifest_sha256 must be a 64-character sha256 hex digest"
        )
    scenario_hashes = benchmark.get("scenario_hashes")
    if not isinstance(scenario_hashes, dict) or not scenario_hashes:
        errors.append("benchmark.scenario_hashes must not be empty")
    else:
        for scenario_path, scenario_hash in scenario_hashes.items():
            if not SHA256_RE.fullmatch(str(scenario_hash)):
                errors.append(
                    f"benchmark.scenario_hashes[{scenario_path!r}] must be sha256 hex"
                )

    metrics = _object(submission.get("metrics"))
    total_trials = _int_or_default(metrics.get("total_trials"), 0)
    if total_trials <= 0:
        errors.append("metrics.total_trials must be positive")
    elif total_trials < MIN_RECOMMENDED_TRIALS:
        warnings.append(
            f"metrics.total_trials is below the recommended minimum of {MIN_RECOMMENDED_TRIALS}"
        )

    verification = _object(submission.get("verification"))
    trust_level = str(verification.get("trust_level") or "")
    if trust_level == "self_reported":
        warnings.append(
            "self_reported rows are accepted but should be treated as unverified"
        )
    elif trust_level == "github_actions":
        for field in ("github_run_url", "github_repository", "github_sha"):
            if not str(verification.get(field) or "").strip():
                errors.append(f"github_actions requires verification.{field}")
    elif trust_level != "maintainer_rerun":
        errors.append(
            "verification.trust_level must be self_reported, github_actions, or maintainer_rerun"
        )

    generated_at = str(verification.get("generated_at") or "")
    if not _is_iso_datetime(generated_at):
        errors.append("verification.generated_at must be an ISO-8601 datetime")
    if not str(verification.get("generated_by") or "").startswith("agent-anvil/"):
        warnings.append("verification.generated_by should start with agent-anvil/")

    return HealthReport(path=path, errors=errors, warnings=warnings)


def check_generated_index(index_path: Path) -> list[str]:
    payload = _read_json(index_path)
    rows = payload.get("rows")
    if not isinstance(rows, list):
        return ["leaderboard index must contain a rows array"]

    errors: list[str] = []
    required_fields = (
        "submission_schema_version",
        "submission_generated_by",
        "benchmark_manifest_sha256",
        "benchmark_scenario_count",
    )
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            errors.append(f"row {index}: expected object")
            continue
        for field in required_fields:
            if not row.get(field):
                errors.append(f"row {index}: missing {field}")
    return errors


def check_all_submissions(submissions_dir: Path) -> list[HealthReport]:
    reports: list[HealthReport] = []
    for path in sorted(submissions_dir.glob("*.json")):
        try:
            submission = _read_json(path)
        except ValueError as exc:
            reports.append(HealthReport(path=path, errors=[str(exc)], warnings=[]))
            continue
        reports.append(check_submission_health(path, submission))
    return reports


def render_markdown_summary(
    reports: list[HealthReport], index_errors: list[str]
) -> str:
    error_count = sum(len(report.errors) for report in reports) + len(index_errors)
    warning_count = sum(len(report.warnings) for report in reports)
    lines = [
        "## Agent Anvil leaderboard health",
        "",
        f"Submissions checked: {len(reports)}",
        f"Errors: {error_count}",
        f"Warnings: {warning_count}",
    ]
    if error_count or warning_count:
        lines.extend(["", "| File | Severity | Message |", "| --- | --- | --- |"])
        for report in reports:
            for error in report.errors:
                lines.append(f"| `{report.path}` | error | {error} |")
            for warning in report.warnings:
                lines.append(f"| `{report.path}` | warning | {warning} |")
        for error in index_errors:
            lines.append(f"| `leaderboard.json` | error | {error} |")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Agent Anvil leaderboard submission health."
    )
    parser.add_argument("--submissions-dir", type=Path, default=Path("submissions"))
    parser.add_argument(
        "--leaderboard-json", type=Path, default=Path("leaderboard.json")
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    reports = check_all_submissions(args.submissions_dir)
    index_errors = (
        check_generated_index(args.leaderboard_json)
        if args.leaderboard_json.exists()
        else []
    )
    summary = render_markdown_summary(reports, index_errors)
    _write_step_summary(summary)

    for report in reports:
        for error in report.errors:
            print(f"::error file={report.path}::{error}", file=sys.stderr)
        for warning in report.warnings:
            print(f"::warning file={report.path}::{warning}", file=sys.stderr)
    for error in index_errors:
        print(f"::error file={args.leaderboard_json}::{error}", file=sys.stderr)

    has_errors = any(report.errors for report in reports) or bool(index_errors)
    if has_errors:
        return 1
    print("Leaderboard submission health checks passed")
    return 0


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("expected JSON object")
    return payload


def _object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _int_or_default(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _is_iso_datetime(value: str) -> bool:
    if not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _write_step_summary(summary: str) -> None:
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with Path(summary_path).open("a", encoding="utf-8") as file:
        file.write(summary)
        file.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
