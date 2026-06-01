"""Tests V41 — CBOT_SUPPORT_SCORE (offline, master synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v41_cbot_support as v41


def _synthetic_master(n=900, seed=12):
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


def test_compute_support_bounded_and_causal():
    df = _synthetic_master()
    sup = v41.compute_cbot_support(df)
    assert set(sup["cbot_support"].unique()) <= {"NO_SIGNAL", "LOW", "MEDIUM", "HIGH"}
    s = sup["cbot_support_score"].dropna()
    assert s.min() >= 0 and s.max() <= 3
    assert sup.loc[sup["cbot_support"] == "NO_SIGNAL", "cbot_support_score"].isna().all()


def test_run_v41_returns_binary_split(tmp_path, monkeypatch):
    monkeypatch.setattr(v41, "V41_DIR", tmp_path)
    out = v41.run_v41_cbot_support(_synthetic_master())
    if out["verdict"] != "TOO_FEW":
        assert "by_tier" in out
        assert out["verdict"] in {
            "CBOT_SUPPORT_SEPARATES_ADVERSE",
            "CBOT_SUPPORT_BINARY_ROBUST_GRADED_NOISY",
            "CBOT_SUPPORT_WEAK",
        }


def test_report_block_is_context_not_veto(tmp_path, monkeypatch):
    monkeypatch.setattr(v41, "V41_DIR", tmp_path)
    block = v41.cbot_support_report_block(_synthetic_master())
    assert block == "" or "pas un veto" in block.lower()
