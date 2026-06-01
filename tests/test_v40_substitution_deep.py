"""Tests V40 — substitution blé/maïs approfondie (offline, master synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v40_substitution_deep as v40


def _synthetic_master(n=900, seed=13):
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
        "corn_realized_vol_20": s.pct_change().rolling(20).std().values,
        "ema_oi_total": rng.uniform(500, 5000, n),
        "curve_backwardation_proxy": rng.normal(0, 1, n),
        "gas_close": 3 + np.cumsum(rng.normal(0, 0.05, n)),
    }, index=idx)


def test_eu_specificity_reports_both_corrs():
    df = _synthetic_master()
    out = v40.eu_specificity(df)
    assert "corr_ratio_basis_EU" in out and "corr_ratio_cbot" in out
    assert "substitution_is_EU_specific" in out


def test_run_v40_flags_matif_data_gated(tmp_path, monkeypatch):
    monkeypatch.setattr(v40, "V40_DIR", tmp_path)
    out = v40.run_v40_substitution_deep(_synthetic_master())
    if out.get("verdict") != "TOO_SHORT":
        assert "data_gated" in out
        assert "matif_wheat_corn_ratio" in out["data_gated"]
