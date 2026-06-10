"""V153 — labels START/IN_PROGRESS sans lookahead + renommage PROGRESS_SCORE."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.research import v153_start_vs_inprogress as v153


def _synth(n=400, seed=0):
    """Série basis_z avec plusieurs cycles montée->compression, + colonnes prix factices."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    bz = 1.0 + 1.2 * np.sin(t / 30.0) + rng.normal(0, 0.05, n)
    px = 200 + np.cumsum(rng.normal(0, 0.5, n))
    return pd.DataFrame({
        "ema_cbot_basis_zscore_52w": bz,
        "cbot_eur_t": px, "ema_close": px + 70, "corn_close": px, "wheat_close": px + 20,
    })


def test_progress_score_is_renamed():
    df = _synth()
    out = v153.compression_progress_score(df)
    assert "compression_progress_score" in out.columns
    assert "compression_progress" in out.columns
    assert "compression_trigger" not in out.columns


def test_start_events_detected():
    df = _synth()
    ev = v153.start_events(df)
    assert ev.sum() >= 2  # plusieurs cycles -> plusieurs débuts


def test_start_label_no_lookahead():
    """START_h{H}[i] ne doit dépendre que de [i-LOCKOUT, i+H] : tronquer après i+H ne change pas la valeur."""
    df = _synth()
    H = 10
    full = v153.start_label(df, horizon=H)
    for i in (60, 120, 200, 300):
        truncated = v153.start_label(df.iloc[: i + H + 1].copy(), horizon=H)
        a, b = full.iloc[i], truncated.iloc[i]
        assert (pd.isna(a) and pd.isna(b)) or a == b, f"lookahead à i={i}: {a} vs {b}"


def test_inprog_label_forward_only():
    df = _synth()
    y = v153.inprog_label(df, horizon=10)
    # le dernier point n'a pas de futur -> 0 (pas de drop futur observable)
    assert y.iloc[-1] == 0.0
    assert set(y.dropna().unique()).issubset({0.0, 1.0})


def test_run_v153_outputs_both_universes():
    df = _synth(n=500)
    out = v153.run_v153(df, horizon=10)
    assert out["rename"]["descriptive_now"] == "COMPRESSION_PROGRESS_SCORE"
    assert "START" in out and "INPROG" in out
    assert out["verdict"] in ("START_SCORE_PREDICTIVE_ADD_TO_REPORT",
                              "START_TIMING_REMAINS_HARD_DESCRIPTIVE_ONLY")
