"""Tests pour NB-EMA-04 — Relation EMA/CBOT cointégration."""

from __future__ import annotations

import json

import pytest

from mais.research.ema_cbot_cointegration import build_cbot_cointegration, save_cbot_cointegration


def test_build_returns_dict():
    data = build_cbot_cointegration()
    assert isinstance(data, dict)


def test_required_keys():
    data = build_cbot_cointegration()
    for key in [
        "n_overlap_days",
        "static_correlation",
        "engle_granger",
        "johansen",
        "granger_ema_to_cbot",
        "granger_cbot_to_ema",
        "rolling_corr_260d",
        "key_findings",
    ]:
        assert key in data, f"Clé manquante : {key}"


def test_overlap_days_sufficient():
    data = build_cbot_cointegration()
    assert data["n_overlap_days"] >= 2000, f"Overlap insuffisant : {data['n_overlap_days']}"


def test_engle_granger_keys():
    data = build_cbot_cointegration()
    eg = data["engle_granger"]
    if "error" in eg:
        pytest.skip("statsmodels non disponible")
    for k in ["stat", "p_value", "cointegrated_5pct"]:
        assert k in eg


def test_cointegration_confirmed():
    data = build_cbot_cointegration()
    eg = data["engle_granger"]
    if "error" in eg:
        pytest.skip("statsmodels non disponible")
    assert eg["cointegrated_5pct"] is True, f"Cointégration non confirmée : p={eg['p_value']:.4f}"


def test_granger_cbot_to_ema_significant():
    data = build_cbot_cointegration()
    g = data["granger_cbot_to_ema"]
    if "error" in g:
        pytest.skip("statsmodels non disponible")
    assert g["granger_significant_5pct"] is True, f"Granger CBOT→EMA non significatif : p={g['best_p_value']:.4f}"


def test_corr_price_levels_high():
    data = build_cbot_cointegration()
    corr = data["static_correlation"]["corr_price_levels"]
    assert corr >= 0.85, f"Corrélation niveaux faible : {corr:.3f}"


def test_rolling_corr_positive():
    data = build_cbot_cointegration()
    rc = data["rolling_corr_260d"]
    assert rc["mean_corr"] >= 0.5, f"Corrélation rolling moyenne faible : {rc['mean_corr']:.3f}"


def test_vecm_half_life_positive():
    data = build_cbot_cointegration()
    vecm = data["vecm"]
    if "skipped" in vecm or "error" in vecm:
        pytest.skip("VECM non estimé")
    hl = vecm.get("half_life_days")
    if hl and not (hl != hl):  # not nan
        assert hl > 0, f"Demi-vie VECM négative : {hl}"


def test_save_creates_json(tmp_path):
    out = save_cbot_cointegration(tmp_path / "test_coint.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "engle_granger" in data
    assert "key_findings" in data
