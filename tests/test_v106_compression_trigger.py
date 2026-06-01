"""Tests CT-09/10/11 (v106) — compression trigger (offline)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v106_compression_trigger as v106


def _synthetic_master(n=900, seed=21):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2014-01-01", periods=n)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    wc = 1.3 + 0.15 * np.sin(np.linspace(0, 10 * np.pi, n)) + rng.normal(0, 0.02, n)
    basis = 40 * (wc - 1.0) + 14 * np.sin(np.linspace(0, 12 * np.pi, n)) + rng.normal(0, 2, n)
    ema = cbot + basis
    bz = (pd.Series(basis) - pd.Series(basis).rolling(60, min_periods=20).mean()) / (
        pd.Series(basis).rolling(60, min_periods=20).std() + 1e-9)
    return pd.DataFrame({
        "cbot_eur_t": cbot, "ema_close": ema, "corn_close": cbot * 9.5,
        "wheat_close": cbot * 9.5 * wc,
        "ema_cbot_basis": basis, "ema_cbot_basis_zscore_52w": bz.values,
    }, index=idx)


def test_trigger_features_causal():
    f = v106.trigger_features(_synthetic_master())
    for c in ("bz_chg_3", "ema_minus_cbot_5", "wc_chg_10", "cbot_ret_5"):
        assert c in f.columns


def test_compute_trigger_score_bounds():
    tr = v106.compute_trigger_score(_synthetic_master())
    active = tr["compression_trigger"].isin(["NONE", "EARLY", "CONFIRMED"])
    assert tr.loc[active, "compression_trigger_score"].between(0, 4).all()


def test_run_v106(tmp_path, monkeypatch):
    monkeypatch.setattr(v106, "V106_DIR", tmp_path)
    out = v106.run_v106_trigger(_synthetic_master())
    assert out["version"] == "V106-COMPRESSION-TRIGGER"
    assert out["verdict"] in (
        "COMPRESSION_TRIGGER_LEADING_ADD_TO_REPORT",
        "COMPRESSION_TRIGGER_REFLECTS_ONGOING_NOT_LEADING",
        "COMPRESSION_TRIGGER_WEAK_CONTEXT_ONLY")
    assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"


def test_report_block(tmp_path):
    assert isinstance(v106.compression_trigger_report_block(_synthetic_master()), str)
