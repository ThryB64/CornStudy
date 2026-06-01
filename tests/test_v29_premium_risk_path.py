"""Tests V29 — exploration C (premium × drawdown) + D (chemin de compression)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v29_premium_risk_path as v29


def _synthetic_master(n=520, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-01", periods=n)  # hors holdout 2024
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    # basis oscillant qui dépasse régulièrement +1 sigma
    basis = 30 + 18 * np.sin(np.linspace(0, 12 * np.pi, n)) + rng.normal(0, 2, n)
    ema = cbot + basis
    bz = (basis - pd.Series(basis).rolling(60, min_periods=20).mean()) / (
        pd.Series(basis).rolling(60, min_periods=20).std() + 1e-9)
    df = pd.DataFrame({
        "corn_close": cbot * 9.5,  # cents proxy
        "cbot_eur_t": cbot,
        "ema_close": ema,
        "ema_cbot_basis": basis,
        "ema_cbot_basis_zscore_52w": bz.values,
        "corn_realized_vol_20": pd.Series(cbot).pct_change().rolling(20).std().values,
        "ema_oi_total": rng.uniform(500, 5000, n),
    }, index=idx)
    return df


def test_compression_path_classifies():
    df = _synthetic_master()
    out = v29.run_compression_path(df)
    assert out["version"] == "V29-D-COMPRESSION-PATH"
    if out["verdict"] == "COMPRESSION_PATH_DONE":
        labels = set(out["path_counts"])
        assert labels & {"CBOT_DRIVEN", "EMA_DRIVEN", "BOTH", "ADVERSE", "unknown"}
        assert out["n_known"] >= 0


def test_premium_x_drawdown_runs():
    df = _synthetic_master()
    out = v29.run_premium_x_drawdown(df)
    assert out["version"] == "V29-C-PREMIUM-X-DRAWDOWN"
    assert out["verdict"] in {"PREMIUM_X_DRAWDOWN_DONE", "TOO_FEW", "NO_RISK_SCORE"}


def test_drawdown_risk_score_series():
    df = _synthetic_master()
    s = v29._drawdown_risk_score(df)
    assert isinstance(s, pd.Series)
    assert len(s) == len(df)
