from __future__ import annotations

import importlib.util
from datetime import UTC, datetime
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
            "total_trials": 100,
            "repo_url": "https://github.com/acme/safe-agent",
            "generated_at": "2026-05-20T12:00:00Z",
            "benchmark_name": "agent_anvil_trace_eval_benchmark",
            "benchmark_manifest_sha256": "a" * 64,
            "benchmark_scenario_count": 5,
            "submission_schema_version": "agent-anvil.leaderboard.v1",
            "submission_generated_by": "agent-anvil/0.2.20",
            "provenance_status": "maintainer_rerun",
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
            "generated_at": "2026-04-01T12:00:00Z",
            "benchmark_name": "agent_anvil_trace_eval_benchmark",
            "benchmark_manifest_sha256": "b" * 64,
            "benchmark_scenario_count": 5,
            "submission_schema_version": "agent-anvil.leaderboard.v1",
            "submission_generated_by": "agent-anvil/0.2.22",
            "provenance_status": "attested",
        },
        {
            "agent_name": "Local Draft",
            "trust_level": "self_reported",
            "trace_aware_pass_rate": 45.0,
            "answer_only_missed_failure_rate": 12.0,
            "total_trials": 10,
            "generated_at": "2025-12-01T12:00:00Z",
            "benchmark_name": "custom_agent_benchmark",
            "benchmark_scenario_count": 1,
            "submission_schema_version": "agent-anvil.leaderboard.v1",
            "submission_generated_by": "agent-anvil/0.2.20",
        },
    ]


def test_normalize_rows_adds_rank_badges_and_defaults() -> None:
    view = load_view_module()

    rows = view.normalize_rows(
        {"rows": sample_rows()}, now=datetime(2026, 5, 23, tzinfo=UTC)
    )

    assert rows[0]["rank"] == 1
    assert rows[0]["trust_badge"] == "[maintainer rerun]"
    assert rows[0]["freshness_badge"] == "[fresh]"
    assert rows[0]["compatibility_badge"] == "[agent-anvil benchmark]"
    assert rows[0]["provenance_badge"] == "[maintainer rerun]"
    assert rows[0]["health_badge"] == "[healthy]"
    assert rows[1]["trust_badge"] == "[GitHub Actions]"
    assert rows[1]["provenance_badge"] == "[attested]"
    assert rows[1]["freshness_badge"] == "[aging]"
    assert rows[2]["agent_version"] == ""
    assert rows[2]["provenance_badge"] == "[self-reported]"
    assert rows[2]["freshness_badge"] == "[stale]"
    assert rows[2]["compatibility_badge"] == "[custom benchmark]"
    assert rows[2]["health_badge"] == "[needs review]"
    assert rows[2]["health_issues"] == [
        "self_reported",
        "stale",
        "custom_benchmark",
        "low_trials",
    ]


def test_filter_rows_searches_filters_and_sorts() -> None:
    view = load_view_module()
    rows = view.normalize_rows(
        {"rows": sample_rows()}, now=datetime(2026, 5, 23, tzinfo=UTC)
    )

    filtered = view.filter_rows(
        rows,
        search="agent",
        trust_level="github_actions",
        min_trials=25,
        freshness="all",
        compatibility="all",
        health="all",
        sort_by="trace_aware_pass_rate",
        descending=True,
    )

    assert [row["agent_name"] for row in filtered] == ["Demo Agent"]


def test_filter_rows_can_sort_by_missed_failure_rate_ascending() -> None:
    view = load_view_module()
    rows = view.normalize_rows(
        {"rows": sample_rows()}, now=datetime(2026, 5, 23, tzinfo=UTC)
    )

    filtered = view.filter_rows(
        rows,
        search="",
        trust_level="all",
        min_trials=0,
        freshness="all",
        compatibility="all",
        health="all",
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
    rows = view.normalize_rows(
        {"rows": sample_rows()}, now=datetime(2026, 5, 23, tzinfo=UTC)
    )

    summary = view.summary_markdown(rows)

    assert "Rows: 3" in summary
    assert "Best trace-aware pass rate: 91.5%" in summary
    assert "Answer-only missed failures: 71" in summary
    assert "Stale rows: 1" in summary
    assert "Needs review rows: 1" in summary
    assert "Custom benchmark rows: 1" in summary
    assert "maintainer rerun: 1" in summary
    assert "GitHub Actions: 1" in summary
    assert "attested: 1" in summary


def test_filter_rows_can_filter_stale_submissions() -> None:
    view = load_view_module()
    rows = view.normalize_rows(
        {"rows": sample_rows()}, now=datetime(2026, 5, 23, tzinfo=UTC)
    )

    filtered = view.filter_rows(
        rows,
        search="",
        trust_level="all",
        min_trials=0,
        freshness="stale",
        compatibility="all",
        health="all",
        sort_by="rank",
        descending=False,
    )

    assert [row["agent_name"] for row in filtered] == ["Local Draft"]


def test_filter_rows_can_filter_compatibility_and_health() -> None:
    view = load_view_module()
    rows = view.normalize_rows(
        {"rows": sample_rows()}, now=datetime(2026, 5, 23, tzinfo=UTC)
    )

    filtered = view.filter_rows(
        rows,
        search="",
        trust_level="all",
        min_trials=0,
        freshness="all",
        compatibility="custom",
        health="needs_review",
        sort_by="rank",
        descending=False,
    )

    assert [row["agent_name"] for row in filtered] == ["Local Draft"]


def test_table_values_use_public_columns() -> None:
    view = load_view_module()
    rows = view.normalize_rows(
        {"rows": sample_rows()}, now=datetime(2026, 5, 23, tzinfo=UTC)
    )

    table = view.table_values(rows[:1])

    assert view.DISPLAY_COLUMNS[0] == "rank"
    assert view.DISPLAY_COLUMNS[-1] == "evidence_sha256"
    assert "freshness_badge" in view.DISPLAY_COLUMNS
    assert "provenance_badge" in view.DISPLAY_COLUMNS
    assert "compatibility_badge" in view.DISPLAY_COLUMNS
    assert "health_badge" in view.DISPLAY_COLUMNS
    assert "generated_at" in view.DISPLAY_COLUMNS
    assert table[0][view.DISPLAY_COLUMNS.index("agent_name")] == "Safe Agent"
