"""Tests V7-10 — Event study premium."""

import numpy as np
import pandas as pd

from mais.research.event_study_v7 import (
    EVENT_TYPES,
    compute_abnormal_return,
    compute_event_window,
    run_event_study,
)


def _make_prices(n: int = 500) -> pd.Series:
    rng = np.random.default_rng(42)
    dates = pd.date_range("2013-01-01", periods=n, freq="B")
    return pd.Series(200 + np.cumsum(rng.normal(0, 2, n)), index=dates)


def test_event_window_valid():
    prices = _make_prices()
    w = compute_event_window(prices, prices.index[100], pre=30, post=60)
    assert w is not None
    assert len(w) == 91  # 30 + 1 + 60


def test_event_window_too_close_to_start():
    prices = _make_prices()
    w = compute_event_window(prices, prices.index[5], pre=30, post=60)
    assert w is None


def test_abnormal_return_no_events():
    prices = _make_prices()
    result = compute_abnormal_return(prices, [])
    assert result["n_events"] == 0
    assert result["p_value"] is None


def test_abnormal_return_with_events():
    prices = _make_prices(600)
    events = [prices.index[100], prices.index[200], prices.index[300]]
    result = compute_abnormal_return(prices, events)
    assert result["n_events"] <= 3
    if result["n_events"] > 0:
        assert 0 <= result["p_value"] <= 1


def test_run_event_study_all_types():
    prices = _make_prices(600)
    result = run_event_study(prices)
    assert set(result["results"].keys()) == set(EVENT_TYPES.keys())
    assert result["n_event_types"] == 8


def test_run_event_study_window_config():
    prices = _make_prices(600)
    result = run_event_study(prices)
    assert result["window_pre"] == 30
    assert result["window_post"] == 60
