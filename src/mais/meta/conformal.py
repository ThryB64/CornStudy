"""Split-conformal prediction intervals.

Given a set of point predictions and ground truth on a CALIBRATION set,
returns the symmetric quantile of absolute residuals. New predictions get
intervals (pred - q, pred + q) with marginal coverage >= 1 - alpha.

This is the simplest conformal recipe; for time-series we use a rolling
calibration window to mitigate distribution shift.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def calibrate_conformal_intervals(
    y_true: pd.Series, y_pred: pd.Series, alpha: float = 0.1,
    rolling_window: int | None = 252,
) -> pd.DataFrame:
    """Return a DataFrame with columns: y_pred, q, lo, hi.

    If ``rolling_window`` is given, the quantile is recomputed on a rolling
    window of past residuals (better for non-stationary series).
    """
    res = (y_true - y_pred).abs()
    if rolling_window:
        q = res.rolling(rolling_window, min_periods=max(50, rolling_window // 4)).quantile(1 - alpha)
    else:
        q_val = float(res.dropna().quantile(1 - alpha))
        q = pd.Series(q_val, index=res.index)
    out = pd.DataFrame({
        "y_pred": y_pred.values,
        "q": q.values,
        "lo": (y_pred - q).values,
        "hi": (y_pred + q).values,
    }, index=y_pred.index)
    return out
