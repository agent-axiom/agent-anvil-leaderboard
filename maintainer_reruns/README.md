# Maintainer Reruns

This directory stores maintainer rerun attestations.

Each `*.json` file is an audit artifact that promotes an existing leaderboard
row to `maintainer_rerun` only after CI verifies:

- `submission_path` exists in `leaderboard.json`
- `submission_evidence_sha256` matches the row evidence hash
- `rerun.github_run_url` points to a successful GitHub Actions run
- `rerun.github_repository` and `rerun.github_sha` match that run

Example:

```json
{
  "schema_version": "agent-anvil.maintainer-rerun.v1",
  "submission_path": "submissions/acme-agent.json",
  "submission_evidence_sha256": "sha256-from-leaderboard-row",
  "maintainer": "agent-axiom",
  "rerun": {
    "github_run_url": "https://github.com/agent-axiom/agent-anvil/actions/runs/123456789",
    "github_repository": "agent-axiom/agent-anvil",
    "github_sha": "abcdef123456"
  }
}
```

Do not edit the original submission when adding a maintainer rerun. Keep the
maintainer evidence separate so the provenance remains visible.

Maintainers can also run the **Create Maintainer Rerun Attestation** workflow
from the Actions tab. It accepts the same fields, validates the generated JSON
against the current leaderboard index, and uploads a `maintainer-rerun-attestation`
artifact that can be added to this directory in a pull request.
