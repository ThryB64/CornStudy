"""Tests V18-LIT — réplication littérature."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mais.research.v18_literature_replication import (
    _verdict,
    run_basis_convergence,
    run_options_replication,
    run_replication_summary,
)


@pytest.fixture
def synthetic_df():
    rng = np.random.default_rng(18)
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
        "corn_realized_vol_20": np.abs(rng.normal(0.2, 0.05, n)),
        "cot_mm_net": rng.normal(0, 1, n),
        "cot_mm_long_pct": rng.uniform(0, 1, n),
        "cot_mm_short_pct": rng.uniform(0, 1, n),
        "cot_mm_net_pct_oi_x": rng.normal(0, 1, n),
        "corn_soy_ratio": rng.uniform(0.3, 0.5, n),
        "corn_wheat_ratio": rng.uniform(0.7, 1.0, n),
        "corn_oil_ratio": rng.uniform(1, 3, n),
        "corn_gas_ratio": rng.uniform(20, 40, n),
        "spread_corn_wheat": rng.normal(0, 5, n),
        "wasde_ending_stocks_surprise_vs_trend": rng.normal(0, 1, n),
        "wasde_production_surprise_vs_trend": rng.normal(0, 1, n),
        "wasde_exports_surprise_vs_trend": rng.normal(0, 1, n),
        "days_to_next_wasde": rng.integers(1, 30, n),
        "wx_belt_heat_days_38c_30": rng.uniform(0, 10, n),
        "wx_belt_rain_deficit_14d": rng.normal(0, 1, n),
        "wx_belt_gdd_accumulated": np.cumsum(rng.uniform(0, 5, n)),
        "drought_composite": rng.uniform(0, 1, n),
    }, index=idx)


def test_verdict_mapping():
    assert _verdict(0.03) == "ADD_TO_INDICATOR"
    assert _verdict(0.01) == "WATCHLIST"
    assert _verdict(0.0) == "KEEP_AS_EXPLANATION"
    assert _verdict(-0.05) == "NO_GO"
    assert _verdict(None) == "NO_GO"


def test_convergence_halflife(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v18_literature_replication as mod
    monkeypatch.setattr(mod, "V18_DIR", tmp_path)
    out = run_basis_convergence(synthetic_df)
    assert out["verdict"] == "KEEP_AS_EXPLANATION"
    assert out["global_half_life_days"] is not None


def test_options_blocked(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v18_literature_replication as mod
    monkeypatch.setattr(mod, "V18_DIR", tmp_path)
    out = run_options_replication(synthetic_df)
    assert out["verdict"] == "DATA_BLOCKED"


def test_replication_summary(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v18_literature_replication as mod
    monkeypatch.setattr(mod, "V18_DIR", tmp_path)
    out = run_replication_summary(synthetic_df)
    assert out["verdict"] == "REPLICATION_SUMMARY_DONE"
    valid = {"ADD_TO_INDICATOR", "WATCHLIST", "KEEP_AS_EXPLANATION", "NO_GO", "DATA_BLOCKED"}
    for v in out["matrix"].values():
        assert v["verdict"] in valid
    assert out["matrix"]["options"]["verdict"] == "DATA_BLOCKED"
