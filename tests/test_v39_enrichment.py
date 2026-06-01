"""Tests V39-ENRICH — batch d'expériences d'enrichissement (offline, master synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v39_enrichment as v39


def _synthetic_master(n=900, seed=11):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2014-01-01", periods=n)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    wc = 1.3 + 0.15 * np.sin(np.linspace(0, 10 * np.pi, n)) + rng.normal(0, 0.02, n)
    basis = 40 * (wc - 1.0) + 12 * np.sin(np.linspace(0, 12 * np.pi, n)) + rng.normal(0, 2, n)
    ema = cbot + basis
    bz = (pd.Series(basis) - pd.Series(basis).rolling(60, min_periods=20).mean()) / (
        pd.Series(basis).rolling(60, min_periods=20).std() + 1e-9)
    s = pd.Series(cbot)
    return pd.DataFrame({
        "corn_close": cbot * 9.5, "cbot_eur_t": cbot, "ema_close": ema,
        "ema_cbot_basis": basis, "ema_cbot_basis_zscore_52w": bz.values,
        "wheat_close": cbot * 9.5 * wc,
        "corn_realized_vol_20": s.pct_change().rolling(20).std().values,
        "corn_sma_50": s.rolling(50).mean().values,
        "ema_oi_total": rng.uniform(500, 5000, n),
        "curve_backwardation_proxy": rng.normal(0, 1, n),
        "ethanol_production_kbd": 1000 + np.cumsum(rng.normal(0, 2, n)),
        "wasde_stocks_to_use_ratio": 0.12 + 0.03 * np.sin(np.linspace(0, 6 * np.pi, n)),
        "cot_mm_net_pct_oi_x": rng.normal(0, 10, n),
    }, index=idx)


def test_causal_z_is_shifted():
    df = _synthetic_master()
    z = v39._causal_z(df["ethanol_production_kbd"])
    assert z.iloc[:120].isna().all()  # fenêtre expandante -> début NaN


def test_run_v39_returns_all_experiments(tmp_path, monkeypatch):
    monkeypatch.setattr(v39, "V39_DIR", tmp_path)
    out = v39.run_v39_enrichment(_synthetic_master())
    assert out["version"] == "V39-ENRICH"
    for k in ["E1_duration", "E2_cost_tail", "E3_ethanol", "E4_cbot_trend", "E5_storage", "E6_cot"]:
        assert k in out
    assert out["E3_ethanol"].get("verdict") in {
        "ETHANOL_RELATED_TO_BASIS", "ETHANOL_WEAK_DRIVER_OF_EU_BASIS", "TOO_SHORT", "NO_DATA"}
