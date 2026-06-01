"""Tests CT-02 (v105) — event study autour du début de compression (offline)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v104_compression_start as v104
import mais.research.v105_compression_event_study as v105


def _synthetic_master(n=900, seed=21):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2014-01-01", periods=n)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    wc = 1.3 + 0.15 * np.sin(np.linspace(0, 10 * np.pi, n)) + rng.normal(0, 0.02, n)
    basis = 40 * (wc - 1.0) + 14 * np.sin(np.linspace(0, 12 * np.pi, n)) + rng.normal(0, 2, n)
    ema = cbot + basis
    bz = (pd.Series(basis) - pd.Series(basis).rolling(60, min_periods=20).mean()) / (
        pd.Series(basis).rolling(60, min_periods=20).std() + 1e-9)
    s = pd.Series(cbot)
    return pd.DataFrame({
        "corn_close": cbot * 9.5, "cbot_eur_t": cbot, "ema_close": ema,
        "ema_cbot_basis": basis, "ema_cbot_basis_zscore_52w": bz.values,
        "wheat_close": cbot * 9.5 * wc,
        "corn_sma_50": (s * 9.5).rolling(50).mean().values,
        "corn_logret_20d": np.log(s / s.shift(20)).values,
        "corn_realized_vol_20": s.pct_change().rolling(20).std().values,
        "ema_oi_total": rng.uniform(500, 5000, n),
        "curve_backwardation_proxy": rng.normal(0, 1, n),
        "cot_mm_net_pct_oi_x": rng.normal(0, 10, n),
    }, index=idx)


def test_run_v105(tmp_path, monkeypatch):
    df = _synthetic_master()
    # construire les turning points dans un parquet temporaire
    monkeypatch.setattr(v104, "OUT_PARQUET", tmp_path / "tp.parquet")
    monkeypatch.setattr(v104, "V104_DIR", tmp_path)
    monkeypatch.setattr(v104, "EPISODES", tmp_path / "absent_ep.parquet")
    v104.run_v104_compression_start(df)
    monkeypatch.setattr(v105, "TP_PARQUET", tmp_path / "tp.parquet")
    monkeypatch.setattr(v105, "V105_DIR", tmp_path)
    monkeypatch.setattr(v105, "EVENT_PNG", tmp_path / "ev.png")
    out = v105.run_v105_event_study(df, make_png=False)
    assert out["version"] == "V105-EVENT-STUDY"
    if out["verdict"] not in ("TOO_FEW", "TOO_FEW_ALIGNED"):
        assert "pre_start_means_t_minus10_to_t_minus1" in out
        assert "bz_at_t0" in out
        assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"
