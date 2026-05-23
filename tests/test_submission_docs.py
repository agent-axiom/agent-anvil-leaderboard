from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SubmissionDocsTests(unittest.TestCase):
    def test_pr_template_contains_submission_checklist(self) -> None:
        template = ROOT / ".github" / "pull_request_template.md"

        text = template.read_text(encoding="utf-8")

        self.assertIn("Leaderboard Submission Checklist", text)
        self.assertIn("anvil leaderboard validate", text)
        self.assertIn("raw traces", text)
        self.assertIn("github_actions", text)
        self.assertIn("HF Space", text)

    def test_contributing_guide_explains_submission_flow(self) -> None:
        text = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

        self.assertIn("How To Submit", text)
        self.assertIn("leaderboard_submission.json", text)
        self.assertIn("submissions/<agent-name>.json", text)
        self.assertIn("No Raw Traces", text)
        self.assertIn("Trust Levels", text)

    def test_submissions_readme_documents_file_contract(self) -> None:
        text = (ROOT / "submissions" / "README.md").read_text(encoding="utf-8")

        self.assertIn("one JSON file per agent result", text)
        self.assertIn("Do not edit leaderboard.csv", text)
        self.assertIn("self_reported", text)
        self.assertIn("github_actions", text)
        self.assertIn("maintainer_rerun", text)
