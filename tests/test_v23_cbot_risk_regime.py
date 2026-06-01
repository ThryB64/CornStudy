"""Tests V23 — risque drawdown CBOT + reversion conditionnelle au régime."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mais.research.v23_cbot_risk_and_regime import (
    run_cbot_drawdown_risk_module,
    run_regime_conditional_basis,
)


@pytest.fixture
def synthetic_df():
    rng = np.random.default_rng(23)
    n = 3000
    idx = pd.date_range("2007-01-01", periods=n, freq="B")
    corn = pd.Series(400 + np.cumsum(rng.normal(0, 4, n)), index=idx)
    lr = np.log(corn).diff()
    cbot_eur = corn / 3.0
    bz = np.zeros(n)
    for t in range(1, n):
        bz[t] = 0.95 * bz[t - 1] + rng.normal(0, 0.3)
    ema = cbot_eur.values + 30 - 5 * bz + rng.normal(0, 2, n)
    return pd.DataFrame({
        "corn_close": corn,
        "cbot_eur_t": cbot_eur,
        "ema_close": ema,
        "ema_cbot_basis": ema - cbot_eur.values,
        "ema_cbot_basis_zscore_52w": bz,
        "curve_backwardation_proxy": rng.normal(0, 0.2, n),
        "corn_logret_1d": lr,
        "corn_logret_5d": np.log(corn).diff(5),
        "corn_logret_20d": np.log(corn).diff(20),
        "corn_realized_vol_20": lr.rolling(20).std(),
        "corn_rsi_14": rng.uniform(20, 80, n),
        "corn_macd_hist": rng.normal(0, 1, n),
        "corn_atr_14": np.abs(rng.normal(8, 2, n)),
        "wx_belt_heat_days_38c_30": rng.uniform(0, 10, n),
        "wx_belt_rain_deficit_14d": rng.normal(0, 1, n),
        "wx_belt_gdd_accumulated": np.cumsum(rng.uniform(0, 5, n)),
        "drought_composite": rng.uniform(0, 1, n),
        "condition_gd_ex_pct": rng.uniform(40, 90, n),
        "ema_oi_total": rng.uniform(1000, 5000, n),
    }, index=idx)


def test_drawdown_risk_module(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v23_cbot_risk_and_regime as mod
    monkeypatch.setattr(mod, "V23_DIR", tmp_path)
    out = run_cbot_drawdown_risk_module(synthetic_df)
    assert out["verdict"] == "CBOT_DRAWDOWN_RISK_MODULE_DONE"
    assert "drawdown_5pct_h20" in out["results"]


def test_regime_conditional_basis(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v23_cbot_risk_and_regime as mod
    monkeypatch.setattr(mod, "V23_DIR", tmp_path)
    out = run_regime_conditional_basis(synthetic_df)
    assert out["verdict"] in {"REGIME_BASIS_DONE", "TOO_FEW"}
    if out["verdict"] == "REGIME_BASIS_DONE":
        assert "cbot_below_trend" in out and "cbot_above_trend" in out
        assert isinstance(out["hypothesis_supported"], bool)
