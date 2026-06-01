"""Tests V11 — programme discipliné."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mais.research.v11_simplified_program import (
    _benjamini_hochberg,
    run_basis_change_regression,
    run_cost_aware_decision,
    run_forward_regime_filter,
    run_promote_simplified,
    run_simple_rules_lab_v11,
)


@pytest.fixture
def synthetic_df():
    rng = np.random.default_rng(2)
    n = 2200
    idx = pd.date_range("2010-01-01", periods=n, freq="B")
    cbot = 150 + np.cumsum(rng.normal(0, 1, n))
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
        "ema_data_availability_score": np.clip(rng.normal(0.8, 0.1, n), 0, 1),
        "days_to_next_wasde": rng.integers(3, 30, n),
        "corn_macd_hist": rng.normal(0, 1, n),
        "corn_realized_vol_20": np.abs(rng.normal(0.2, 0.05, n)),
    }, index=idx)
    return df


def test_bh_correction():
    # p très petits -> retenus ; grands -> rejetés
    keep = _benjamini_hochberg([0.001, 0.002, 0.5, 0.9], q=0.10)
    assert keep[0] and keep[1]
    assert not keep[3]


def test_promote_simplified(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v11_simplified_program as mod
    monkeypatch.setattr(mod, "V11_DIR", tmp_path)
    out = run_promote_simplified(synthetic_df)
    assert out["verdict"] in {"PROMOTE_SIMPLIFIED", "KEEP_6VAR"}
    assert "model_2var_simplified" in out["comparison"]
    assert "model_6var" in out["comparison"]


def test_forward_regime_filter(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v11_simplified_program as mod
    monkeypatch.setattr(mod, "V11_DIR", tmp_path)
    out = run_forward_regime_filter(synthetic_df)
    assert out["verdict"] in {"REGIME_FILTER_HELPS_FORWARD", "REGIME_FILTER_POST_HOC_ONLY"}


def test_cost_aware_decision(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v11_simplified_program as mod
    monkeypatch.setattr(mod, "V11_DIR", tmp_path)
    out = run_cost_aware_decision(synthetic_df)
    assert out["verdict"] in {"COST_AWARE_BREAKS_WALL", "COST_WALL_PERSISTS", "TOO_FEW_TRADES"}


def test_basis_change_regression(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v11_simplified_program as mod
    monkeypatch.setattr(mod, "V11_DIR", tmp_path)
    out = run_basis_change_regression(synthetic_df)
    assert out["verdict"] == "BASIS_CHANGE_REGRESSION_DONE"
    assert out["best_horizon_by_sign_da"] is not None


def test_simple_rules_lab(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v11_simplified_program as mod
    monkeypatch.setattr(mod, "V11_DIR", tmp_path)
    out = run_simple_rules_lab_v11(synthetic_df)
    assert out["verdict"] in {"STABLE_RULES_FOUND", "NO_RULE_SURVIVES_COST_AND_FDR"}
    assert out["n_rules_tested"] > 0
    assert "bh_significant" in out["top_rules_by_pvalue"][0]
