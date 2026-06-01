"""Tests V86 — CBOT_SUPPORT v2 (offline, ENSO=None)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v86_cbot_support_v2 as v86


def _synthetic_master(n=900, seed=21):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2014-01-01", periods=n)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    wc = 1.3 + 0.15 * np.sin(np.linspace(0, 10 * np.pi, n)) + rng.normal(0, 0.02, n)
    basis = 40 * (wc - 1.0) + 14 * np.sin(np.linspace(0, 12 * np.pi, n)) + rng.normal(0, 2, n)
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


def test_compute_v2_tiers():
    df = _synthetic_master()
    sup = v86.compute_cbot_support_v2(df, enso_regime=None)
    active = sup["cbot_support_v2"].isin(["LOW", "MEDIUM", "HIGH"])
    assert sup.loc[active, "cbot_support_v2_score"].between(0, 5).all()
    assert int(sup["n_components"].iloc[0]) == 4  # ENSO absent


def test_run_v86(tmp_path, monkeypatch):
    monkeypatch.setattr(v86, "V86_DIR", tmp_path)
    out = v86.run_v86_cbot_support_v2(_synthetic_master(), with_network=False)
    assert out["version"] == "V86-CBOT-SUPPORT-V2"
    if out["verdict"] != "TOO_FEW":
        assert out["verdict"] in ("CBOT_SUPPORT_V2_ADD_TO_DAILY_REPORT", "CBOT_SUPPORT_V2_NO_GAIN_KEEP_V1")
        assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"


def test_report_block(tmp_path):
    assert isinstance(v86.cbot_support_v2_report_block(_synthetic_master()), str)
