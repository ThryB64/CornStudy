"""Tests pour NB-EMA-03 — Séries continues EMA."""

from __future__ import annotations

import json

import pytest

from mais.research.ema_continuous_series import build_continuous_series, save_continuous_series


def test_build_returns_dict():
    data = build_continuous_series()
    assert isinstance(data, dict)


def test_required_keys():
    data = build_continuous_series()
    for key in [
        "invariant_check",
        "gaps_raw",
        "gaps_adjusted",
        "price_stats_raw",
        "price_stats_adjusted",
        "return_stats_raw",
        "return_stats_adjusted",
        "divergence_raw_vs_adjusted",
        "key_findings",
    ]:
        assert key in data, f"Clé manquante : {key}"


def test_invariant_holds():
    data = build_continuous_series()
    ic = data["invariant_check"]
    assert ic["invariant_holds"] is True, f"Invariant violé : {ic['n_violations']} violations"
    assert ic["max_residual"] < 0.01, f"Résidu max trop élevé : {ic['max_residual']}"


def test_coverage_rate_consistent():
    data = build_continuous_series()
    cov_raw = data["gaps_raw"]["coverage_rate"]
    cov_adj = data["gaps_adjusted"]["coverage_rate"]
    assert abs(cov_raw - cov_adj) < 0.001, "Coverage raw vs adj diverge"
    assert 0.70 <= cov_raw <= 0.95, f"Coverage inattendue : {cov_raw:.3f}"


def test_n_gaps_consistent_with_audit():
    data = build_continuous_series()
    assert data["gaps_raw"]["n_gaps_ge5"] == 46, "Nombre de gaps ≥5j inconsistant avec NB-EMA-01"


def test_adf_returns_stationary():
    data = build_continuous_series()
    adf = data["adf_returns_adjusted"]
    if "error" in adf:
        pytest.skip("statsmodels non disponible")
    assert adf["verdict"] == "stationary", f"Retours non stationnaires : p={adf['p_value']:.4f}"


def test_return_stats_keys():
    data = build_continuous_series()
    for label in ["return_stats_raw", "return_stats_adjusted"]:
        rs = data[label]
        for k in ["n", "mean_daily_ret", "std_daily_ret", "annualized_vol"]:
            assert k in rs, f"{label}: clé manquante {k}"


def test_direction_agreement_high():
    data = build_continuous_series()
    da = data["divergence_raw_vs_adjusted"].get("direction_agreement")
    if da is not None:
        assert da >= 0.95, f"Direction agreement raw/adj trop faible : {da:.3f}"


def test_save_creates_json(tmp_path):
    out = save_continuous_series(tmp_path / "test_continuous.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "invariant_check" in data
    assert data["invariant_check"]["invariant_holds"] is True
