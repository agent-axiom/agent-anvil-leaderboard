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

For a `github_actions` row, copy
[`examples/github-actions-submission.yml`](examples/github-actions-submission.yml)
into `.github/workflows/` in your agent repository. That workflow exports a
submission with GitHub run metadata, creates a GitHub artifact attestation for
`leaderboard_submission.json`, and uploads a JSON artifact you can add to this
repository. Reviewers can verify provenance with:

```bash
gh attestation verify leaderboard_submission.json -R OWNER/REPO
```

For a complete public example, see
[agent-anvil-demo-agent](https://github.com/agent-axiom/agent-anvil-demo-agent).
Its current attested reference row comes from
[GitHub Actions run 26542584290](https://github.com/agent-axiom/agent-anvil-demo-agent/actions/runs/26542584290)
and the original end-to-end submission flow was accepted in
[agent-anvil-leaderboard#5](https://github.com/agent-axiom/agent-anvil-leaderboard/pull/5).

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
  The leaderboard CI verifies that the run exists, completed successfully, and
  matches `verification.github_repository` and `verification.github_sha`. New
  rows should also include a verifiable GitHub artifact attestation for the
  submitted JSON.
- `maintainer_rerun`: independently reproduced by maintainers.

The leaderboard makes this boundary explicit instead of pretending that a public
benchmark cannot be gamed.

## Maintainer Reruns

Maintainers can promote a row to `maintainer_rerun` by adding a JSON attestation
under `maintainer_reruns/`. The attestation must reference the original
`submission_path`, match the row `evidence_sha256`, and include a successful
GitHub Actions rerun URL plus repository/SHA metadata.

The **Create Maintainer Rerun Attestation** workflow can generate and validate
that JSON from workflow inputs, then upload the attestation as a reviewable
artifact for a pull request.

Keep maintainer evidence separate from the original submission so reviewers can
see both the submitter claim and the maintainer reproduction record.
