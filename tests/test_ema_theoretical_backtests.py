from __future__ import annotations

import json

from mais.research.ema_theoretical_backtests import (
    build_theoretical_backtests,
    save_theoretical_backtests,
)


def test_theoretical_backtests_required_keys():
    data = build_theoretical_backtests()
    assert "results" in data
    assert "key_findings" in data
    assert data["status"] == "THEORETICAL_ONLY_NOT_PRODUCTION"


def test_theoretical_backtests_cover_strategies():
    names = {row["strategy"] for row in build_theoretical_backtests()["results"]}
    assert "ema_direct_momentum" in names
    assert "relative_basis_z_rule" in names
    assert "basis_extreme_mean_reversion" in names


def test_theoretical_backtests_cover_horizons():
    horizons = {row["horizon_days"] for row in build_theoretical_backtests()["results"]}
    assert {40, 60}.issubset(horizons)


def test_theoretical_backtests_have_costs():
    data = build_theoretical_backtests()
    assert data["cost_assumption_eur_t_per_leg"] > 0


def test_save_theoretical_backtests(tmp_path):
    out = save_theoretical_backtests(tmp_path / "theoretical_backtests.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "production_verdict" in data["key_findings"]
