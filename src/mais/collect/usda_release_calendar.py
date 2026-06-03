"""VN-C5 — Calendrier de publication USDA (dates de rapports) pour l'attribution exacte des événements.

Objectif : fournir les dates EXACTES des rapports (WASDE, Grain Stocks, Acreage, Crop Production) plutôt que
l'approximation « 8-12 du mois » de `usda_calendar_collector`. Best-effort : si une source live est
parseable, on renvoie les dates exactes (`is_exact=True`) ; sinon on retombe sur l'approximation existante en
le FLAGGANT honnêtement (`is_exact=False`). On ne hardcode pas de fausses dates précises.

RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

from typing import Any

import pandas as pd


def _approx_dates(year: int) -> list[pd.Timestamp]:
    """Approximation : WASDE ~ vers le 10 de chaque mois (réutilise la logique existante)."""
    from mais.collect.usda_calendar_collector import _wasde_dates
    return _wasde_dates(pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year}-12-31"))


def _try_fetch_exact(year: int, timeout: int = 20) -> list[pd.Timestamp] | None:
    """Tente une récupération live des dates exactes USDA ; None si indisponible/non parseable."""
    import json
    import urllib.request
    # endpoint best-effort (peut changer / être indisponible) — on échoue proprement
    url = f"https://www.usda.gov/oce/commodity/wasde/release-dates-{year}.json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "mais-research/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
            data = json.loads(r.read().decode("utf-8"))
        dates = [pd.Timestamp(d) for d in data.get("wasde", [])]
        return dates or None
    except Exception:  # noqa: BLE001
        return None


def wasde_release_dates(year: int, try_network: bool = True) -> dict[str, Any]:
    exact = _try_fetch_exact(year) if try_network else None
    if exact:
        return {"year": year, "dates": [str(d.date()) for d in exact], "is_exact": True,
                "source": "usda_live", "n": len(exact)}
    approx = _approx_dates(year)
    return {"year": year, "dates": [str(d.date()) for d in approx], "is_exact": False,
            "source": "approximation_~10th", "n": len(approx),
            "note": "Dates approchées (~10 du mois). À vérifier sur usda.gov/oce/commodity/wasde. "
                    "L'attribution V137 reste valable mais avec une tolérance plus large."}
