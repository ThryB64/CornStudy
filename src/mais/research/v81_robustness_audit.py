"""V81 — Audit de robustesse de l'edge short-premium : stabilité leave-one-year-out + confond crise.

L'edge baseline (≈81% win, ≈+12.8 €/t sur 42 trades) repose sur peu d'observations. Avant toute confiance,
on vérifie qu'il n'est pas porté par une seule année (notamment le bull 2020-2022, cf. confond V79) :

- stats PAR année (n, win, PnL, ADVERSE) ;
- leave-one-year-out (LOYO) : recalcule win/PnL en RETIRANT chaque année -> l'edge survit-il partout ?
- ex-crise : edge hors 2020-2022 ;
- sensibilité au coût (0 / 2 / 5 €/t par leg, appliqué au PnL).

Aucun fit, aucune optimisation ; pur diagnostic de stabilité. Baseline figée inchangée.
Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V81_DIR = ARTEFACTS_DIR / "v81"
V81_DIR.mkdir(parents=True, exist_ok=True)
CRISIS = (2020, 2021, 2022)


def _trades(df: pd.DataFrame) -> pd.DataFrame:
    from mais.research.v17_research_indicator import build_trades_detailed
    from mais.research.v32_adverse_path_research import build_adverse_frame
    t = build_trades_detailed(df)
    if len(t) == 0:
        return t
    t = t.rename(columns={"pnl_z0_max90_sl20": "pnl"})
    t["year"] = pd.to_datetime(t["entry_date"]).dt.year
    adv = build_adverse_frame(df)
    if len(adv):
        t = t.merge(adv[["entry_date", "adverse"]], on="entry_date", how="left")
    return t


def _stats(sub: pd.DataFrame, cost: float = 0.0) -> dict[str, Any]:
    if len(sub) == 0:
        return {"n": 0}
    pnl = sub["pnl"] - cost
    return {"n": int(len(sub)), "win_rate": round(float((pnl > 0).mean()), 3),
            "mean_pnl": round(float(pnl.mean()), 2),
            "adverse_rate": round(float(sub["adverse"].mean()), 3) if "adverse" in sub else None}


def run_v81_robustness(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    t = _trades(df)
    if len(t) < 15:
        return {"version": "V81-ROBUSTNESS", "verdict": "TOO_FEW", "n": int(len(t))}

    overall = _stats(t)
    by_year = {int(y): _stats(g) for y, g in t.groupby("year")}

    # leave-one-year-out
    loyo = {}
    for y in sorted(t["year"].unique()):
        loyo[int(y)] = _stats(t[t["year"] != y])
    loyo_pnls = [v["mean_pnl"] for v in loyo.values()]
    loyo_wins = [v["win_rate"] for v in loyo.values()]
    edge_stable_loyo = bool(min(loyo_pnls) > 0 and min(loyo_wins) >= 0.6)

    # ex-crise
    ex_crisis = _stats(t[~t["year"].isin(CRISIS)])
    crisis_only = _stats(t[t["year"].isin(CRISIS)])
    edge_survives_ex_crisis = bool(ex_crisis.get("n", 0) >= 8 and ex_crisis["mean_pnl"] > 0
                                   and ex_crisis["win_rate"] >= 0.6)

    # sensibilité au coût
    cost_sens = {f"cost_{c}": _stats(t, cost=c) for c in (0.0, 2.0, 5.0)}
    profitable_at_cost5 = bool(cost_sens["cost_5.0"]["mean_pnl"] > 0)

    # année la plus contributrice (part du PnL total)
    total_pnl = float(t["pnl"].sum())
    year_share = {int(y): round(float(g["pnl"].sum() / total_pnl), 3)
                  for y, g in t.groupby("year")} if total_pnl != 0 else {}
    max_year_share = max(year_share.values()) if year_share else None

    if edge_stable_loyo and edge_survives_ex_crisis:
        verdict = "EDGE_STABLE_NOT_DRIVEN_BY_ONE_YEAR"
    elif edge_survives_ex_crisis:
        verdict = "EDGE_SURVIVES_EX_CRISIS_SOME_YEAR_SENSITIVITY"
    else:
        verdict = "EDGE_FRAGILE_CONCENTRATED"

    out = {
        "version": "V81-ROBUSTNESS",
        "overall": overall,
        "by_year": by_year,
        "loyo_min_mean_pnl": round(float(min(loyo_pnls)), 2),
        "loyo_min_win_rate": round(float(min(loyo_wins)), 3),
        "edge_stable_loyo": edge_stable_loyo,
        "ex_crisis": ex_crisis,
        "crisis_only": crisis_only,
        "edge_survives_ex_crisis": edge_survives_ex_crisis,
        "cost_sensitivity": cost_sens,
        "profitable_at_cost_5": profitable_at_cost5,
        "year_pnl_share": year_share,
        "max_single_year_pnl_share": max_year_share,
        "verdict": verdict,
        "interpretation": (
            f"Edge global {overall['win_rate']} win / {overall['mean_pnl']} €/t. LOYO : pire année retirée "
            f"-> PnL min {round(float(min(loyo_pnls)), 2)}, win min {round(float(min(loyo_wins)), 3)}. "
            f"Hors crise 2020-2022 : {ex_crisis.get('win_rate')} win / {ex_crisis.get('mean_pnl')} €/t "
            f"(n={ex_crisis.get('n')}). À coût 5 €/t/leg : {cost_sens['cost_5.0']['mean_pnl']} €/t. "
            f"Part PnL de l'année la plus contributrice : {max_year_share}. "
            "Diagnostic de stabilité : l'edge est crédible s'il survit LOYO ET hors crise."),
        "caveat": "n=42, descriptif. Coût appliqué linéairement au PnL z→0. Aucun fit/optimisation.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V81_DIR / "v81_robustness.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
