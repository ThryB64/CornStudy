"""Tests V46 — alignement de settlement CBOT/EMA (offline, master synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v46_settlement_alignment as v46


def _synthetic_master(n=900, seed=17):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2014-01-01", periods=n)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    basis = 35 + 10 * np.sin(np.linspace(0, 14 * np.pi, n)) + rng.normal(0, 2, n)
    ema = cbot + basis
    bz = (pd.Series(basis) - pd.Series(basis).rolling(60, min_periods=20).mean()) / (
        pd.Series(basis).rolling(60, min_periods=20).std() + 1e-9)
    return pd.DataFrame({
        "cbot_eur_t": cbot, "ema_close": ema, "corn_close": cbot * 9.5,
        "ema_cbot_basis": basis, "ema_cbot_basis_zscore_52w": bz.values,
    }, index=idx)


def test_aligned_basis_shift():
    df = _synthetic_master()
    b0 = v46.aligned_basis(df, 0)
    b1 = v46.aligned_basis(df, 1)
    assert b0.notna().sum() > b1.notna().sum() - 5  # k=1 a 1 NaN de plus au début
    assert not b0.equals(b1)


def test_run_v46_returns_alignment_table(tmp_path, monkeypatch):
    monkeypatch.setattr(v46, "V46_DIR", tmp_path)
    out = v46.run_v46_alignment(_synthetic_master())
    assert out["version"] == "V46-SETTLEMENT-ALIGNMENT"
    assert set(out["by_alignment"].keys()) == {-1, 0, 1}
    assert out["verdict"] in {
        "REALIGN_HELPS_LIVE", "NONSYNC_REAL_BUT_REALIGN_MARGINAL_LIVE", "ALIGNMENT_NEGLIGIBLE"}
