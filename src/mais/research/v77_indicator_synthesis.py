"""V77 — Synthèse de l'indicateur research : un objet unique assemblant toute la pile de diagnostics.

Consolide, pour une date donnée (par défaut la dernière), le signal figé et tous les diagnostics construits :
tier (V17), ADVERSE_RISK (V38 tier + V64 explication), CBOT_SUPPORT (V41), PHYSICAL_TENSION (V54), objectif
recommandé (V56), horizon probable de compression (V72), une confiance dérivée et une raison d'abstention
éventuelle. AUCUN nouveau modèle, AUCUN veto : c'est une vue d'ensemble lisible, research-only.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR

V77_DIR = ARTEFACTS_DIR / "v77"
V77_DIR.mkdir(parents=True, exist_ok=True)


def _confidence(tier: str, adverse: str, support: str) -> str:
    """Confiance research dérivée (pas une proba) : signal fort + risque bas + CBOT porté = haute."""
    if tier == "NO_SIGNAL":
        return "none"
    score = 0
    score += {"SHORT_PREMIUM_EXTREME": 2, "SHORT_PREMIUM_STRONG": 1}.get(tier, 0)
    score += {"LOW": 1, "MEDIUM": 0, "HIGH": -1}.get(adverse, 0)
    score += {"HIGH": 1, "MEDIUM": 0, "LOW": -1}.get(support, 0)
    return "high" if score >= 2 else ("medium" if score >= 0 else "low")


def _horizon_for_support(df: pd.DataFrame, support: str) -> dict[str, Any]:
    try:
        from mais.research.v72_survival_reversion import run_v72_survival
        v72 = run_v72_survival(df)
        block = v72.get("by_cbot_support", {}).get(support) or v72.get("overall", {})
        return {"median_days_to_z05": block.get("median_days_to_z05"),
                "median_days_to_z0": block.get("median_days_to_z0")}
    except Exception:  # noqa: BLE001
        return {"median_days_to_z05": None, "median_days_to_z0": None}


def synthesize_indicator(df: pd.DataFrame, as_of: str | None = None) -> dict[str, Any]:
    from mais.research.v17_research_indicator import compute_indicator_v17
    from mais.research.v38_adverse_risk import compute_adverse_risk
    from mais.research.v41_cbot_support import compute_cbot_support
    from mais.research.v54_physical_tension import compute_physical_tension
    from mais.research.v56_target_recommendation import recommend_target
    from mais.research.v64_adverse_risk_v2 import compute_adverse_risk_v2, explain_row

    ind = compute_indicator_v17(df)
    if len(ind) == 0:
        return {"version": "V77-INDICATOR-SYNTHESIS", "verdict": "NO_DATA"}
    if ind.index.name != "date" and "date" in ind.columns:
        ind = ind.set_index("date")
    row_date = pd.Timestamp(as_of) if as_of else ind.index[-1]
    if row_date not in ind.index:
        row_date = ind.index[-1]
    sig = ind.loc[row_date]
    tier = str(sig["signal"])

    ar = compute_adverse_risk(df)
    cs = compute_cbot_support(df)
    pt = compute_physical_tension(df)
    arv2 = compute_adverse_risk_v2(df)

    def _at(frame, col):
        return frame[col].get(row_date) if col in frame else None
    adverse = _at(ar, "adverse_risk") or "NO_SIGNAL"
    support = _at(cs, "cbot_support") or "NO_SIGNAL"
    tension = _at(pt, "physical_tension") or "NO_SIGNAL"

    active = tier not in ("NO_SIGNAL",) and not str(tier).startswith("UNCERTAIN")
    target = recommend_target(adverse, support, tension) if active else None
    confidence = _confidence(tier, adverse, support)
    horizon = _horizon_for_support(df, support) if active else {}

    reasons = []
    if row_date in arv2.index:
        reasons = explain_row(arv2.loc[row_date])

    # raison d'abstention (CONTEXTE, pas un veto) : faisceau défavorable
    abstain = None
    if not active:
        abstain = "pas de signal actif (basis_z < 1) ou signal rétrogradé UNCERTAIN (data/roll/vol)"
    elif adverse == "HIGH" and support == "LOW":
        abstain = ("faisceau défavorable (ADVERSE_RISK HIGH + CBOT non porteur) : objectif prudent z→0.5 "
                   "seulement, ne pas renforcer — RESEARCH, pas un veto")

    out = {
        "version": "V77-INDICATOR-SYNTHESIS",
        "as_of": str(row_date.date()),
        "signal_tier": tier,
        "basis_z": round(float(sig["basis_z"]), 3) if pd.notna(sig.get("basis_z")) else None,
        "basis_eur_t": round(float(sig["basis"]), 2) if pd.notna(sig.get("basis")) else None,
        "adverse_risk": adverse,
        "cbot_support": support,
        "physical_tension": tension,
        "recommended_target": target,
        "objective_prudent": "z->0.5",
        "objective_full": "z->0",
        "horizon_estimate_days": horizon,
        "confidence": confidence,
        "explanation": reasons,
        "reason_to_abstain": abstain,
        "stop_eur_t": -20.0,
        "verdict": "SYNTHESIS_BUILT",
        "disclaimer": ("Vue d'ensemble research. Diagnostics = CONTEXTE, jamais des vetos. La règle figée "
                       "(short basis-haut) est inchangée. RESEARCH_ONLY_NOT_TRADING."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V77_DIR / "v77_synthesis_latest.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def synthesis_report_block(df: pd.DataFrame) -> str:
    s = synthesize_indicator(df)
    if s.get("verdict") != "SYNTHESIS_BUILT":
        return ""
    h = s.get("horizon_estimate_days", {})
    htxt = (f"~{h.get('median_days_to_z05')} j → z0.5, ~{h.get('median_days_to_z0')} j → z0"
            if h.get("median_days_to_z05") is not None else "n/a")
    lines = [
        "### Synthèse indicateur (V77 — vue d'ensemble research)",
        f"- Date : {s['as_of']} · Signal : **{s['signal_tier']}** (basis_z={s['basis_z']}, "
        f"basis={s['basis_eur_t']} €/t)",
        f"- ADVERSE_RISK : {s['adverse_risk']} · CBOT_SUPPORT : {s['cbot_support']} · "
        f"PHYSICAL_TENSION : {s['physical_tension']}",
        f"- Objectif recommandé : **{s['recommended_target']}** · horizon probable : {htxt} · "
        f"confiance : {s['confidence']}",
    ]
    if s.get("explanation"):
        lines.append(f"- Facteurs de risque : {'; '.join(s['explanation'])}")
    if s.get("reason_to_abstain"):
        lines.append(f"- Abstention suggérée : {s['reason_to_abstain']}")
    lines.append("- Diagnostics = CONTEXTE, jamais un veto ; règle figée inchangée. RESEARCH_ONLY_NOT_TRADING.")
    return "\n".join(lines)
