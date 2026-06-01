"""Tests V60 — météo comme driver du basis (offline, master synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v60_weather_basis_driver as v60


def _synthetic(n=1500, seed=5):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2012-01-02", periods=n)
    doy = idx.dayofyear.to_numpy()
    heat = 0.6 * np.sin((doy - 100) / 365 * 2 * np.pi) + rng.normal(0, 0.8, n)
    basis = 35 + 12 * np.sin(np.linspace(0, 14 * np.pi, n)) + rng.normal(0, 2, n)
    bz = (pd.Series(basis) - pd.Series(basis).rolling(60, min_periods=20).mean()) / (
        pd.Series(basis).rolling(60, min_periods=20).std() + 1e-9)
    return pd.DataFrame({
        "cbot_eur_t": 150 + np.cumsum(rng.normal(0, 1, n)),
        "ema_cbot_basis": basis, "ema_cbot_basis_zscore_52w": bz.values,
        "wx_belt_tmax_c_anom_z": heat,
        "wx_belt_rain_deficit_14d": rng.normal(0, 1, n),
        "wx_belt_prcp_30_anom_z": rng.normal(0, 1, n),
    }, index=idx)


def test_run_v60(tmp_path, monkeypatch):
    monkeypatch.setattr(v60, "V60_DIR", tmp_path)
    out = v60.run_v60_weather_basis(_synthetic())
    assert out["version"] == "V60-WEATHER-BASIS"
    if out["verdict"] != "NO_WEATHER_DATA":
        assert "lead_lag" in out and "conditional_basis_level" in out
        assert out["verdict"] in (
            "US_HEAT_PRECEDES_BASIS_WIDENING_EU_PREMIUM",
            "US_HEAT_PRECEDES_BASIS_COMPRESSION_CBOT_CATCHUP",
            "US_HEAT_NOT_A_CLEAR_BASIS_DRIVER")
        assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"


def test_no_weather():
    df = _synthetic(n=200)
    df["wx_belt_tmax_c_anom_z"] = np.nan
    assert v60.run_v60_weather_basis(df)["verdict"] == "NO_WEATHER_DATA"
