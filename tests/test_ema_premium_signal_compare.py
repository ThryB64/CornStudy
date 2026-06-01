from __future__ import annotations

import json

from mais.research.ema_premium_signal_compare import (
    build_premium_signal_compare,
    save_premium_signal_compare,
)


def test_premium_signal_compare_required_keys():
    data = build_premium_signal_compare()
    assert "results" in data
    assert "key_findings" in data


def test_premium_signal_compare_has_h40_h90():
    horizons = {row["horizon"] for row in build_premium_signal_compare()["results"]}
    assert {40, 90}.issubset(horizons)


def test_premium_signal_compare_has_required_strategies():
    rows = [item for result in build_premium_signal_compare()["results"] for item in result["results"]]
    strategies = {row["strategy"] for row in rows}
    assert "ml_model" in strategies
    assert "basis_zscore_rule" in strategies
    assert "combined_equal_weight" in strategies


def test_premium_signal_compare_best_strategy_reported():
    data = build_premium_signal_compare()
    assert data["key_findings"]["h40_best_strategy"]
    assert data["key_findings"]["h90_best_strategy"]


def test_save_premium_signal_compare(tmp_path):
    out = save_premium_signal_compare(tmp_path / "premium_compare.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "ML" in data["scope"]
