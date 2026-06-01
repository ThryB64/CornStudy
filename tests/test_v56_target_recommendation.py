"""Tests V56 — règle d'objectif recommandé (offline, master synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v56_target_recommendation as v56


def test_recommend_target_rule():
    assert v56.recommend_target("LOW", "HIGH", "LOW") == "z->0"
    assert v56.recommend_target("HIGH", "HIGH", "LOW") == "z->0.5"
    assert v56.recommend_target("LOW", "LOW", "LOW") == "z->0.5"
    assert v56.recommend_target("LOW", "MEDIUM", "HIGH") == "z->0.5"


def _synthetic_master(n=900, seed=21):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2014-01-01", periods=n)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    wc = 1.3 + 0.15 * np.sin(np.linspace(0, 10 * np.pi, n)) + rng.normal(0, 0.02, n)
    basis = 40 * (wc - 1.0) + 12 * np.sin(np.linspace(0, 12 * np.pi, n)) + rng.normal(0, 2, n)
    ema = cbot + basis
    bz = (pd.Series(basis) - pd.Series(basis).rolling(60, min_periods=20).mean()) / (
        pd.Series(basis).rolling(60, min_periods=20).std() + 1e-9)
    s = pd.Series(cbot)
    spread = rng.normal(-1.5, 2.0, n)
    return pd.DataFrame({
        "corn_close": cbot * 9.5, "cbot_eur_t": cbot, "ema_close": ema,
        "ema_cbot_basis": basis, "ema_cbot_basis_zscore_52w": bz.values,
        "wheat_close": cbot * 9.5 * wc,
        "corn_sma_50": (s * 9.5).rolling(50).mean().values,
        "corn_logret_20d": np.log(s / s.shift(20)).values,
        "corn_realized_vol_20": s.pct_change().rolling(20).std().values,
        "ema_oi_total": rng.uniform(500, 5000, n),
        "ema_backwardation_flag": (spread > 0).astype(int),
        "ema_spread_f0_f1": spread,
        "curve_backwardation_proxy": rng.normal(0, 1, n),
        "cot_mm_net_pct_oi_x": rng.normal(0, 10, n),
    }, index=idx)


def test_run_v56(tmp_path, monkeypatch):
    monkeypatch.setattr(v56, "V56_DIR", tmp_path)
    out = v56.run_v56_target(_synthetic_master())
    assert out["version"] == "V56-TARGET-RECO"
    if out["verdict"] != "TOO_FEW":
        assert out["n_recommended_prudent_z05"] + out["n_recommended_full_z0"] == out["n_trades"]
        assert "reco_mean_pnl" in out
        assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"


def test_report_block_runs():
    block = v56.target_recommendation_report_block(_synthetic_master())
    assert isinstance(block, str)
