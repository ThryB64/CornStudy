"""Tests V7-30 — Red team validation."""

import numpy as np
import pandas as pd
import pytest

from mais.research.red_team_validation import (
    _auc_stability_across_years,
    _auc_vs_null_ratio,
    _class_balance_check,
    _n_oof_minimum,
    _no_target_in_features_check,
    _overfitting_gap_check,
    _permutation_auc,
    _random_feature_baseline,
    _temporal_shuffle_degradation,
    run_red_team,
)


def _synthetic_signal(n: int = 300, seed: int = 42) -> tuple:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2015-01-01", periods=n, freq="B")
    y_score = rng.uniform(0, 1, n)
    # Slightly biased toward correct: add score to a threshold
    y_true = (y_score + rng.normal(0, 0.3, n) > 0.5).astype(int)
    return dates, y_true, y_score


def test_permutation_auc_null_p_value():
    dates, y_true, y_score = _synthetic_signal()
    result = _permutation_auc(y_true, y_score, n_permutations=200)
    assert "p_value" in result
    assert 0.0 <= result["p_value"] <= 1.0


def test_permutation_auc_perfect_signal():
    rng = np.random.default_rng(0)
    n = 200
    y_true = rng.integers(0, 2, n)
    y_score = y_true.astype(float) + rng.normal(0, 0.01, n)
    result = _permutation_auc(y_true, y_score, n_permutations=200)
    assert result["observed_auc"] > 0.9
    assert result["passed"]


def test_random_feature_baseline():
    _, y_true, _ = _synthetic_signal()
    result = _random_feature_baseline(y_true, n_features=10)
    assert result["passed"]
    assert 0.3 <= result["random_auc"] <= 0.7


def test_temporal_shuffle_degrades_perfect_signal():
    rng = np.random.default_rng(7)
    n = 300
    y_true = rng.integers(0, 2, n)
    y_score = y_true.astype(float) + rng.normal(0, 0.05, n)
    result = _temporal_shuffle_degradation(y_true, y_score)
    assert result["observed_auc"] > result["shuffled_auc"]


def test_class_balance_normal():
    rng = np.random.default_rng(0)
    y_true = rng.integers(0, 2, 300)
    result = _class_balance_check(y_true)
    assert result["passed"]


def test_class_balance_extreme():
    y_true = np.zeros(300, dtype=int)
    result = _class_balance_check(y_true)
    assert not result["passed"]


def test_n_oof_minimum_ok():
    result = _n_oof_minimum(100)
    assert result["passed"]


def test_n_oof_minimum_fragile():
    result = _n_oof_minimum(20)
    assert not result["passed"]


def test_overfitting_gap_ok():
    result = _overfitting_gap_check(auc_train=0.85, auc_oof=0.80)
    assert result["passed"]


def test_overfitting_gap_fails():
    result = _overfitting_gap_check(auc_train=0.99, auc_oof=0.60)
    assert not result["passed"]


def test_no_target_in_features_clean():
    features = ["ema_spread", "vol_30d", "basis_score"]
    result = _no_target_in_features_check(features)
    assert result["passed"]


def test_no_target_in_features_leak():
    features = ["ema_spread", "y_rel_outperform_h90"]
    result = _no_target_in_features_check(features)
    assert not result["passed"]
    assert "y_rel_outperform_h90" in result["suspect_features"]


def test_auc_vs_null_ratio_ok():
    result = _auc_vs_null_ratio(auc=0.80)
    assert result["passed"]


def test_auc_vs_null_ratio_fail():
    result = _auc_vs_null_ratio(auc=0.51)
    assert not result["passed"]


def test_auc_stability_across_years():
    dates, y_true, y_score = _synthetic_signal(n=500)
    result = _auc_stability_across_years(dates, y_true, y_score, min_auc_per_year=0.3)
    assert "year_aucs" in result


def test_run_red_team_returns_verdict():
    dates, y_true, y_score = _synthetic_signal(n=500)
    result = run_red_team(
        y_true=y_true,
        y_score=y_score,
        dates=dates,
        feature_names=["feat_a", "feat_b"],
        auc_train=0.70,
        n_oof=300,
        n_permutations=100,
    )
    assert "verdict" in result
    assert result["verdict"] in {"GO_RESEARCH", "NEEDS_REVIEW", "RED_FLAG"}
    assert result["n_tests"] == 11
    assert 0 <= result["n_passed"] <= 11
