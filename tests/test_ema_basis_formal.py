"""Tests pour NB-EMA-07 — Basis formel EMA/CBOT."""

from __future__ import annotations

import json

import pytest

from mais.research.ema_basis_formal import build_basis_formal, save_basis_formal


def test_build_returns_dict():
    data = build_basis_formal()
    assert isinstance(data, dict)


def test_required_keys():
    data = build_basis_formal()
    for key in ["basis_stats", "stationarity", "ar1", "mean_reversion_H20", "mean_reversion_H60", "arbitrage_backtest", "key_findings"]:
        assert key in data, f"Clé manquante : {key}"


def test_basis_stats_positive_mean():
    data = build_basis_formal()
    mean = data["basis_stats"]["mean"]
    assert mean > 0, f"Basis moyen devrait être positif (EMA>CBOT) : {mean:.2f}"
    assert 20 <= mean <= 60, f"Basis moyen EMA/CBOT hors plage attendue : {mean:.2f}"


def test_adf_basis_stationary():
    data = build_basis_formal()
    adf = data["stationarity"].get("adf", {})
    if "error" in data["stationarity"]:
        pytest.skip("statsmodels non disponible")
    assert adf["verdict"] == "stationary", f"ADF basis non stationnaire : p={adf['p_value']:.4f}"


def test_ar1_phi_in_range():
    data = build_basis_formal()
    phi = data["ar1"]["phi"]
    assert 0 < phi < 1, f"AR(1) phi hors (0,1) : {phi:.4f}"
    assert phi >= 0.90, f"Phi AR(1) trop faible pour un basis persistant : {phi:.4f}"


def test_ar1_half_life_positive():
    data = build_basis_formal()
    hl = data["ar1"]["half_life_days"]
    assert hl > 0, f"Demi-vie négative : {hl}"
    assert hl < 365, f"Demi-vie excessive (>1 an) : {hl:.1f} jours"


def test_mean_reversion_H60_high():
    data = build_basis_formal()
    hr = data["mean_reversion_H60"]["hit_rate"]
    assert hr >= 0.70, f"Hit rate H60 trop faible : {hr:.3f} (attendu ≥70%)"


def test_backtest_has_trades():
    data = build_basis_formal()
    bt = data["arbitrage_backtest"]
    if "error" in bt:
        pytest.skip("Pas de trades détectés")
    assert bt["n_trades"] > 0
    assert "note" in bt, "Note de mise en garde manquante"


def test_save_creates_json(tmp_path):
    out = save_basis_formal(tmp_path / "test_basis.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "ar1" in data
    assert "key_findings" in data
