"""V49 — Jambe LONG premium : un basis anormalement BAS se révèle-t-il à la hausse ?

L'étude s'est concentrée sur le SHORT premium (basis_z>1 -> la prime se comprime). Question symétrique :
quand basis_z < −1 (EMA anormalement BAS vs CBOT), le basis remonte-t-il vers 0 (long EMA / short CBOT) ?
V13 avait suggéré une asymétrie (short ≫ long). On le teste PROPREMENT, en miroir exact de la méthode short
(entrée non-overlap, sortie z→−0.5 / z→0, stop −20, max 90 j) et on COMPARE les deux jambes.

Discipline : exploratoire et DESCRIPTIF. La règle figée reste short-only ; ce module documente l'asymétrie,
il ne crée pas de signal long.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V49_DIR = ARTEFACTS_DIR / "v49"
V49_DIR.mkdir(parents=True, exist_ok=True)
MAX_HOLD = 90
STOP = -20.0
SEP = 40


def _sim_long(ema, cbot, bz, i, z_exit, max_hold, stop):
    """Trade LONG basis : profit quand EMA SURperforme le CBOT (le basis remonte). Sortie z→−z_exit."""
    n = len(ema)
    e0, c0, z0 = ema[i], cbot[i], bz[i]
    if np.isnan(e0) or np.isnan(c0) or np.isnan(z0):
        return None
    mae = 0.0
    last = None
    for t in range(1, max_hold + 1):
        j = i + t
        if j >= n or np.isnan(ema[j]) or np.isnan(cbot[j]):
            continue
        pnl = 1.0 * ((ema[j] / e0 - 1) - (cbot[j] / c0 - 1)) * e0  # long basis
        mae = min(mae, pnl)
        last = (pnl, t, bz[j], j)
        if pnl <= stop:
            return {"pnl": pnl, "days": t, "exit_z": bz[j], "mae": mae, "reverted": 0, "stopped": 1}
        if not np.isnan(bz[j]) and bz[j] >= -z_exit:  # remonté vers la cible
            return {"pnl": pnl, "days": t, "exit_z": bz[j], "mae": mae,
                    "reverted": int(z_exit == 0.0), "stopped": 0}
    if last is None:
        return None
    return {"pnl": last[0], "days": last[1], "exit_z": last[2], "mae": mae, "reverted": 0, "stopped": 0}


def long_leg_trades(df: pd.DataFrame) -> pd.DataFrame:
    ema = df["ema_close"].values
    cbot = df["cbot_eur_t"].values
    bz = df["ema_cbot_basis_zscore_52w"].values
    dates = df.index
    cand = np.where((df["ema_cbot_basis_zscore_52w"] < -1.0).values)[0]
    kept, last = [], None
    for i in cand:
        if last is None or (dates[i] - last).days >= SEP:
            kept.append(i)
            last = dates[i]
    rows = []
    for i in kept:
        r = _sim_long(ema, cbot, bz, i, 0.0, MAX_HOLD, STOP)
        if r is None:
            continue
        rows.append({
            "entry_date": str(dates[i].date()), "entry_z": round(float(bz[i]), 3),
            "pnl": round(float(r["pnl"]), 2), "days": int(r["days"]),
            "mae": round(float(r["mae"]), 2), "reverted": int(r["reverted"]), "stopped": int(r["stopped"]),
            "win": int(r["pnl"] > 0),
            # ADVERSE long = le basis s'écarte ENCORE plus bas au lieu de remonter
            "adverse": int(r["pnl"] <= 0 and r["reverted"] == 0),
        })
    return pd.DataFrame(rows)


def _stats(t: pd.DataFrame) -> dict[str, Any]:
    if len(t) == 0:
        return {"n": 0}
    return {"n": int(len(t)), "win_rate": round(float(t["win"].mean()), 3),
            "mean_pnl": round(float(t["pnl"].mean()), 2), "median_pnl": round(float(t["pnl"].median()), 2),
            "adverse_rate": round(float(t["adverse"].mean()), 3),
            "mean_days": round(float(t["days"].mean()), 1), "worst_mae": round(float(t["mae"].min()), 2)}


def run_v49_long_leg(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    long_t = long_leg_trades(df)
    if len(long_t) < 10:
        return {"version": "V49-LONG-PREMIUM-LEG", "verdict": "TOO_FEW", "n": int(len(long_t))}
    long_stats = _stats(long_t)

    # jambe short (réutilise la fiche existante, conditions équivalentes)
    from mais.research.v17_research_indicator import build_trades_detailed
    sd = build_trades_detailed(df)
    short_stats = {}
    if len(sd):
        short_stats = {"n": int(len(sd)), "win_rate": round(float(sd["win"].mean()), 3),
                       "mean_pnl": round(float(sd["pnl_z0_max90_sl20"].mean()), 2),
                       "median_pnl": round(float(sd["pnl_z0_max90_sl20"].median()), 2),
                       "mean_days": round(float(sd["duration_days"].mean()), 1)}

    long_works = bool(long_stats["mean_pnl"] > 0 and long_stats["win_rate"] >= 0.55)
    short_better = bool(short_stats and long_stats["mean_pnl"] < short_stats["mean_pnl"])
    verdict = ("LONG_LEG_ALSO_WORKS" if long_works and not short_better
               else "ASYMMETRY_CONFIRMED_SHORT_BETTER" if short_better
               else "LONG_LEG_WEAK")
    out = {
        "version": "V49-LONG-PREMIUM-LEG",
        "long_leg": long_stats,
        "short_leg": short_stats,
        "verdict": verdict,
        "interpretation": (
            "Jambe LONG (basis_z<−1, pari que la prime remonte) comparée à la jambe SHORT (basis_z>1). "
            "Asymétrie attendue : le short premium (vendre une prime EU trop chère) est plus robuste que "
            "l'achat d'une prime trop basse, car une prime basse peut refléter une faiblesse réelle d'EMA / "
            "un CBOT trop cher qui se corrige autrement. DESCRIPTIF : la règle reste short-only."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    long_t.to_parquet(V49_DIR / "long_leg_trades.parquet", index=False)
    (V49_DIR / "v49_long_leg.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
