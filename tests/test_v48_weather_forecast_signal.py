"""Tests V48 — météo prévue favorable/défavorable (oracle borne supérieure, offline)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v48_weather_forecast_signal as v48


def _synthetic_master(n=1500, seed=19):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2013-01-01", periods=n)
    heat = rng.normal(0, 1, n)
    cbot = 150 + np.cumsum(0.3 * heat + rng.normal(0, 1.0, n))  # chaleur pousse un peu le CBOT
    return pd.DataFrame({
        "cbot_eur_t": cbot, "ema_close": cbot + 35,
        "ema_cbot_basis": np.full(n, 35.0),
        "ema_cbot_basis_zscore_52w": rng.normal(0, 1, n),
        "wx_belt_tmax_c_anom_z": heat,
        "wx_belt_rain_deficit_14d": rng.normal(0, 1, n),
        "wx_belt_prcp_30_anom_z": rng.normal(0, 1, n),
    }, index=idx)


def test_oracle_stress_is_future_window():
    df = _synthetic_master()
    s = v48.oracle_forecast_stress(df, lead=14)
    # la fin de série n'a pas de vraie valeur : NaN (fenêtre future indispo) ou 0 (hors saison, poids nul)
    tail = s.iloc[-14:]
    assert (tail.isna() | (tail == 0)).all()


def test_run_v48_verdict(tmp_path, monkeypatch):
    monkeypatch.setattr(v48, "V48_DIR", tmp_path)
    out = v48.run_v48_forecast_signal(_synthetic_master())
    assert out["version"] == "V48-WEATHER-FORECAST-SIGNAL"
    assert "extreme_event_oracle" in out
    assert out["verdict"] in {
        "SIGNAL_IN_EXTREME_FORECAST_NOT_MEAN_COLLECT_FORWARD_EXTREMES",
        "SIGNAL_IS_IN_THE_FORECAST_COLLECT_FORWARD",
        "EVEN_PERFECT_MEAN_FORECAST_WEAK",
    }
