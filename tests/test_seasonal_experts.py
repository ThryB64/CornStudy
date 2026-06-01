"""Tests V7-06 — Modèles saisonniers experts."""

import numpy as np
import pandas as pd
import pytest

from mais.research.seasonal_experts_v7 import (
    ALL_POLICY_NAMES,
    backtest_seasonal_policy,
    compute_policy_coverage,
    crop_year_expert,
    event_driven,
    get_crop_phase,
    get_policy_mask,
    monthly_expert,
    rolling_52w_best,
    run_seasonal_expert_comparison,
)


def _make_dates(n: int = 600) -> pd.DatetimeIndex:
    return pd.date_range("2015-01-01", periods=n, freq="B")


def _make_binary_series(dates: pd.DatetimeIndex, seed: int = 42) -> pd.Series:
    rng = np.random.default_rng(seed)
    return pd.Series(rng.integers(0, 2, len(dates)).astype(float), index=dates)


def test_get_crop_phase_all_months():
    expected = {
        3: "PLANTING", 4: "PLANTING", 5: "PLANTING",
        6: "GROWING", 7: "GROWING", 8: "GROWING",
        9: "HARVEST", 10: "HARVEST", 11: "HARVEST",
        12: "POST_HARVEST", 1: "POST_HARVEST", 2: "POST_HARVEST",
    }
    for month, phase in expected.items():
        assert get_crop_phase(month) == phase, f"Month {month}: expected {phase}"


def test_monthly_expert_returns_bool():
    dates = _make_dates()
    mask = monthly_expert(dates)
    assert mask.dtype == bool
    assert len(mask) == len(dates)


def test_monthly_expert_active_in_favorable_months():
    dates = _make_dates()
    favorable = frozenset({3, 4})
    mask = monthly_expert(dates, favorable_months=favorable)
    assert mask[dates.month == 3].all()
    assert mask[dates.month == 4].all()
    assert not mask[dates.month == 1].any()


def test_crop_year_expert_active_growing_post_harvest():
    dates = _make_dates(500)
    mask = crop_year_expert(dates)
    # Growing = June-Aug, Post_harvest = Dec-Feb
    growing_months = {6, 7, 8}
    post_harvest_months = {12, 1, 2}
    active_months = set(dates[mask].month.unique())
    assert active_months.issubset(growing_months | post_harvest_months)


def test_rolling_52w_best_returns_bool():
    dates = _make_dates(400)
    y_train = _make_binary_series(dates[:300])
    mask = rolling_52w_best(dates, y_train)
    assert mask.dtype == bool


def test_event_driven_active_start_of_month():
    dates = _make_dates(300)
    mask = event_driven(dates)
    # All days with day <= 7 should be active
    early_days = dates[dates.day <= 7]
    assert mask[early_days].all()


def test_get_policy_mask_all_policies():
    dates = _make_dates(300)
    y_train = _make_binary_series(dates[:200])
    for policy in ALL_POLICY_NAMES:
        mask = get_policy_mask(policy, dates, y_train)
        assert isinstance(mask, pd.Series)
        assert len(mask) == len(dates)


def test_get_policy_mask_no_filter_all_true():
    dates = _make_dates()
    mask = get_policy_mask("no_filter", dates)
    assert mask.all()


def test_get_policy_mask_unknown_raises():
    dates = _make_dates()
    with pytest.raises(ValueError, match="inconnue"):
        get_policy_mask("invalid_policy", dates)


def test_compute_policy_coverage_structure():
    dates = _make_dates(300)
    result = compute_policy_coverage("monthly_classic", dates)
    assert "coverage" in result
    assert 0.0 <= result["coverage"] <= 1.0


def test_backtest_no_signal():
    dates = _make_dates(300)
    y_true = _make_binary_series(dates)
    y_pred = pd.Series(0.0, index=dates)  # no confidence → no trade
    result = backtest_seasonal_policy(dates, y_true, y_pred, "monthly_classic")
    assert result["n_trades"] == 0
    assert result["verdict"] == "NO_SIGNAL"


def test_backtest_with_signal():
    dates = _make_dates(300)
    y_true = _make_binary_series(dates)
    y_pred = pd.Series(0.8, index=dates)  # always confident
    result = backtest_seasonal_policy(dates, y_true, y_pred, "no_filter")
    assert result["n_trades"] > 0
    assert result["verdict"] == "RESEARCH_ONLY_NOT_TRADING"


def test_run_comparison_structure():
    dates = _make_dates(500)
    y_true = _make_binary_series(dates)
    result = run_seasonal_expert_comparison(dates, y_true)
    assert result["n_dates"] == len(dates)
    assert set(result["coverages"].keys()) == set(ALL_POLICY_NAMES)
    assert "v6_reference" in result
