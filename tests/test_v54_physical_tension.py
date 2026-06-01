"""Tests V54 — physical tension score (offline, master synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v54_physical_tension as v54


def _synthetic(n=700, seed=7):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-01", periods=n)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    basis = 30 + 14 * np.sin(np.linspace(0, 12 * np.pi, n)) + rng.normal(0, 2, n)
    bz = (pd.Series(basis) - pd.Series(basis).rolling(60, min_periods=20).mean()) / (
        pd.Series(basis).rolling(60, min_periods=20).std() + 1e-9)
    spread = rng.normal(-1.5, 2.0, n)
    backw = (spread > 0).astype(int)
    return pd.DataFrame({
        "cbot_eur_t": cbot, "ema_close": cbot + basis,
        "ema_cbot_basis": basis, "ema_cbot_basis_zscore_52w": bz.values,
        "ema_backwardation_flag": backw, "ema_spread_f0_f1": spread,
    }, index=idx)


def test_compute_physical_tension_tiers():
    pt = v54.compute_physical_tension(_synthetic())
    assert "physical_tension" in pt.columns
    assert set(pt["physical_tension"].unique()) <= {
        "NO_SIGNAL", "NO_CURVE_DATA", "LOW", "MEDIUM", "HIGH"}
    active = pt["physical_tension"].isin(["LOW", "MEDIUM", "HIGH"])
    # score borné 0..2 là où actif
    assert pt.loc[active, "physical_tension_score"].between(0, 2).all()


def test_run_v54(tmp_path, monkeypatch):
    monkeypatch.setattr(v54, "V54_DIR", tmp_path)
    out = v54.run_v54_tension(_synthetic())
    assert out["version"] == "V54-PHYSICAL-TENSION"
    assert "coverage" in out
    assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"


def test_no_curve_data_marked():
    df = _synthetic()
    df["ema_backwardation_flag"] = np.nan
    df["ema_spread_f0_f1"] = np.nan
    pt = v54.compute_physical_tension(df)
    active = pt["basis_z"] >= 1.0
    assert (pt.loc[active, "physical_tension"] == "NO_CURVE_DATA").any()
