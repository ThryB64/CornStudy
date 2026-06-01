"""Tests V108 — reconstruction basis live + ADVERSE_RISK live (offline, fetchers mockés)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v107_live_context_refresh as v107
import mais.research.v108_live_basis_reconstruction as v108


def test_reconstruct_cbot_eur_t():
    # ZC ~447 cents, eurusd 1.1655 -> ~151 €/t (conversion projet)
    zc = pd.Series([447.0])
    eur = pd.Series([1.1655])
    out = v108.reconstruct_cbot_eur_t(zc, eur)
    assert abs(float(out.iloc[0]) - 150.9) < 1.5


def test_run_v108(tmp_path, monkeypatch):
    jp = tmp_path / "journal.parquet"
    pd.DataFrame([{"price_date": pd.Timestamp("2026-06-01"), "signal_tier": "SHORT_PREMIUM_EXTREME",
                   "basis_z_used": 2.04, "basis_official_eur_t": 75.93, "cbot_eur_t": 151.0}
                  ]).to_parquet(jp, index=False)
    monkeypatch.setattr(v108, "V108_DIR", tmp_path)
    monkeypatch.setattr(v108, "OFFICIAL_JOURNAL", jp)
    idx = pd.bdate_range(end="2026-06-01", periods=300)
    rng = np.random.default_rng(0)
    zc = pd.Series(447.0 + rng.normal(0, 3, len(idx)), index=idx)
    market = pd.DataFrame({"corn_close": zc, "wheat_close": zc * 1.25}, index=idx)
    monkeypatch.setattr(v107, "fetch_live_market", lambda try_network=True: market)
    monkeypatch.setattr(v107, "_yahoo_daily", lambda sym, rng="5y", timeout=30: pd.Series(
        1.165, index=idx))
    monkeypatch.setattr(v108, "_substitution_fit_from_master",
                        lambda: {"slope": 0.3, "intercept": 0.1, "resid_std": 0.8})
    out = v108.run_v108_live_basis(try_network=True)
    assert out["version"] == "V108-LIVE-BASIS"
    assert out["reconstruction_ok"] is True
    assert out["adverse_risk_live"] in ("LOW", "MEDIUM", "HIGH", "NO_SIGNAL")


def test_run_v108_offline(tmp_path, monkeypatch):
    jp = tmp_path / "journal.parquet"
    pd.DataFrame([{"price_date": pd.Timestamp("2026-06-01"), "basis_z_used": 2.0,
                   "basis_official_eur_t": 75.0, "cbot_eur_t": 151.0}]).to_parquet(jp, index=False)
    monkeypatch.setattr(v108, "V108_DIR", tmp_path)
    monkeypatch.setattr(v108, "OFFICIAL_JOURNAL", jp)
    monkeypatch.setattr(v107, "fetch_live_market", lambda try_network=True: pd.DataFrame())
    out = v108.run_v108_live_basis(try_network=False)
    assert out["verdict"] == "NO_MARKET_DATA_OFFLINE"
