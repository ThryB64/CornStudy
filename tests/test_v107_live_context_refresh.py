"""Tests V107 — refresh contexte live (offline, fetch + journal mockés)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v107_live_context_refresh as v107


def _market(n=400, seed=2):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2024-09-01", periods=n)
    corn = 450 + np.cumsum(rng.normal(0, 2, n))
    return pd.DataFrame({
        "corn_close": corn, "wheat_close": corn * 1.2 + rng.normal(0, 5, n),
        "soy_close": corn * 2.4, "oil_close": 70 + np.cumsum(rng.normal(0, 0.2, n)),
        "gas_close": 3 + np.cumsum(rng.normal(0, 0.02, n)),
    }, index=idx)


def test_build_live_context_frame():
    frame = v107.build_live_context_frame(_market(), official_basis_z=2.04)
    assert "corn_sma_50" in frame.columns
    assert frame["ema_cbot_basis_zscore_52w"].iloc[-1] == 2.04
    assert frame["ema_cbot_basis_zscore_52w"].iloc[:-1].isna().all()


def test_run_v107(tmp_path, monkeypatch):
    jp = tmp_path / "journal.parquet"
    pd.DataFrame([{"price_date": pd.Timestamp("2026-06-01"), "signal_tier": "SHORT_PREMIUM_EXTREME",
                   "basis_z_used": 2.039}]).to_parquet(jp, index=False)
    monkeypatch.setattr(v107, "V107_DIR", tmp_path)
    monkeypatch.setattr(v107, "OFFICIAL_JOURNAL", jp)
    mk = _market()
    mk.index = pd.bdate_range(end="2026-06-01", periods=len(mk))  # finit à la date du signal
    monkeypatch.setattr(v107, "fetch_live_market", lambda try_network=True: mk)
    monkeypatch.setattr(v107, "fetch_live_cot",
                        lambda try_network=True: {"report_date": "2026-05-26", "mm_net_pct_oi": 0.11})
    monkeypatch.setattr(v107, "_cot_historical_median", lambda: 0.02)
    out = v107.run_v107_context_refresh(try_network=True)
    assert out["version"] == "V107-CONTEXT-REFRESH"
    assert out["verdict"] in ("CONTEXT_REFRESHED_FRESH", "CONTEXT_REFRESHED_BUT_LAGGED")
    assert out["cbot_support_v2_live"] in ("LOW", "MEDIUM", "HIGH", "NO_SIGNAL")
    assert out["cot_favorable"] == 1  # 0.11 > 0.02
    assert out["context_lag_days"] <= 5


def test_run_v107_offline(tmp_path, monkeypatch):
    jp = tmp_path / "journal.parquet"
    pd.DataFrame([{"price_date": pd.Timestamp("2026-06-01"), "signal_tier": "SHORT_PREMIUM_EXTREME",
                   "basis_z_used": 2.0}]).to_parquet(jp, index=False)
    monkeypatch.setattr(v107, "V107_DIR", tmp_path)
    monkeypatch.setattr(v107, "OFFICIAL_JOURNAL", jp)
    monkeypatch.setattr(v107, "fetch_live_market", lambda try_network=True: pd.DataFrame())
    out = v107.run_v107_context_refresh(try_network=False)
    assert out["verdict"] == "NO_MARKET_DATA_OFFLINE"
