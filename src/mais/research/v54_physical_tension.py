"""V54 — PHYSICAL_TENSION_SCORE : la prime EMA haute est-elle adossée à une tension physique réelle ?

Hypothèse (issue de V30 sur la courbe officielle) : un basis haut DOUBLÉ d'une courbe EMA en backwardation
(front au-dessus des échéances suivantes) traduit une rareté physique locale -> la prime est plus justifiée,
se comprime plus lentement -> objectif prudent. Un basis haut en contango franc est plus probablement une
anomalie -> compression plus probable. On assemble un score RÈGLE-BASÉ (aucun fit), miroir structurel de
V38/V41, à partir des features de courbe causales (toutes shift(1), cf. euronext_curve).

- backwardation (front > échéance suivante) -> +1 tension
- spread front-second au-dessus de sa médiane expandante (front relativement cher) -> +1

Score 0..2 -> PHYSICAL_TENSION LOW / MEDIUM / HIGH. CONTEXTE, jamais un veto.

LIMITE HONNÊTE : la courbe EMA (proxy/officielle) ne couvre qu'une fenêtre récente (~330 j) qui ne recouvre
pas les 42 trades historiques (2014-2023). Le SCORE est donc utilisable en LIVE/forward, mais sa VALIDATION
par palier sur les trades reste `WAITING_DATA` tant que la courbe officielle ne s'est pas accumulée.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V54_DIR = ARTEFACTS_DIR / "v54"
V54_DIR.mkdir(parents=True, exist_ok=True)

_NOTE = {
    "HIGH": "courbe tendue (backwardation/front cher) -> prime plus justifiée, compression plus lente",
    "MEDIUM": "tension physique partielle",
    "LOW": "courbe détendue (contango) -> prime haute plus probablement anomalie -> compression probable",
}


def compute_physical_tension(df: pd.DataFrame) -> pd.DataFrame:
    """Score PHYSICAL_TENSION règle-basé par date (composants causaux de courbe, aucun fit)."""
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    backw = pd.to_numeric(df.get("ema_backwardation_flag"), errors="coerce")
    spread = pd.to_numeric(df.get("ema_spread_f0_f1"), errors="coerce")

    have_curve = backw.notna() | spread.notna()
    active = (bz >= 1.0) & have_curve

    spread_med = spread.expanding(min_periods=40).median()
    c_backwardation = (backw == 1).astype("Int64")
    c_tight_front = (spread > spread_med).astype("Int64")
    score = c_backwardation.fillna(0) + c_tight_front.fillna(0)

    tier = pd.Series("NO_SIGNAL", index=df.index)
    tier[active & (score == 0)] = "LOW"
    tier[active & (score == 1)] = "MEDIUM"
    tier[active & (score >= 2)] = "HIGH"
    # signal actif mais courbe absente : on le marque explicitement (live dégradé)
    tier[(bz >= 1.0) & ~have_curve] = "NO_CURVE_DATA"

    out = pd.DataFrame({
        "basis_z": bz,
        "ema_backwardation_flag": backw,
        "ema_spread_f0_f1": spread,
        "c_backwardation": c_backwardation,
        "c_tight_front": c_tight_front,
        "physical_tension_score": pd.Series(score, index=df.index).where(active),
        "physical_tension": tier,
    }, index=df.index)
    out["note"] = out["physical_tension"].map(_NOTE).fillna("")
    out["statut"] = "RESEARCH_ONLY_NOT_TRADING"
    return out


def run_v54_tension(df: pd.DataFrame) -> dict[str, Any]:
    """Valide le palier si la courbe recouvre des trades ; sinon WAITING_DATA honnête + couverture live."""
    assert_no_holdout(df)
    pt = compute_physical_tension(df)
    active = pt["physical_tension"].isin(["LOW", "MEDIUM", "HIGH"])
    n_active = int(active.sum())
    n_no_curve = int((pt["physical_tension"] == "NO_CURVE_DATA").sum())

    coverage = {
        "n_signal_days_with_curve": n_active,
        "n_signal_days_without_curve": n_no_curve,
        "tier_distribution": pt.loc[active, "physical_tension"].value_counts().to_dict(),
    }

    # tentative de validation : compression conditionnelle au palier, là où la courbe existe
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    by_tier: dict[str, Any] = {}
    horizon = 40
    fwd = basis.shift(-horizon) - basis
    for tier in ("LOW", "MEDIUM", "HIGH"):
        mask = (pt["physical_tension"] == tier) & fwd.notna()
        if int(mask.sum()) >= 8:
            sub = fwd[mask]
            by_tier[tier] = {
                "n": int(mask.sum()),
                "compression_rate": round(float((sub < 0).mean()), 3),
                "mean_basis_change_40d": round(float(sub.mean()), 2),
            }

    rates = {k: by_tier[k]["compression_rate"] for k in ("LOW", "MEDIUM", "HIGH") if k in by_tier}
    # tension HAUTE -> compression PLUS LENTE (rate plus bas) : on attend LOW>=MEDIUM>=HIGH
    validatable = len(rates) >= 2
    monotone_dec = validatable and list(rates.values()) == sorted(rates.values(), reverse=True)

    if not validatable:
        verdict = "PHYSICAL_TENSION_SCORE_BUILT_VALIDATION_WAITING_DATA"
    elif monotone_dec:
        verdict = "PHYSICAL_TENSION_HIGH_LESS_COMPRESSIBLE"
    else:
        verdict = "PHYSICAL_TENSION_NOT_DISCRIMINANT_SMALL_WINDOW"

    out = {
        "version": "V54-PHYSICAL-TENSION",
        "coverage": coverage,
        "compression_by_tier": by_tier,
        "compression_rate_by_tier": rates,
        "compression_monotone_decreasing_with_tension": monotone_dec,
        "verdict": verdict,
        "components": {
            "c_backwardation": "front EMA > échéance suivante (backwardation_flag)",
            "c_tight_front": "spread front-second au-dessus de sa médiane expandante",
        },
        "usage": ("PHYSICAL_TENSION = CONTEXTE. HIGH -> prime plus justifiée, viser objectif PRUDENT z→0.5, "
                  "compression plus lente. LOW (contango) -> prime haute plus probablement anomalie. "
                  "Jamais un veto. Alimente V56 (objectif recommandé) et la v2 d'ADVERSE_RISK."),
        "note": ("Courbe EMA proxy/officielle limitée à une fenêtre récente : score utilisable en LIVE, "
                 "validation historique sur les 42 trades en attente d'accumulation forward."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V54_DIR / "v54_physical_tension.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def physical_tension_report_block(df: pd.DataFrame) -> str:
    """Bloc markdown CONTEXTE PHYSICAL_TENSION pour la dernière date (jamais un veto)."""
    pt = compute_physical_tension(df)
    if len(pt) == 0:
        return ""
    last = pt.iloc[-1]
    tier = last["physical_tension"]
    if tier == "NO_SIGNAL":
        return ""
    if tier == "NO_CURVE_DATA":
        return ("### Contexte PHYSICAL_TENSION (V54 — CONTEXTE)\n"
                "- Signal actif mais **courbe EMA indisponible** à cette date : tension non évaluable.\n")
    facts = []
    facts.append("backwardation" if last["c_backwardation"] == 1 else "pas de backwardation")
    facts.append("front cher vs médiane" if last["c_tight_front"] == 1 else "front non tendu")
    return (
        "### Contexte PHYSICAL_TENSION (V54 — CONTEXTE, pas un veto)\n"
        f"- Niveau : **{tier}** (score {int(last['physical_tension_score'])}/2)\n"
        f"- Facteurs courbe : {'; '.join(facts)}\n"
        f"- Lecture : {last['note']}\n"
        "- HIGH = prime adossée à une tension physique → compression plus lente, objectif prudent. "
        "RESEARCH_ONLY_NOT_TRADING.\n"
    )
