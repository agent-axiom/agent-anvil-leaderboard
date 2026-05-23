from __future__ import annotations

import importlib.util
from pathlib import Path


def load_view_module():
    module_path = Path(__file__).resolve().parents[1] / "space" / "leaderboard_view.py"
    spec = importlib.util.spec_from_file_location("leaderboard_view", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_rows() -> list[dict[str, object]]:
    return [
        {
            "agent_name": "Safe Agent",
            "agent_version": "v2",
            "trust_level": "maintainer_rerun",
            "trace_aware_pass_rate": 91.5,
            "final_answer_pass_rate": 99.0,
            "answer_only_missed_failures": 1,
            "answer_only_missed_failure_rate": 2.0,
            "total_trials": 50,
            "repo_url": "https://github.com/acme/safe-agent",
        },
        {
            "agent_name": "Demo Agent",
            "agent_version": "sha",
            "trust_level": "github_actions",
            "trace_aware_pass_rate": 30.0,
            "final_answer_pass_rate": 100.0,
            "answer_only_missed_failures": 70,
            "answer_only_missed_failure_rate": 70.0,
            "total_trials": 100,
            "repo_url": "https://github.com/agent-axiom/agent-anvil-demo-agent",
        },
        {
            "agent_name": "Local Draft",
            "trust_level": "self_reported",
            "trace_aware_pass_rate": 45.0,
            "answer_only_missed_failure_rate": 12.0,
            "total_trials": 10,
        },
    ]


def test_normalize_rows_adds_rank_badges_and_defaults() -> None:
    view = load_view_module()

    rows = view.normalize_rows({"rows": sample_rows()})

    assert rows[0]["rank"] == 1
    assert rows[0]["trust_badge"] == "[maintainer rerun]"
    assert rows[1]["trust_badge"] == "[GitHub Actions]"
    assert rows[2]["agent_version"] == ""


def test_filter_rows_searches_filters_and_sorts() -> None:
    view = load_view_module()
    rows = view.normalize_rows({"rows": sample_rows()})

    filtered = view.filter_rows(
        rows,
        search="agent",
        trust_level="github_actions",
        min_trials=25,
        sort_by="trace_aware_pass_rate",
        descending=True,
    )

    assert [row["agent_name"] for row in filtered] == ["Demo Agent"]


def test_filter_rows_can_sort_by_missed_failure_rate_ascending() -> None:
    view = load_view_module()
    rows = view.normalize_rows({"rows": sample_rows()})

    filtered = view.filter_rows(
        rows,
        search="",
        trust_level="all",
        min_trials=0,
        sort_by="answer_only_missed_failure_rate",
        descending=False,
    )

    assert [row["agent_name"] for row in filtered] == [
        "Safe Agent",
        "Local Draft",
        "Demo Agent",
    ]


def test_summary_markdown_highlights_trust_mix_and_missed_failures() -> None:
    view = load_view_module()
    rows = view.normalize_rows({"rows": sample_rows()})

    summary = view.summary_markdown(rows)

    assert "Rows: 3" in summary
    assert "Best trace-aware pass rate: 91.5%" in summary
    assert "Answer-only missed failures: 71" in summary
    assert "maintainer rerun: 1" in summary
    assert "GitHub Actions: 1" in summary


def test_table_values_use_public_columns() -> None:
    view = load_view_module()
    rows = view.normalize_rows({"rows": sample_rows()})

    table = view.table_values(rows[:1])

    assert view.DISPLAY_COLUMNS[0] == "rank"
    assert view.DISPLAY_COLUMNS[-1] == "evidence_sha256"
    assert table[0][view.DISPLAY_COLUMNS.index("agent_name")] == "Safe Agent"
