"""Test V35 — moteur de compression CBOT (offline, master synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.research.v35_cbot_compression_engine import run_v35_compression_engine


def _synthetic_master(n=520, seed=4):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-01", periods=n)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    basis = 30 + 18 * np.sin(np.linspace(0, 12 * np.pi, n)) + rng.normal(0, 2, n)
    ema = cbot + basis
    bz = (basis - pd.Series(basis).rolling(60, min_periods=20).mean()) / (
        pd.Series(basis).rolling(60, min_periods=20).std() + 1e-9)
    return pd.DataFrame({
        "corn_close": cbot * 9.5, "cbot_eur_t": cbot, "ema_close": ema,
        "ema_cbot_basis": basis, "ema_cbot_basis_zscore_52w": bz.values,
        "corn_realized_vol_20": pd.Series(cbot).pct_change().rolling(20).std().values,
        "ema_oi_total": rng.uniform(500, 5000, n),
        "curve_backwardation_proxy": rng.normal(0, 1, n),
    }, index=idx)


def test_v35_runs_and_returns_verdict():
    out = run_v35_compression_engine(_synthetic_master())
    assert out["version"] == "V35-CBOT-ENGINE"
    assert out["verdict"] in {"CBOT_PATH_PARTIALLY_PREDICTABLE", "CBOT_PATH_DOMINATES_BUT_HARD_TO_TIME",
                              "TOO_FEW", "TOO_FEW_COMPRESSIONS"}
