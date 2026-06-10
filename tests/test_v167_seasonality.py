"""V167 — saisonnalité des départs de compression."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.research import v167_start_seasonality as v167


def _synth(years=6, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2015-01-01", periods=years * 252, freq="B")
    t = np.arange(len(idx))
    # prime qui monte l'été puis se compresse (saisonnalité annuelle ~252j)
    bz = 1.0 + 1.2 * np.sin(2 * np.pi * t / 252.0) + rng.normal(0, 0.05, len(idx))
    return pd.DataFrame({"ema_cbot_basis_zscore_52w": bz}, index=idx)


def test_seasonality_maps_months_and_seasons():
    out = v167.run_v167(_synth())
    assert out["verdict"] == "SEASONALITY_MAPPED"
    assert out["n_episodes"] >= 8
    assert sum(out["starts_by_month"].values()) == out["n_episodes"]
    assert out["peak_start_season"] in ("DJF", "MAM", "JJA", "SON")
    assert set(out["by_season"]) <= {"DJF", "MAM", "JJA", "SON"}


def test_too_few_episodes_guard():
    df = pd.DataFrame({"ema_cbot_basis_zscore_52w": np.full(100, 0.1)},
                      index=pd.date_range("2020-01-01", periods=100, freq="B"))
    assert v167.run_v167(df)["verdict"] == "TOO_FEW_EPISODES"
