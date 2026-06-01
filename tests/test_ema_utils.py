"""Tests pour UTIL-EMA-01 — Fonctions utilitaires EMA."""

from __future__ import annotations

import numpy as np
import pandas as pd

from mais.research.ema_utils import (
    benjamini_hochberg,
    binary_target_from_condition,
    binary_target_from_future_return,
    bootstrap_ci,
    crop_year,
    direction_accuracy,
    expanding_zscore,
    walk_forward_splits,
)


def test_crop_year_october():
    assert crop_year(pd.Timestamp("2023-10-15")) == 2023


def test_crop_year_september():
    assert crop_year(pd.Timestamp("2023-09-30")) == 2022


def test_crop_year_january():
    assert crop_year(pd.Timestamp("2024-01-10")) == 2023


def test_expanding_zscore_anti_leakage():
    s = pd.Series(range(100), dtype=float)
    z = expanding_zscore(s, min_periods=10)
    # shift(1) means first 10 non-null values start after index 10
    assert z.iloc[:10].isna().all(), "Pas de valeurs avant min_periods"
    # Values should not be computed from future data
    assert not z.isna().all()


def test_bootstrap_ci_contains_truth():
    rng = np.random.default_rng(0)
    values = rng.normal(0.5, 0.1, 500)
    ci = bootstrap_ci(values, np.mean, n_draws=500)
    assert ci["ci_lo"] <= ci["estimate"] <= ci["ci_hi"]
    assert ci["ci_lo"] < 0.6 and ci["ci_hi"] > 0.4


def test_bootstrap_ci_keys():
    ci = bootstrap_ci(np.array([1.0, 2.0, 3.0]), np.mean)
    for k in ["estimate", "ci_lo", "ci_hi", "alpha", "n_draws"]:
        assert k in ci


def test_direction_accuracy_perfect():
    y = np.array([1.0, -1.0, 1.0, -1.0])
    assert direction_accuracy(y, y) == 1.0


def test_direction_accuracy_worst():
    y = np.array([1.0, -1.0, 1.0])
    pred = -y
    assert direction_accuracy(y, pred) == 0.0


def test_direction_accuracy_ignores_zeros():
    y = np.array([1.0, 0.0, -1.0])
    pred = np.array([1.0, 999.0, -1.0])
    assert direction_accuracy(y, pred) == 1.0


def test_binary_target_from_future_return_preserves_tail_nan():
    ret = pd.Series([0.1, -0.2, np.nan])
    target = binary_target_from_future_return(ret)
    assert target.tolist()[:2] == [1.0, 0.0]
    assert np.isnan(target.iloc[-1])


def test_binary_target_from_condition_uses_valid_mask():
    condition = pd.Series([True, False, True])
    valid = pd.Series([True, True, False])
    target = binary_target_from_condition(condition, valid)
    assert target.tolist()[:2] == [1.0, 0.0]
    assert np.isnan(target.iloc[-1])


def test_walk_forward_splits_length():
    dates = pd.Series(pd.date_range("2010-10-01", "2020-09-30", freq="B"))
    splits = walk_forward_splits(dates, min_train_years=3)
    assert len(splits) > 0
    for s in splits:
        assert s["n_train_years"] >= 3
        assert "test_crop_year" in s


def test_benjamini_hochberg_all_null():
    ps = [0.5, 0.6, 0.7, 0.8]
    rejected = benjamini_hochberg(ps, alpha=0.05)
    assert not any(rejected)


def test_benjamini_hochberg_all_significant():
    ps = [0.001, 0.002, 0.003, 0.004]
    rejected = benjamini_hochberg(ps, alpha=0.05)
    assert any(rejected)


def test_benjamini_hochberg_empty():
    assert benjamini_hochberg([]) == []
