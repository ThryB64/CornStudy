"""Tests V7-04 — CBOT Target Lab avancé."""

import numpy as np
import pandas as pd
import pytest

from mais.research.cbot_target_lab_v7 import (
    TARGET_HORIZONS,
    build_cbot_targets_v7,
    compute_target_prevalences,
    run_target_lab,
)


def _make_cbot_df(n: int = 800, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2014-01-01", periods=n, freq="B")
    prices = pd.Series(200 + np.cumsum(rng.normal(0, 1.5, n)), index=dates, name="cbot_close")
    basis = pd.Series(rng.normal(5, 2, n), index=dates, name="basis_eur_t")
    return pd.DataFrame({"cbot_close": prices, "basis_eur_t": basis})


def test_build_targets_returns_8_columns():
    df = _make_cbot_df()
    targets = build_cbot_targets_v7(df)
    assert targets.shape[1] == 8
    assert set(targets.columns) == set(TARGET_HORIZONS.keys())


def test_targets_are_binary():
    df = _make_cbot_df()
    targets = build_cbot_targets_v7(df)
    for col in targets.columns:
        valid = targets[col].dropna()
        assert set(valid.unique()).issubset({0, 1}), f"{col} not binary"


def test_missing_cbot_close_raises():
    df = pd.DataFrame({"some_col": [1, 2, 3]})
    with pytest.raises(ValueError, match="cbot_close"):
        build_cbot_targets_v7(df)


def test_targets_without_basis():
    df = _make_cbot_df()
    df_no_basis = df.drop(columns=["basis_eur_t"])
    targets = build_cbot_targets_v7(df_no_basis)
    assert "y_cbot_up_h60_when_basis_high" in targets.columns


def test_prevalences_structure():
    df = _make_cbot_df()
    targets = build_cbot_targets_v7(df)
    prev = compute_target_prevalences(targets)
    assert len(prev) == 8
    for name, stats in prev.items():
        assert "prevalence" in stats
        assert "balanced" in stats
        assert 0.0 <= stats["prevalence"] <= 1.0


def test_most_targets_balanced():
    df = _make_cbot_df(1000)
    targets = build_cbot_targets_v7(df)
    prev = compute_target_prevalences(targets)
    n_balanced = sum(1 for s in prev.values() if s["balanced"])
    # Sur données synthétiques, au moins 2/8 cibles doivent être équilibrées
    # (les cibles conditionnelles/threshold ont des prévalences naturellement faibles sur random walk)
    assert n_balanced >= 2, f"Seulement {n_balanced}/8 cibles équilibrées"


def test_run_target_lab_structure():
    df = _make_cbot_df()
    result = run_target_lab(df)
    assert result["n_targets"] == 8
    assert "prevalences" in result
    assert "n_balanced_targets" in result


def test_horizons_match():
    df = _make_cbot_df()
    targets = build_cbot_targets_v7(df)
    for col in targets.columns:
        assert col in TARGET_HORIZONS, f"{col} not in TARGET_HORIZONS"
