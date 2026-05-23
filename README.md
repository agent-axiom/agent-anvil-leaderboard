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

Live views:

- Hugging Face Space: https://huggingface.co/spaces/ifif/agent-anvil-leaderboard
- Hugging Face Dataset: https://huggingface.co/datasets/ifif/agent-anvil-leaderboard-data

## Submit A Result

Full contributor instructions are in [CONTRIBUTING.md](CONTRIBUTING.md). The
accepted file contract is documented in [submissions/README.md](submissions/README.md).

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
python3 scripts/verify_github_runs.py
python3 scripts/apply_maintainer_reruns.py
```

After a pull request is merged into `main`, the same workflow publishes the
rebuilt `leaderboard.csv`, `leaderboard.json`, and Space files to Hugging Face
when the repository secret `HF_TOKEN` is configured.

## Trust Levels

- `self_reported`: generated outside recognized CI
- `github_actions`: generated in GitHub Actions and includes a public run URL
  that this repository verifies through the GitHub API
- `maintainer_rerun`: independently reproduced by maintainers

Maintainer reruns are stored as separate audit artifacts under
`maintainer_reruns/`. They do not rewrite the original submission; CI applies
them to the generated index after checking the rerun evidence.

Public rows should not pretend to prevent all gaming. The benchmark is visible,
so the leaderboard makes the verification boundary explicit.

## Files

- `submissions/*.json`: accepted submission artifacts
- `leaderboard.csv`: tabular index for quick inspection
- `leaderboard.json`: machine-readable index for the public Space
- `maintainer_reruns/*.json`: maintainer reproduction attestations
- `space/`: Hugging Face Space scaffold

## Hugging Face Space

The live Space reads the published Dataset index by default:

```text
https://huggingface.co/datasets/ifif/agent-anvil-leaderboard-data/resolve/main/leaderboard.json
```

Override the source with:

```text
LEADERBOARD_INDEX_URL=https://raw.githubusercontent.com/agent-axiom/agent-anvil-leaderboard/main/leaderboard.json
```

The Space reads only the generated index. Raw traces and tool outputs stay with
the submitting team unless they intentionally publish them.

## Maintainer Setup

Set this repository secret so merges to `main` can refresh Hugging Face:

```text
HF_TOKEN=<write token for the Dataset and Space>
```

The publish step writes only aggregate leaderboard files and the Space app. It
does not upload raw traces, model outputs, or tool outputs.
