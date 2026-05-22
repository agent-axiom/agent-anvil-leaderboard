from __future__ import annotations

import argparse
import os
import re
import shutil
import tempfile
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Iterator

DEFAULT_DATASET_ID = "ifif/agent-anvil-leaderboard-data"
DEFAULT_SPACE_ID = "ifif/agent-anvil-leaderboard"

REQUIRED_ROOT_FILES = [
    "leaderboard.csv",
    "leaderboard.json",
]
REQUIRED_SPACE_FILES = [
    "README.md",
    "app.py",
    "requirements.txt",
]


def prepare_publish_directories(
    *,
    root: Path,
    output_dir: Path,
    dataset_id: str,
) -> tuple[Path, Path]:
    root = root.resolve()
    output_dir = output_dir.resolve()
    dataset_dir = output_dir / "dataset"
    space_dir = output_dir / "space"

    _require_inputs(root)
    _reset_dir(dataset_dir)
    _reset_dir(space_dir)

    shutil.copytree(root / "submissions", dataset_dir / "submissions")
    for filename in REQUIRED_ROOT_FILES:
        shutil.copy2(root / filename, dataset_dir / filename)
    _write_dataset_readme(dataset_dir)

    for filename in REQUIRED_SPACE_FILES:
        source = root / "space" / filename
        target = space_dir / filename
        if filename == "app.py":
            target.write_text(
                _with_dataset_index_default(
                    source.read_text(encoding="utf-8"),
                    dataset_id=dataset_id,
                ),
                encoding="utf-8",
            )
        else:
            shutil.copy2(source, target)

    return dataset_dir, space_dir


def publish_to_huggingface(
    *,
    token: str,
    dataset_id: str,
    space_id: str,
    dataset_dir: Path,
    space_dir: Path,
) -> None:
    from huggingface_hub import HfApi

    api = HfApi(token=token)
    api.create_repo(dataset_id, repo_type="dataset", private=False, exist_ok=True)
    api.upload_folder(
        repo_id=dataset_id,
        repo_type="dataset",
        folder_path=str(dataset_dir),
        commit_message="Publish Agent Anvil leaderboard data",
    )
    api.create_repo(
        space_id,
        repo_type="space",
        space_sdk="gradio",
        private=False,
        exist_ok=True,
    )
    api.upload_folder(
        repo_id=space_id,
        repo_type="space",
        folder_path=str(space_dir),
        commit_message="Publish Agent Anvil leaderboard Space",
    )


def dataset_index_url(dataset_id: str) -> str:
    return f"https://huggingface.co/datasets/{dataset_id}/resolve/main/leaderboard.json"


def _require_inputs(root: Path) -> None:
    for filename in REQUIRED_ROOT_FILES:
        _require_file(root / filename)
    _require_file(root / "submissions")
    for filename in REQUIRED_SPACE_FILES:
        _require_file(root / "space" / filename)


def _require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(str(path))


def _reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def _write_dataset_readme(dataset_dir: Path) -> None:
    (dataset_dir / "README.md").write_text(
        "\n".join(
            [
                "---",
                "license: mit",
                "tags:",
                "- agent-evals",
                "- leaderboard",
                "- ai-agents",
                "- openai",
                "---",
                "",
                "# Agent Anvil Leaderboard Data",
                "",
                "Public Agent Anvil leaderboard submissions and generated index.",
                "",
                "Source repository: "
                "https://github.com/agent-axiom/agent-anvil-leaderboard",
                "",
                "This dataset stores aggregate leaderboard submissions only. "
                "Raw traces, model outputs, and tool outputs are not included.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _with_dataset_index_default(app_text: str, *, dataset_id: str) -> str:
    return re.sub(
        r"https://huggingface\.co/datasets/[^\"']+/resolve/main/leaderboard\.json",
        dataset_index_url(dataset_id),
        app_text,
    )


@contextmanager
def _temp_or_path(path: str | None) -> Iterator[str]:
    if path:
        with nullcontext(path) as output_path:
            yield output_path
    else:
        with tempfile.TemporaryDirectory(prefix="agent-anvil-hf-") as output_path:
            yield output_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish Agent Anvil leaderboard indexes to Hugging Face."
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-dir")
    parser.add_argument(
        "--dataset-id",
        default=os.getenv("HF_DATASET_ID", DEFAULT_DATASET_ID),
    )
    parser.add_argument(
        "--space-id",
        default=os.getenv("HF_SPACE_ID", DEFAULT_SPACE_ID),
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    with _temp_or_path(args.output_dir) as output_path:
        dataset_dir, space_dir = prepare_publish_directories(
            root=args.root,
            output_dir=Path(output_path),
            dataset_id=args.dataset_id,
        )
        print(f"dataset_dir={dataset_dir}")
        print(f"space_dir={space_dir}")
        print(f"index={dataset_index_url(args.dataset_id)}")

        if args.dry_run:
            return 0

        token = os.getenv("HF_TOKEN")
        if not token:
            raise SystemExit("HF_TOKEN is required unless --dry-run is used")

        publish_to_huggingface(
            token=token,
            dataset_id=args.dataset_id,
            space_id=args.space_id,
            dataset_dir=dataset_dir,
            space_dir=space_dir,
        )
        print(f"dataset=https://huggingface.co/datasets/{args.dataset_id}")
        print(f"space=https://huggingface.co/spaces/{args.space_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
