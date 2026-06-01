"""Tests V65 — CBOT rebound engine (offline, master synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v65_cbot_rebound_engine as v65


def _synthetic(n=1200, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2013-01-01", periods=n)
    corn = 150 + np.cumsum(rng.normal(0, 1.0, n))
    s = pd.Series(corn, index=idx)
    return pd.DataFrame({
        "corn_close": corn,
        "corn_sma_50": s.rolling(50).mean().values,
        "corn_logret_20d": np.log(s / s.shift(20)).values,
        "corn_logret_5d": np.log(s / s.shift(5)).values,
        "corn_rsi_14": (50 + 10 * rng.normal(0, 1, n)).clip(0, 100),
        "corn_realized_vol_20": s.pct_change().rolling(20).std().values,
        "cot_mm_net_pct_oi_x": rng.normal(0, 10, n),
        "corn_wheat_ratio": 0.8 + rng.normal(0, 0.05, n),
        "soy_close": corn * 2.5 + rng.normal(0, 5, n),
        "usd_index_close": 95 + np.cumsum(rng.normal(0, 0.1, n)),
        # minimal pour build_adverse_frame
        "cbot_eur_t": corn, "ema_close": corn + 30, "ema_cbot_basis": 30 + rng.normal(0, 2, n),
        "ema_cbot_basis_zscore_52w": rng.normal(0, 1, n),
    }, index=idx)


def test_rebound_features_shifted():
    f = v65.rebound_features(_synthetic())
    assert "dist_sma50" in f.columns and "drawdown60" in f.columns
    assert len(f.columns) == 10


def test_run_v65(tmp_path, monkeypatch):
    monkeypatch.setattr(v65, "V65_DIR", tmp_path)
    out = v65.run_v65_rebound(_synthetic())
    assert out["version"] == "V65-CBOT-REBOUND"
    if out["verdict"] != "NO_DATA":
        assert "oof_by_horizon" in out
        assert out["verdict"] in (
            "CBOT_REBOUND_OOF_USEFUL_ADD_TO_CBOT_SUPPORT",
            "CBOT_REBOUND_OOF_WEAK_KEEP_RULE_BASED_SUPPORT")
        assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"
