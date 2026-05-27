## Leaderboard Submission Checklist

Submission file:

- [ ] I added exactly one result file under `submissions/`.
- [ ] The file name is stable and readable, for example `acme-support-agent.json`.
- [ ] I generated the file with `anvil leaderboard export`.
- [ ] I ran `anvil leaderboard validate submissions/<agent-name>.json`.
- [ ] I checked CI health warnings for benchmark compatibility, stale evidence,
      and low trial counts.
- [ ] If claiming `github_actions`, I used the copy-paste workflow or otherwise
      generated a GitHub artifact attestation for the submitted JSON.
- [ ] I understand maintainers may run `anvil leaderboard reproduce` in a
      sandbox before marking the row as `maintainer_rerun`.

Privacy and artifact boundary:

- [ ] The submission does not include raw traces, model outputs, tool outputs, secrets, or PII.
- [ ] Artifact hashes point to files controlled by the submitting team.
- [ ] I understand that the public HF Space displays aggregate rows only.

Trust level:

- [ ] `self_reported`: generated locally or outside a public CI run.
- [ ] `github_actions`: generated in GitHub Actions and includes
      `verification.github_run_url`, `verification.github_repository`, and
      `verification.github_sha` that CI can verify through the GitHub API.
      New rows should also pass `gh attestation verify` for the submitted JSON.
- [ ] `maintainer_rerun`: reproduced by Agent Anvil maintainers.

Reviewer notes:

- Agent name:
- Agent version:
- Benchmark name:
- Public repository:
- Public CI run URL, if claiming `github_actions`:
