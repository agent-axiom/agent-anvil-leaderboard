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
    warning: str


def verify_submission(
    *,
    path: Path,
    submission: dict[str, Any],
    run_command: RunCommand,
) -> list[AttestationReport]:
    verification = submission.get("verification")
    if not isinstance(verification, dict):
        return []
    if verification.get("trust_level") != "github_actions":
        return []

    repository = str(verification.get("github_repository") or "").strip()
    if not repository:
        return [
            AttestationReport(
                path=path,
                repository="",
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
                warning="gh CLI is not available; could not verify artifact attestation",
            )
        ]

    if completed.returncode == 0:
        return []

    detail = (completed.stderr or completed.stdout or "").strip()
    suffix = f": {detail}" if detail else ""
    return [
        AttestationReport(
            path=path,
            repository=repository,
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
                    warning=f"invalid JSON; skipped attestation verification: {exc}",
                )
            )
            continue
        if not isinstance(payload, dict):
            reports.append(
                AttestationReport(
                    path=path,
                    repository="",
                    warning="expected JSON object; skipped attestation verification",
                )
            )
            continue
        reports.extend(
            verify_submission(path=path, submission=payload, run_command=run_command)
        )
    return reports


def render_markdown_summary(reports: list[AttestationReport]) -> str:
    lines = [
        "## Artifact attestation warnings",
        "",
        f"Warnings: {len(reports)}",
    ]
    if reports:
        lines.extend(["", "| File | Repository | Warning |", "| --- | --- | --- |"])
        for report in reports:
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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, *, run_command: RunCommand | None = None) -> int:
    args = parse_args(argv)
    runner = run_command or _run_command
    reports = verify_all_submissions(
        submissions_dir=args.submissions_dir,
        run_command=runner,
    )
    summary = render_markdown_summary(reports)
    _write_step_summary(summary)

    for report in reports:
        print(f"::warning file={report.path}::{report.warning}", file=sys.stderr)

    if reports and args.strict:
        return 1
    print("Artifact attestation verification completed")
    return 0


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
