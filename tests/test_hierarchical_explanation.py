"""Tests VN-D4 — explication hiérarchique par familles."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v_hierarchical_explanation as he


def _master(n=700):
    rng = np.random.default_rng(1)
    idx = pd.date_range("2015-01-01", periods=n, freq="B")
    z = 1.0 + np.abs(np.cumsum(rng.normal(0, 0.1, n))) % 1.5
    df = pd.DataFrame({"ema_cbot_basis_zscore_52w": z,
                       "cbot_close": np.linspace(380, 470, n) + rng.normal(0, 5, n),
                       "corn_wheat_ratio": 0.5 + rng.normal(0, 0.02, n),
                       "cot_mm_net": rng.normal(1000, 200, n)}, index=idx)
    df.index.name = "Date"
    return df


def test_run(tmp_path, monkeypatch):
    df = _master()
    monkeypatch.setattr(he, "V_DIR", tmp_path)
    monkeypatch.setattr(he, "assert_no_holdout", lambda d: None)
    out = he.run_v_hierarchical(df)
    assert out["verdict"] == "EXPLANATORY_FAMILIES_RANKED"
    assert "family_marginal_auc" in out
    assert "MARKET" in out["family_marginal_auc"]


def test_no_data(tmp_path, monkeypatch):
    df = _master(120)
    df["ema_cbot_basis_zscore_52w"] = 0.2
    monkeypatch.setattr(he, "V_DIR", tmp_path)
    monkeypatch.setattr(he, "assert_no_holdout", lambda d: None)
    assert he.run_v_hierarchical(df)["verdict"] == "NO_DATA"
