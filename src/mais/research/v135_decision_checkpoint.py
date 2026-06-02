"""V135 — Checkpoint décisionnel après V122-V134.

Agrège les verdicts des modules et range chaque brique en : AMÉLIORE (entre dans l'indicateur), EXPLICATIF
(garde en doc, pas de valeur décisionnelle live), BLOQUÉ (données), FORWARD (à laisser mûrir). Donne aussi
l'avis sur un éventuel paper-trading research (et pourquoi on reste analytique). Lecture seule des artefacts.

Statut : RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

from mais.paths import ARTEFACTS_DIR

V135_DIR = ARTEFACTS_DIR / "v135"
V135_DIR.mkdir(parents=True, exist_ok=True)

# (module, artefact relatif, clé verdict, catégorie a priori)
MODULES = [
    ("V122 consistency", "v122/v122_consistency.json", "verdict", "IMPROVES"),
    ("V123 freshness", "v123/v123_freshness.json", "verdict", "IMPROVES"),
    ("V124 monitoring v2", "v124/v124_active_monitoring.json", "verdict", "IMPROVES"),
    ("V125 curve accumulation", "v125/v125_curve_accumulation.json", "verdict", "IMPROVES"),
    ("V126 MATIF substitution", "v126/v126_substitution.json", "verdict", "IMPROVES"),
    ("V127 weather US", "v127/v127_weather_us.json", "verdict", "FORWARD"),
    ("V128 intraday probe", "v128/v128_intraday_probe.json", "verdict", "BLOCKED"),
    ("V129 event library", "v129/v129_event_library.json", "verdict", "EXPLANATORY"),
    ("V130 regime econometrics", "v130/v130_regime_econometrics.json", "verdict", "IMPROVES"),
    ("V131 target reco v3", "v131/v131_target_v3.json", "verdict", "IMPROVES"),
    ("V132 indicator v3", "v132/indicator_v3_latest.json", "verdict", "IMPROVES"),
    ("V133 monthly report v2", "v133/v133_monthly_v2.json", "verdict", "IMPROVES"),
    ("V134 sourcing plan", "v134/v134_sourcing_plan.json", "verdict", "EXPLANATORY"),
]

GO_VERDICTS = {"LIVE_SIGNAL_CONSISTENT", "CONTEXT_COHERENT", "ACTIVE_MONITORING_READY",
               "CURVE_HISTORY_BUILT", "SUBSTITUTION_SIGNAL_READY", "ADD_TO_HORIZON_ESTIMATE",
               "ADD_TO_INDICATOR", "INDICATOR_V3_BUILT", "MONTHLY_REPORT_V2_BUILT",
               "EVENT_LIBRARY_READY", "DATA_SOURCE_PLAN_READY", "WEATHER_WARNING_READY"}
WATCH_VERDICTS = {"WATCHLIST", "PROXY_OK_FORWARD_ACCUMULATING", "CONTEXT_DEGRADED"}
BLOCK_VERDICTS = {"DATA_BLOCKED", "NO_FORECAST_DATA", "OFFLINE_SKIP", "NO_CURVE_HISTORY"}


def _read(rel) -> dict[str, Any]:
    try:
        return json.loads((ARTEFACTS_DIR / rel).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gate(verdict: str | None) -> str:
    if verdict in GO_VERDICTS:
        return "GO"
    if verdict in WATCH_VERDICTS:
        return "WATCHLIST"
    if verdict in BLOCK_VERDICTS:
        return "NO_GO"
    return "UNKNOWN"


def run_v135_checkpoint() -> dict[str, Any]:
    rows = []
    for name, rel, key, category in MODULES:
        art = _read(rel)
        verdict = art.get(key)
        rows.append({"module": name, "verdict": verdict, "gate": _gate(verdict),
                     "category": category, "present": bool(art)})

    improves = [r["module"] for r in rows if r["category"] == "IMPROVES" and r["gate"] == "GO"]
    explanatory = [r["module"] for r in rows if r["category"] == "EXPLANATORY"]
    blocked = [r["module"] for r in rows if r["gate"] == "NO_GO" or r["category"] == "BLOCKED"]
    forward = [r["module"] for r in rows if r["category"] == "FORWARD"]

    out = {
        "version": "V135-DECISION-CHECKPOINT",
        "verdict": "CHECKPOINT_READY",
        "modules": rows,
        "improves_indicator": improves,
        "explanatory_only": explanatory,
        "data_blocked": blocked,
        "continue_forward": forward,
        "paper_trading_recommended": False,
        "decision": (
            "L'indicateur reste ANALYTIQUE (research-only). Les briques décisionnelles (cohérence V122, "
            "fraîcheur V123, monitoring V124, horizon par tier V130, reco v3 V131, synthèse V132) AMÉLIORENT "
            "la décision (objectif/horizon/santé) sans toucher la baseline. Les briques explicatives (V129 "
            "catalyseurs, V134 sourcing) éclairent le POURQUOI. Le paper-trading research n'est PAS justifié "
            "tant que le forward officiel n'a pas ≥6 mois et que le z reste proxy_implied : on accumule "
            "d'abord. Aucune bascule vers du trading réel."),
        "next_roadmap": [
            "Accumuler le forward officiel jusqu'aux milestones 10/40/90 j (V124) puis ≥6 mois (V133).",
            "Brancher Open-Meteo historical (révisions V127) et USDA calendar (attribution V129) — gratuit.",
            "Re-décider PHYSICAL_TENSION/substitution quand l'historique officiel s'accumule (V125/V126).",
        ],
        "note": "Lecture seule des artefacts. CONTEXTE, jamais un veto. Baseline figée, holdout verrouillé.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V135_DIR / "v135_checkpoint.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def checkpoint_report_block() -> str:
    s = run_v135_checkpoint()
    return (
        "### Checkpoint décisionnel (V135)\n"
        f"- Améliorent l'indicateur : {', '.join(s['improves_indicator']) or 'aucun'}\n"
        f"- Explicatifs : {', '.join(s['explanatory_only'])}\n"
        f"- Bloqués (données) : {', '.join(s['data_blocked'])}\n"
        f"- À mûrir en forward : {', '.join(s['continue_forward'])}\n"
        f"- Paper-trading recommandé : **{s['paper_trading_recommended']}** (reste analytique). "
        "RESEARCH_ONLY_NOT_TRADING.\n"
    )
