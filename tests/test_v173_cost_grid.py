"""V173 — grille coûts×slippage par régime (offline, frame synthétique hors holdout)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.research import v173_cost_grid as v173


def _synth():
    idx = pd.date_range("2008-01-01", "2016-12-31", freq="B")
    t = np.arange(len(idx))
    rng = np.random.default_rng(0)
    bz = 2.1 * np.sin(2 * np.pi * t / 252.0) + rng.normal(0, 0.05, len(idx))
    cbot = 150 + np.cumsum(rng.normal(0, 0.1, len(idx)))
    ema = cbot + 60 + 18 * bz
    return pd.DataFrame({"ema_close": ema, "cbot_eur_t": cbot,
                         "ema_cbot_basis_zscore_52w": bz}, index=idx)


def test_death_cost_monotone_in_slippage():
    out = v173.run_v173_cost_grid(_synth())
    assert out["verdict"] == "COST_GRID_BUILT_DESCRIPTIVE"
    g = out["full_grid_all_trades"]
    # à coût fixe, plus de slippage -> moyenne nette plus basse
    assert g["cost0.0_slip0.0"]["mean_net"] >= g["cost0.0_slip1.0"]["mean_net"]
    assert g["cost0.0_slip0.0"]["mean_net"] >= g["cost8.0_slip0.0"]["mean_net"]


def test_strata_have_min_n_and_all_present():
    out = v173.run_v173_cost_grid(_synth())
    assert "ALL" in out["strata"]
    assert all(v["n"] >= 5 for v in out["strata"].values())


def test_net_math_two_legs():
    out = v173.run_v173_cost_grid(_synth())
    g = out["full_grid_all_trades"]
    # net(cost c, slip s) = gross - 2*(c+s) : l'écart entre deux cases ne dépend que de la grille
    d = g["cost0.0_slip0.0"]["mean_net"] - g["cost3.0_slip0.0"]["mean_net"]
    assert abs(d - 6.0) < 0.05
