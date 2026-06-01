"""Shared pytest fixtures."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_prices() -> pd.DataFrame:
    """A 1500-day synthetic price series (geometric Brownian motion)."""
    rng = np.random.default_rng(42)
    n = 1500
    dates = pd.bdate_range("2015-01-02", periods=n)
    daily_ret = rng.normal(0.0001, 0.012, size=n)
    price = 400.0 * np.exp(np.cumsum(daily_ret))
    return pd.DataFrame({
        "Date": dates,
        "corn_close": price,
        "corn_open":  price * (1 + rng.normal(0, 0.001, size=n)),
        "corn_high":  price * (1 + np.abs(rng.normal(0, 0.005, size=n))),
        "corn_low":   price * (1 - np.abs(rng.normal(0, 0.005, size=n))),
        "corn_volume": rng.integers(50_000, 500_000, size=n).astype(float),
    })


@pytest.fixture
def synthetic_features(synthetic_prices: pd.DataFrame) -> pd.DataFrame:
    """A few legit lagged features computed from prices."""
    df = synthetic_prices.copy()
    p = df["corn_close"]
    df["corn_logret_1d_lag1"] = np.log(p).diff().shift(1)
    df["corn_sma_20_lag1"] = p.rolling(20, min_periods=20).mean().shift(1)
    df["corn_realized_vol_20_lag1"] = (
        np.log(p).diff().rolling(20, min_periods=20).std().shift(1) * np.sqrt(252)
    )
    return df[["Date", "corn_logret_1d_lag1", "corn_sma_20_lag1", "corn_realized_vol_20_lag1"]]


@pytest.fixture
def synthetic_targets(synthetic_prices: pd.DataFrame) -> pd.DataFrame:
    from mais.targets import TargetSpec, build_targets
    return build_targets(synthetic_prices, TargetSpec(horizons=(5, 10, 20, 30)))


@pytest.fixture(scope="session")
def project_root() -> pd.DataFrame:
    from mais.paths import PROJECT_ROOT
    return PROJECT_ROOT
