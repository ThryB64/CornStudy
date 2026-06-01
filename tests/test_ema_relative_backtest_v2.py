from __future__ import annotations

import json

from mais.research.ema_relative_backtest_v2 import (
    build_relative_backtest_v2,
    save_relative_backtest_v2,
)


def test_relative_backtest_v2_required_keys():
    data = build_relative_backtest_v2()
    assert "results" in data
    assert "key_findings" in data
    assert data["status"] == "RESEARCH_ONLY_NOT_TRADING"


def test_relative_backtest_v2_has_cost_stress():
    costs = {row["cost_per_leg_eur_t"] for row in build_relative_backtest_v2()["results"]}
    assert {1.0, 2.0, 3.0, 5.0}.issubset(costs)


def test_relative_backtest_v2_has_weekly_strategies():
    strategies = {row["strategy"] for row in build_relative_backtest_v2()["results"]}
    assert "h40_top20_confidence_weekly" in strategies
    assert "h90_combined_top40_weekly" in strategies


def test_relative_backtest_v2_keeps_production_no_go():
    data = build_relative_backtest_v2()
    assert data["production_verdict"] == "NO_PRODUCTION_BACKTEST"


def test_save_relative_backtest_v2(tmp_path):
    out = save_relative_backtest_v2(tmp_path / "backtest_v2.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["protocol"]["entries"] == "weekly Friday last available observation"
