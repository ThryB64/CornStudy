from __future__ import annotations

import json

from mais.research.roll_season_backtest_v6 import (
    build_roll_season_backtest_v6,
    save_roll_season_backtest_v6,
)


def test_roll_season_backtest_has_required_sections():
    data = build_roll_season_backtest_v6()

    assert data["source_quality"] == "exploratoire_barchart_proxy"
    assert data["production_verdict"] == "RESEARCH_ONLY_NOT_TRADING"
    assert data["policy_results"]
    assert data["backtests"]
    assert data["key_findings"]["best_policy"]


def test_roll_aware_policies_are_reported():
    data = build_roll_season_backtest_v6()
    policies = {row["policy"] for row in data["policy_results"]}

    assert "no_roll_proxy" in policies
    assert "strong_season_no_roll" in policies
    assert "top40_no_roll" in policies


def test_seasonal_and_agreement_scenarios_are_reported():
    data = build_roll_season_backtest_v6()
    scenarios = {row["scenario"] for row in data["policy_results"]}

    assert "seasonal_expert" in scenarios
    assert "h40_h90_agreement" in scenarios


def test_backtests_include_cost_stress():
    data = build_roll_season_backtest_v6()
    costs = {row["cost_per_leg"] for row in data["backtests"]}

    assert {1.0, 2.0, 3.0, 5.0, 8.0} <= costs


def test_backtest_trades_are_non_overlapping():
    data = build_roll_season_backtest_v6()
    rows = [row for row in data["backtests"] if row.get("trades")]
    assert rows
    for row in rows:
        trades = row["trades"]
        for previous, current in zip(trades, trades[1:], strict=False):
            assert current["entry_date"] > previous["exit_date"]


def test_save_roll_season_backtest_v6_writes_json(tmp_path):
    out = save_roll_season_backtest_v6(tmp_path / "roll_season_backtest_v6.json")
    data = json.loads(out.read_text(encoding="utf-8"))

    assert out.exists()
    assert data["key_findings"]["interpretation"]
