"""VN-C2 — Eurostat COMEXT (bulk) : flux physiques import/export maïs UE.

Requalification : COMEXT n'est PAS DATA_BLOCKED — le bulk download CSV mensuel/annuel existe (depuis 1988).
Mais ce n'est pas une petite API : best-effort, fichiers volumineux. On tente la récupération d'une série
maïs (code CN 1005) ; en cas d'échec réseau/format, on renvoie un statut HONNÊTE (DATA_BLOCKED ce run) sans
fabriquer de donnée.

Anti-leakage : données mensuelles avec lag de publication -> shift à appliquer en aval (C3). Détrend YoY
obligatoire en aval (les niveaux dérivent, cf V71). RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

# Code CN maïs (1005 = maize). Endpoint bulk Eurostat (peut évoluer).
COMEXT_CN_MAIZE = "1005"
BULK_HINT = ("https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing"
             "?sort=1&dir=comext (DS-045409, CSV mensuel/annuel)")


def fetch_comext_maize(try_network: bool = True, fetch=None) -> pd.DataFrame | None:
    """Tente une série mensuelle import/export maïs UE. None si indisponible (best-effort)."""
    if not try_network:
        return None
    if fetch is not None:  # injection pour tests
        try:
            return fetch()
        except Exception:  # noqa: BLE001
            return None
    # Le bulk COMEXT requiert un téléchargement de fichier zip volumineux + parsing dédié ; non automatisé
    # ici de façon fiable -> on renvoie None (DATA_BLOCKED ce run) plutôt que de bricoler une fausse série.
    return None


def run_comext_status(try_network: bool = True, fetch=None) -> dict[str, Any]:
    df = fetch_comext_maize(try_network=try_network, fetch=fetch)
    if df is None or len(df) == 0:
        return {"version": "COMEXT-BULK", "verdict": "DATA_BLOCKED_THIS_RUN",
                "requalified_from": "DATA_BLOCKED -> PARTIAL_BEST_EFFORT",
                "path": BULK_HINT,
                "note": "Le bulk existe mais n'a pas été récupéré/parse ce run (fichier volumineux). "
                        "Pas de fausse série. À automatiser (download zip + parse CN 1005).",
                "status": "RESEARCH_ONLY_NOT_TRADING"}
    return {"version": "COMEXT-BULK", "verdict": "COMEXT_SERIES_READY",
            "n_months": int(len(df)), "cn_code": COMEXT_CN_MAIZE,
            "first": str(df.index.min()), "last": str(df.index.max()),
            "note": "Détrend YoY obligatoire en aval (niveaux dérivent, cf V71).",
            "status": "RESEARCH_ONLY_NOT_TRADING"}
