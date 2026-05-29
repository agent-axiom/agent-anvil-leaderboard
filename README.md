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
into your agent repository and run it from the Actions tab. The workflow also
creates a GitHub artifact attestation for `leaderboard_submission.json`; after
downloading the artifact you can verify provenance with:

```bash
gh attestation verify leaderboard_submission.json -R OWNER/REPO
```

If you want the workflow to open the leaderboard pull request for you, copy
[examples/github-actions-auto-pr.yml](examples/github-actions-auto-pr.yml)
instead. It still runs the benchmark in your repository, attests the aggregate
JSON, checks out this leaderboard repository, and opens a PR with a generated
body. Configure a `LEADERBOARD_PR_TOKEN` secret that can push a branch and open
pull requests against this repository. The leaderboard still does not run arbitrary agents;
it only validates the submitted JSON and provenance evidence.

Verified end-to-end reference:
[agent-anvil-demo-agent](https://github.com/agent-axiom/agent-anvil-demo-agent)
generates an attested `github_actions` submission. The current public reference
row comes from
[GitHub Actions run 26656805979](https://github.com/agent-axiom/agent-anvil-demo-agent/actions/runs/26656805979),
which auto-opened the accepted leaderboard pull request
[agent-anvil-leaderboard#18](https://github.com/agent-axiom/agent-anvil-leaderboard/pull/18).

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
uvx --from git+https://github.com/agent-axiom/agent-anvil@v0.2.23 \
  anvil leaderboard build submissions \
  --out leaderboard.csv \
  --json-out leaderboard.json \
  --no-artifacts
python3 scripts/check_submission_health.py
python3 scripts/verify_github_runs.py
python3 scripts/apply_maintainer_reruns.py
python3 scripts/verify_attestations.py --warn-only
```

After a pull request is merged into `main`, the same workflow publishes the
rebuilt `leaderboard.csv`, `leaderboard.json`, and Space files to Hugging Face
when the repository secret `HF_TOKEN` is configured.

## Trust Levels

- `self_reported`: generated outside recognized CI
- `github_actions`: generated in GitHub Actions and includes a public run URL
  that this repository verifies through the GitHub API, plus a GitHub artifact
  attestation for the submitted JSON
- `maintainer_rerun`: independently reproduced by maintainers

Maintainer reruns are stored as separate audit artifacts under
`maintainer_reruns/`. They do not rewrite the original submission; CI applies
them to the generated index after checking the rerun evidence.

For a maintainer rerun, generate a reviewable reproduction script from the
submitted row and execute it only in a sandbox:

```bash
uvx --from git+https://github.com/agent-axiom/agent-anvil@v0.2.23 \
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
health summary and provenance table, so reviewers can see trust warnings, run
metadata, and attestation status without opening CI logs.

## Artifact attestation warnings

For `github_actions` rows, CI also runs `scripts/verify_attestations.py` to ask
GitHub whether the submitted JSON has a verifiable artifact attestation from the
claimed repository. Existing rows remain visible with provenance badges. New `github_actions` rows without attestations fail CI, while `self_reported` rows remain accepted and explicitly labeled as unverified.

The generated `leaderboard.json` and `leaderboard.csv` include:

- `provenance_status`: `attested`, `missing`, `self_reported`, or
  `maintainer_rerun`
- `provenance_badge`: compact display label for the public Space and dataset
- `provenance_warning`: verifier output when provenance is missing or invalid

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
