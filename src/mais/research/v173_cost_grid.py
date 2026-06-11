"""V173 — Grille de stress coûts × slippage par régime : où meurt l'edge ?

Sur le ledger réel des trades baseline (entrée z>1, sortie z0 max90, stop -20 — V17, inchangé), on
applique une grille de coûts aller-retour (2 jambes) et on mesure le COÛT-SEUIL DE MORT (le plus grand
coût/jambe où la moyenne nette reste > 0), globalement et par strate : palier d'entrée, saison, crise,
contexte CBOT. Purement descriptif : aucun seuil n'est ré-optimisé, la baseline ne bouge pas.
RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout
from mais.research.v17_research_indicator import build_trades_detailed

V173_DIR = ARTEFACTS_DIR / "v173"
V173_DIR.mkdir(parents=True, exist_ok=True)

COSTS_PER_LEG = [0.0, 1.0, 2.0, 3.0, 5.0, 8.0]
SLIPPAGES_PER_LEG = [0.0, 0.5, 1.0]
PRIMARY_SLIPPAGE = 0.5
GROSS_COL = "pnl_z0_max90_sl20"


def _death_cost(gross: pd.Series, slippage: float) -> float | None:
    """Plus grand coût/jambe de la grille où la moyenne nette reste positive."""
    alive = [c for c in COSTS_PER_LEG if (gross - 2 * (c + slippage)).mean() > 0]
    return max(alive) if alive else None


def _stratum_stats(g: pd.DataFrame) -> dict[str, Any]:
    gross = g[GROSS_COL]
    net3 = gross - 2 * (3.0 + PRIMARY_SLIPPAGE)
    return {
        "n": int(len(g)),
        "gross_mean": round(float(gross.mean()), 2),
        "death_cost_per_leg_slip05": _death_cost(gross, PRIMARY_SLIPPAGE),
        "mean_net_cost3_slip05": round(float(net3.mean()), 2),
        "hit_rate_cost3_slip05": round(float((net3 > 0).mean()), 3),
    }


def run_v173_cost_grid(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    ledger = build_trades_detailed(df)
    if ledger.empty:
        return {"version": "V173-COST-GRID", "verdict": "MISSING_DATA"}
    gross = ledger[GROSS_COL]

    full_grid = {}
    for c in COSTS_PER_LEG:
        for s in SLIPPAGES_PER_LEG:
            net = gross - 2 * (c + s)
            full_grid[f"cost{c}_slip{s}"] = {
                "mean_net": round(float(net.mean()), 2),
                "pct_positive": round(float((net > 0).mean()), 3),
                "total_net": round(float(net.sum()), 1),
            }

    strata: dict[str, Any] = {"ALL": _stratum_stats(ledger)}
    for col, label in (("tier", "tier"), ("season", "season"),
                       ("crisis", "crisis"), ("cbot_context", "cbot_context")):
        if col not in ledger.columns:
            continue
        for val, g in ledger.groupby(col):
            if len(g) >= 5:
                strata[f"{label}={val}"] = _stratum_stats(g)

    death_all = strata["ALL"]["death_cost_per_leg_slip05"]
    out = {
        "version": "V173-COST-GRID",
        "verdict": "COST_GRID_BUILT_DESCRIPTIVE",
        "n_trades": int(len(ledger)),
        "grid_costs_per_leg": COSTS_PER_LEG, "grid_slippages_per_leg": SLIPPAGES_PER_LEG,
        "full_grid_all_trades": full_grid,
        "strata": strata,
        "headline": (f"Coût de mort global (slippage 0.5/jambe) : {death_all} €/t/jambe ; "
                     "voir strates pour où l'edge survit le plus longtemps."),
        "guardrails": [
            "baseline inchangée (z>1, sortie z0 max90, stop -20) ; aucun seuil ré-optimisé",
            "strates avec n<5 omises ; lecture descriptive, pas une règle de filtrage",
            "cohérent V10/V15 : le mur des coûts reste la contrainte n°1 du statut RESEARCH_ONLY",
        ],
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V173_DIR / "v173_cost_grid.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
