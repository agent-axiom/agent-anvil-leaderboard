from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


GITHUB_RUN_URL_RE = re.compile(
    r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/actions/runs/[0-9]+/?$"
)
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def write_attestation(
    *,
    output_dir: Path,
    submission_path: str,
    submission_evidence_sha256: str,
    maintainer: str,
    rerun_github_run_url: str,
    rerun_github_repository: str,
    rerun_github_sha: str,
) -> Path:
    submission_path = _clean_submission_path(submission_path)
    submission_evidence_sha256 = _require_text(
        "submission_evidence_sha256",
        submission_evidence_sha256,
    )
    maintainer = _require_text("maintainer", maintainer)
    rerun_github_run_url = _clean_run_url(rerun_github_run_url)
    rerun_github_repository = _clean_repository(rerun_github_repository)
    rerun_github_sha = _require_text("rerun_github_sha", rerun_github_sha)

    payload: dict[str, Any] = {
        "schema_version": "agent-anvil.maintainer-rerun.v1",
        "submission_path": submission_path,
        "submission_evidence_sha256": submission_evidence_sha256,
        "maintainer": maintainer,
        "rerun": {
            "github_run_url": rerun_github_run_url,
            "github_repository": rerun_github_repository,
            "github_sha": rerun_github_sha,
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / Path(submission_path).name
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path


def _clean_submission_path(value: str) -> str:
    value = _require_text("submission_path", value)
    if "\\" in value or ".." in Path(value).parts:
        raise ValueError("submission_path must not contain path traversal")
    if not value.startswith("submissions/"):
        raise ValueError("submission_path must be under submissions/")
    if Path(value).suffix != ".json":
        raise ValueError("submission_path must point to a JSON file")
    return value


def _clean_run_url(value: str) -> str:
    value = _require_text("rerun_github_run_url", value)
    if not GITHUB_RUN_URL_RE.match(value):
        raise ValueError("expected a GitHub Actions run URL")
    return value.rstrip("/")


def _clean_repository(value: str) -> str:
    value = _require_text("rerun_github_repository", value)
    if not REPOSITORY_RE.match(value):
        raise ValueError("expected owner/repo")
    return value


def _require_text(name: str, value: str) -> str:
    value = str(value or "").strip()
    if not value:
        raise ValueError(f"{name} is required")
    return value


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write an Agent Anvil maintainer rerun attestation JSON artifact."
    )
    parser.add_argument("--output-dir", type=Path, default=Path("maintainer_reruns"))
    parser.add_argument("--submission-path", required=True)
    parser.add_argument("--submission-evidence-sha256", required=True)
    parser.add_argument("--maintainer", required=True)
    parser.add_argument("--rerun-github-run-url", required=True)
    parser.add_argument("--rerun-github-repository", required=True)
    parser.add_argument("--rerun-github-sha", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output = write_attestation(
        output_dir=args.output_dir,
        submission_path=args.submission_path,
        submission_evidence_sha256=args.submission_evidence_sha256,
        maintainer=args.maintainer,
        rerun_github_run_url=args.rerun_github_run_url,
        rerun_github_repository=args.rerun_github_repository,
        rerun_github_sha=args.rerun_github_sha,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
