"""V137 — Attribution par DATES de rapports USDA (raffine V129).

V129 attribuait CBOT_WASDE via un proxy (saut journalier marqué) faute de calendrier. Ici on utilise les
dates de rapports USDA déjà connues du collecteur (`usda_calendar_collector`) : WASDE (~8-12 du mois),
Grain Stocks (trimestriel), Acreage (annuel). Pour chaque épisode de compression (V129), on regarde si sa
fenêtre [pic→chute] contient une date de rapport ET un mouvement CBOT marqué → on affine l'étiquette en
CBOT_WASDE / CBOT_GRAIN_STOCKS / CBOT_ACREAGE. C'est DESCRIPTIF ex-post (jamais une feature).

Le calendrier WASDE est approché (jour exact non scrappé) → on tolère ±2 j. Verdict EVENT_DATES_READY.
assert_no_holdout sur le master. Statut : RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V137_DIR = ARTEFACTS_DIR / "v137"
V137_DIR.mkdir(parents=True, exist_ok=True)
WINDOW_TOLERANCE_DAYS = 2
CBOT_MOVE = 0.02


def report_calendar(start: pd.Timestamp, end: pd.Timestamp) -> dict[str, list[pd.Timestamp]]:
    from mais.collect.usda_calendar_collector import (
        _annual_acreage,
        _quarterly_grain_stocks,
        _wasde_dates,
    )
    return {"WASDE": _wasde_dates(start, end),
            "GRAIN_STOCKS": _quarterly_grain_stocks(start, end),
            "ACREAGE": _annual_acreage(start, end)}


def _contains_report(window_dates: pd.DatetimeIndex, events: list[pd.Timestamp]) -> bool:
    if len(window_dates) == 0:
        return False
    lo = window_dates.min() - pd.Timedelta(days=WINDOW_TOLERANCE_DAYS)
    hi = window_dates.max() + pd.Timedelta(days=WINDOW_TOLERANCE_DAYS)
    return any(lo <= e <= hi for e in events)


def run_v137_event_dates(df: pd.DataFrame) -> dict[str, Any]:
    from mais.research.v129_event_catalyst_library import detect_compression_events
    assert_no_holdout(df)
    events = detect_compression_events(df)
    if len(events) == 0:
        return {"version": "V137-EVENT-DATES", "verdict": "NO_EVENTS"}
    cal = report_calendar(df.index.min(), df.index.max())

    rows = []
    for _, e in events.iterrows():
        peak, end = pd.Timestamp(e["peak_date"]), pd.Timestamp(e["end_date"])
        win = df.loc[peak:end]
        cbot = pd.to_numeric(win.get("cbot_close"), errors="coerce").dropna()
        cbot_ret = float(np.log(cbot.iloc[-1] / cbot.iloc[0])) if len(cbot) >= 2 and cbot.iloc[0] > 0 else 0.0
        label = "NO_REPORT"
        for rep in ("WASDE", "GRAIN_STOCKS", "ACREAGE"):
            if _contains_report(win.index, cal[rep]):
                label = f"CBOT_{rep}" if cbot_ret >= CBOT_MOVE else f"{rep}_NO_CBOT_MOVE"
                break
        rows.append({"peak_date": str(peak.date()), "end_date": str(end.date()),
                     "cbot_ret": round(cbot_ret, 4), "report_label": label})
    lib = pd.DataFrame(rows)
    counts = lib["report_label"].value_counts().to_dict()
    n_with_report = int((~lib["report_label"].eq("NO_REPORT")).sum())
    n_cbot_report = int(lib["report_label"].str.startswith("CBOT_").sum())

    out = {
        "version": "V137-EVENT-DATES",
        "verdict": "EVENT_DATES_READY",
        "n_events": int(len(lib)),
        "report_label_counts": {str(k): int(v) for k, v in counts.items()},
        "n_episodes_overlap_report": n_with_report,
        "n_cbot_report_driven": n_cbot_report,
        "calendar_counts": {k: len(v) for k, v in cal.items()},
        "interpretation": (
            f"{len(lib)} épisodes ; {n_with_report} chevauchent une date de rapport USDA (±{WINDOW_TOLERANCE_DAYS} j) "
            f"— **chevauchement quasi mécanique** (WASDE mensuel + fenêtres ~19 j), donc PEU discriminant en soi. "
            f"L'information utile : {n_cbot_report} épisodes avec un mouvement CBOT marqué (≥{CBOT_MOVE:.0%}) autour "
            "du rapport → CBOT_WASDE/GRAIN_STOCKS. Affine l'attribution V129 (proxy saut journalier donnait 1 seul "
            "CBOT_WASDE) en distinguant rapport-AVEC-réaction-CBOT vs rapport-SANS. Calendrier approché (±2 j) ; "
            "DESCRIPTIF ex-post, jamais une feature."),
        "note": "Réutilise usda_calendar_collector (dates approchées) + détection d'épisodes V129. "
                "Pour des dates exactes : scraper le calendrier USDA officiel (V134 WATCHLIST).",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    lib.to_parquet(V137_DIR / "event_date_attribution.parquet", index=False)
    (V137_DIR / "v137_event_dates.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def event_dates_report_block() -> str:
    artefact = V137_DIR / "v137_event_dates.json"
    if not artefact.exists():
        return ""
    try:
        s = json.loads(artefact.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    if s.get("verdict") != "EVENT_DATES_READY":
        return ""
    return (
        "### Attribution par dates de rapports USDA (V137)\n"
        f"- {s['n_events']} épisodes · {s['n_episodes_overlap_report']} chevauchent un rapport "
        f"({s['n_cbot_report_driven']} CBOT-driven) · {s['report_label_counts']}\n"
        "- Raffine V129 (proxy → dates). DESCRIPTIF ex-post. RESEARCH_ONLY_NOT_TRADING.\n"
    )
