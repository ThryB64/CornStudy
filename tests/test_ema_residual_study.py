"""Tests pour NB-EMA-06 — Étude du résidu EU."""

from __future__ import annotations

import json

import pytest

from mais.research.ema_residual_study import build_residual_study, save_residual_study


def test_build_returns_dict():
    data = build_residual_study()
    assert isinstance(data, dict)


def test_required_keys():
    data = build_residual_study()
    for key in [
        "n_obs",
        "residual_stats",
        "extreme_events_3sigma",
        "extreme_events_2sigma",
        "directional_study",
        "rolling_vol_60d",
        "key_findings",
    ]:
        assert key in data, f"Clé manquante : {key}"


def test_residual_mean_near_zero():
    data = build_residual_study()
    mean = data["residual_stats"]["mean"]
    assert abs(mean) < 1e-10, f"Moyenne résidu non nulle : {mean:.2e} (OLS doit centrer)"


def test_extreme_events_3sigma_verdict():
    data = build_residual_study()
    cat = data["extreme_events_3sigma"]
    assert cat["verdict"] in ("CATALOG_BUILT", "NO_EXTREME_EVENT_ENOUGH")
    if cat["verdict"] == "CATALOG_BUILT":
        assert cat["n_events"] >= 3


def test_extreme_events_2sigma_more_than_3sigma():
    data = build_residual_study()
    n3 = data["extreme_events_3sigma"]["n_events"]
    n2 = data["extreme_events_2sigma"]["n_events"]
    assert n2 >= n3, "Moins d'événements 2σ que 3σ"


def test_catalog_built_has_top5():
    data = build_residual_study()
    cat = data["extreme_events_3sigma"]
    if cat["verdict"] == "CATALOG_BUILT":
        assert "top5_positive" in cat
        assert "top5_negative" in cat


def test_adf_residual_stationary():
    data = build_residual_study()
    adf = data["directional_study"].get("adf_residual", {})
    if "error" in adf:
        pytest.skip("statsmodels non disponible")
    assert adf["verdict"] == "stationary", f"Résidu non stationnaire : p={adf['p_value']:.4f}"


def test_da_persistence_reported():
    data = build_residual_study()
    da = data["directional_study"]["da_sign_persistence_lag1"]
    assert 0.0 <= da <= 1.0, f"DA persistence hors [0,1] : {da}"


def test_save_creates_json(tmp_path):
    out = save_residual_study(tmp_path / "test_residual.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "extreme_events_3sigma" in data
    assert "key_findings" in data
