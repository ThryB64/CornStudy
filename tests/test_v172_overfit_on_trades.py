"""V172-REAL — pack anti-overfitting branché sur les trades simulés (hors holdout 2024)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.research import v172_overfit_on_trades as v172r


def _synth():
    # 2008->2016 (évite le holdout 2024), prime cyclique -> entrées z>seuil puis compression
    idx = pd.date_range("2008-01-01", "2016-12-31", freq="B")
    t = np.arange(len(idx))
    rng = np.random.default_rng(0)
    bz = 2.1 * np.sin(2 * np.pi * t / 252.0) + rng.normal(0, 0.05, len(idx))
    cbot = 150 + np.cumsum(rng.normal(0, 0.1, len(idx)))
    ema = cbot + 60 + 18 * bz  # basis = 60 + 18*bz ; quand bz tombe, ema retombe vers cbot
    return pd.DataFrame({"ema_close": ema, "cbot_eur_t": cbot,
                         "ema_cbot_basis_zscore_52w": bz}, index=idx)


def test_threshold_family_produces_trades():
    df = _synth()
    for thr in (0.5, 1.0, 1.5):
        trades = v172r._trades_for_threshold(df, thr)
        assert len(trades) >= 3
        # moins de trades quand le seuil monte
    assert len(v172r._trades_for_threshold(df, 0.5)) >= len(v172r._trades_for_threshold(df, 1.5))


def test_run_real_overfit_pack():
    out = v172r.run_v172_on_real_trades(_synth())
    assert out["verdict"] in ("SURVIVES_MULTIPLICITY", "FRAGILE_UNDER_MULTIPLICITY")
    assert out["baseline_n_trades"] > 0
    assert set(out["deflated_sharpe_by_n_trials"]) == {"1", "6", "50", "100"}
    assert out["pbo"]["verdict"] in ("ROBUST", "OVERFIT_LIKELY", "SKIP")
    # DSR décroît (ou reste) quand n_trials monte
    d1 = out["deflated_sharpe_by_n_trials"]["1"]["deflated_sharpe_ratio"]
    d100 = out["deflated_sharpe_by_n_trials"]["100"]["deflated_sharpe_ratio"]
    assert d100 <= d1 + 1e-9
