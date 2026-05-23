# Submissions

Store one JSON file per agent result in this directory.

Recommended file name:

```text
submissions/<agent-name>.json
```

Rules:

- Use `anvil leaderboard export` to generate the file.
- Run `anvil leaderboard validate submissions/<agent-name>.json` before opening
  a pull request.
- Do not edit leaderboard.csv or leaderboard.json manually; CI rebuilds them.
- Do not include raw traces, model outputs, tool outputs, secrets, or PII.

Trust levels:

- `self_reported`
- `github_actions`
- `maintainer_rerun`

Rows claiming `github_actions` must include `verification.github_run_url`,
`verification.github_repository`, and `verification.github_sha`. CI verifies
that evidence through the GitHub API before publishing the leaderboard.
