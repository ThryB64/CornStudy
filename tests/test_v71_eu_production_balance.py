"""Tests V71 — bilan physique EU (production EC MARS), offline (fetch mocké)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.collect.ec_mars as ec_mars
import mais.research.v71_eu_production_balance as v71


def _synthetic_master(n=900, seed=21):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2014-01-01", periods=n)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    basis = 35 + 12 * np.sin(np.linspace(0, 12 * np.pi, n)) + rng.normal(0, 2, n)
    bz = (pd.Series(basis) - pd.Series(basis).rolling(60, min_periods=20).mean()) / (
        pd.Series(basis).rolling(60, min_periods=20).std() + 1e-9)
    s = pd.Series(cbot)
    return pd.DataFrame({
        "corn_close": cbot * 9.5, "cbot_eur_t": cbot, "ema_close": cbot + basis,
        "ema_cbot_basis": basis, "ema_cbot_basis_zscore_52w": bz.values,
        "wheat_close": cbot * 9.5 * 1.3,
        "corn_sma_50": (s * 9.5).rolling(50).mean().values,
        "corn_logret_20d": np.log(s / s.shift(20)).values,
        "corn_realized_vol_20": s.pct_change().rolling(20).std().values,
        "ema_oi_total": rng.uniform(500, 5000, n),
        "curve_backwardation_proxy": rng.normal(0, 1, n),
        "cot_mm_net_pct_oi_x": rng.normal(0, 10, n),
    }, index=idx)


def _fake_ec(*a, **k):
    dates = pd.date_range("2013-01-01", "2018-12-31")
    rng = np.random.default_rng(0)
    anom = np.where(dates.year % 2 == 0, -3000.0, 3000.0)  # années paires = rares
    return pd.DataFrame({
        "Date": dates,
        "ec_mars_production_eu_kt_lag1": 60000 + rng.normal(0, 100, len(dates)),
        "ec_mars_prod_anomaly_eu_lag1": anom,
        "ec_mars_prod_yoy_pct_lag1": rng.normal(0, 2, len(dates)),
    })


def test_run_v71(tmp_path, monkeypatch):
    monkeypatch.setattr(v71, "V71_DIR", tmp_path)
    monkeypatch.setattr(ec_mars, "build_ec_mars_features", _fake_ec)
    out = v71.run_v71_eu_production(_synthetic_master())
    assert out["version"] == "V71-EU-PRODUCTION"
    if out["verdict"] != "NO_DATA_EU_PRODUCTION":
        assert "hypothesis_support_score" in out
        assert out["verdict"] in (
            "EU_LOW_PRODUCTION_JUSTIFIES_PREMIUM_ADD_TO_ADVERSE_RISK_FORWARD",
            "EU_PRODUCTION_PARTIAL_SIGNAL_WATCHLIST",
            "EU_PRODUCTION_NOT_DISCRIMINANT")
        assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"


def test_no_data(tmp_path, monkeypatch):
    monkeypatch.setattr(v71, "V71_DIR", tmp_path)
    monkeypatch.setattr(ec_mars, "build_ec_mars_features", lambda *a, **k: pd.DataFrame())
    out = v71.run_v71_eu_production(_synthetic_master())
    assert out["verdict"] == "NO_DATA_EU_PRODUCTION"
