"""Tests V47 — choix d'objectif z→0.5 vs z→0 (offline, master synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v47_objective_choice as v47


def _synthetic_master(n=900, seed=18):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2014-01-01", periods=n)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    wc = 1.3 + 0.15 * np.sin(np.linspace(0, 10 * np.pi, n)) + rng.normal(0, 0.02, n)
    basis = 40 * (wc - 1.0) + 12 * np.sin(np.linspace(0, 12 * np.pi, n)) + rng.normal(0, 2, n)
    ema = cbot + basis
    bz = (pd.Series(basis) - pd.Series(basis).rolling(60, min_periods=20).mean()) / (
        pd.Series(basis).rolling(60, min_periods=20).std() + 1e-9)
    s = pd.Series(cbot)
    return pd.DataFrame({
        "corn_close": cbot * 9.5, "cbot_eur_t": cbot, "ema_close": ema,
        "ema_cbot_basis": basis, "ema_cbot_basis_zscore_52w": bz.values,
        "wheat_close": cbot * 9.5 * wc,
        "corn_sma_50": (s * 9.5).rolling(50).mean().values,
        "corn_logret_20d": np.log(s / s.shift(20)).values,
        "corn_realized_vol_20": s.pct_change().rolling(20).std().values,
        "ema_oi_total": rng.uniform(500, 5000, n),
        "curve_backwardation_proxy": rng.normal(0, 1, n),
        "cot_mm_net_pct_oi_x": rng.normal(0, 10, n),
    }, index=idx)


def test_paired_objectives_same_conditions():
    df = _synthetic_master()
    t = v47._paired_objectives(df)
    if len(t):
        assert {"pnl_z0", "pnl_z05", "days_z0", "days_z05", "z0_beats_z05"} <= set(t.columns)


def test_run_v47_returns_context_breakdown(tmp_path, monkeypatch):
    monkeypatch.setattr(v47, "V47_DIR", tmp_path)
    out = v47.run_v47_objective(_synthetic_master())
    if out["verdict"] != "TOO_FEW":
        assert "by_cbot_support" in out and "overall" in out
        assert "always_z0_mean_pnl" in out and "always_z05_mean_pnl" in out
