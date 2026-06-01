"""Tests V22 — stabilisation live : gate de fraîcheur + classification pipeline."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.research.data_freshness import compute_freshness, staleness_verdict


def test_staleness_verdict_thresholds():
    assert staleness_verdict(0) == "OK"
    assert staleness_verdict(2) == "OK"
    assert staleness_verdict(4) == "WARNING_STALE"
    assert staleness_verdict(10) == "NO_SIGNAL_STALE"
    assert staleness_verdict(None) == "NO_SIGNAL_STALE"


def _df_ending(last_date: str, n: int = 60):
    idx = pd.date_range(end=last_date, periods=n, freq="B")
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "cbot_eur_t": 150 + rng.normal(0, 1, n),
        "ema_close": 180 + rng.normal(0, 1, n),
        "eurusd": 1.1 + rng.normal(0, 0.01, n),
        "ema_cbot_basis_zscore_52w": rng.normal(0, 1, n),
    }, index=idx)


def test_freshness_fresh_data_allows_signal():
    today = pd.Timestamp.today().normalize()
    df = _df_ending(str((today - pd.tseries.offsets.BDay(1)).date()))
    fr = compute_freshness(df, as_of=today)
    assert fr["signal_allowed"] is True
    assert fr["freshness_verdict"] == "OK"


def test_freshness_stale_data_blocks_signal():
    df = _df_ending("2025-07-25")  # très ancien vs aujourd'hui
    fr = compute_freshness(df, as_of=pd.Timestamp("2026-05-31"))
    assert fr["signal_allowed"] is False
    assert fr["freshness_verdict"] == "NO_SIGNAL_STALE"
    assert fr["staleness_days"] > 5
    assert fr["last_basis_date"] == "2025-07-25"


def test_integrated_indicator_applies_freshness_gate(tmp_path, monkeypatch):
    import mais.research.v21_indicator_integration as mod
    monkeypatch.setattr(mod, "V21_DIR", tmp_path)
    # données se terminant longtemps avant aujourd'hui -> signal live doit être gaté
    idx = pd.date_range("2008-01-01", periods=2600, freq="B")
    rng = np.random.default_rng(3)
    cbot = pd.Series(150 + np.cumsum(rng.normal(0, 1, 2600)), index=idx)
    bz = np.zeros(2600)
    for t in range(1, 2600):
        bz[t] = 0.95 * bz[t - 1] + rng.normal(0, 0.3)
    ema = cbot.values + 30 - 5 * bz + rng.normal(0, 2, 2600)
    df = pd.DataFrame({
        "cbot_eur_t": cbot, "ema_close": ema, "ema_cbot_basis": ema - cbot.values,
        "ema_cbot_basis_zscore_52w": bz, "ema_oi_total": rng.uniform(1000, 5000, 2600),
        "corn_realized_vol_20": np.abs(rng.normal(0.2, 0.05, 2600)),
        "curve_backwardation_proxy": rng.normal(0, 0.2, 2600),
        "wx_belt_heat_days_38c_30": rng.uniform(0, 10, 2600),
        "wx_belt_rain_deficit_14d": rng.normal(0, 1, 2600),
        "drought_composite": rng.uniform(0, 1, 2600),
    }, index=idx)
    out = mod.run_integrated_indicator(df)
    snap = out["latest_integrated_snapshot"]
    if snap is not None:
        # données de 2008-2018 -> périmées en 2026 -> signal gaté
        assert out["freshness"]["signal_allowed"] is False
        assert snap["premium_signal"] == "UNCERTAIN_DATA_STALE"
        assert snap["raw_signal_before_freshness_gate"] is not None
