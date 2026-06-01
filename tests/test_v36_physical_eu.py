"""Tests V36 — drivers physiques EU (offline, master + TTF synthétiques)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v36_physical_eu_drivers as v36


def _synthetic_master(n=520, seed=5):
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
        "wheat_close": cbot * 9.5 * (1.3 + rng.normal(0, 0.05, n)),
    }, index=idx)


def _fake_phys(index):
    rng = np.random.default_rng(7)
    return pd.DataFrame({
        "ttf_eur": rng.uniform(10, 50, len(index)),
        "ttf_z": rng.normal(0, 1, len(index)),
        "ttf_mom_60": rng.normal(0, 0.2, len(index)),
    }, index=index)


def test_v36_honest_overfit_flag(monkeypatch, tmp_path):
    monkeypatch.setattr(v36, "V36_DIR", tmp_path)
    monkeypatch.setattr(v36, "_eu_physical_series", _fake_phys)
    out = v36.run_v36_physical(_synthetic_master())
    if out["verdict"] not in {"NO_TTF_DATA", "TOO_FEW_TRADES"}:
        assert "basis_corr_wheat_corn_ratio" in out
        # avec n_adverse petit, le gain AUC doit être signalé non robuste
        if out.get("n_features_full_model", 0) > out.get("n_adverse_events", 99):
            assert out["adverse_verdict"] == "ADVERSE_AUC_GAIN_NOT_ROBUST_TOO_FEW_EVENTS"


def test_eu_physical_series_real_csv():
    # le vrai CSV eu_cross_assets existe : ttf_z doit être produit
    idx = pd.bdate_range("2016-01-01", periods=400)
    phys = v36._eu_physical_series(idx)
    assert "ttf_z" in phys.columns
