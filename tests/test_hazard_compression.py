"""Tests VN-D1 — hazard time-to-compression (synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v_hazard_compression as hz


def _master(n=700):
    rng = np.random.default_rng(0)
    idx = pd.date_range("2015-01-01", periods=n, freq="B")
    # basis_z oscille au-dessus de 1 souvent, avec réversion
    z = 1.0 + np.abs(np.cumsum(rng.normal(0, 0.1, n))) % 1.5
    cbot = np.linspace(380, 470, n) + rng.normal(0, 5, n)
    df = pd.DataFrame({"ema_cbot_basis_zscore_52w": z, "cbot_close": cbot,
                       "corn_wheat_ratio": 0.5 + rng.normal(0, 0.02, n)}, index=idx)
    df.index.name = "Date"
    return df


def test_target_shape():
    df = _master(300)
    y = hz._target(df, 10)
    assert len(y) == len(df)
    assert set(np.unique(y.dropna())).issubset({0.0, 1.0})


def test_run_default_watchlist(tmp_path, monkeypatch):
    df = _master(700)
    monkeypatch.setattr(hz, "V_DIR", tmp_path)
    monkeypatch.setattr(hz, "assert_no_holdout", lambda d: None)
    out = hz.run_v_hazard(df)
    assert out["verdict"] in ("HAZARD_ADDS_SIGNAL", "WATCHLIST_NO_CLEAR_EDGE")
    assert "by_horizon" in out
    assert out["drop_threshold"] == 0.5


def test_no_data(tmp_path, monkeypatch):
    df = _master(100)
    df["ema_cbot_basis_zscore_52w"] = 0.2  # jamais > 1
    monkeypatch.setattr(hz, "V_DIR", tmp_path)
    monkeypatch.setattr(hz, "assert_no_holdout", lambda d: None)
    assert hz.run_v_hazard(df)["verdict"] == "NO_DATA"
