"""Tests V130 — économétrie du basis par régimes (synthétique, statsmodels optionnel)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v130_basis_regime_econometrics as v130


def _ar1_series(n=800, phi=0.95, seed=0):
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for t in range(1, n):
        x[t] = phi * x[t - 1] + rng.normal(0, 0.3)
    idx = pd.date_range("2015-01-01", periods=n, freq="B")
    df = pd.DataFrame({"ema_cbot_basis_zscore_52w": x}, index=idx)
    df.index.name = "Date"
    return df


def test_halflife():
    assert v130._halflife(0.5) == round(-np.log(2) / np.log(0.5), 1)
    assert v130._halflife(1.0) is None
    assert v130._halflife(-0.2) is None


def test_ar1_recovers_phi():
    df = _ar1_series(phi=0.9)
    z = df["ema_cbot_basis_zscore_52w"]
    res = v130._ar1(z.iloc[:-1].to_numpy(), z.iloc[1:].to_numpy())
    assert 0.8 < res["phi"] < 0.98


def test_tar_model_runs():
    df = _ar1_series()
    tar = v130.tar_model(df)
    assert "linear_ar1" in tar and "above_threshold" in tar


def test_run_verdict(tmp_path, monkeypatch):
    df = _ar1_series()
    monkeypatch.setattr(v130, "V130_DIR", tmp_path)
    monkeypatch.setattr(v130, "assert_no_holdout", lambda d: None)
    out = v130.run_v130_regime_econometrics(df)
    assert out["verdict"] in ("ADD_TO_HORIZON_ESTIMATE", "WATCHLIST")
    assert "half_life_by_tier" in out


def test_report_block(tmp_path, monkeypatch):
    df = _ar1_series()
    monkeypatch.setattr(v130, "V130_DIR", tmp_path)
    monkeypatch.setattr(v130, "assert_no_holdout", lambda d: None)
    v130.run_v130_regime_econometrics(df)
    block = v130.regime_econometrics_report_block()
    assert "V130" in block
