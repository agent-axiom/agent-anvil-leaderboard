from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, NamedTuple


RunCommand = Callable[[list[str]], subprocess.CompletedProcess[str]]


class AttestationReport(NamedTuple):
    path: Path
    repository: str
    status: str
    warning: str

    @property
    def failed(self) -> bool:
        return bool(self.warning)


def verify_submission(
    *,
    path: Path,
    submission: dict[str, Any],
    run_command: RunCommand,
) -> list[AttestationReport]:
    verification = submission.get("verification")
    if not isinstance(verification, dict):
        return [
            AttestationReport(
                path=path,
                repository="",
                status="missing",
                warning="missing verification object; skipped attestation verification",
            )
        ]
    trust_level = str(verification.get("trust_level") or "")
    if trust_level == "self_reported":
        return [
            AttestationReport(path=path, repository="", status="self_reported", warning="")
        ]
    if trust_level == "maintainer_rerun":
        return [
            AttestationReport(
                path=path, repository="", status="maintainer_rerun", warning=""
            )
        ]
    if trust_level != "github_actions":
        return [
            AttestationReport(
                path=path,
                repository="",
                status="missing",
                warning=f"unsupported trust level {trust_level!r}; skipped attestation verification",
            )
        ]

    repository = str(verification.get("github_repository") or "").strip()
    if not repository:
        return [
            AttestationReport(
                path=path,
                repository="",
                status="missing",
                warning="github_actions row is missing verification.github_repository",
            )
        ]

    command = ["gh", "attestation", "verify", str(path), "-R", repository]
    try:
        completed = run_command(command)
    except FileNotFoundError:
        return [
            AttestationReport(
                path=path,
                repository=repository,
                status="missing",
                warning="gh CLI is not available; could not verify artifact attestation",
            )
        ]

    if completed.returncode == 0:
        return [
            AttestationReport(
                path=path, repository=repository, status="attested", warning=""
            )
        ]

    detail = (completed.stderr or completed.stdout or "").strip()
    suffix = f": {detail}" if detail else ""
    return [
        AttestationReport(
            path=path,
            repository=repository,
            status="missing",
            warning=f"gh attestation verify failed for {repository}{suffix}",
        )
    ]


def verify_all_submissions(
    *,
    submissions_dir: Path,
    run_command: RunCommand,
) -> list[AttestationReport]:
    reports: list[AttestationReport] = []
    for path in sorted(submissions_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            reports.append(
                AttestationReport(
                    path=path,
                    repository="",
                    status="missing",
                    warning=f"invalid JSON; skipped attestation verification: {exc}",
                )
            )
            continue
        if not isinstance(payload, dict):
            reports.append(
                AttestationReport(
                    path=path,
                    repository="",
                    status="missing",
                    warning="expected JSON object; skipped attestation verification",
                )
            )
            continue
        reports.extend(
            verify_submission(path=path, submission=payload, run_command=run_command)
        )
    return reports


def render_markdown_summary(reports: list[AttestationReport]) -> str:
    warning_count = sum(1 for report in reports if report.failed)
    attested_count = sum(1 for report in reports if report.status == "attested")
    lines = [
        "## Artifact attestation warnings",
        "",
        f"Checked rows: {len(reports)}",
        f"Attested rows: {attested_count}",
        f"Warnings: {warning_count}",
    ]
    warnings = [report for report in reports if report.failed]
    if warnings:
        lines.extend(["", "| File | Repository | Warning |", "| --- | --- | --- |"])
        for report in warnings:
            repository = report.repository or "-"
            lines.append(f"| `{report.path}` | `{repository}` | {report.warning} |")
    else:
        lines.append("")
        lines.append("All checked GitHub Actions submissions had verifiable attestations.")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify GitHub artifact attestations for Agent Anvil leaderboard rows."
    )
    parser.add_argument("--submissions-dir", type=Path, default=Path("submissions"))
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when a github_actions submission has no verifiable attestation.",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Accepted for readability; warn-only is the default.",
    )
    parser.add_argument(
        "--leaderboard-json",
        type=Path,
        default=Path("leaderboard.json"),
        help="Annotate this leaderboard JSON index with provenance status when it exists.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, *, run_command: RunCommand | None = None) -> int:
    args = parse_args(argv)
    runner = run_command or _run_command
    reports = verify_all_submissions(
        submissions_dir=args.submissions_dir,
        run_command=runner,
    )
    if args.leaderboard_json.exists():
        annotate_leaderboard_json(args.leaderboard_json, reports)
    summary = render_markdown_summary(reports)
    _write_step_summary(summary)

    for report in reports:
        if report.failed:
            print(f"::warning file={report.path}::{report.warning}", file=sys.stderr)

    if any(report.failed for report in reports) and args.strict:
        return 1
    print("Artifact attestation verification completed")
    return 0


def annotate_leaderboard_json(
    leaderboard_json: Path, reports: list[AttestationReport]
) -> None:
    try:
        payload = json.loads(leaderboard_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    if not isinstance(payload, dict):
        return
    rows = payload.get("rows")
    if not isinstance(rows, list):
        return

    by_path = {_normalize_path(report.path): report for report in reports}
    for row in rows:
        if not isinstance(row, dict):
            continue
        report = by_path.get(_normalize_path(Path(str(row.get("submission_path") or ""))))
        if report is None:
            report = _default_report_for_row(row)
        row["provenance_status"] = report.status
        row["provenance_badge"] = _provenance_badge(report.status)
        if report.warning:
            row["provenance_warning"] = report.warning
        else:
            row.pop("provenance_warning", None)
    leaderboard_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _default_report_for_row(row: dict[str, Any]) -> AttestationReport:
    trust_level = str(row.get("trust_level") or "")
    status = {
        "self_reported": "self_reported",
        "maintainer_rerun": "maintainer_rerun",
        "github_actions": "missing",
    }.get(trust_level, "missing")
    warning = (
        "github_actions row has no local submission file for attestation verification"
        if trust_level == "github_actions"
        else ""
    )
    return AttestationReport(
        path=Path(str(row.get("submission_path") or "")),
        repository="",
        status=status,
        warning=warning,
    )


def _provenance_badge(status: str) -> str:
    return {
        "attested": "[attested]",
        "missing": "[missing attestation]",
        "self_reported": "[self-reported]",
        "maintainer_rerun": "[maintainer rerun]",
    }.get(status, "[unknown provenance]")


def _normalize_path(path: Path) -> str:
    return path.as_posix().lstrip("./")


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )


def _write_step_summary(summary: str) -> None:
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with Path(summary_path).open("a", encoding="utf-8") as file:
        file.write(summary)
        file.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
