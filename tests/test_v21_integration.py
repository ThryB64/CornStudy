"""Tests V21 — intégration indicateur + collecteur météo prévue (fonctions pures)."""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from mais.collect.openmeteo_forecast_collector import _rows_from_daily, save_forecast
from mais.research.v21_indicator_integration import (
    compute_cbot_context,
    compute_integrated_indicator,
    decompose_compression_path,
    run_integrated_indicator,
)


@pytest.fixture
def synthetic_df():
    rng = np.random.default_rng(21)
    n = 2800
    idx = pd.date_range("2008-01-01", periods=n, freq="B")
    cbot = pd.Series(150 + np.cumsum(rng.normal(0, 1, n)), index=idx)
    bz = np.zeros(n)
    for t in range(1, n):
        bz[t] = 0.95 * bz[t - 1] + rng.normal(0, 0.3)
    ema = cbot.values + 30 - 5 * bz + rng.normal(0, 2, n)
    return pd.DataFrame({
        "cbot_eur_t": cbot,
        "ema_close": ema,
        "ema_cbot_basis": ema - cbot.values,
        "ema_cbot_basis_zscore_52w": bz,
        "ema_oi_total": rng.uniform(1000, 5000, n),
        "corn_realized_vol_20": np.abs(rng.normal(0.2, 0.05, n)),
        "curve_backwardation_proxy": rng.normal(0, 0.2, n),
        "wx_belt_heat_days_38c_30": rng.uniform(0, 10, n),
        "wx_belt_rain_deficit_14d": rng.normal(0, 1, n),
        "drought_composite": rng.uniform(0, 1, n),
        "condition_gd_ex_pct": rng.uniform(40, 90, n),
    }, index=idx)


def test_compression_path(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v21_indicator_integration as mod
    monkeypatch.setattr(mod, "V21_DIR", tmp_path)
    out = decompose_compression_path(synthetic_df)
    assert out["verdict"] == "COMPRESSION_PATH_DECOMPOSED"
    paths = set(out["path_distribution"])
    assert paths <= {"EMA_DRIVEN", "CBOT_DRIVEN", "BOTH", "ADVERSE"}
    # parts cohérentes
    s = out["share_compression_via_cbot_up"] + out["share_compression_via_ema_down"] + out["share_both"]
    assert 0.0 <= s <= 1.0


def test_cbot_context_labels(synthetic_df):
    ctx = compute_cbot_context(synthetic_df)
    assert set(ctx["cbot_context"].unique()) <= {
        "CBOT_NEUTRAL", "CBOT_BULLISH_WEATHER", "CBOT_RISK_OFF", "CBOT_UPTREND"}
    assert set(ctx["drawdown_risk"].unique()) <= {"low", "medium", "high"}


def test_integrated_indicator(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v21_indicator_integration as mod
    monkeypatch.setattr(mod, "V21_DIR", tmp_path)
    ind = compute_integrated_indicator(synthetic_df)
    assert "cbot_context" in ind.columns and "compression_path_hint" in ind.columns
    out = run_integrated_indicator(synthetic_df)
    assert out["verdict"] == "INTEGRATED_INDICATOR_DONE"


def test_forecast_rows_builder():
    daily = {"time": ["2023-06-02", "2023-06-03"],
             "temperature_2m_max": [30.0, 31.0], "precipitation_sum": [0.0, 5.0]}
    rows = _rows_from_daily(daily, date(2023, 6, 1), "iowa")
    assert len(rows) == 4  # 2 vars × 2 jours
    leads = {r["lead_time_days"] for r in rows}
    assert leads == {1, 2}
    assert all(r["forecast_valid_date"] > r["forecast_issue_date"] for r in rows)


def test_forecast_save_skips_offline(monkeypatch):
    # Sans réseau, save_forecast doit renvoyer SKIP proprement (pas d'exception)
    import mais.collect.openmeteo_forecast_collector as col

    def _boom(*a, **k):
        raise NotImplementedError("offline")
    monkeypatch.setattr(col, "fetch_forecast", _boom)
    out = save_forecast(region="us")
    assert out["status"] == "SKIP"
