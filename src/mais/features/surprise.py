"""Surprise features (Phase 1 NEW).

The price doesn't react to the *level* of WASDE production, it reacts to the
*surprise*: the gap between what was published and what was expected.

Without an analyst-consensus subscription, we approximate the surprise three
ways and let the model figure out which one is most informative:

    surprise_vs_prev   = value - value.shift(1)
    surprise_vs_5y     = value - rolling(5y).mean()
    surprise_vs_trend  = value - linear_trend(value, last 24m)

This module takes any DataFrame with fundamental variables and adds the three
surprise variants for each numeric column.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_surprise_features(
    df: pd.DataFrame,
    exclude_cols: list[str] | None = None,
    rolling_5y_window: int = 60,   # 60 monthly obs ~ 5 years if monthly data
    trend_window: int = 24,
) -> pd.DataFrame:
    """For each numeric column not in ``exclude_cols``, add three surprise variants."""
    exclude = set(exclude_cols or [])
    out = df.copy()
    target_cols = [c for c in df.columns
                    if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]

    for c in target_cols:
        s = df[c].astype(float)
        out[f"{c}_surprise_vs_prev"] = s - s.shift(1)

        # Rolling 5y mean (use min_periods=12 to avoid full warm-up)
        roll = s.rolling(rolling_5y_window, min_periods=min(12, rolling_5y_window // 2))
        out[f"{c}_surprise_vs_5y"] = s - roll.mean()

        # Linear-trend surprise: residual from rolling OLS on a 24m window.
        # Cheap proxy: extrapolate using the slope of the previous trend_window points.
        out[f"{c}_surprise_vs_trend"] = _trend_surprise(s, trend_window)

    return out


def _trend_surprise(s: pd.Series, window: int) -> pd.Series:
    """Compute s_t - (a_{t-1} + b_{t-1} * t) where a, b are fitted on the
    previous ``window`` observations (excluding t itself)."""
    out = pd.Series(np.nan, index=s.index, dtype=float)
    vals = s.values
    n = len(vals)
    if n < window + 1:
        return out
    x = np.arange(window, dtype=float)
    for i in range(window, n):
        y = vals[i - window: i]
        if np.isnan(y).any():
            continue
        # Simple OLS slope
        x_mean = x.mean()
        y_mean = y.mean()
        denom = ((x - x_mean) ** 2).sum()
        if denom == 0:
            continue
        b = ((x - x_mean) * (y - y_mean)).sum() / denom
        a = y_mean - b * x_mean
        expected = a + b * window  # next step
        out.iloc[i] = vals[i] - expected
    return out
