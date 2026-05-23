## Leaderboard Submission Checklist

Submission file:

- [ ] I added exactly one result file under `submissions/`.
- [ ] The file name is stable and readable, for example `acme-support-agent.json`.
- [ ] I generated the file with `anvil leaderboard export`.
- [ ] I ran `anvil leaderboard validate submissions/<agent-name>.json`.

Privacy and artifact boundary:

- [ ] The submission does not include raw traces, model outputs, tool outputs, secrets, or PII.
- [ ] Artifact hashes point to files controlled by the submitting team.
- [ ] I understand that the public HF Space displays aggregate rows only.

Trust level:

- [ ] `self_reported`: generated locally or outside a public CI run.
- [ ] `github_actions`: generated in GitHub Actions and includes
      `verification.github_run_url`, `verification.github_repository`, and
      `verification.github_sha` that CI can verify through the GitHub API.
- [ ] `maintainer_rerun`: reproduced by Agent Anvil maintainers.

Reviewer notes:

- Agent name:
- Agent version:
- Benchmark name:
- Public repository:
- Public CI run URL, if claiming `github_actions`:
