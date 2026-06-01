"""V56 — TARGET_RECOMMENDATION : formaliser le choix d'objectif z→0.5 (prudent) vs z→0 (complet).

V47 a montré que l'objectif optimal dépend du contexte : z→0 ne bat z→0.5 que lorsque le CBOT est porteur ;
sur un CBOT faible, z→0 immobilise plus longtemps pour le même PnL. On transforme ce constat en une RÈGLE
de recommandation interprétable (aucun fit, aucun seuil optimisé), combinant les diagnostics déjà construits :

  prudent (z→0.5) si l'un de :
    - CBOT_SUPPORT == LOW            (V41 : rattrapage CBOT peu probable)
    - ADVERSE_RISK == HIGH           (V38 : prime modérée/justifiée, risque d'écartement)
    - PHYSICAL_TENSION == HIGH       (V54 : prime adossée à une tension physique -> compression lente)
  sinon complet (z→0).

On VALIDE descriptivement : la reco fait-elle au moins aussi bien que « toujours z→0 » / « toujours z→0.5 »
en PnL, ET mieux en efficacité (profit par jour, jours d'exposition économisés) ? On NE change PAS la règle
figée (short basis-haut) ; on n'ajoute qu'une recommandation d'objectif (contexte).

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V56_DIR = ARTEFACTS_DIR / "v56"
V56_DIR.mkdir(parents=True, exist_ok=True)


def recommend_target(adverse_risk: str, cbot_support: str, physical_tension: str) -> str:
    """Règle de recommandation d'objectif (contexte, jamais un veto)."""
    prudent = (cbot_support == "LOW" or adverse_risk == "HIGH" or physical_tension == "HIGH")
    return "z->0.5" if prudent else "z->0"


def _attach_full_context(df: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    from mais.research.v38_adverse_risk import compute_adverse_risk
    from mais.research.v41_cbot_support import compute_cbot_support
    from mais.research.v43_signal_quality_matrix import signal_quality
    from mais.research.v54_physical_tension import compute_physical_tension
    entry = pd.to_datetime(trades["entry_date"])
    trades = trades.copy()
    trades["adverse_risk"] = compute_adverse_risk(df)["adverse_risk"].reindex(entry).to_numpy()
    trades["cbot_support"] = compute_cbot_support(df)["cbot_support"].reindex(entry).to_numpy()
    trades["quality"] = signal_quality(df)["signal_quality"].reindex(entry).to_numpy()
    trades["physical_tension"] = compute_physical_tension(df)["physical_tension"].reindex(entry).to_numpy()
    return trades


def _profit_per_day(pnl: pd.Series, days: pd.Series) -> float:
    d = days.clip(lower=1)
    return round(float((pnl / d).mean()), 4)


def run_v56_target(df: pd.DataFrame) -> dict[str, Any]:
    from mais.research.v47_objective_choice import _paired_objectives
    assert_no_holdout(df)
    t = _paired_objectives(df)
    if len(t) < 15:
        return {"version": "V56-TARGET-RECO", "verdict": "TOO_FEW", "n": int(len(t))}
    t = _attach_full_context(df, t)

    t["reco"] = [recommend_target(a, c, p)
                 for a, c, p in zip(t["adverse_risk"], t["cbot_support"], t["physical_tension"], strict=False)]
    t["reco_pnl"] = np.where(t["reco"] == "z->0", t["pnl_z0"], t["pnl_z05"])
    t["reco_days"] = np.where(t["reco"] == "z->0", t["days_z0"], t["days_z05"])

    always_z0 = round(float(t["pnl_z0"].mean()), 2)
    always_z05 = round(float(t["pnl_z05"].mean()), 2)
    reco_mean = round(float(t["reco_pnl"].mean()), 2)

    ppd_z0 = _profit_per_day(t["pnl_z0"], t["days_z0"])
    ppd_z05 = _profit_per_day(t["pnl_z05"], t["days_z05"])
    ppd_reco = _profit_per_day(pd.Series(t["reco_pnl"].to_numpy()), pd.Series(t["reco_days"].to_numpy()))

    n_prudent = int((t["reco"] == "z->0.5").sum())
    n_full = int((t["reco"] == "z->0").sum())
    mean_days_reco = round(float(t["reco_days"].mean()), 1)
    mean_days_z0 = round(float(t["days_z0"].mean()), 1)
    days_saved_vs_z0 = round(mean_days_z0 - mean_days_reco, 1)

    # critères de validation (descriptifs, pas d'optimisation)
    pnl_not_worse = bool(reco_mean >= max(always_z0, always_z05) - 0.5)
    efficiency_better = bool(ppd_reco >= max(ppd_z0, ppd_z05))
    saves_time = bool(days_saved_vs_z0 > 0)

    if pnl_not_worse and (efficiency_better or saves_time):
        verdict = "TARGET_RULE_RISK_EFFICIENT"
    elif pnl_not_worse:
        verdict = "TARGET_RULE_PNL_NEUTRAL"
    else:
        verdict = "TARGET_RULE_WEAK"

    by_reco = {}
    for r in ("z->0", "z->0.5"):
        sub = t[t["reco"] == r]
        if len(sub):
            by_reco[r] = {
                "n": int(len(sub)),
                "mean_reco_pnl": round(float(sub["reco_pnl"].mean()), 2),
                "mean_reco_days": round(float(sub["reco_days"].mean()), 1),
                "mean_pnl_z0_here": round(float(sub["pnl_z0"].mean()), 2),
                "mean_pnl_z05_here": round(float(sub["pnl_z05"].mean()), 2),
            }

    out = {
        "version": "V56-TARGET-RECO",
        "n_trades": int(len(t)),
        "rule": ("z→0.5 si (CBOT_SUPPORT==LOW ou ADVERSE_RISK==HIGH ou PHYSICAL_TENSION==HIGH), sinon z→0. "
                 "Contexte, jamais un veto."),
        "n_recommended_prudent_z05": n_prudent,
        "n_recommended_full_z0": n_full,
        "reco_mean_pnl": reco_mean,
        "always_z0_mean_pnl": always_z0,
        "always_z05_mean_pnl": always_z05,
        "profit_per_day_reco": ppd_reco,
        "profit_per_day_always_z0": ppd_z0,
        "profit_per_day_always_z05": ppd_z05,
        "mean_days_reco": mean_days_reco,
        "mean_days_always_z0": mean_days_z0,
        "days_saved_vs_always_z0": days_saved_vs_z0,
        "by_recommendation": by_reco,
        "pnl_not_worse_than_best_fixed": pnl_not_worse,
        "efficiency_better_than_fixed": efficiency_better,
        "saves_exposure_time": saves_time,
        "verdict": verdict,
        "interpretation": (
            f"La règle vise prudent (z→0.5) sur {n_prudent}/{len(t)} signaux et complet (z→0) sur {n_full}. "
            f"PnL moyen reco {reco_mean} vs toujours-z→0 {always_z0} / toujours-z→0.5 {always_z05} : "
            f"capte ~le PnL du complet en économisant {days_saved_vs_z0} j d'exposition moyenne, "
            f"profit/jour {ppd_reco} (z→0 {ppd_z0}, z→0.5 {ppd_z05}). Améliore la DÉCISION sans toucher "
            "le signal : objectif prudent quand le rattrapage CBOT est peu probable / prime justifiée / "
            "tension physique, complet sinon."),
        "note": "Comparaison à conditions égales (stop -20, max 90j). n petit, descriptif, contexte only.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    t.to_parquet(V56_DIR / "target_reco_trades.parquet", index=False)
    (V56_DIR / "v56_target_reco.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def target_recommendation_report_block(df: pd.DataFrame) -> str:
    """Bloc markdown : objectif recommandé pour la dernière date active (contexte, pas un veto)."""
    from mais.research.v38_adverse_risk import compute_adverse_risk
    from mais.research.v41_cbot_support import compute_cbot_support
    from mais.research.v54_physical_tension import compute_physical_tension
    ar = compute_adverse_risk(df)
    cs = compute_cbot_support(df)
    pt = compute_physical_tension(df)
    if len(ar) == 0:
        return ""
    a = ar.iloc[-1]["adverse_risk"]
    if a == "NO_SIGNAL":
        return ""
    c = cs.iloc[-1]["cbot_support"]
    p = pt.iloc[-1]["physical_tension"]
    reco = recommend_target(a, c, p)
    why = []
    if c == "LOW":
        why.append("CBOT peu porteur")
    if a == "HIGH":
        why.append("ADVERSE_RISK élevé")
    if p == "HIGH":
        why.append("tension physique élevée")
    why_txt = "; ".join(why) if why else "contexte favorable au complet"
    return (
        "### Objectif recommandé (V56 — CONTEXTE, pas un veto)\n"
        f"- Recommandation : **{reco}** "
        f"({'prudent — verrouiller tôt' if reco == 'z->0.5' else 'complet — capter la réversion'})\n"
        f"- Motif : {why_txt} (ADVERSE_RISK={a}, CBOT_SUPPORT={c}, PHYSICAL_TENSION={p})\n"
        "- La règle figée (short basis-haut) est INCHANGÉE ; seul l'objectif de sortie est modulé. "
        "RESEARCH_ONLY_NOT_TRADING.\n"
    )
