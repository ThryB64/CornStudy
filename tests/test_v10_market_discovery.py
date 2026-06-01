"""Tests V10 — Market Discovery."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mais.research.v10_market_discovery import (
    run_basis_econometrics,
    run_cost_survival,
    run_feature_attribution,
    run_horizon_sweep,
    run_regime_conditioning,
    run_simplified_model,
)


@pytest.fixture
def synthetic_df():
    rng = np.random.default_rng(1)
    n = 1600
    idx = pd.date_range("2011-01-01", periods=n, freq="B")
    cbot = 150 + np.cumsum(rng.normal(0, 1, n))
    # basis mean-reverting AR(1) phi=0.95
    bz = np.zeros(n)
    for t in range(1, n):
        bz[t] = 0.95 * bz[t - 1] + rng.normal(0, 0.3)
    ema = cbot + 30 - 5 * bz + rng.normal(0, 2, n)
    df = pd.DataFrame({
        "cbot_eur_t": cbot,
        "ema_close": ema,
        "ema_cbot_basis": ema - cbot,
        "ema_cbot_basis_zscore_52w": bz,
        "eurusd": 1.1 + rng.normal(0, 0.02, n),
        "ema_oi_total": rng.uniform(1000, 5000, n),
        "corn_realized_vol_20": np.abs(rng.normal(0.2, 0.05, n)),
        "corn_macd_hist": rng.normal(0, 1, n),
    }, index=idx)
    return df


def test_basis_econometrics_halflife(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v10_market_discovery as mod
    monkeypatch.setattr(mod, "V10_DIR", tmp_path)
    out = run_basis_econometrics(synthetic_df)
    assert "basis_z" in out
    # AR(1) phi~0.95 -> half-life ~13.5 jours, doit être détecté mean-reverting
    assert out["basis_z"]["ar1_phi"] > 0.8
    assert out["verdict"] in {"BASIS_MEAN_REVERTING", "BASIS_SLOW_OR_NONSTATIONARY"}


def test_feature_attribution_ranks(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v10_market_discovery as mod
    monkeypatch.setattr(mod, "V10_DIR", tmp_path)
    out = run_feature_attribution(synthetic_df, n_repeats=2)
    assert out["verdict"] == "ATTRIBUTION_DONE"
    assert len(out["ranking"]) == 6
    # basis_z doit ressortir important (le signal y est construit dessus)
    assert "basis_z" in out["ranking"][:3]


def test_horizon_sweep(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v10_market_discovery as mod
    monkeypatch.setattr(mod, "V10_DIR", tmp_path)
    out = run_horizon_sweep(synthetic_df)
    assert out["verdict"] == "HORIZON_SWEEP_DONE"
    assert out["best_horizon"] is not None


def test_cost_survival(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v10_market_discovery as mod
    monkeypatch.setattr(mod, "V10_DIR", tmp_path)
    out = run_cost_survival(synthetic_df)
    assert out["verdict"] in {"COST_WALL_BROKEN_FORWARD", "COST_WALL_CONFIRMED", "TOO_FEW_TRADES"}
    if "selectivity_curve" in out:
        assert "top_100pct_conf" in out["selectivity_curve"]


def test_regime_conditioning(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v10_market_discovery as mod
    monkeypatch.setattr(mod, "V10_DIR", tmp_path)
    out = run_regime_conditioning(synthetic_df)
    assert out["verdict"] == "REGIME_ANALYSIS_DONE"
    assert "results_by_regime" in out


def test_simplified_model(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v10_market_discovery as mod
    monkeypatch.setattr(mod, "V10_DIR", tmp_path)
    out = run_simplified_model(synthetic_df)
    assert out["verdict"] in {"SIMPLER_IS_BETTER", "SIMPLIFICATION_NEUTRAL"}
    assert set(out["results_by_subset"]) == set(mod.FEATURE_SUBSETS)
    assert out["best_subset"] is not None
