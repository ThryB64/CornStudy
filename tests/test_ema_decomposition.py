"""Tests V7-09 — Décomposition dynamique EMA."""

import numpy as np
import pandas as pd
import pytest

from mais.research.ema_decomposition_v7 import (
    COMPONENTS,
    compute_variance_attribution,
    decompose_ema_returns,
    run_ema_decomposition,
)


def _make_ema_df(n: int = 400, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2012-01-01", periods=n, freq="B")
    return pd.DataFrame(
        {
            "ema_close": 200 + np.cumsum(rng.normal(0, 2, n)),
            "cbot_close_eur": 185 + np.cumsum(rng.normal(0, 2, n)),
            "eurusd": 1.10 + np.cumsum(rng.normal(0, 0.005, n)),
        },
        index=dates,
    )


def test_decompose_returns_correct_columns():
    df = _make_ema_df()
    result = decompose_ema_returns(df, window=60)
    for col in COMPONENTS:
        assert col in result.columns
    assert "residual" in result.columns
    assert "r2_rolling" in result.columns


def test_decompose_missing_ema_raises():
    df = pd.DataFrame({"other": [1, 2, 3]})
    with pytest.raises(ValueError, match="ema_close"):
        decompose_ema_returns(df)


def test_decompose_minimal_columns():
    n = 300
    dates = pd.date_range("2015-01-01", periods=n, freq="B")
    rng = np.random.default_rng(0)
    df = pd.DataFrame(
        {"ema_close": 200 + np.cumsum(rng.normal(0, 1, n))},
        index=dates,
    )
    result = decompose_ema_returns(df, window=60)
    assert len(result) == n


def test_variance_attribution_sums():
    df = _make_ema_df()
    decomp = decompose_ema_returns(df, window=60)
    attr = compute_variance_attribution(decomp)
    assert set(attr.keys()) == set(COMPONENTS)
    # Attribution values should be non-negative
    assert all(v >= 0 for v in attr.values())


def test_run_ema_decomposition_structure():
    df = _make_ema_df()
    result = run_ema_decomposition(df, window=60)
    assert "global_variance_attribution" in result
    assert "dominant_component" in result
    assert result["dominant_component"] in COMPONENTS
    assert result["n_dates"] == len(df)


def test_run_with_full_columns():
    df = _make_ema_df(500)
    result = run_ema_decomposition(df, window=60)
    assert result["columns_available"]["cbot_close_eur"] is True
    assert result["columns_available"]["eurusd"] is True
