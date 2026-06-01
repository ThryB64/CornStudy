from __future__ import annotations

import json

from mais.research.ema_relative_backtest_v3 import (
    build_relative_backtest_v3,
    save_relative_backtest_v3,
)


def test_relative_backtest_v3_required_keys():
    data = build_relative_backtest_v3()
    assert "results" in data
    assert "protocol" in data
    assert "key_findings" in data


def test_relative_backtest_v3_train_only_protocol():
    protocol = build_relative_backtest_v3()["protocol"]
    assert "prior years only" in protocol["threshold"]
    assert protocol["target"] == "relative_ema_outperformance_h90"


def test_relative_backtest_v3_has_slippage_stress():
    stresses = {row["slippage_per_leg_eur_t"] for row in build_relative_backtest_v3()["results"]}
    assert {1.0, 2.0, 3.0, 5.0}.issubset(stresses)


def test_relative_backtest_v3_is_research_only():
    data = build_relative_backtest_v3()
    assert data["status"] == "RESEARCH_ONLY_NOT_TRADING"
    assert data["production_verdict"] == "NO_PRODUCTION_BACKTEST"


def test_save_relative_backtest_v3(tmp_path):
    out = save_relative_backtest_v3(tmp_path / "bt_v3.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["protocol"]["non_overlap"].startswith("strict")
