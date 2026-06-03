"""VN-E2 — Microstructure événementielle EMA : réaction intra-soir autour des événements.

Lit le journal de capture du soir (VN-E1) et mesure, par événement (jour + label), l'évolution du front, du
spread front-next et de la forme de courbe entre les créneaux 17:55 → 20:15 CET, ainsi que le mouvement CBOT.
C'est la donnée qui manque pour comprendre les DÉBUTS de compression autour des WASDE/appels d'offres.

Honnête : WATCHLIST tant que peu d'événements sont accumulés (E1 doit tourner en forward les jours de
rapports). Descriptif ex-post. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR

V_DIR = ARTEFACTS_DIR / "event_microstructure"
V_DIR.mkdir(parents=True, exist_ok=True)
MIN_EVENTS = 3


def run_v_event_microstructure() -> dict[str, Any]:
    from mais.collect.euronext_evening_snapshots import load_evening_journal
    rows = load_evening_journal()
    if len(rows) == 0:
        return {"version": "EVENT-MICROSTRUCTURE", "verdict": "FORWARD_ONLY_ACCUMULATING", "n_snapshots": 0,
                "note": "Aucun snapshot du soir encore. Lancer run_evening_event_capture.py les jours d'événements.",
                "status": "RESEARCH_ONLY_NOT_TRADING"}
    df = pd.DataFrame(rows)
    df["event_day"] = df.get("effective_session_date", df.get("price_date"))
    by_event = []
    for (day, label), g in df.groupby([df["event_day"], df.get("event_label", "GENERIC")]):
        g = g.sort_values("slot_cet")
        if len(g) < 2:
            continue
        fs = pd.to_numeric(g["front_settle"], errors="coerce")
        sp = pd.to_numeric(g["front_next_spread"], errors="coerce")
        cb = pd.to_numeric(g.get("cbot_last"), errors="coerce")
        by_event.append({
            "event_day": str(day), "event_label": label, "n_slots": int(len(g)),
            "front_move": round(float(fs.iloc[-1] - fs.iloc[0]), 2) if fs.notna().sum() >= 2 else None,
            "spread_move": round(float(sp.iloc[-1] - sp.iloc[0]), 2) if sp.notna().sum() >= 2 else None,
            "cbot_move": round(float(cb.iloc[-1] - cb.iloc[0]), 2) if cb.notna().sum() >= 2 else None,
            "shape_first": g["curve_shape"].iloc[0], "shape_last": g["curve_shape"].iloc[-1],
        })
    n_events = len(by_event)
    verdict = "MICROSTRUCTURE_READY" if n_events >= MIN_EVENTS else "WATCHLIST_FEW_EVENTS"
    out = {
        "version": "EVENT-MICROSTRUCTURE",
        "verdict": verdict,
        "n_snapshots": int(len(df)),
        "n_events": n_events,
        "by_event": by_event,
        "interpretation": (
            f"{len(df)} snapshots du soir, {n_events} événement(s) avec ≥2 créneaux. Réaction intra-soir "
            "(front, spread, CBOT) mesurée par événement. "
            + ("Assez d'événements pour commencer à lire la microstructure des débuts de compression."
               if n_events >= MIN_EVENTS else
               "Trop peu d'événements -> WATCHLIST, s'accumule en forward (E1 les jours de rapports).")),
        "note": "Descriptif ex-post. Dépend de l'accumulation E1.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V_DIR / "event_microstructure.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
