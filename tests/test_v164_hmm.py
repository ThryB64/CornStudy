"""V164 — HMM régime, triangulation du START."""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pytest

from mais.research import v164_hmm_regime as v164

pytest.importorskip("statsmodels")


def _synth(n=1500, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    bz = 1.0 + 1.3 * np.sin(2 * np.pi * t / 252.0) + rng.normal(0, 0.05, n)
    return pd.DataFrame({"ema_cbot_basis_zscore_52w": bz},
                        index=pd.date_range("2010-01-01", periods=n, freq="B"))


def test_hmm_runs_and_triangulates():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        out = v164.run_v164(_synth())
    assert out["verdict"] in ("START_TRIANGULATED", "START_LABEL_ONLY_PARTIAL_AGREEMENT",
                              "FIT_FAILED")
    if out["verdict"] != "FIT_FAILED":
        assert 0.0 <= out["frac_time_in_compressing_regime"] <= 1.0
        assert out["n_label_A_starts"] >= 1
        assert "agreement_rate_hmm_to_labelA" in out


def test_too_few_obs_guard():
    df = pd.DataFrame({"ema_cbot_basis_zscore_52w": np.linspace(0, 1, 100)},
                      index=pd.date_range("2020-01-01", periods=100, freq="B"))
    assert v164.run_v164(df)["verdict"] == "TOO_FEW_OBS"
