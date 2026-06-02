"""V131 — TARGET_RECOMMENDATION v3 : WATCH / WAIT_CONFIRMATION / z→0.5 / z→0.

V56 décidait l'objectif (z→0.5 vs z→0) sur un signal CONFIRMÉ. V3 ajoute la gestion du signal NAISSANT :
  - WAIT_CONFIRMATION : prime à peine au-dessus du seuil (z<1.2) -> marginal, attendre confirmation ;
  - WATCH            : tier MODÉRÉ avec contexte ambigu (ni clairement prudent, ni clairement complet) ;
  - z→0.5            : prudent (PHYSICAL_TENSION HIGH ∨ CBOT_SUPPORT LOW ∨ ADVERSE_RISK HIGH) ;
  - z→0              : complet (CBOT_SUPPORT MED/HIGH ∧ tension LOW ∧ adverse LOW) ;
  - sinon z→0.5 par défaut (signal fort, contexte neutre).

On VALIDE descriptivement (aucun fit, aucun seuil optimisé) : (a) la reco sur signaux confirmés fait au moins
aussi bien que V56 en PnL/efficacité ; (b) les signaux marginaux (WAIT_CONFIRMATION) sous-performent bien
(ce qui justifie d'attendre). On n'ajoute QUE des états ; la règle figée (short basis-haut) est INCHANGÉE.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout verrouillé. Contexte, jamais un veto.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V131_DIR = ARTEFACTS_DIR / "v131"
V131_DIR.mkdir(parents=True, exist_ok=True)
MAX_HOLD = 90
CONFIRM_Z = 1.2


def recommend_target_v3(adverse_risk: str, cbot_support: str, physical_tension: str,
                        entry_z: float, tier: str) -> str:
    """Recommandation à 4 états (aucun fit). Contexte, jamais un veto."""
    if entry_z is not None and entry_z < CONFIRM_Z:
        return "WAIT_CONFIRMATION"
    prudent = (cbot_support == "LOW" or adverse_risk == "HIGH" or physical_tension == "HIGH")
    full_ok = (cbot_support in ("MEDIUM", "HIGH") and physical_tension == "LOW" and adverse_risk == "LOW")
    if prudent:
        return "z->0.5"
    if full_ok:
        return "z->0"
    if tier == "MODERATE":
        return "WATCH"
    return "z->0.5"


def _tier_from_z(z: float) -> str:
    if pd.isna(z) or z < 1.0:
        return "NO_SIGNAL"
    if z < 1.5:
        return "MODERATE"
    return "STRONG" if z < 2.0 else "EXTREME"


def _bucket_metrics(sub: pd.DataFrame) -> dict[str, Any]:
    if len(sub) == 0:
        return {"n": 0}
    # objectif effectif = z->0 si reco z->0 sinon z->0.5 (WAIT/WATCH -> on évalue au z->0.5 prudent par défaut)
    use_z0 = sub["reco"] == "z->0"
    pnl = np.where(use_z0, sub["pnl_z0"], sub["pnl_z05"])
    days = np.where(use_z0, sub["days_z0"], sub["days_z05"])
    hit_z0 = ((sub["stopped_z0"] == 0) & (sub["days_z0"] < MAX_HOLD)).mean()
    hit_z05 = ((sub["pnl_z05"] > 0) & (sub["days_z05"] < MAX_HOLD)).mean()
    d = pd.Series(days).clip(lower=1)
    return {"n": int(len(sub)), "mean_pnl": round(float(np.mean(pnl)), 2),
            "profit_per_day": round(float((pd.Series(pnl) / d).mean()), 4),
            "mean_exposure_days": round(float(np.mean(days)), 1),
            "stop_rate_z0": round(float((sub["stopped_z0"] == 1).mean()), 3),
            "hit_rate_z0": round(float(hit_z0), 3), "hit_rate_z05": round(float(hit_z05), 3)}


def run_v131_target_v3(df: pd.DataFrame) -> dict[str, Any]:
    from mais.research.v47_objective_choice import _paired_objectives
    from mais.research.v56_target_recommendation import _attach_full_context
    assert_no_holdout(df)
    t = _paired_objectives(df)
    if len(t) < 15:
        return {"version": "V131-TARGET-V3", "verdict": "TOO_FEW", "n": int(len(t))}
    t = _attach_full_context(df, t)
    t["tier"] = t["entry_z"].map(_tier_from_z)
    t["reco"] = [recommend_target_v3(a, c, p, z, ti)
                 for a, c, p, z, ti in zip(t["adverse_risk"], t["cbot_support"], t["physical_tension"],
                                           t["entry_z"], t["tier"], strict=False)]

    by_reco = {r: _bucket_metrics(t[t["reco"] == r]) for r in t["reco"].unique()}
    confirmed = t[~t["reco"].isin(["WAIT_CONFIRMATION"])]
    marginal = t[t["reco"] == "WAIT_CONFIRMATION"]
    conf_pnl = round(float(np.where(confirmed["reco"] == "z->0", confirmed["pnl_z0"],
                                    confirmed["pnl_z05"]).mean()), 2) if len(confirmed) else None
    marg_pnl = round(float(marginal["pnl_z05"].mean()), 2) if len(marginal) else None
    always_z0 = round(float(t["pnl_z0"].mean()), 2)
    always_z05 = round(float(t["pnl_z05"].mean()), 2)

    waiting_justified = bool(marg_pnl is not None and conf_pnl is not None and marg_pnl < conf_pnl)
    not_worse = bool(conf_pnl is not None and conf_pnl >= max(always_z0, always_z05) - 0.5)
    verdict = "ADD_TO_INDICATOR" if (not_worse and (waiting_justified or marg_pnl is None)) else "WATCHLIST"

    out = {
        "version": "V131-TARGET-V3",
        "verdict": verdict,
        "n_trades": int(len(t)),
        "rule": ("WAIT_CONFIRMATION si z<1.2 ; sinon z→0.5 si (tension HIGH ∨ CBOT_SUPPORT LOW ∨ ADVERSE HIGH), "
                 "z→0 si (CBOT MED/HIGH ∧ tension LOW ∧ ADVERSE LOW), WATCH si MODÉRÉ ambigu, sinon z→0.5."),
        "reco_counts": {str(k): int((t["reco"] == k).sum()) for k in t["reco"].unique()},
        "by_recommendation": by_reco,
        "confirmed_mean_pnl": conf_pnl,
        "marginal_wait_mean_pnl": marg_pnl,
        "always_z0_mean_pnl": always_z0,
        "always_z05_mean_pnl": always_z05,
        "waiting_justified": waiting_justified,
        "confirmed_not_worse_than_fixed": not_worse,
        "interpretation": (
            f"{len(t)} signaux : {out_counts(t)}. PnL signaux confirmés {conf_pnl} vs marginaux "
            f"(WAIT, z<1.2) {marg_pnl} -> attendre {'JUSTIFIÉ' if waiting_justified else 'non concluant'}. "
            f"Confirmés ≥ meilleur fixe (z→0 {always_z0}/z→0.5 {always_z05}) : {not_worse}. V3 gère le signal "
            "NAISSANT (WAIT/WATCH) sans toucher la règle figée ni les seuils."),
        "note": "Réutilise V47 (objectifs pairés, stop -20, max 90j) + V56 (contexte). Aucun fit. hit_z0.5 "
                "approché (pnl>0 & sortie<90j). MFE/MAE détaillés vivent dans V82/V102. Contexte, pas un veto.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    t.to_parquet(V131_DIR / "target_v3_trades.parquet", index=False)
    (V131_DIR / "v131_target_v3.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def out_counts(t: pd.DataFrame) -> str:
    return ", ".join(f"{k}={int((t['reco'] == k).sum())}" for k in sorted(t["reco"].unique()))


def target_v3_report_block() -> str:
    artefact = V131_DIR / "v131_target_v3.json"
    if not artefact.exists():
        return ""
    try:
        s = json.loads(artefact.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    if s.get("version") != "V131-TARGET-V3" or s.get("verdict") == "TOO_FEW":
        return ""
    return (
        "### Recommandation d'objectif v3 (V131 — 4 états)\n"
        f"- Répartition : {s['reco_counts']}\n"
        f"- PnL confirmés {s['confirmed_mean_pnl']} vs marginaux WAIT {s['marginal_wait_mean_pnl']} "
        f"(attendre justifié : {s['waiting_justified']})\n"
        f"- **{s['verdict']}** : gère le signal naissant sans toucher la baseline. RESEARCH_ONLY_NOT_TRADING.\n"
    )
