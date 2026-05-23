from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable, NamedTuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


RUN_URL_RE = re.compile(
    r"^https://github\.com/"
    r"(?P<owner>[A-Za-z0-9_.-]+)/"
    r"(?P<repo>[A-Za-z0-9_.-]+)/"
    r"actions/runs/"
    r"(?P<run_id>[0-9]+)"
    r"/?$"
)


class GitHubRunRef(NamedTuple):
    owner: str
    repo: str
    run_id: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"


FetchRun = Callable[[GitHubRunRef], dict[str, Any]]


def parse_github_run_url(url: str) -> GitHubRunRef:
    match = RUN_URL_RE.match(url.strip())
    if not match:
        raise ValueError(f"expected a GitHub Actions run URL, got: {url!r}")
    return GitHubRunRef(
        owner=match.group("owner"),
        repo=match.group("repo"),
        run_id=match.group("run_id"),
    )


def fetch_github_run(parsed: GitHubRunRef, *, token: str | None = None) -> dict[str, Any]:
    request = Request(
        f"https://api.github.com/repos/{parsed.full_name}/actions/runs/{parsed.run_id}",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"GitHub API returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"GitHub API request failed: {exc.reason}") from exc


def verify_submission(
    *,
    path: Path,
    submission: dict[str, Any],
    fetch_run: FetchRun,
) -> list[str]:
    verification = submission.get("verification")
    if not isinstance(verification, dict):
        return [f"{path}: missing verification object"]

    trust_level = verification.get("trust_level")
    if trust_level != "github_actions":
        return []

    errors: list[str] = []
    run_url = str(verification.get("github_run_url") or "").strip()
    if not run_url:
        return [f"{path}: github_actions requires verification.github_run_url"]

    try:
        parsed = parse_github_run_url(run_url)
    except ValueError as exc:
        return [f"{path}: {exc}"]

    expected_repo = str(verification.get("github_repository") or "").strip()
    if not expected_repo:
        errors.append("requires verification.github_repository")
    elif expected_repo != parsed.full_name:
        errors.append(
            f"{path}: github_repository {expected_repo!r} does not match run URL "
            f"{parsed.full_name!r}"
        )

    try:
        run = fetch_run(parsed)
    except RuntimeError as exc:
        return [f"{path}: {exc}"]

    status = run.get("status")
    conclusion = run.get("conclusion")
    if status != "completed":
        errors.append(f"{path}: run status is {status!r}, expected 'completed'")
    if conclusion != "success":
        errors.append(f"{path}: run conclusion is {conclusion!s}, expected success")

    run_repo = _run_repository_name(run)
    if run_repo and run_repo != parsed.full_name:
        errors.append(
            f"{path}: GitHub API repository {run_repo!r} does not match run URL "
            f"{parsed.full_name!r}"
        )

    expected_sha = str(verification.get("github_sha") or "").strip()
    run_sha = str(run.get("head_sha") or "").strip()
    if not expected_sha:
        errors.append("requires verification.github_sha")
    elif run_sha and not run_sha.startswith(expected_sha):
        errors.append(
            f"{path}: github_sha does not match run head_sha "
            f"({expected_sha!r} vs {run_sha!r})"
        )

    return errors


def verify_all_submissions(
    *,
    submissions_dir: Path,
    fetch_run: FetchRun,
) -> list[str]:
    errors: list[str] = []
    for path in sorted(submissions_dir.glob("*.json")):
        try:
            submission = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path}: invalid JSON: {exc}")
            continue
        if not isinstance(submission, dict):
            errors.append(f"{path}: expected JSON object")
            continue
        errors.extend(verify_submission(path=path, submission=submission, fetch_run=fetch_run))
    return errors


def _run_repository_name(run: dict[str, Any]) -> str:
    repository = run.get("repository")
    if isinstance(repository, dict):
        full_name = repository.get("full_name")
        if isinstance(full_name, str):
            return full_name
    return ""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify GitHub Actions evidence for Agent Anvil leaderboard rows."
    )
    parser.add_argument("--submissions-dir", type=Path, default=Path("submissions"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")

    errors = verify_all_submissions(
        submissions_dir=args.submissions_dir,
        fetch_run=lambda parsed: fetch_github_run(parsed, token=token),
    )
    if errors:
        for error in errors:
            print(f"::error::{error}", file=sys.stderr)
        return 1

    print("GitHub Actions evidence verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
