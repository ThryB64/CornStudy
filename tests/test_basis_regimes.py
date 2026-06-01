"""Tests V7-08 — Régimes de basis EMA/CBOT."""

import numpy as np
import pandas as pd
import pytest

from mais.research.basis_regimes_v7 import (
    REGIME_NAMES,
    _build_regimes,
    _classify_regime,
    compute_regime_stats,
    run_basis_regimes,
)


def _make_ema_df(n: int = 500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2014-01-01", periods=n, freq="B")
    return pd.DataFrame(
        {
            "ema_close": 200 + np.cumsum(rng.normal(0, 2, n)),
            "cbot_close_eur": 190 + np.cumsum(rng.normal(0, 2, n)),
        },
        index=dates,
    )


def test_build_regimes_schema():
    df = _make_ema_df()
    result = _build_regimes(df)
    required = ["corn_close", "return_60d", "realized_vol_60d", "regime_score", "regime"]
    for col in required:
        assert col in result.columns, f"Missing column: {col}"
    assert result.index.name == "Date"


def test_build_regimes_valid_regime_names():
    df = _make_ema_df()
    result = _build_regimes(df)
    assert set(result["regime"].dropna().unique()).issubset(REGIME_NAMES)


def test_build_regimes_score_range():
    df = _make_ema_df()
    result = _build_regimes(df)
    score = result["regime_score"].dropna()
    assert ((score >= -1.0) & (score <= 1.0)).all()


def test_build_regimes_without_cbot():
    df = _make_ema_df().drop(columns=["cbot_close_eur"])
    result = _build_regimes(df)
    assert "regime" in result.columns


def test_build_regimes_missing_ema_raises():
    df = pd.DataFrame({"other_col": [1, 2, 3]})
    with pytest.raises(ValueError, match="ema_close"):
        _build_regimes(df)


def test_classify_regime_all_cases():
    assert _classify_regime(0.0, 0.0, 0.8) == "ROLL_DISTORTED"
    assert _classify_regime(2.0, 0.0, 0.0) == "HIGH_STABLE"
    assert _classify_regime(1.5, -1.0, 0.0) == "HIGH_COMPRESSING"
    assert _classify_regime(1.5, 1.0, 0.0) == "HIGH_EXPANDING"
    assert _classify_regime(-1.5, 0.0, 0.0) == "LOW_BASIS"
    assert _classify_regime(0.0, 0.0, 0.0) == "NORMAL"


def test_regime_stats_all_regimes_present():
    df = _make_ema_df()
    regimes_df = _build_regimes(df)
    stats = compute_regime_stats(regimes_df)
    for regime in REGIME_NAMES:
        assert regime in stats["regime_stats"]


def test_regime_stats_frequencies_sum_to_one():
    df = _make_ema_df()
    regimes_df = _build_regimes(df)
    stats = compute_regime_stats(regimes_df)
    total_freq = sum(s["frequency"] for s in stats["regime_stats"].values())
    assert abs(total_freq - 1.0) < 1e-4


def test_run_basis_regimes_structure():
    df = _make_ema_df()
    result = run_basis_regimes(df)
    assert "dominant_regime" in result
    assert result["dominant_regime"] in REGIME_NAMES
    assert "regime_distribution" in result
    assert result["n_dates"] == len(df)
