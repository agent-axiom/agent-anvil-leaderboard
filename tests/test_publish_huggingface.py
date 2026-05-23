from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


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


def test_prepare_publish_directories(tmp_path: Path) -> None:
    module = load_publish_module()
    repo = tmp_path / "repo"
    out = tmp_path / "out"
    repo.mkdir()
    write_minimal_repo(repo)
    (repo / "maintainer_reruns").mkdir()
    (repo / "maintainer_reruns" / "demo.json").write_text(
        '{"schema_version":"agent-anvil.maintainer-rerun.v1"}',
        encoding="utf-8",
    )

    dataset_dir, space_dir = module.prepare_publish_directories(
        root=repo,
        output_dir=out,
        dataset_id="ifif/agent-anvil-leaderboard-data",
    )

    assert (dataset_dir / "leaderboard.csv").read_text(encoding="utf-8").startswith("rank")
    assert (dataset_dir / "leaderboard.json").read_text(encoding="utf-8").startswith("{")
    assert (dataset_dir / "submissions" / "demo.json").exists()
    assert (dataset_dir / "maintainer_reruns" / "demo.json").exists()
    assert "Agent Anvil Leaderboard Data" in (dataset_dir / "README.md").read_text(
        encoding="utf-8"
    )
    assert (space_dir / "app.py").exists()
    assert (space_dir / "requirements.txt").exists()


def test_prepare_publish_directories_requires_generated_index(tmp_path: Path) -> None:
    module = load_publish_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    write_minimal_repo(repo)
    (repo / "leaderboard.json").unlink()

    with pytest.raises(FileNotFoundError, match="leaderboard.json"):
        module.prepare_publish_directories(
            root=repo,
            output_dir=tmp_path / "out",
            dataset_id="ifif/agent-anvil-leaderboard-data",
        )
