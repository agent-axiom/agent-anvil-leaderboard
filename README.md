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
For a verified GitHub Actions row, copy
[examples/github-actions-submission.yml](examples/github-actions-submission.yml)
into your agent repository and run it from the Actions tab.

Verified end-to-end reference:
[agent-anvil-demo-agent](https://github.com/agent-axiom/agent-anvil-demo-agent)
generated a `github_actions` submission in
[GitHub Actions run 26336840349](https://github.com/agent-axiom/agent-anvil-demo-agent/actions/runs/26336840349),
then submitted it through
[agent-anvil-leaderboard#5](https://github.com/agent-axiom/agent-anvil-leaderboard/pull/5).

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
uvx --from git+https://github.com/agent-axiom/agent-anvil@v0.2.22 \
  anvil leaderboard build submissions \
  --out leaderboard.csv \
  --json-out leaderboard.json \
  --no-artifacts
python3 scripts/check_submission_health.py
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

For a maintainer rerun, generate a reviewable reproduction script from the
submitted row and execute it only in a sandbox:

```bash
uvx --from git+https://github.com/agent-axiom/agent-anvil@v0.2.22 \
  anvil leaderboard reproduce submissions/<agent-name>.json \
  --out reproduce_leaderboard_submission.sh
```

The script clones the submitted repository at the claimed commit, reruns the
benchmark, exports a fresh submission, and compares the evidence hash plus
headline metrics.

Public rows should not pretend to prevent all gaming. The benchmark is visible,
so the leaderboard makes the verification boundary explicit.

## Submission Health

CI runs `scripts/check_submission_health.py` after rebuilding the generated
index. The check fails malformed rows, verifies that benchmark hash metadata is
present in `leaderboard.json`, and emits warnings for self-reported, stale, or
low-trial submissions. The Space displays benchmark compatibility and health
badges so readers can distinguish the canonical Agent Anvil benchmark from
custom experiments. Pull requests also get a sticky PR comment with the same
health summary, so reviewers can see trust warnings without opening CI logs.

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
