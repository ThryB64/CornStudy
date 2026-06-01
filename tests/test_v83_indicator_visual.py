"""Tests V-VISUAL — génération des figures de l'indicateur (offline)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v83_indicator_visual as viz


def _synthetic_master(n=900, seed=21):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2014-01-01", periods=n)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    wc = 1.3 + 0.15 * np.sin(np.linspace(0, 10 * np.pi, n)) + rng.normal(0, 0.02, n)
    basis = 40 * (wc - 1.0) + 14 * np.sin(np.linspace(0, 12 * np.pi, n)) + rng.normal(0, 2, n)
    bz = (pd.Series(basis) - pd.Series(basis).rolling(60, min_periods=20).mean()) / (
        pd.Series(basis).rolling(60, min_periods=20).std() + 1e-9)
    s = pd.Series(cbot)
    return pd.DataFrame({
        "corn_close": cbot * 9.5, "cbot_eur_t": cbot, "ema_close": cbot + basis,
        "ema_cbot_basis": basis, "ema_cbot_basis_zscore_52w": bz.values,
        "wheat_close": cbot * 9.5 * wc,
        "corn_sma_50": (s * 9.5).rolling(50).mean().values,
        "corn_logret_20d": np.log(s / s.shift(20)).values,
        "corn_realized_vol_20": s.pct_change().rolling(20).std().values,
        "ema_oi_total": rng.uniform(500, 5000, n),
        "curve_backwardation_proxy": rng.normal(0, 1, n),
        "cot_mm_net_pct_oi_x": rng.normal(0, 10, n),
    }, index=idx)


def test_build_visual(tmp_path):
    out = viz.build_indicator_visual(_synthetic_master(), out_png=tmp_path / "ind.png")
    assert out["verdict"] in ("VISUAL_BUILT", "NO_DATA")
    if out["verdict"] == "VISUAL_BUILT":
        assert (tmp_path / "ind.png").exists()


def test_build_event_study(tmp_path):
    out = viz.build_event_study(_synthetic_master(), out_png=tmp_path / "ev.png")
    assert out["verdict"] in ("EVENT_STUDY_BUILT", "NO_DATA")
    if out["verdict"] == "EVENT_STUDY_BUILT":
        assert (tmp_path / "ev.png").exists()
