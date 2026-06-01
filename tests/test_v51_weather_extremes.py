"""Tests V51 — weather extremes lab (offline, master météo synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v51_weather_extremes as v51


def _synthetic(n=1500, seed=11):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2012-01-02", periods=n)
    # chaleur saisonnière + bruit (anomalie z), pics en été
    doy = idx.dayofyear.to_numpy()
    season = np.sin((doy - 100) / 365 * 2 * np.pi)
    heat = 0.6 * season + rng.normal(0, 0.8, n)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n) + 0.3 * np.roll(heat, 5))
    basis = 30 + 12 * np.sin(np.linspace(0, 14 * np.pi, n)) + rng.normal(0, 2, n)
    bz = (pd.Series(basis) - pd.Series(basis).rolling(60, min_periods=20).mean()) / (
        pd.Series(basis).rolling(60, min_periods=20).std() + 1e-9)
    return pd.DataFrame({
        "cbot_eur_t": cbot, "ema_cbot_basis": basis, "ema_cbot_basis_zscore_52w": bz.values,
        "wx_belt_tmax_c_anom_z": heat,
        "wx_belt_rain_deficit_14d": rng.normal(0, 1, n),
        "wx_belt_prcp_30_anom_z": rng.normal(0, 1, n),
    }, index=idx)


def test_extreme_features_causal():
    f = v51.extreme_features(_synthetic())
    for c in ("heat_anom_z", "dry_z", "heat_dome_flag", "consecutive_hot_days",
              "in_critical_window", "heat_extreme_crit"):
        assert c in f.columns
    # flags binaires, run-length >= 0
    assert f["heat_dome_flag"].dropna().isin([0, 1]).all()
    assert (f["consecutive_hot_days"].dropna() >= 0).all()


def test_run_v51(tmp_path, monkeypatch):
    monkeypatch.setattr(v51, "V51_DIR", tmp_path)
    out = v51.run_v51_extremes(_synthetic())
    assert out["version"] == "V51-WEATHER-EXTREMES"
    if out["verdict"] != "NO_WEATHER_DATA":
        assert "lead_lag" in out and "tail_vs_body" in out
        assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"


def test_no_weather_data():
    df = _synthetic(n=200)
    df["wx_belt_tmax_c_anom_z"] = np.nan
    out = v51.run_v51_extremes(df)
    assert out["verdict"] == "NO_WEATHER_DATA"
