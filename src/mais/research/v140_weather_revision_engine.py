"""V140 — Weather forecast revision engine : mapper la météo prévue/révisée vers les deux canaux.

V127 collecte les extrêmes prévus + révisions ; C4 en fait une tape. V140 CONSOLIDE en un moteur orienté
DÉCISION : il mappe les warnings météo dans les deux canaux de l'indicateur —
  - US (corn belt)  -> CBOT_SUPPORT  (stress/chaleur US prévu = soutien haussier CBOT, donc compression de la
                                      prime plus probable par rattrapage CBOT)
  - Europe          -> PHYSICAL_TENSION / ADVERSE_RISK (stress EU prévu = tension locale = prime plus justifiée)

Rappel V45 : le RÉALISÉ ne prédit pas le CBOT ; c'est la PRÉVISION et surtout sa RÉVISION qui sont leading.
Si aucune donnée forecast n'est disponible, on renvoie NO_WEATHER_DATA (honnête), pas un UNKNOWN figé.
Lecture des artefacts V127 + tape C4. Contexte, jamais un veto. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

from mais.paths import ARTEFACTS_DIR

V_DIR = ARTEFACTS_DIR / "weather_revision_engine"
V_DIR.mkdir(parents=True, exist_ok=True)


def _read(rel) -> dict[str, Any]:
    try:
        return json.loads((ARTEFACTS_DIR / rel).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _channel(region: str) -> dict[str, Any]:
    a = _read(f"v127/v127_weather_{region}.json")
    if a.get("verdict") != "WEATHER_WARNING_READY":
        return {"available": False}
    tier = a.get("stress_tier")
    rev = a.get("revision_vs_prev") or {}
    d_score = rev.get("d_score")
    return {"available": True, "issue_date": a.get("issue_date"), "stress_tier": tier,
            "heat_days_gt32": a.get("heat_days_gt32"), "heat_days_gt35": a.get("heat_days_gt35"),
            "dry_deficit": a.get("dry_deficit"), "revision_d_score": d_score}


def run_v140_weather_engine() -> dict[str, Any]:
    us = _channel("us")
    eu = _channel("eu")
    if not us.get("available") and not eu.get("available"):
        return {"version": "V140-WEATHER-ENGINE", "verdict": "NO_WEATHER_DATA",
                "note": "Aucune prévision V127 disponible (lancer le collecteur). Pas d'UNKNOWN figé.",
                "status": "RESEARCH_ONLY_NOT_TRADING"}

    warnings = {}
    # US -> CBOT_SUPPORT
    if us.get("available"):
        lvl = us["stress_tier"]
        rising = (us.get("revision_d_score") or 0) > 0
        warnings["CBOT_SUPPORT_via_US_weather"] = {
            "level": lvl, "revision_worsening": bool(rising),
            "reading": ("stress US prévu élevé/croissant -> soutien CBOT, compression prime plus probable"
                        if lvl == "HIGH" or rising else "pas de stress US prévu marqué")}
    # EU -> PHYSICAL_TENSION / ADVERSE
    if eu.get("available"):
        lvl = eu["stress_tier"]
        rising = (eu.get("revision_d_score") or 0) > 0
        warnings["PHYSICAL_TENSION_via_EU_weather"] = {
            "level": lvl, "revision_worsening": bool(rising),
            "reading": ("stress EU prévu élevé/croissant -> tension locale, prime plus JUSTIFIÉE (objectif "
                        "prudent z->0.5)" if lvl == "HIGH" or rising else "pas de stress EU prévu marqué")}

    out = {
        "version": "V140-WEATHER-ENGINE",
        "verdict": "WEATHER_ENGINE_READY",
        "us": us, "eu": eu,
        "channel_warnings": warnings,
        "interpretation": (
            f"Météo prévue mappée aux canaux : US {us.get('stress_tier')} -> CBOT_SUPPORT, "
            f"EU {eu.get('stress_tier')} -> PHYSICAL_TENSION/ADVERSE. Le signal LEADING est la RÉVISION "
            "(Δscore), pas le niveau réalisé (V45). Contexte, jamais un veto."),
        "note": "Consolide V127 (extrêmes prévus) + C4 (révisions). Si pas de prévision -> NO_WEATHER_DATA.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V_DIR / "v140_weather_engine.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def weather_engine_report_block() -> str:
    artefact = V_DIR / "v140_weather_engine.json"
    if not artefact.exists():
        return ""
    try:
        s = json.loads(artefact.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    if s.get("verdict") != "WEATHER_ENGINE_READY":
        return ""
    w = s.get("channel_warnings", {})
    lines = [f"- {k} : niveau **{v['level']}**" + (" (révision ⬆)" if v.get("revision_worsening") else "")
             for k, v in w.items()]
    return ("### Moteur météo → canaux (V140)\n" + "\n".join(lines)
            + "\n- Leading = la révision, pas le réalisé (V45). Contexte, jamais un veto. RESEARCH_ONLY_NOT_TRADING.\n")
