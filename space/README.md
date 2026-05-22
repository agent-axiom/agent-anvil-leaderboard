# Agent Anvil Leaderboard Space

This Hugging Face Space renders the public Agent Anvil leaderboard from the
generated `leaderboard.json` index.

Set this Space variable:

```text
LEADERBOARD_INDEX_URL=https://raw.githubusercontent.com/agent-axiom/agent-anvil-leaderboard/main/leaderboard.json
```

The app does not execute user agents. It only reads aggregate leaderboard rows
that were validated by this repository's GitHub Actions workflow.
