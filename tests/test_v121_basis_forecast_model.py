"""Tests V121 — modèle de prévision du basis (offline)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v121_basis_forecast_model as v121


def _synthetic_master(n=800, seed=5):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-01", periods=n)
    bz = np.zeros(n)
    for t in range(1, n):
        bz[t] = 0.93 * bz[t - 1] + rng.normal(0, 0.4)  # AR(1) mean-reverting
    cbot = 150 + np.cumsum(rng.normal(0, 1, n))
    return pd.DataFrame({
        "cbot_eur_t": cbot, "corn_close": cbot * 9.5, "wheat_close": cbot * 9.5 * 1.3,
        "ema_cbot_basis_zscore_52w": bz,
    }, index=idx)


def test_build_and_ols():
    d = v121._build(_synthetic_master())
    assert {"bz", "bz_lag1", "cbot_ret_lag1", "wc_chg_lag1"} <= set(d.columns)
    beta = v121._ols(d["bz_lag1"].to_numpy().reshape(-1, 1), d["bz"].to_numpy())
    assert len(beta) == 2


def test_run_v121(tmp_path, monkeypatch):
    monkeypatch.setattr(v121, "V121_DIR", tmp_path)
    monkeypatch.setattr(v121, "MIN_TRAIN", 200)
    out = v121.run_v121_forecast(_synthetic_master())
    assert out["version"] == "V121-BASIS-FORECAST"
    if out["verdict"] != "TOO_SHORT":
        assert "by_horizon" in out and "h1" in out["by_horizon"]
        # sur un AR(1) synthétique, le modèle doit battre la marche aléatoire à h>1
        assert out["by_horizon"]["h5"]["skill_AR1_vs_RW"] > 0
        assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"
