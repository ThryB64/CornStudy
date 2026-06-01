"""Tests V71b — localité géographique production EU (offline, fetch mocké)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.collect.ec_mars as ec_mars
import mais.collect.franceagrimer as fa
import mais.research.v71b_eu_production_locality as v71b


def _master(n=2600, seed=4):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2012-01-02", periods=n)
    basis = 30 + 8 * np.sin(np.linspace(0, 20 * np.pi, n)) + rng.normal(0, 2, n)
    return pd.DataFrame({"ema_cbot_basis": basis, "cbot_eur_t": 180 + rng.normal(0, 5, n)}, index=idx)


def _fake_ec(*a, **k):
    dates = pd.date_range("2011-01-01", "2024-12-31")
    yr = dates.year
    prod = 60000 + (yr - 2011) * 500.0  # tendance
    return pd.DataFrame({"Date": dates, "ec_mars_production_eu_kt_lag1": prod})


def _fake_fa(*a, **k):
    dates = pd.date_range("2011-01-01", "2024-12-31")
    yr = dates.year
    fr = 14000 + np.where(yr % 2 == 0, -1500.0, 1000.0)  # variation marquée
    return pd.DataFrame({
        "Date": dates,
        "fr_mais_production_kt_lag1": fr,
        "fr_ro_hu_mais_total_kt_lag1": fr + 11000.0,
    })


def test_run_v71b(tmp_path, monkeypatch):
    monkeypatch.setattr(v71b, "V71B_DIR", tmp_path)
    monkeypatch.setattr(ec_mars, "build_ec_mars_features", _fake_ec)
    monkeypatch.setattr(fa, "build_franceagrimer_features", _fake_fa)
    out = v71b.run_v71b_locality(_master())
    assert out["version"] == "V71B-EU-LOCALITY"
    if out["verdict"] != "NO_DATA_EU_PRODUCTION":
        assert "corr_by_geography" in out
        assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"


def test_no_data(tmp_path, monkeypatch):
    monkeypatch.setattr(v71b, "V71B_DIR", tmp_path)
    monkeypatch.setattr(ec_mars, "build_ec_mars_features", lambda *a, **k: pd.DataFrame())
    monkeypatch.setattr(fa, "build_franceagrimer_features", lambda *a, **k: pd.DataFrame())
    assert v71b.run_v71b_locality(_master())["verdict"] == "NO_DATA_EU_PRODUCTION"
