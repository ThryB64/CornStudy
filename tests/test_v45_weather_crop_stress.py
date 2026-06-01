"""Tests V45 — météo & stress cultural (offline, master synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v45_weather_crop_stress as v45


def _synthetic_master(n=1200, seed=16):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2014-01-01", periods=n)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    basis = 35 + 10 * np.sin(np.linspace(0, 14 * np.pi, n)) + rng.normal(0, 2, n)
    ema = cbot + basis
    bz = (pd.Series(basis) - pd.Series(basis).rolling(60, min_periods=20).mean()) / (
        pd.Series(basis).rolling(60, min_periods=20).std() + 1e-9)
    return pd.DataFrame({
        "cbot_eur_t": cbot, "ema_close": ema, "corn_close": cbot * 9.5,
        "ema_cbot_basis": basis, "ema_cbot_basis_zscore_52w": bz.values,
        "wx_belt_tmax_c_anom_z": rng.normal(0, 1, n),
        "wx_belt_rain_deficit_14d": rng.normal(0, 1, n),
        "wx_belt_prcp_30_anom_z": rng.normal(0, 1, n),
        "drought_composite": 70 + np.cumsum(rng.normal(0, 0.3, n)),
    }, index=idx)


def test_crop_stress_is_causal_and_phenological():
    df = _synthetic_master()
    s = v45.crop_stress_index(df)
    for c in ["crop_stress_us", "phenology_weight", "in_critical_window"]:
        assert c in s.columns
    # hors fenêtre (janvier) le poids est nul -> stress nul ou NaN
    jan = s[s.index.month == 1]["phenology_weight"]
    assert (jan == 0.0).all()


def test_run_v45_offline_no_network(tmp_path, monkeypatch):
    monkeypatch.setattr(v45, "V45_DIR", tmp_path)
    out = v45.run_v45_weather(_synthetic_master(), try_network=False)
    assert out["version"] == "V45-WEATHER-CROP-STRESS"
    assert "E1_us_stress_vs_cbot" in out and "E2_us_stress_vs_basis" in out
    assert out["forward_collect"]["status"] in {"WAITING_NETWORK"}
