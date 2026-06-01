"""Tests V19 — CBOT risk lab + infrastructure météo prévisionnelle (anti-leakage)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mais.features.weather_forecast import (
    ForecastLeakageError,
    assert_forecast_no_leakage,
    build_forecast_features,
    make_synthetic_forecast_archive,
)
from mais.research.v19_cbot_lab import (
    cbot_risk_targets,
    run_cbot_risk_lab,
    run_cot_weather_interaction,
)


@pytest.fixture
def synthetic_df():
    rng = np.random.default_rng(19)
    n = 3000
    idx = pd.date_range("2007-01-01", periods=n, freq="B")
    corn = pd.Series(400 + np.cumsum(rng.normal(0, 4, n)), index=idx)
    lr = np.log(corn).diff()
    df = pd.DataFrame({
        "corn_close": corn,
        "corn_logret_1d": lr,
        "corn_logret_5d": np.log(corn).diff(5),
        "corn_logret_20d": np.log(corn).diff(20),
        "corn_realized_vol_20": lr.rolling(20).std(),
        "corn_rsi_14": rng.uniform(20, 80, n),
        "corn_macd_hist": rng.normal(0, 1, n),
        "corn_atr_14": np.abs(rng.normal(8, 2, n)),
        "cot_mm_net_pct_oi_x": rng.normal(0, 1, n),
        "cot_mm_long_pct": rng.uniform(0, 1, n),
        "cot_mm_short_pct": rng.uniform(0, 1, n),
        "cot_mm_net": rng.normal(0, 1, n),
        "wasde_ending_stocks_surprise_vs_trend": rng.normal(0, 1, n),
        "wasde_production_surprise_vs_trend": rng.normal(0, 1, n),
        "wasde_exports_surprise_vs_trend": rng.normal(0, 1, n),
        "wx_belt_heat_days_38c_30": rng.uniform(0, 10, n),
        "wx_belt_rain_deficit_14d": rng.normal(0, 1, n),
        "wx_belt_gdd_accumulated": np.cumsum(rng.uniform(0, 5, n)),
        "drought_composite": rng.uniform(0, 1, n),
        "condition_gd_ex_pct": rng.uniform(40, 90, n),
    }, index=idx)
    return df


# --- CBOT lab ---

def test_cbot_risk_targets(synthetic_df):
    tg = cbot_risk_targets(synthetic_df)
    assert "drawdown_5pct_h20" in tg and "rally_5pct_h20" in tg and "vol_spike_h10" in tg
    for s in tg.values():
        vals = set(s.dropna().unique())
        assert vals <= {0.0, 1.0}


def test_cbot_risk_lab(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v19_cbot_lab as mod
    monkeypatch.setattr(mod, "V19_DIR", tmp_path)
    out = run_cbot_risk_lab(synthetic_df)
    assert out["verdict"] == "CBOT_RISK_LAB_DONE"
    assert "drawdown_5pct_h20" in out["results"]


def test_cot_weather_interaction(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v19_cbot_lab as mod
    monkeypatch.setattr(mod, "V19_DIR", tmp_path)
    out = run_cot_weather_interaction(synthetic_df)
    assert out["verdict"] == "COT_WEATHER_DONE"


# --- Météo prévisionnelle / anti-leakage ---

def test_forecast_no_leakage_ok():
    fc = make_synthetic_forecast_archive(n_days=30)
    assert_forecast_no_leakage(fc)  # ne doit pas lever


def test_forecast_leakage_detected_bad_valid():
    fc = make_synthetic_forecast_archive(n_days=10)
    fc.loc[fc.index[0], "forecast_valid_date"] = fc["forecast_valid_date"].iloc[0] + pd.Timedelta(days=5)
    with pytest.raises(ForecastLeakageError):
        assert_forecast_no_leakage(fc)


def test_forecast_leakage_detected_future_run():
    fc = make_synthetic_forecast_archive(n_days=10)
    as_of = fc["forecast_issue_date"].min()  # un seul run autorisé
    with pytest.raises(ForecastLeakageError):
        assert_forecast_no_leakage(fc, as_of=as_of)


def test_forecast_features_revision_and_anomaly():
    fc = make_synthetic_forecast_archive(n_days=60, seed=1)
    feats = build_forecast_features(fc, normals={"tmax": 28.0, "precip": 3.0})
    assert len(feats) > 30
    # révisions présentes et finies (sauf 1er jour)
    assert "fc_tmax_revision" in feats.columns
    assert feats["fc_tmax_revision"].iloc[1:].notna().any()
    assert "fc_tmax_anom" in feats.columns
