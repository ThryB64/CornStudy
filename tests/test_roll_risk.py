"""Tests V7-07 — Roll-aware premium model."""

import numpy as np
import pandas as pd
import pytest

from mais.features.roll_risk import (
    apply_roll_veto,
    compute_roll_aware_report,
    compute_roll_risk_score,
)


def _make_roll_df(n: int = 200, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2015-01-01", periods=n, freq="B")
    return pd.DataFrame(
        {
            "ema_close": 200 + np.cumsum(rng.normal(0, 1, n)),
            "days_to_expiry": np.tile(np.arange(30, 0, -1), n // 30 + 1)[:n],
            "roll_gap": rng.normal(0, 2, n),
        },
        index=dates,
    )


def test_score_range():
    df = _make_roll_df()
    score = compute_roll_risk_score(df)
    assert ((score >= 0) & (score <= 1)).all()


def test_score_name():
    df = _make_roll_df()
    assert compute_roll_risk_score(df).name == "roll_risk_score"


def test_score_no_dte_col():
    df = _make_roll_df().drop(columns=["days_to_expiry"])
    score = compute_roll_risk_score(df)
    assert ((score >= 0) & (score <= 1)).all()


def test_score_no_gap_col():
    df = _make_roll_df().drop(columns=["roll_gap"])
    score = compute_roll_risk_score(df)
    assert ((score >= 0) & (score <= 1)).all()


def test_high_risk_near_expiry():
    df = _make_roll_df()
    # Days before expiry: DTE=1 → score DTE = 1.0 - 1/30 ≈ 0.97
    df["days_to_expiry"] = 1
    score = compute_roll_risk_score(df)
    assert score.mean() > 0.5


def test_apply_roll_veto_neutralizes():
    df = _make_roll_df()
    score = pd.Series(0.9, index=df.index)  # all high risk
    signals = pd.DataFrame({"proba_h90": 0.7}, index=df.index)
    result = apply_roll_veto(signals, score, threshold=0.7)
    assert result["proba_h90"].isna().all()


def test_apply_roll_veto_keeps_low_risk():
    df = _make_roll_df()
    score = pd.Series(0.3, index=df.index)  # all low risk
    signals = pd.DataFrame({"proba_h90": 0.7}, index=df.index)
    result = apply_roll_veto(signals, score, threshold=0.7)
    assert (result["proba_h90"] == 0.7).all()


def test_report_structure():
    df = _make_roll_df()
    report = compute_roll_aware_report(df)
    assert "mean_roll_risk" in report
    assert "pct_high_risk" in report
    assert "n_veto_days" in report
    assert 0.0 <= report["mean_roll_risk"] <= 1.0
