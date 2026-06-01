"""Tests V120 — économétrie du basis (offline ; statsmodels requis, sinon skip propre)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v120_basis_econometrics as v120


def _synthetic_master(n=700, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-01", periods=n)
    # basis_z = AR(1) stationnaire (mean-reverting) -> doit donner ADF stationnaire + demi-vie finie
    bz = np.zeros(n)
    for t in range(1, n):
        bz[t] = 0.92 * bz[t - 1] + rng.normal(0, 0.4)
    cbot = 150 + np.cumsum(rng.normal(0, 1, n))
    return pd.DataFrame({
        "cbot_eur_t": cbot, "corn_close": cbot * 9.5, "wheat_close": cbot * 9.5 * 1.3,
        "ema_cbot_basis": 35 + bz * 5,
        "ema_cbot_basis_zscore_52w": bz,
    }, index=idx)


def test_ljung_box_and_adf():
    df = _synthetic_master()
    bz = df["ema_cbot_basis_zscore_52w"].to_numpy()
    adf = v120._adf(bz)
    if adf is not None:  # statsmodels présent
        assert "stationary" in adf
    lb = v120._ljung_box(bz, 10)
    if lb is not None:
        assert "white_noise" in lb


def test_run_v120(tmp_path, monkeypatch):
    monkeypatch.setattr(v120, "V120_DIR", tmp_path)
    out = v120.run_v120_econometrics(_synthetic_master())
    assert out["version"] == "V120-BASIS-ECONOMETRICS"
    if out["verdict"] not in ("TOO_SHORT", "STATSMODELS_MISSING"):
        assert "adf_basis_z_level" in out
        assert "ljung_box_diff" in out
        assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"
