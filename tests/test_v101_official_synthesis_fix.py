"""Tests V101 — fix synthèse officielle live (offline, journal mocké)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v101_official_synthesis_fix as v101


def _master(n=600, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2014-01-01", periods=n)
    cbot = 150 + np.cumsum(rng.normal(0, 1, n))
    basis = 35 + rng.normal(0, 3, n)
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
        "cot_mm_net_pct_oi_x": rng.normal(0, 10, n),
        "ema_backwardation_flag": (rng.normal(0, 1, n) > 0).astype(int),
        "ema_spread_f0_f1": rng.normal(-1.5, 2, n),
    }, index=idx)


def _journal():
    return pd.DataFrame([{
        "price_date": pd.Timestamp("2026-06-01"), "signal_tier": "SHORT_PREMIUM_EXTREME",
        "basis_official_eur_t": 75.93, "basis_z_used": 2.039, "z_source": "proxy_implied",
        "cbot_eur_t": 151.07, "eurusd": 1.1655, "objective_prudent": "z->0.5", "objective_full": "z->0",
        "median_horizon_days": 23, "curve_shape": None, "warnings": "NON_REVERSION_RISK_HIGH",
    }])


def test_official_synthesis_uses_journal(tmp_path, monkeypatch):
    jp = tmp_path / "journal.parquet"
    _journal().to_parquet(jp, index=False)
    monkeypatch.setattr(v101, "V101_DIR", tmp_path)
    monkeypatch.setattr(v101, "V99_LATEST", tmp_path / "v99_latest.json")
    monkeypatch.setattr(v101, "OFFICIAL_JOURNAL", jp)
    out = v101.run_v101_official_synthesis(_master())
    assert out["verdict"] == "OFFICIAL_SYNTHESIS_FIXED"
    assert out["as_of"] == "2026-06-01"
    assert out["signal_tier"] == "SHORT_PREMIUM_EXTREME"
    assert out["signal_tier"] != "UNCERTAIN_ROLL"
    assert out["context_lag_days"] > 100
    assert (tmp_path / "v99_latest.json").exists()


def test_fallback_no_journal(tmp_path, monkeypatch):
    monkeypatch.setattr(v101, "V101_DIR", tmp_path)
    monkeypatch.setattr(v101, "OFFICIAL_JOURNAL", tmp_path / "absent.parquet")
    out = v101.run_v101_official_synthesis(_master(), write_v99_latest=False)
    assert out["verdict"] == "NO_OFFICIAL_JOURNAL_FALLBACK_PROXY"
