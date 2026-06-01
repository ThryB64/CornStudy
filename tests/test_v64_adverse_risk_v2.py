"""Tests V64 — ADVERSE_RISK v2 (offline, master synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v64_adverse_risk_v2 as v64


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


def test_compute_v2_tiers_and_score():
    r = v64.compute_adverse_risk_v2(_synthetic_master())
    active = r["adverse_risk_v2"].isin(["LOW", "MEDIUM", "HIGH"])
    assert r.loc[active, "adverse_risk_v2_score"].between(0, 8).all()
    # score = somme des 8 flags
    flagcols = [c for c in r.columns if c.startswith("c_")]
    assert len(flagcols) == 8


def test_run_v64(tmp_path, monkeypatch):
    monkeypatch.setattr(v64, "V64_DIR", tmp_path)
    out = v64.run_v64_adverse_v2(_synthetic_master())
    assert out["version"] == "V64-ADVERSE-RISK-V2"
    if out["verdict"] != "TOO_FEW":
        assert "binary_split" in out
        assert out["verdict"] in (
            "ADVERSE_RISK_V2_SEPARATES_AND_EXPLAINS",
            "ADVERSE_RISK_V2_EXPLAINS_BUT_V1_SEPARATES_BETTER_KEEP_V1_SCORE",
            "ADVERSE_RISK_V2_WEAK_USE_V1")
        assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"


def test_report_block_runs():
    assert isinstance(v64.adverse_risk_v2_report_block(_synthetic_master()), str)
