"""V152 — event study 2.0 (aligné start A, CI bootstrap, censure)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.research import v152_event_study_v2 as es


def _synth(n=500, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    bz = 1.0 + 1.3 * np.sin(t / 35.0) + rng.normal(0, 0.05, n)
    basis = 50 + 20 * np.sin(t / 35.0) + rng.normal(0, 1, n)
    return pd.DataFrame({"ema_cbot_basis_zscore_52w": bz, "ema_cbot_basis": basis})


def test_event_study_builds_with_ci_and_censoring():
    out = es.build_event_study(_synth(), pre=20, post=60, n_boot=200, make_plot=False)
    assert out["verdict"] == "EVENT_STUDY_BUILT"
    assert out["n_episodes"] >= 5
    s = out["series"]["basis_z"]
    L = out["pre"] + out["post"] + 1
    for key in ("mean", "median", "q25", "q75", "ci95_lo", "ci95_hi", "n_at_offset"):
        assert len(s[key]) == L
    # IC contient la moyenne, quantiles ordonnés
    for i in range(L):
        assert s["ci95_lo"][i] <= s["mean"][i] + 1e-6
        assert s["mean"][i] <= s["ci95_hi"][i] + 1e-6
        assert s["q25"][i] <= s["q75"][i] + 1e-6


def test_compression_visible_post_start():
    """Sur une série cyclique, la médiane du basis_z baisse entre start et +post."""
    out = es.build_event_study(_synth(), pre=20, post=60, n_boot=100, make_plot=False)
    assert out["median_basis_z_at_post"] < out["median_basis_z_at_start"]


def test_too_few_episodes_guard():
    df = pd.DataFrame({"ema_cbot_basis_zscore_52w": np.full(50, 0.2),
                       "ema_cbot_basis": np.full(50, 10.0)})  # jamais de prime élevée
    out = es.build_event_study(df, make_plot=False)
    assert out["verdict"] == "TOO_FEW_EPISODES"
