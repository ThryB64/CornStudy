"""Tests V32 — détection du chemin ADVERSE (offline, master synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v32_adverse_path_research as v32


def _synthetic_master(n=520, seed=3):
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


def test_classify_path_signs():
    ema = pd.Series({pd.Timestamp("2015-01-01"): 200.0, pd.Timestamp("2015-02-01"): 190.0})
    cbot = pd.Series({pd.Timestamp("2015-01-01"): 150.0, pd.Timestamp("2015-02-01"): 160.0})
    # CBOT monte, EMA baisse -> basis comprime, CBOT contribue le plus
    assert v32._classify_path(ema, cbot, "2015-01-01", "2015-02-01") in {"CBOT_DRIVEN", "BOTH"}
    ema2 = pd.Series({pd.Timestamp("2015-01-01"): 200.0, pd.Timestamp("2015-02-01"): 215.0})
    cbot2 = pd.Series({pd.Timestamp("2015-01-01"): 150.0, pd.Timestamp("2015-02-01"): 150.0})
    # EMA monte, CBOT stable -> basis s'écarte -> ADVERSE
    assert v32._classify_path(ema2, cbot2, "2015-01-01", "2015-02-01") == "ADVERSE"


def test_run_v32_produces_verdict():
    df = _synthetic_master()
    out = v32.run_v32_adverse(df)
    assert out["version"] == "V32-ADVERSE"
    assert out["verdict"] in {"ADVERSE_PARTIALLY_PREDICTABLE", "ADVERSE_WEAKLY_PREDICTABLE", "TOO_FEW"}
    if out["verdict"] != "TOO_FEW":
        assert "profile_adverse" in out and "separators_adverse_minus_compressed" in out


def test_build_frame_has_entry_features():
    df = _synthetic_master()
    adf = v32.build_adverse_frame(df)
    if len(adf):
        for c in ["entry_z", "basis_level", "backwardation", "adverse", "path"]:
            assert c in adf.columns
