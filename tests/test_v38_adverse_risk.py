"""Tests V38 — module ADVERSE_RISK (offline, master synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v38_adverse_risk as v38


def _synthetic_master(n=900, seed=8):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2014-01-01", periods=n)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    wc = 1.3 + 0.15 * np.sin(np.linspace(0, 10 * np.pi, n)) + rng.normal(0, 0.02, n)
    basis = 40 * (wc - 1.0) + 12 * np.sin(np.linspace(0, 12 * np.pi, n)) + rng.normal(0, 2, n)
    ema = cbot + basis
    bz = (pd.Series(basis) - pd.Series(basis).rolling(60, min_periods=20).mean()) / (
        pd.Series(basis).rolling(60, min_periods=20).std() + 1e-9)
    return pd.DataFrame({
        "corn_close": cbot * 9.5, "cbot_eur_t": cbot, "ema_close": ema,
        "ema_cbot_basis": basis, "ema_cbot_basis_zscore_52w": bz.values,
        "wheat_close": cbot * 9.5 * wc,
        "corn_realized_vol_20": pd.Series(cbot).pct_change().rolling(20).std().values,
        "ema_oi_total": rng.uniform(500, 5000, n),
        "ema_data_availability_score": np.full(n, 0.9),
        "curve_backwardation_proxy": rng.normal(0, 1, n),
    }, index=idx)


def test_compute_adverse_risk_is_causal_and_bounded():
    df = _synthetic_master()
    risk = v38.compute_adverse_risk(df)
    for c in ["adverse_risk", "adverse_risk_score", "recommended_objective"]:
        assert c in risk.columns
    assert set(risk["adverse_risk"].unique()) <= {"NO_SIGNAL", "LOW", "MEDIUM", "HIGH"}
    s = risk["adverse_risk_score"].dropna()
    assert s.min() >= 0 and s.max() <= 3
    # score causal : NaN tant que pas de signal actif
    assert risk.loc[risk["adverse_risk"] == "NO_SIGNAL", "adverse_risk_score"].isna().all()


def test_run_v38_returns_tier_validation(tmp_path, monkeypatch):
    monkeypatch.setattr(v38, "V38_DIR", tmp_path)
    out = v38.run_v38_adverse_risk(_synthetic_master())
    if out["verdict"] != "TOO_FEW":
        assert "by_tier" in out
        assert out["verdict"] in {
            "ADVERSE_RISK_TIER_SEPARATES",
            "ADVERSE_RISK_TIER_SEPARATES_OBJECTIVE_NEUTRAL",
            "ADVERSE_RISK_TIER_WEAK",
        }


def test_report_block_never_a_veto(tmp_path, monkeypatch):
    monkeypatch.setattr(v38, "V38_DIR", tmp_path)
    block = v38.adverse_risk_report_block(_synthetic_master())
    assert "pas un veto" in block.lower() or "sans objet" in block.lower()
