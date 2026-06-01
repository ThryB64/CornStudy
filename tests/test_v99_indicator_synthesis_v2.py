"""Tests V99 — synthèse indicateur v2 (offline)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v99_indicator_synthesis_v2 as v99


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
        "ema_backwardation_flag": (rng.normal(0, 1, n) > 0).astype(int),
        "ema_spread_f0_f1": rng.normal(-1.5, 2, n),
        "curve_backwardation_proxy": rng.normal(0, 1, n),
        "cot_mm_net_pct_oi_x": rng.normal(0, 10, n),
        "data_quality": np.ones(n),
    }, index=idx)


def test_synthesize_v2(tmp_path, monkeypatch):
    monkeypatch.setattr(v99, "V99_DIR", tmp_path)
    monkeypatch.setattr(v99, "WX_JOURNAL", tmp_path / "none.jsonl")
    out = v99.synthesize_indicator_v2(_synthetic_master(), with_network=False)
    assert out["version"] == "V99-SYNTHESIS-V2"
    if out["verdict"] == "SYNTHESIS_V2_BUILT":
        assert "enso_context" in out and "substitution_warning" in out and "weather_warning" in out
        assert "cbot_support_v2" in out
        assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"


def test_report_block(tmp_path, monkeypatch):
    monkeypatch.setattr(v99, "V99_DIR", tmp_path)
    monkeypatch.setattr(v99, "WX_JOURNAL", tmp_path / "none.jsonl")
    assert isinstance(v99.synthesis_v2_report_block(_synthetic_master(), with_network=False), str)
