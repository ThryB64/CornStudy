"""V134 — Plan de sourcing des données manquantes.

Documente, pour chaque source utile mais non (entièrement) disponible : disponibilité, coût probable,
contraintes, accès API, statut. Sert de feuille de route quand une brique est DATA_BLOCKED (V126 historique,
V128 intraday, COMEXT, MARS...). Aucun réseau : connaissance structurée, à tenir à jour.

Statut : RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

from mais.paths import ARTEFACTS_DIR

V134_DIR = ARTEFACTS_DIR / "v134"
V134_DIR.mkdir(parents=True, exist_ok=True)

SOURCES: list[dict[str, Any]] = [
    {"source": "Euronext Web Services / Datashop", "use": "historique officiel EMA/EBM (settlement+OI) profond",
     "availability": "commercial", "cost": "abonnement (licence données de marché)", "api": "REST sous licence",
     "constraints": "redistribution restreinte ; clé API payante",
     "status": "WATCHLIST", "unblocks": ["V126 historique", "z rolling officiel V27", "PHYSICAL_TENSION backtest"]},
    {"source": "Bloomberg / LSEG (Refinitiv) / Barchart / CQG / TT", "use": "intraday CBOT + EMA aligné, courbe profonde",
     "availability": "commercial", "cost": "élevé (terminal/flux pro)", "api": "propriétaire",
     "constraints": "coût, licence ; overkill pour un projet research",
     "status": "DATA_BLOCKED_PAID", "unblocks": ["V128 intraday aligné", "courbe historique"]},
    {"source": "Open-Meteo Historical Forecast API", "use": "archive de prévisions 'telle que connue J' (révisions)",
     "availability": "gratuit", "cost": "0 (rate-limited)", "api": "REST public",
     "constraints": "timeouts fréquents sur longues fenêtres ; itérer par run/lead",
     "status": "PARTIAL_BEST_EFFORT", "unblocks": ["V127 révisions multi-lead"]},
    {"source": "NOAA GFS / GEFS (ensemble)", "use": "prévision d'ensemble (incertitude, extrêmes)",
     "availability": "gratuit", "cost": "0", "api": "NOMADS/grib (lourd)",
     "constraints": "volumineux (grib2), parsing lourd ; Open-Meteo suffit pour le warning",
     "status": "WATCHLIST", "unblocks": ["V127 incertitude d'ensemble fine"]},
    {"source": "EC MARS (JRC) bulletins rendements EU", "use": "anticipations de rendement maïs EU",
     "availability": "public (bulletins)", "cost": "0", "api": "pas d'API propre (PDF/portail)",
     "constraints": "format bulletin non structuré ; cadence mensuelle",
     "status": "PARTIAL_BEST_EFFORT", "unblocks": ["balance EU (V71)", "EU_BALANCE_UPDATE (V129)"]},
    {"source": "FranceAgriMer", "use": "bilans/stocks maïs France (driver le plus local, V71b)",
     "availability": "public", "cost": "0", "api": "datasets/portail (semi-structuré)",
     "constraints": "publication décalée ; granularité variable",
     "status": "PARTIAL_BEST_EFFORT", "unblocks": ["driver local FR (V71b)"]},
    {"source": "Eurostat COMEXT (DS-045409)", "use": "flux physiques import/export maïs EU",
     "availability": "public mais hors API de dissémination", "cost": "0", "api": "non exposé sur l'API standard",
     "constraints": "dataset non servi par l'API de dissémination ; bulk download manuel",
     "status": "DATA_BLOCKED", "unblocks": ["flux physiques EU (prime locale)"]},
    {"source": "USDA NASS QuickStats / WASDE calendar", "use": "dates exactes des rapports (catalyseurs V129)",
     "availability": "gratuit", "cost": "0", "api": "QuickStats REST (clé gratuite)",
     "constraints": "clé API ; calendrier WASDE à scraper séparément",
     "status": "WATCHLIST", "unblocks": ["attribution CBOT_WASDE exacte (V129)"]},
    {"source": "CFTC f_disagg (COT désagrégé)", "use": "managed-money net %OI (CBOT_SUPPORT)",
     "availability": "gratuit", "cost": "0", "api": "fichier texte public",
     "constraints": "hebdomadaire (Tuesday-of-record publié vendredi)",
     "status": "OK", "unblocks": ["déjà branché V107"]},
    {"source": "DX=F (dollar index futures)", "use": "contexte dollar",
     "availability": "Yahoo 404", "cost": "0", "api": "indispo",
     "constraints": "endpoint cassé ; substitut EUR/USD utilisé",
     "status": "DATA_BLOCKED_SUBSTITUTED", "unblocks": ["substitut EUR/USD suffit"]},
]


def run_v134_sourcing_plan() -> dict[str, Any]:
    by_status: dict[str, int] = {}
    for s in SOURCES:
        by_status[s["status"]] = by_status.get(s["status"], 0) + 1
    actionable = [s["source"] for s in SOURCES if s["status"] in ("WATCHLIST", "PARTIAL_BEST_EFFORT")]
    blocked = [s["source"] for s in SOURCES if s["status"].startswith("DATA_BLOCKED")]
    out = {
        "version": "V134-DATA-SOURCING-PLAN",
        "verdict": "DATA_SOURCE_PLAN_READY",
        "n_sources": len(SOURCES),
        "status_counts": by_status,
        "actionable_next": actionable,
        "blocked": blocked,
        "sources": SOURCES,
        "interpretation": (
            f"{len(SOURCES)} sources cartographiées. Actionnables (gratuit/best-effort) : {actionable}. "
            f"Bloquées (payant/hors API) : {blocked}. Priorité research gratuite : Open-Meteo historical "
            "(révisions V127), USDA QuickStats + calendrier WASDE (attribution V129), MARS/FranceAgriMer "
            "(balance EU). L'historique officiel profond (Euronext/Bloomberg) reste le seul vrai déblocage "
            "payant ; le forward l'accumule gratuitement avec le temps."),
        "note": "Connaissance structurée, sans réseau. À tenir à jour quand une source change de statut.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V134_DIR / "v134_sourcing_plan.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def sourcing_plan_report_block() -> str:
    s = run_v134_sourcing_plan()
    return (
        "### Plan de sourcing des données (V134)\n"
        f"- {s['n_sources']} sources · statuts {s['status_counts']}\n"
        f"- Actionnables : {', '.join(s['actionable_next'])}\n"
        f"- Bloquées : {', '.join(s['blocked'])}\n"
        "- DATA_SOURCE_PLAN_READY. RESEARCH_ONLY_NOT_TRADING.\n"
    )
