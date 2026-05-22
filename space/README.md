---
title: Agent Anvil Leaderboard
colorFrom: blue
colorTo: purple
sdk: gradio
app_file: app.py
pinned: false
---

# Agent Anvil Leaderboard Space

This Hugging Face Space renders the public Agent Anvil leaderboard from the
generated `leaderboard.json` index.

By default it reads the published Agent Anvil leaderboard Dataset:

```text
https://huggingface.co/datasets/ifif/agent-anvil-leaderboard-data/resolve/main/leaderboard.json
```

Override the source with this Space variable:

```text
LEADERBOARD_INDEX_URL=https://raw.githubusercontent.com/agent-axiom/agent-anvil-leaderboard/main/leaderboard.json
```

The app does not execute user agents. It only reads aggregate leaderboard rows
that were validated by this repository's GitHub Actions workflow.
