"""Tests V149 — visuel multi-vues (EMA/CBOT + multi-seuils), synthétique."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v149_indicator_multiview as v149


def _master(n=900):
    rng = np.random.default_rng(0)
    idx = pd.date_range("2016-01-01", periods=n, freq="B")
    z = 0.5 + np.abs(np.cumsum(rng.normal(0, 0.12, n))) % 2.2
    cbot = np.linspace(150, 135, n) + rng.normal(0, 3, n)
    basis = 40 + z * 8 + rng.normal(0, 2, n)
    ema = cbot + basis
    df = pd.DataFrame({"ema_cbot_basis_zscore_52w": z, "ema_cbot_basis": basis,
                       "ema_close": ema, "cbot_eur_t": cbot}, index=idx)
    df.index.name = "Date"
    return df


def test_threshold_distribution_monotone_n():
    dist = v149.threshold_distribution(_master())
    ns = [d["n_signals"] for d in dist]
    # n décroît (ou égal) quand le seuil monte
    assert all(ns[i] >= ns[i + 1] for i in range(len(ns) - 1))
    assert dist[0]["threshold"] == 0.5 and dist[-1]["threshold"] == 2.0


def test_ema_cbot_visual(tmp_path, monkeypatch):
    monkeypatch.setattr(v149, "assert_no_holdout", lambda d: None)
    out = v149.build_ema_cbot_visual(_master(), out_png=tmp_path / "emacbot.png")
    assert out["verdict"] == "EMA_CBOT_VISUAL_BUILT"
    assert (tmp_path / "emacbot.png").exists()


def test_multithreshold_visual(tmp_path, monkeypatch):
    monkeypatch.setattr(v149, "assert_no_holdout", lambda d: None)
    out = v149.build_multithreshold_visual(_master(), out_png=tmp_path / "multi.png")
    assert out["verdict"] == "MULTITHRESHOLD_VISUAL_BUILT"
    assert (tmp_path / "multi.png").exists()
    assert "metric_caveat" in out and "best-case" in out["metric_caveat"].lower()
