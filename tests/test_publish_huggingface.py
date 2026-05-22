from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


def load_publish_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "publish_huggingface.py"
    spec = importlib.util.spec_from_file_location("publish_huggingface", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_minimal_repo(root: Path) -> None:
    (root / "submissions").mkdir()
    (root / "space").mkdir()
    (root / "submissions" / "demo.json").write_text("{}", encoding="utf-8")
    (root / "leaderboard.csv").write_text("rank,agent_name\n1,demo\n", encoding="utf-8")
    (root / "leaderboard.json").write_text('{"rows":[]}\n', encoding="utf-8")
    (root / "space" / "README.md").write_text(
        "---\nsdk: gradio\napp_file: app.py\n---\n# Space\n",
        encoding="utf-8",
    )
    (root / "space" / "app.py").write_text("print('space')\n", encoding="utf-8")
    (root / "space" / "requirements.txt").write_text("gradio\n", encoding="utf-8")


class PublishHuggingFaceTests(unittest.TestCase):
    def test_prepare_publish_directories(self) -> None:
        from tempfile import TemporaryDirectory

        module = load_publish_module()
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            out = tmp_path / "out"
            repo.mkdir()
            write_minimal_repo(repo)

            dataset_dir, space_dir = module.prepare_publish_directories(
                root=repo,
                output_dir=out,
                dataset_id="ifif/agent-anvil-leaderboard-data",
            )

            self.assertTrue(
                (dataset_dir / "leaderboard.csv")
                .read_text(encoding="utf-8")
                .startswith("rank")
            )
            self.assertTrue(
                (dataset_dir / "leaderboard.json")
                .read_text(encoding="utf-8")
                .startswith("{")
            )
            self.assertTrue((dataset_dir / "submissions" / "demo.json").exists())
            self.assertIn(
                "Agent Anvil Leaderboard Data",
                (dataset_dir / "README.md").read_text(encoding="utf-8"),
            )
            self.assertTrue((space_dir / "app.py").exists())
            self.assertTrue((space_dir / "requirements.txt").exists())

    def test_prepare_publish_directories_requires_generated_index(self) -> None:
        from tempfile import TemporaryDirectory

        module = load_publish_module()
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            repo.mkdir()
            write_minimal_repo(repo)
            (repo / "leaderboard.json").unlink()

            with self.assertRaisesRegex(FileNotFoundError, "leaderboard.json"):
                module.prepare_publish_directories(
                    root=repo,
                    output_dir=tmp_path / "out",
                    dataset_id="ifif/agent-anvil-leaderboard-data",
                )
