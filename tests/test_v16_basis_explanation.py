"""Tests V16 — explication économique du basis."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mais.research.v16_basis_explanation import (
    run_basis_drivers,
    run_basis_fair_value,
    run_curve_structure,
)


@pytest.fixture
def synthetic_df():
    rng = np.random.default_rng(16)
    n = 2600
    idx = pd.date_range("2009-01-01", periods=n, freq="B")
    cbot = 150 + np.cumsum(rng.normal(0, 1, n))
    eurusd = 1.1 + rng.normal(0, 0.03, n)
    gas = 20 + np.cumsum(rng.normal(0, 0.1, n))
    bz = np.zeros(n)
    for t in range(1, n):
        bz[t] = 0.95 * bz[t - 1] + rng.normal(0, 0.3)
    # basis dépend de FX + saison + anomalie
    season = np.sin(2 * np.pi * idx.month / 12)
    basis = 30 + 10 * (eurusd - 1.1) + 3 * season - 5 * bz + rng.normal(0, 2, n)
    ema = cbot + basis
    return pd.DataFrame({
        "cbot_eur_t": cbot,
        "ema_close": ema,
        "ema_cbot_basis": basis,
        "ema_cbot_basis_zscore_52w": bz,
        "eurusd": eurusd,
        "usd_index_close": 95 + rng.normal(0, 1, n),
        "oil_close": 70 + np.cumsum(rng.normal(0, 0.2, n)),
        "gas_close": gas,
        "corn_gas_ratio": cbot / gas,
        "corn_oil_ratio": cbot / 70,
        "ema_contango_flag": rng.integers(0, 2, n).astype(float),
        "ema_backwardation_flag": rng.integers(0, 2, n).astype(float),
        "curve_backwardation_proxy": rng.normal(0, 0.2, n),
    }, index=idx)


def test_fair_value(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v16_basis_explanation as mod
    monkeypatch.setattr(mod, "V16_DIR", tmp_path)
    out = run_basis_fair_value(synthetic_df)
    assert out["verdict"] in {"MISPRICING_BETTER", "BASIS_Z_REMAINS_BEST"}
    assert out["fair_value_oof_r2_mean"] is not None
    assert "short_rule_basis_z" in out and "short_rule_mispricing" in out


def test_curve_structure(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v16_basis_explanation as mod
    monkeypatch.setattr(mod, "V16_DIR", tmp_path)
    out = run_curve_structure(synthetic_df)
    assert out["verdict"] == "CURVE_STRUCTURE_EXPLORATORY"
    assert "results" in out


def test_basis_drivers(synthetic_df, tmp_path, monkeypatch):
    import mais.research.v16_basis_explanation as mod
    monkeypatch.setattr(mod, "V16_DIR", tmp_path)
    out = run_basis_drivers(synthetic_df)
    assert out["verdict"] == "BASIS_DRIVERS_DONE"
    assert out["oof_r2_mean"] is not None
    assert len(out["top_drivers"]) >= 1
    # eurusd doit ressortir (le basis synthétique en dépend)
    assert "eurusd" in out["standardized_coefficients"]
