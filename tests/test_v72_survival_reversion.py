"""Tests V72 — survival / time-to-reversion (offline)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v72_survival_reversion as v72


def test_km_median_basic():
    # 10 events à t=10, 10 à t=30 -> médiane ~ entre, S<=0.5 atteint à t=30
    durs = [10] * 4 + [30] * 6
    evts = [1] * 10
    m = v72._km_median(durs, evts)
    assert m in (10.0, 30.0)


def test_km_median_censored_none():
    # tout censuré -> médiane non atteinte
    assert v72._km_median([90, 90, 90], [0, 0, 0]) is None


def test_time_to_event():
    bz = np.array([2.0, 1.5, 0.4, -0.1])
    d, e = v72._time_to_event(bz, 0, 0.5, 90)
    assert e == 1 and d == 2


def _synthetic_master(n=900, seed=21):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2014-01-01", periods=n)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    basis = 35 + 12 * np.sin(np.linspace(0, 12 * np.pi, n)) + rng.normal(0, 2, n)
    bz = (pd.Series(basis) - pd.Series(basis).rolling(60, min_periods=20).mean()) / (
        pd.Series(basis).rolling(60, min_periods=20).std() + 1e-9)
    s = pd.Series(cbot)
    return pd.DataFrame({
        "corn_close": cbot * 9.5, "cbot_eur_t": cbot, "ema_close": cbot + basis,
        "ema_cbot_basis": basis, "ema_cbot_basis_zscore_52w": bz.values,
        "wheat_close": cbot * 9.5 * 1.3,
        "corn_sma_50": (s * 9.5).rolling(50).mean().values,
        "corn_logret_20d": np.log(s / s.shift(20)).values,
        "cot_mm_net_pct_oi_x": rng.normal(0, 10, n),
    }, index=idx)


def test_run_v72(tmp_path, monkeypatch):
    monkeypatch.setattr(v72, "V72_DIR", tmp_path)
    out = v72.run_v72_survival(_synthetic_master())
    assert out["version"] == "V72-SURVIVAL-REVERSION"
    if out["verdict"] != "TOO_FEW":
        assert "overall" in out and out["overall"]["n"] >= 15
        assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"
