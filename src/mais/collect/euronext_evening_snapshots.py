"""VN-E1 — Capture intraday du SOIR les jours d'événements (sans intraday payant).

Depuis le 2026-04-13, EMA (Corn) Euronext trade jusqu'à 20:15 CET (DSP toujours 18:30 CET), pour réagir aux
WASDE/Crop Production et appels d'offres pendant que le CME est encore ouvert. On exploite ça en répétant des
SNAPSHOTS PUBLICS aux créneaux 17:55 / 18:05 / 18:20 / 18:35 / 19:00 / 20:15 CET les jours d'événements, et en
journalisant front/next spread, OI, et CBOT — append-only, timing estampillé (PROVISIONAL avant 18:30,
FINAL après 18:35). C'est la donnée qui manque pour comprendre les DÉBUTS de compression.

Réseau requis (SKIP propre hors ligne). Append-only, jamais réécrit. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from mais.paths import DATA_DIR

EVENING_JOURNAL = DATA_DIR / "premium" / "evening_event_snapshots.jsonl"
SLOTS_CET = ["17:55", "18:05", "18:20", "18:35", "19:00", "20:15"]


def capture_evening_snapshot(slot: str, event_label: str = "GENERIC", try_network: bool = True,
                             fetch_curve=None, fetch_cbot=None,
                             collected_at_utc: datetime | None = None) -> dict[str, Any]:
    """Un snapshot daté d'un créneau du soir : structure de courbe EMA + CBOT, timing estampillé."""
    if not try_network:
        return {"version": "EVENING-SNAPSHOT", "verdict": "OFFLINE_SKIP", "slot": slot}
    if fetch_curve is None:
        from mais.collect.euronext_official_live import fetch_official_ema
        fetch_curve = fetch_official_ema
    try:
        curve = fetch_curve()
    except Exception as exc:  # noqa: BLE001
        return {"version": "EVENING-SNAPSHOT", "verdict": "NO_CURVE", "slot": slot,
                "reason": f"{type(exc).__name__}: {str(exc)[:60]}"}
    from mais.research.v109_ema_curve_live_tension import curve_structure
    st = curve_structure(curve)
    if st is None:
        return {"version": "EVENING-SNAPSHOT", "verdict": "CURVE_INSUFFICIENT", "slot": slot}

    cbot_last = None
    if fetch_cbot is None:
        try:
            from mais.research.v107_live_context_refresh import _yahoo_daily
            cbot_last = float(_yahoo_daily("ZC=F", rng="5d").dropna().iloc[-1])
        except Exception:  # noqa: BLE001
            cbot_last = None
    else:
        cbot_last = fetch_cbot()

    from mais.premium.session_timing import stamp_timing
    price_date = str(curve["price_date"].iloc[0].date()) if "price_date" in curve else None
    rec = stamp_timing({"price_date": price_date, "slot_cet": slot, "event_label": event_label,
                        "front_contract": st["front_contract"], "front_settle": st["front_settle"],
                        "next_contract": st["next_contract"], "next_settle": st["next_settle"],
                        "front_next_spread": st["front_next_spread"], "curve_shape": st["curve_shape"],
                        "front_oi": st["front_oi"], "cbot_last": cbot_last},
                       collected_at_utc=collected_at_utc)
    EVENING_JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    with EVENING_JOURNAL.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, default=str) + "\n")
    return {"version": "EVENING-SNAPSHOT", "verdict": "SNAPSHOT_LOGGED", "slot": slot,
            "record_status": rec["record_status"], "front_next_spread": st["front_next_spread"],
            "curve_shape": st["curve_shape"], "logged_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}


def load_evening_journal() -> list[dict[str, Any]]:
    if not EVENING_JOURNAL.exists():
        return []
    out = []
    for ln in EVENING_JOURNAL.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
    return out
