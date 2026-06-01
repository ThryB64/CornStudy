"""Tests V44 — mécanisme & magnitude (offline, master synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v44_mechanism_magnitude as v44


def _synthetic_master(n=900, seed=15):
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
    }, index=idx)


def test_lead_lag_returns_cross_corr():
    out = v44.lead_lag_cbot_ema(_synthetic_master())
    if out.get("verdict") != "TOO_SHORT":
        assert "cross_corr_by_lag" in out and "contemporaneous" in out
        assert out["verdict"] in {"NONSYNC_PRICING_PEAK_AT_1D", "CONTEMPORANEOUS_DOMINANT"}


def test_run_v44_all(tmp_path, monkeypatch):
    monkeypatch.setattr(v44, "V44_DIR", tmp_path)
    out = v44.run_v44_all(_synthetic_master())
    assert out["version"] == "V44-MECHANISM-MAGNITUDE"
    for k in ["E1_lead_lag", "E2_magnitude", "E3_seasonality"]:
        assert k in out
    cond = out["E2_magnitude"].get("conditional_drop", {})
    assert "mean_drop_when_signal" in cond
