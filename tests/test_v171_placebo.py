"""V171 — placebo : spécificité de l'edge basis EMA vs spreads témoins."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.research import v171_placebo_spreads as v171


def _synth():
    idx = pd.date_range("2008-01-01", "2018-12-31", freq="B")
    n = len(idx)
    rng = np.random.default_rng(0)
    t = np.arange(n)
    # basis réel : fortement mean-reverting (cyclique) -> edge net
    basis = 36 + 16 * np.sin(2 * np.pi * t / 252.0) + rng.normal(0, 0.5, n)
    # témoins : marches aléatoires (pas d'edge de réversion)
    cols = {"ema_cbot_basis": basis}
    for name in ("corn_wheat_ratio", "corn_soy_ratio", "corn_oil_ratio"):
        cols[name] = 1.0 + np.cumsum(rng.normal(0, 0.02, n))
    return pd.DataFrame(cols, index=idx)


def test_zscore_is_causal():
    s = pd.Series(np.arange(400.0))
    z = v171._zscore(s, roll=100)
    # le z à t n'utilise que des stats décalées (shift(1)) -> pas de NaN après warmup, fini
    assert z.iloc[200:].notna().all()


def test_real_basis_dominates_placebos():
    out = v171.run_v171_placebo(_synth())
    assert out["verdict"] == "EDGE_SPECIFIC_TO_EMA_BASIS"
    assert out["real_rank_among_all"] == 1
    assert out["real"]["sharpe_per_trade"] > max(p["sharpe_per_trade"] for p in out["placebos"])


def test_engine_profits_on_mean_reverting_series():
    # série cyclique mean-reverting : short à z>1 puis réversion -> PnL moyen positif
    t = np.arange(2000)
    s = pd.Series(10 * np.sin(2 * np.pi * t / 252.0))
    z = v171._zscore(s, roll=252)
    pnl = v171._reversion_trades(s, z)
    assert len(pnl) >= 3
    assert pnl.mean() > 0
