"""Tests V141/V142 — validateurs forward courbe + MATIF (gated)."""
from __future__ import annotations

import pandas as pd

import mais.research.v141_curve_forward_validation as v141
import mais.research.v142_matif_forward_validation as v142


def test_v141_watchlist(tmp_path, monkeypatch):
    p = tmp_path / "curve.parquet"
    pd.DataFrame({"price_date": pd.to_datetime(["2026-05-29", "2026-06-01"]),
                  "front_next_spread": [15.25, 11.75], "curve_shape": ["BACKWARDATION"] * 2}).to_parquet(p, index=False)
    monkeypatch.setattr(v141, "CURVE_HISTORY", p)
    monkeypatch.setattr(v141, "V_DIR", tmp_path)
    out = v141.run_v141_curve_validation()
    assert out["verdict"] == "WATCHLIST_NEED_MORE_DATA"
    assert out["n_days"] == 2


def test_v141_built(tmp_path, monkeypatch):
    p = tmp_path / "curve.parquet"
    n = 25
    pd.DataFrame({"price_date": pd.bdate_range("2026-05-01", periods=n),
                  "front_next_spread": [10.0 + i * 0.1 for i in range(n)],
                  "curve_shape": ["BACKWARDATION"] * n}).to_parquet(p, index=False)
    monkeypatch.setattr(v141, "CURVE_HISTORY", p)
    monkeypatch.setattr(v141, "V_DIR", tmp_path)
    out = v141.run_v141_curve_validation()
    assert out["verdict"] == "CURVE_VALIDATION_BUILT"
    assert out["pct_backwardation"] == 1.0


def test_v142_no_history(tmp_path, monkeypatch):
    monkeypatch.setattr(v142, "RATIO_HISTORY", tmp_path / "absent.parquet")
    assert v142.run_v142_matif_validation()["verdict"] == "NO_RATIO_HISTORY"


def test_v142_watchlist(tmp_path, monkeypatch):
    p = tmp_path / "ratio.parquet"
    pd.DataFrame({"price_date": pd.to_datetime(["2026-06-01", "2026-06-02"]),
                  "ratio": [0.914, 0.915]}).to_parquet(p, index=False)
    monkeypatch.setattr(v142, "RATIO_HISTORY", p)
    monkeypatch.setattr(v142, "V_DIR", tmp_path)
    out = v142.run_v142_matif_validation()
    assert out["verdict"] == "WATCHLIST_NEED_MORE_DATA"
    assert out["ratio_last"] == 0.915
