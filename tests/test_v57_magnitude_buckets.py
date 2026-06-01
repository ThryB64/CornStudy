"""Tests V57 — classes de magnitude de compression (offline, master synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v57_magnitude_buckets as v57


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
    return pd.DataFrame({
        "corn_close": cbot * 9.5, "cbot_eur_t": cbot, "ema_close": ema,
        "ema_cbot_basis": basis, "ema_cbot_basis_zscore_52w": bz.values,
        "wheat_close": cbot * 9.5 * wc,
        "corn_sma_50": (s * 9.5).rolling(50).mean().values,
        "corn_logret_20d": np.log(s / s.shift(20)).values,
        "cot_mm_net_pct_oi_x": rng.normal(0, 10, n),
    }, index=idx)


def test_run_v57(tmp_path, monkeypatch):
    monkeypatch.setattr(v57, "V57_DIR", tmp_path)
    out = v57.run_v57_buckets(_synthetic_master())
    assert out["version"] == "V57-MAGNITUDE-BUCKETS"
    if out["verdict"] != "TOO_FEW":
        o = out["overall"]
        for k in ("mfe_gt_5", "mfe_gt_10", "mfe_gt_20", "reach_z05_le40_rate", "reach_z0_le90_rate"):
            assert 0.0 <= o[k] <= 1.0
        assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"


def test_outcomes_bounds():
    o = v57._signal_outcomes(_synthetic_master())
    assert {"mfe", "reach_z05_le40", "reach_z0_le90"} <= set(o.columns)
    assert o["reach_z05_le40"].isin([0, 1]).all()
    assert o["reach_z0_le90"].isin([0, 1]).all()
