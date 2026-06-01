"""Tests V7-39 — Score de qualité des données (features/data_quality.py)."""

import numpy as np
import pandas as pd
import pytest

from mais.features.data_quality import (
    QUALITY_WEIGHTS,
    compute_data_quality_score,
    compute_quality_prediction_correlation,
    compute_quality_report,
)


def _make_perfect_df(n: int = 200) -> pd.DataFrame:
    dates = pd.date_range("2015-01-01", periods=n, freq="B")
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {
            "cot_net_position": rng.normal(size=n),
            "wasde_stocks": rng.normal(size=n),
            "eia_ethanol": rng.normal(size=n),
            "ema_close": rng.uniform(150, 250, n),
            "cbot_close": rng.uniform(140, 240, n),
            "ema_cbot_basis_eur": rng.normal(0, 5, n),
        },
        index=dates,
    )


def _make_empty_df(n: int = 200) -> pd.DataFrame:
    return pd.DataFrame(index=pd.date_range("2015-01-01", periods=n, freq="B"))


def test_score_perfect_data():
    df = _make_perfect_df()
    score = compute_data_quality_score(df)
    assert len(score) == len(df)
    assert (score == 1.0).all()


def test_score_empty_df():
    df = _make_empty_df()
    score = compute_data_quality_score(df)
    assert (score == 0.0).all()


def test_score_partial_data():
    df = _make_perfect_df(100)
    df.loc[df.index[:50], "cot_net_position"] = np.nan
    score = compute_data_quality_score(df)
    assert score.iloc[:50].mean() < 1.0
    assert score.iloc[50:].mean() == pytest.approx(1.0)


def test_weights_sum_to_one():
    assert sum(QUALITY_WEIGHTS.values()) == pytest.approx(1.0)


def test_score_name():
    score = compute_data_quality_score(_make_perfect_df())
    assert score.name == "data_quality_score"


def test_report_structure():
    report = compute_quality_report(_make_perfect_df())
    assert "mean_quality_score" in report
    assert "components" in report
    assert set(report["components"].keys()) == set(QUALITY_WEIGHTS.keys())
    assert report["mean_quality_score"] == pytest.approx(1.0)


def test_report_pct_high_quality_perfect():
    report = compute_quality_report(_make_perfect_df())
    assert report["pct_high_quality"] == pytest.approx(1.0)


def test_report_pct_low_quality_empty():
    report = compute_quality_report(_make_empty_df())
    assert report["pct_low_quality"] == pytest.approx(1.0)


def test_quality_error_correlation():
    df = _make_perfect_df(300)
    # Make quality score non-constant by dropping some data
    df.loc[df.index[::3], "cot_net_position"] = np.nan
    df.loc[df.index[::5], "wasde_stocks"] = np.nan
    rng = np.random.default_rng(42)
    errors = pd.Series(rng.normal(size=300), index=df.index)
    result = compute_quality_prediction_correlation(df, errors)
    assert "quality_error_correlation" in result
    corr = result["quality_error_correlation"]
    assert not np.isnan(corr)
    assert -1.0 <= corr <= 1.0
