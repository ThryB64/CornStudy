"""Tests V49 — jambe long premium (offline, master synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v49_long_premium_leg as v49


def _synthetic_master(n=900, seed=20):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2014-01-01", periods=n)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    basis = 35 + 14 * np.sin(np.linspace(0, 16 * np.pi, n)) + rng.normal(0, 2, n)
    ema = cbot + basis
    bz = (pd.Series(basis) - pd.Series(basis).rolling(60, min_periods=20).mean()) / (
        pd.Series(basis).rolling(60, min_periods=20).std() + 1e-9)
    return pd.DataFrame({
        "cbot_eur_t": cbot, "ema_close": ema, "corn_close": cbot * 9.5,
        "ema_cbot_basis": basis, "ema_cbot_basis_zscore_52w": bz.values,
        "corn_realized_vol_20": pd.Series(cbot).pct_change().rolling(20).std().values,
        "ema_oi_total": rng.uniform(500, 5000, n),
        "curve_backwardation_proxy": rng.normal(0, 1, n),
    }, index=idx)


def test_long_leg_trades_built():
    t = v49.long_leg_trades(_synthetic_master())
    if len(t):
        assert {"entry_z", "pnl", "win", "adverse", "reverted"} <= set(t.columns)
        assert (t["entry_z"] < -1.0 + 1e-9).all()  # entrées basis bas


def test_run_v49_compares_legs(tmp_path, monkeypatch):
    monkeypatch.setattr(v49, "V49_DIR", tmp_path)
    out = v49.run_v49_long_leg(_synthetic_master())
    if out["verdict"] != "TOO_FEW":
        assert "long_leg" in out and "short_leg" in out
        assert out["verdict"] in {
            "LONG_LEG_ALSO_WORKS", "ASYMMETRY_CONFIRMED_SHORT_BETTER", "LONG_LEG_WEAK"}
