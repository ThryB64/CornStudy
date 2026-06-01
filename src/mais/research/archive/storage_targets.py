"""Storage-oriented targets for farmer decision backtests."""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_storage_targets(
    prices: pd.DataFrame,
    *,
    price_col: str = "corn_close",
    cost_1m: float = 8.0,
    cost_3m: float = 15.0,
    cost_6m: float = 25.0,
) -> pd.DataFrame:
    """Build storage value and opportunity targets from future prices."""
    df = prices[["Date", price_col]].copy()
    df["Date"] = pd.to_datetime(df["Date"])
    price = pd.to_numeric(df[price_col], errors="coerce")
    out = pd.DataFrame({"Date": df["Date"].values})
    out["y_storage_value_1m"] = price.shift(-20) - price - cost_1m
    out["y_storage_value_3m"] = price.shift(-60) - price - cost_3m
    out["y_storage_value_6m"] = price.shift(-120) - price - cost_6m
    out["y_max_opportunity_3m"] = price.iloc[::-1].rolling(60, min_periods=1).max().iloc[::-1] - price - cost_3m
    future_rank = _future_rank(price, horizon=252)
    out["y_sell_partial_flag"] = (future_rank > 0.75).astype(float)
    out.loc[future_rank.isna(), "y_sell_partial_flag"] = np.nan
    return out


def assert_storage_targets_not_in_features(features: pd.DataFrame) -> None:
    """Guardrail: storage targets must never enter build_features()."""
    forbidden = [col for col in features.columns if col.startswith("y_storage_") or col.startswith("y_max_opportunity_")]
    if "y_sell_partial_flag" in features.columns:
        forbidden.append("y_sell_partial_flag")
    if forbidden:
        raise AssertionError(f"Storage targets leaked into features: {forbidden}")


def _future_rank(price: pd.Series, horizon: int) -> pd.Series:
    out = pd.Series(np.nan, index=price.index, dtype=float)
    for i, value in enumerate(price):
        future = price.iloc[i + 1 : i + 1 + horizon].dropna()
        if len(future) < min(20, horizon):
            continue
        out.iloc[i] = float((future <= value).mean())
    return out
