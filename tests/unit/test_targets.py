"""Verify the construction of multi-horizon targets."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mais.targets import DEFAULT_HORIZONS, TargetSpec, build_targets


def test_targets_have_all_horizons(synthetic_targets):
    for H in DEFAULT_HORIZONS:
        assert f"y_logret_h{H}" in synthetic_targets.columns
        assert f"y_up_h{H}" in synthetic_targets.columns
        assert f"y_class_h{H}" in synthetic_targets.columns
        assert f"y_realized_vol_h{H}" in synthetic_targets.columns


def test_logret_is_correct(synthetic_prices, synthetic_targets):
    p = synthetic_prices["corn_close"].values
    expected = np.log(p[5]) - np.log(p[0])
    got = synthetic_targets["y_logret_h5"].iloc[0]
    assert pytest.approx(expected, rel=1e-12) == got


def test_last_h_rows_have_nan(synthetic_prices, synthetic_targets):
    n = len(synthetic_prices)
    assert synthetic_targets["y_logret_h5"].iloc[n - 1 :].isna().all()
    assert synthetic_targets["y_logret_h30"].iloc[n - 30:].isna().all()


def test_up_target_consistency(synthetic_targets):
    s = synthetic_targets[["y_logret_h5", "y_up_h5"]].dropna()
    expected = (s["y_logret_h5"] > 0).astype(int)
    assert (s["y_up_h5"].astype(int) == expected).all()


def test_class_bins_are_anti_leakage(synthetic_prices):
    """Verify class bins at time t do not depend on data after t.

    We compute classes on the first 800 rows, then on the first 1500 rows.
    The class assigned to row i (i < 800) must be the same in both runs."""
    short = synthetic_prices.iloc[:800].copy()
    long = synthetic_prices.iloc[:1500].copy()
    spec = TargetSpec(horizons=(5,), expanding_min_points=200)
    t_short = build_targets(short, spec)
    t_long = build_targets(long, spec)
    common = t_short.merge(t_long[["Date", "y_class_h5"]], on="Date",
                            suffixes=("_s", "_l")).dropna()
    assert (common["y_class_h5_s"] == common["y_class_h5_l"]).all()


def test_class_values_in_range(synthetic_targets):
    valid = synthetic_targets["y_class_h5"].dropna()
    assert valid.min() >= 0
    assert valid.max() <= 9  # 10 bins by default
