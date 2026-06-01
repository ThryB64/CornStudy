"""Tests V80 — spreads inter-commodités (offline)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v80_intercommodity_spreads as v80


def _master(n=1200, seed=7):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2013-01-01", periods=n)
    corn = 150 + np.cumsum(rng.normal(0, 1.0, n))
    return pd.DataFrame({
        "corn_close": corn,
        "soy_close": corn * 2.5 + rng.normal(0, 5, n),
        "oil_close": 70 + np.cumsum(rng.normal(0, 0.3, n)),
        "gas_close": 3 + np.cumsum(rng.normal(0, 0.02, n)),
        "wheat_close": corn * 1.3 + rng.normal(0, 4, n),
        "cbot_eur_t": corn,
        "ema_cbot_basis": 35 + rng.normal(0, 3, n),
        "ema_cbot_basis_zscore_52w": rng.normal(0, 1, n),
    }, index=idx)


def test_features_shifted():
    f = v80.intercommodity_features(_master())
    assert set(f.columns) == {"corn_soy_ratio_z", "crude_corn_ratio_z", "gas_z", "corn_wheat_ratio_z"}


def test_run_v80(tmp_path, monkeypatch):
    monkeypatch.setattr(v80, "V80_DIR", tmp_path)
    out = v80.run_v80_intercommodity(_master())
    assert out["version"] == "V80-INTERCOMMODITY"
    if out["verdict"] != "NO_DATA":
        assert "corr_vs_cbot_fwd20" in out and "corr_vs_basis_chg40" in out
        assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"
