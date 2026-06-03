"""VN-C1 — Probe : l'endpoint Euronext public admet-il un historique court caché ?

On ne PRÉSUME pas que oui. On teste quelques variantes de l'endpoint public (pagination `p=1,2,3`, et la
page `fixings`) et on regarde si les lignes renvoyées contiennent PLUSIEURS dates de session distinctes. Si
oui -> HAS_PUBLIC_RANGE (à exploiter). Si non -> NO_PUBLIC_RANGE : on bascule sur les voies officielles
documentées (Euronext Web Services / NextHistory / CFTS, cf. V134), pas sur le scraping du snapshot live.

Best-effort, offline-safe. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
import re
from typing import Any

from mais.paths import ARTEFACTS_DIR

V_DIR = ARTEFACTS_DIR / "euronext_history_probe"
V_DIR.mkdir(parents=True, exist_ok=True)
PROBE_URLS = [
    "https://live.euronext.com/en/pd_ajax/fixings?d=EMA-DPAR&p=1",
    "https://live.euronext.com/en/pd_ajax/fixings?d=EMA-DPAR&p=2",
    "https://live.euronext.com/en/ajax/getPricesFutures/commodities-futures/EMA/DPAR?period=historical",
]
_DATE_RE = re.compile(r"\b(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})\b")


def _distinct_dates(html: str) -> set[str]:
    return set(_DATE_RE.findall(html or ""))


def probe_history(try_network: bool = True, fetch=None) -> dict[str, Any]:
    if not try_network:
        return {"version": "EURONEXT-HISTORY-PROBE", "verdict": "OFFLINE_SKIP"}
    if fetch is None:
        from mais.collect.euronext_endpoint_probe import fetch_endpoint_html
        fetch = fetch_endpoint_html
    results = []
    max_dates = 0
    for url in PROBE_URLS:
        try:
            html = fetch(url=url) if "url" in fetch.__code__.co_varnames else fetch(url)
            n = len(_distinct_dates(html))
            results.append({"url": url, "ok": True, "n_distinct_dates": n})
            max_dates = max(max_dates, n)
        except Exception as exc:  # noqa: BLE001
            results.append({"url": url, "ok": False, "error": f"{type(exc).__name__}: {str(exc)[:60]}"})
    has_range = max_dates >= 3
    out = {
        "version": "EURONEXT-HISTORY-PROBE",
        "verdict": "HAS_PUBLIC_RANGE" if has_range else "NO_PUBLIC_RANGE",
        "max_distinct_dates_seen": max_dates,
        "probes": results,
        "interpretation": (
            "Plusieurs dates distinctes renvoyées -> un historique court public existe, à exploiter prudemment."
            if has_range else
            "Pas d'historique multi-dates sur l'endpoint public -> NO_PUBLIC_RANGE. L'historique officiel passe "
            "par Euronext Web Services / NextHistory / CFTS (V134), pas le scraping du snapshot live."),
        "official_paths": ["Euronext Web Services (REST/JSON, licence)", "Euronext NextHistory (EOD CSV)",
                           "Euronext CFTS API/SFTP (membres)"],
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V_DIR / "euronext_history_probe.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
