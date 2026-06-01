"""Tests pour NB-EMA-11 — Volatilité EMA."""

from __future__ import annotations

import json
import pytest
from mais.research.ema_volatility import build_volatility, save_volatility


def test_build_returns_dict():
    data = build_volatility()
    assert isinstance(data, dict)


def test_required_keys():
    data = build_volatility()
    for key in ["descriptive_vol", "har_model", "garch_model", "vol_regime_stats", "key_findings"]:
        assert key in data, f"Clé manquante : {key}"


def test_mean_vol_realistic():
    data = build_volatility()
    vol = data["descriptive_vol"]["mean_ann_vol_20d"]
    assert 0.05 <= vol <= 0.50, f"Vol annualisée hors plage : {vol:.3f}"


def test_har_r2_computed():
    data = build_volatility()
    r2 = data["har_model"]["r2"]
    assert 0 <= r2 <= 1, f"HAR R² hors [0,1] : {r2}"


def test_har_has_all_betas():
    data = build_volatility()
    har = data["har_model"]
    for k in ["beta_daily", "beta_weekly", "beta_monthly", "intercept"]:
        assert k in har, f"HAR: {k} manquant"


def test_garch_or_unavailable():
    data = build_volatility()
    g = data["garch_model"]
    assert "error" in g or "persistence" in g


def test_vol_regime_stats():
    data = build_volatility()
    rs = data["vol_regime_stats"]
    assert rs["low_vol_std"] < rs["high_vol_std"], "Vol basse devrait avoir sigma < vol haute"


def test_save_creates_json(tmp_path):
    out = save_volatility(tmp_path / "test_vol.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "har_model" in data
    assert "key_findings" in data
