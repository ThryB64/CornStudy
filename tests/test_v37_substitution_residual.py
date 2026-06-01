"""Tests V37 — basis résiduel ajusté substitution blé/maïs (offline)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v37_substitution_residual as v37


def _synthetic_master(n=760, seed=6):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2014-01-01", periods=n)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    wc = 1.3 + 0.15 * np.sin(np.linspace(0, 10 * np.pi, n)) + rng.normal(0, 0.02, n)
    # basis lié au ratio blé/maïs (substitution) + bruit
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
        "curve_backwardation_proxy": rng.normal(0, 1, n),
    }, index=idx)


def test_residual_is_causal_series():
    df = _synthetic_master()
    res = v37.substitution_residual(df)
    for c in ["substitution_pred_basis", "basis_residual", "basis_residual_z"]:
        assert c in res.columns
    # début NaN (fenêtre trailing) -> causal
    assert res["basis_residual_z"].iloc[:120].isna().all()


def test_run_v37_returns_dual_verdict(tmp_path, monkeypatch):
    monkeypatch.setattr(v37, "V37_DIR", tmp_path)
    out = v37.run_v37_residual(_synthetic_master())
    assert out["version"] == "V37-SUBSTITUTION-RESIDUAL"
    if out["verdict"] != "TOO_SHORT":
        assert "predictive_verdict" in out
        assert out["predictive_verdict"] in {"RESIDUAL_ADDS_TO_COMPRESSION", "RESIDUAL_NO_PREDICTIVE_GAIN"}
        assert "adverse_verdict" in out
