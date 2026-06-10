"""V162 — VECM / cointégration EMA-CBOT."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mais.research import v162_vecm_cointegration as v162

pytest.importorskip("statsmodels")


def _cointegrated(n=600, seed=0):
    """CBOT = marche aléatoire ; EMA = CBOT + spread stationnaire (mean-reverting) -> cointégrés."""
    rng = np.random.default_rng(seed)
    cbot = 150 + np.cumsum(rng.normal(0, 1.0, n))
    spread = np.zeros(n)
    for i in range(1, n):
        spread[i] = 0.93 * spread[i - 1] + rng.normal(0, 1.0)  # AR(1) stationnaire
    ema = cbot + 60 + spread
    return pd.DataFrame({"ema_close": ema, "cbot_eur_t": cbot})


def test_ar1_halflife_positive():
    rng = np.random.default_rng(1)
    x = np.zeros(500)
    for i in range(1, 500):
        x[i] = 0.9 * x[i - 1] + rng.normal()
    hl = v162._ar1_halflife(pd.Series(x))
    assert hl is not None and hl > 0


def test_vecm_detects_cointegration_and_halflife():
    out = v162.run_v162(_cointegrated())
    assert out["verdict"] == "COINTEGRATED_VECM_FITTED"
    assert out["full_sample"]["cointegrated"] is True
    assert out["halflife_ecm_resid_days"] is not None
    assert out["who_corrects"] in ("EMA_LEG", "CBOT_LEG")
    assert 0.0 <= out["correction_share_cbot"] <= 1.0


def test_missing_columns_guard():
    out = v162.run_v162(pd.DataFrame({"foo": [1, 2, 3]}))
    assert out["verdict"] == "MISSING_COLUMNS"
