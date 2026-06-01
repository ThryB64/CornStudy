from __future__ import annotations

import json

from mais.research.ema_relative_backtest import build_relative_backtest, save_relative_backtest


def test_relative_backtest_required_keys():
    data = build_relative_backtest()
    assert "results" in data
    assert "key_findings" in data
    assert data["status"] == "RESEARCH_ONLY_NOT_TRADING"
    assert data["production_verdict"] == "NO_PRODUCTION_BACKTEST"


def test_relative_backtest_covers_required_strategies():
    names = {row["strategy"] for row in build_relative_backtest()["results"]}
    assert "model_all" in names
    assert "model_top20_confidence" in names
    assert "model_basis_extreme_filter" in names
    assert "model_top20_basis_extreme" in names
    assert "basis_zscore_rule" in names


def test_relative_backtest_protocol_has_costs():
    protocol = build_relative_backtest()["protocol"]
    assert protocol["cost_per_leg_eur_t"] > 0
    assert protocol["cost_per_trade_eur_t"] == protocol["cost_per_leg_eur_t"] * protocol["legs"]


def test_relative_backtest_ok_rows_have_pnl_metrics():
    rows = [row for row in build_relative_backtest()["results"] if row.get("status") == "OK"]
    assert rows
    assert all("pnl_mean_eur_t" in row for row in rows)
    assert all("max_drawdown_eur_t" in row for row in rows)


def test_save_relative_backtest(tmp_path):
    out = save_relative_backtest(tmp_path / "relative_backtest.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["target"] == "relative_ema_outperformance_h40"
