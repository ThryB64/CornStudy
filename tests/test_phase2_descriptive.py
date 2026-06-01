"""Tests V7 Phase 2 — Tickets descriptifs économiques.

V7-10 (Event study), V7-17 (Inter-commodity),
V7-19 (Structural breaks), V7-25 (Market anomalies).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

# V7-10
from mais.research.event_study_v7 import (
    EVENT_TYPES,
    compute_abnormal_return,
    run_event_study,
)

# V7-17
from mais.features.inter_commodity import (
    SPREAD_DEFINITIONS,
    compute_inter_commodity_spreads,
    run_inter_commodity_analysis,
)

# V7-19
from mais.research.structural_breaks import (
    CANDIDATE_BREAKS,
    compute_chow_breakpoint,
    compute_cusum,
    run_structural_breaks,
)

# V7-25
from mais.research.market_anomalies import (
    ANOMALY_TESTS,
    compute_anomaly_pvalue,
    run_market_anomalies,
)


def _make_prices(n: int = 800, seed: int = 42) -> pd.Series:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2008-01-01", periods=n, freq="B")
    return pd.Series(200 + np.cumsum(rng.normal(0, 2, n)), index=dates)


def _make_binary_target(n: int = 800, seed: int = 42) -> pd.Series:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2008-01-01", periods=n, freq="B")
    return pd.Series(rng.integers(0, 2, n).astype(float), index=dates)


# ── V7-10 Event Study ──────────────────────────────────────────────────────────

def test_compute_abnormal_return_no_events():
    prices = _make_prices()
    result = compute_abnormal_return(prices, [])
    assert result["n_events"] == 0


def test_compute_abnormal_return_basic():
    prices = _make_prices(500)
    event_dates = [prices.index[100], prices.index[200], prices.index[300]]
    result = compute_abnormal_return(prices, event_dates)
    assert result["n_events"] <= 3
    if result["n_events"] > 0:
        assert "p_value" in result
        assert 0 <= result["p_value"] <= 1


def test_run_event_study_structure():
    prices = _make_prices(600)
    result = run_event_study(prices)
    assert result["n_event_types"] == len(EVENT_TYPES)
    assert set(result["results"].keys()) == set(EVENT_TYPES.keys())


def test_run_event_study_n_significant_is_int():
    prices = _make_prices(600)
    result = run_event_study(prices)
    assert isinstance(result["n_significant_events"], int)


# ── V7-17 Inter-Commodity ──────────────────────────────────────────────────────

def test_inter_commodity_spreads_returns_6_cols():
    n = 300
    dates = pd.date_range("2015-01-01", periods=n, freq="B")
    rng = np.random.default_rng(0)
    df = pd.DataFrame(
        {"ema_close": 200 + rng.normal(0, 5, n), "cbot_corn": 185 + rng.normal(0, 5, n)},
        index=dates,
    )
    spreads = compute_inter_commodity_spreads(df)
    assert set(spreads.columns) == set(SPREAD_DEFINITIONS.keys())


def test_inter_commodity_analysis_structure():
    n = 300
    dates = pd.date_range("2015-01-01", periods=n, freq="B")
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"ema_close": 200 + rng.normal(0, 5, n)}, index=dates)
    result = run_inter_commodity_analysis(df)
    assert result["n_spreads"] == len(SPREAD_DEFINITIONS)
    assert "mean_rolling_correlations" in result


# ── V7-19 Structural Breaks ────────────────────────────────────────────────────

def test_chow_insufficient_data():
    n = 50
    dates = pd.date_range("2023-01-01", periods=n, freq="B")
    y = pd.Series(np.ones(n), index=dates)
    x = pd.Series(np.ones(n), index=dates)
    result = compute_chow_breakpoint(y, x, "2022-01-01")
    assert result["chow_stat"] is None  # break date not in range


def test_chow_valid_break():
    prices = _make_prices(800)
    returns = prices.pct_change().dropna()
    x = returns.copy()
    result = compute_chow_breakpoint(returns, x, "2012-07-01")
    if result.get("status") == "INSUFFICIENT_DATA":
        pytest.skip("Not enough data around break date")
    assert "chow_stat" in result


def test_cusum_structure():
    prices = _make_prices(400)
    returns = prices.pct_change().dropna()
    result = compute_cusum(returns, returns.shift(1).fillna(0))
    assert "max_cusum" in result or "status" in result


def test_run_structural_breaks():
    n = 800
    dates = pd.date_range("2007-01-01", periods=n, freq="B")
    rng = np.random.default_rng(0)
    df = pd.DataFrame(
        {"ema_close": 200 + np.cumsum(rng.normal(0, 2, n)),
         "cbot_close_eur": 185 + np.cumsum(rng.normal(0, 2, n))},
        index=dates,
    )
    result = run_structural_breaks(df)
    assert "chow_tests" in result
    assert "cusum" in result
    assert isinstance(result["n_significant_breaks"], int)


def test_run_structural_breaks_missing_ema_raises():
    df = pd.DataFrame({"other": [1, 2, 3]})
    with pytest.raises(ValueError, match="ema_close"):
        run_structural_breaks(df)


# ── V7-25 Market Anomalies ─────────────────────────────────────────────────────

def test_compute_anomaly_pvalue_insufficient_data():
    y = pd.Series([1.0] * 5)
    r = pd.Series([0.5] * 5)
    fn = ANOMALY_TESTS["momentum_20d"]
    result = compute_anomaly_pvalue(r, y, fn)
    assert result.get("status") in {"INSUFFICIENT_DATA", "NAN_CORRELATION", "OK"}


def test_run_market_anomalies_structure():
    prices = _make_prices(500)
    returns = prices.pct_change().dropna()
    y_true = _make_binary_target(len(returns))
    y_true.index = returns.index
    result = run_market_anomalies(returns, y_true, n_permutations=50)
    assert result["n_anomalies_tested"] == len(ANOMALY_TESTS)
    assert "results" in result
    assert isinstance(result["n_significant_after_bh"], int)


def test_run_market_anomalies_q_bh_present():
    prices = _make_prices(400)
    returns = prices.pct_change().dropna()
    y_true = _make_binary_target(len(returns))
    y_true.index = returns.index
    result = run_market_anomalies(returns, y_true, n_permutations=50)
    for name, r in result["results"].items():
        if r.get("status") == "OK":
            assert "q_bh" in r, f"{name} missing q_bh"
