"""Tests V7-31 — Benchmark suite naïf et professionnel."""

import numpy as np
import pandas as pd
import pytest

from mais.research.benchmark_suite import (
    ALL_BENCHMARK_NAMES,
    NaiveBenchmarks,
    ProfessionalBenchmarks,
    _safe_auc,
    compute_delta_auc,
    evaluate_all_benchmarks,
    run_benchmark_suite,
)


def _make_binary_target(n: int = 300, seed: int = 42) -> pd.Series:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2015-01-01", periods=n, freq="B")
    return pd.Series(rng.integers(0, 2, n).astype(float), index=dates)


def _make_prices(n: int = 300, seed: int = 42) -> pd.Series:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2015-01-01", periods=n, freq="B")
    return pd.Series(np.cumsum(rng.normal(0, 1, n)) + 200, index=dates)


def test_random_benchmark_length():
    y = _make_binary_target()
    scores = NaiveBenchmarks.random(y)
    assert len(scores) == len(y)
    assert ((scores >= 0) & (scores <= 1)).all()


def test_persistence_benchmark():
    y = _make_binary_target()
    scores = NaiveBenchmarks.persistence(y)
    assert len(scores) == len(y)
    assert scores.notna().all()


def test_naive_seasonal_benchmark():
    y = _make_binary_target()
    scores = NaiveBenchmarks.naive_seasonal(y)
    assert len(scores) == len(y)
    assert set(scores.unique()).issubset({0.0, 1.0})


def test_always_up_is_constant_one():
    y = _make_binary_target()
    scores = NaiveBenchmarks.always_up(y)
    assert (scores == 1.0).all()


def test_always_down_is_constant_zero():
    y = _make_binary_target()
    scores = NaiveBenchmarks.always_down(y)
    assert (scores == 0.0).all()


def test_momentum_20d():
    prices = _make_prices()
    scores = ProfessionalBenchmarks.momentum_20d(prices)
    assert len(scores) == len(prices)
    assert set(scores.dropna().unique()).issubset({0.0, 0.5, 1.0})


def test_trend_following_52w():
    prices = _make_prices()
    scores = ProfessionalBenchmarks.trend_following_52w(prices)
    assert len(scores) == len(prices)


def test_carry_signal():
    prices = _make_prices()
    scores = ProfessionalBenchmarks.carry_signal(prices)
    assert len(scores) == len(prices)


def test_safe_auc_too_few_samples():
    y = pd.Series([1.0] * 5)
    s = pd.Series([0.5] * 5)
    assert _safe_auc(y, s) is None


def test_safe_auc_pure_class():
    y = pd.Series([1.0] * 50)
    s = pd.Series(np.random.default_rng(0).random(50))
    assert _safe_auc(y, s) is None


def test_evaluate_all_benchmarks_returns_8():
    y = _make_binary_target()
    aucs = evaluate_all_benchmarks(y)
    assert set(aucs.keys()) == set(ALL_BENCHMARK_NAMES)
    assert len(aucs) == 8


def test_compute_delta_auc():
    bench_aucs = {"random": 0.50, "persistence": 0.52, "momentum_20d": 0.55}
    result = compute_delta_auc(auc_model=0.70, benchmark_aucs=bench_aucs)
    assert result["best_baseline"] == "momentum_20d"
    assert result["delta_vs_best"] == pytest.approx(0.70 - 0.55, abs=0.001)


def test_run_benchmark_suite_multi_target():
    y1 = _make_binary_target(300, seed=0)
    y2 = _make_binary_target(300, seed=1)
    targets = {"target_h90": y1, "target_h60": y2}
    result = run_benchmark_suite(targets)
    assert result["n_targets"] == 2
    assert "target_h90" in result["results"]
    assert "target_h60" in result["results"]
    for tgt_result in result["results"].values():
        assert "benchmark_aucs" in tgt_result
        assert "best_benchmark" in tgt_result
