# Agent Anvil Public Leaderboard

This repository stores public Agent Anvil leaderboard submissions and the
generated aggregate index.

Agent authors run Agent Anvil in their own repository or CI, export a compact
`leaderboard_submission.json`, and open a pull request that adds the file under
`submissions/`. The repository CI validates submissions and rebuilds
`leaderboard.csv` and `leaderboard.json`.

The leaderboard intentionally does not execute arbitrary user agents. It
displays aggregate eval metrics, artifact hashes, benchmark hashes, evidence
hashes, and explicit trust labels.

## Submit A Result

In your agent repository:

```bash
uv run anvil paper reproduce
uv run anvil leaderboard export docs/paper/results.json \
  --manifest experiments/paper.yaml \
  --out leaderboard_submission.json \
  --agent-name "My Agent" \
  --agent-version "2026-05-22" \
  --repo-url "https://github.com/acme/my-agent" \
  --commit-sha "$(git rev-parse HEAD)"
uv run anvil leaderboard validate leaderboard_submission.json
```

Then copy the file into this repository:

```text
submissions/acme-my-agent.json
```

Open a pull request. CI will run:

```bash
uvx --from git+https://github.com/agent-axiom/agent-anvil \
  anvil leaderboard build submissions \
  --out leaderboard.csv \
  --json-out leaderboard.json \
  --no-artifacts
```

## Trust Levels

- `self_reported`: generated outside recognized CI
- `github_actions`: generated in GitHub Actions and includes a public run URL
- `maintainer_rerun`: independently reproduced by maintainers

Public rows should not pretend to prevent all gaming. The benchmark is visible,
so the leaderboard makes the verification boundary explicit.

## Files

- `submissions/*.json`: accepted submission artifacts
- `leaderboard.csv`: tabular index for quick inspection
- `leaderboard.json`: machine-readable index for the public Space
- `space/`: Hugging Face Space scaffold

## Hugging Face Space

Create a Hugging Face Space from `space/` and set:

```text
LEADERBOARD_INDEX_URL=https://raw.githubusercontent.com/agent-axiom/agent-anvil-leaderboard/main/leaderboard.json
```

The Space reads only the generated index. Raw traces and tool outputs stay with
the submitting team unless they intentionally publish them.
