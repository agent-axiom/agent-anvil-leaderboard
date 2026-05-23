# Contributing Leaderboard Results

This repository accepts compact Agent Anvil leaderboard submissions. It does
not run arbitrary agents and does not collect raw traces.

## How To Submit

1. Run Agent Anvil in your own repository or CI.
2. Export a `leaderboard_submission.json` file:

   ```bash
   uv run anvil leaderboard export docs/paper/results.json \
     --manifest experiments/paper.yaml \
     --out leaderboard_submission.json \
     --agent-name "My Agent" \
     --agent-version "2026-05-23" \
     --repo-url "https://github.com/acme/my-agent" \
     --commit-sha "$(git rev-parse HEAD)"
   ```

3. Validate the file:

   ```bash
   uv run anvil leaderboard validate leaderboard_submission.json
   ```

4. Copy it to `submissions/<agent-name>.json`.
5. Open a pull request and complete the checklist.

CI rebuilds `leaderboard.csv` and `leaderboard.json`. Do not edit generated
leaderboard index files manually unless you are a maintainer repairing CI
output.

## No Raw Traces

Do not include raw traces, model outputs, tool outputs, secrets, API keys, user
content, or PII in a submission. The public leaderboard needs only aggregate
metrics, benchmark hashes, artifact hashes, and trust metadata.

## Trust Levels

- `self_reported`: generated locally or outside a public CI run.
- `github_actions`: generated in GitHub Actions and includes a public run URL.
- `maintainer_rerun`: independently reproduced by maintainers.

The leaderboard makes this boundary explicit instead of pretending that a public
benchmark cannot be gamed.
