"""Tests V14 — indicateur short-only, survival, robustesse proxy."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mais.research.v14_short_indicator import (
    _km_survival,
    assemble_short_indicator,
    run_proxy_robustness,
    run_reversion_survival,
    run_short_indicator,
)


@pytest.fixture
def synthetic_df():
    rng = np.random.default_rng(11)
    n = 2600
    idx = pd.date_range("2009-01-01", periods=n, freq="B")
    cbot = 150 + np.cumsum(rng.normal(0, 1, n))
    bz = np.zeros(n)
    for t in range(1, n):
        bz[t] = 0.95 * bz[t - 1] + rng.normal(0, 0.3)
    ema = cbot + 30 - 5 * bz + rng.normal(0, 2, n)
    return pd.DataFrame({
        "cbot_eur_t": cbot,
        "ema_close": ema,
        "ema_cbot_basis": ema - cbot,
        "ema_cbot_basis_zscore_52w": bz,
        "eurusd": 1.1 + rng.normal(0, 0.02, n),
        "ema_oi_total": rng.uniform(1000, 5000, n),
        "ema_data_availability_score": np.clip(rng.normal(0.8, 0.1, n), 0, 1),
        "days_to_next_wasde": rng.integers(3, 30, n),
        "corn_macd_hist": rng.normal(0, 1, n),
        "corn_realized_vol_20": np.abs(rng.normal(0.2, 0.05, n)),
    }, index=idx)


def test_km_survival_basic():
    durations = np.array([10, 20, 20, 40, 60])
    observed = np.array([1, 1, 1, 0, 1])
    times, surv, med = _km_survival(durations, observed)
    assert surv[0] <= 1.0
    assert np.all(np.diff(surv) <= 1e-9)  # décroissante


def test_assemble_short_signal_labels(synthetic_df):
    sig = assemble_short_indicator(synthetic_df)
    assert set(sig["signal"].unique()) <= {"SHORT_PREMIUM", "ABSTAIN"}
    assert "confidence" in sig.columns
    assert (sig["confidence"] >= 0).all() and (sig["confidence"] <= 1).all()


def test_run_short_indicator(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v14_short_indicator as mod
    monkeypatch.setattr(mod, "V14_DIR", tmp_path)
    out = run_short_indicator(synthetic_df)
    assert out["verdict"] in {"SHORT_INDICATOR_SURVIVES_COST5", "SHORT_INDICATOR_PARTIAL"}
    assert "relaxed_indicator" in out and "baseline_short_no_gates" in out
    assert "strict_indicator" in out and "over_gating_finding" in out


def test_reversion_survival(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v14_short_indicator as mod
    monkeypatch.setattr(mod, "V14_DIR", tmp_path)
    out = run_reversion_survival(synthetic_df)
    assert out["verdict"] in {"REVERSION_SURVIVAL_DONE", "TOO_FEW"}
    if out["verdict"] == "REVERSION_SURVIVAL_DONE":
        assert 0.0 <= out["p_revert_by_90d"] <= 1.0


def test_proxy_robustness(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v14_short_indicator as mod
    monkeypatch.setattr(mod, "V14_DIR", tmp_path)
    out = run_proxy_robustness(synthetic_df, noise_levels=(0, 5), n_seeds=2)
    assert out["verdict"] in {"PROXY_ROBUST", "PROXY_SENSITIVE"}
    assert "noise_0eur" in out["results_by_noise"]
