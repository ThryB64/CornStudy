"""Tests V60-intraday — basis aligné settlement (offline, intraday synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.intraday_aligned_basis as iab


def _synthetic_intraday(days=40, seed=1):
    rng = np.random.default_rng(seed)
    rows = []
    price = 450.0
    for d in pd.bdate_range("2026-04-01", periods=days):
        for h in (14, 15, 16, 17, 18, 19):
            price += rng.normal(0, 1.0)
            rows.append((pd.Timestamp(d) + pd.Timedelta(hours=h), price))
    idx = pd.DatetimeIndex([r[0] for r in rows], tz="UTC")
    return pd.DataFrame({"close": [r[1] for r in rows]}, index=idx)


def test_align_gap_stats():
    out = iab.align_gap_stats(_synthetic_intraday(), settle_hour_utc=16)
    assert out["verdict"] == "ALIGNMENT_GAP_MEASURED"
    assert out["n_days"] >= 20
    assert out["mean_abs_rel_gap"] >= 0.0


def test_align_gap_no_data():
    assert iab.align_gap_stats(pd.DataFrame())["verdict"] == "NO_INTRADAY"


def test_run_offline_watchlist(tmp_path, monkeypatch):
    monkeypatch.setattr(iab, "V60I_DIR", tmp_path)
    out = iab.run_v60_intraday(try_network=False)
    assert out["version"] == "V60-INTRADAY-BASIS"
    assert out["verdict"] == "WATCHLIST_DATA_GATED"
    assert out["status"] == "RESEARCH_ONLY_NOT_TRADING"
