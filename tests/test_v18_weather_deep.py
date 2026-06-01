"""Tests V18-WEATHER-DEEP."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mais.research.v18_weather_deep import (
    run_weather_basis_justification,
    run_weather_on_trades,
    weather_stress_index,
)


@pytest.fixture
def synthetic_df():
    rng = np.random.default_rng(180)
    n = 2800
    idx = pd.date_range("2008-01-01", periods=n, freq="B")
    cbot = 150 + np.cumsum(rng.normal(0, 1, n))
    bz = np.zeros(n)
    for t in range(1, n):
        bz[t] = 0.95 * bz[t - 1] + rng.normal(0, 0.3)
    ema = cbot + 30 - 5 * bz + rng.normal(0, 2, n)
    return pd.DataFrame({
        "cbot_eur_t": cbot,
        "ema_close": ema,
        "ema_cbot_basis": ema - cbot,
        "ema_cbot_basis_zscore_52w": bz,
        "ema_oi_total": rng.uniform(1000, 5000, n),
        "corn_realized_vol_20": np.abs(rng.normal(0.2, 0.05, n)),
        "curve_backwardation_proxy": rng.normal(0, 0.2, n),
        "wx_belt_heat_days_38c_30": rng.uniform(0, 10, n),
        "wx_belt_rain_deficit_14d": rng.normal(0, 1, n),
        "drought_composite": rng.uniform(0, 1, n),
        "condition_gd_ex_pct": rng.uniform(40, 90, n),
    }, index=idx)


def test_weather_stress_index(synthetic_df):
    s = weather_stress_index(synthetic_df)
    assert len(s) == len(synthetic_df)
    assert s.notna().sum() > 1000


def test_weather_on_trades(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v18_weather_deep as mod
    monkeypatch.setattr(mod, "V18_DIR", tmp_path)
    out = run_weather_on_trades(synthetic_df)
    assert out["verdict"] in {"WEATHER_WARNING_USEFUL", "WEATHER_NEUTRAL", "TOO_FEW", "TOO_FEW_WITH_WX"}


def test_weather_justification(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v18_weather_deep as mod
    monkeypatch.setattr(mod, "V18_DIR", tmp_path)
    out = run_weather_basis_justification(synthetic_df)
    assert out["verdict"] in {"WEATHER_JUSTIFICATION_DONE", "TOO_FEW"}
