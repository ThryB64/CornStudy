#!/usr/bin/env python
"""VN-E1 — Capture du soir les jours d'événements (WASDE/Grain Stocks/Acreage/appels d'offres/chocs météo).

À lancer par cron aux créneaux CET 17:55 / 18:05 / 18:20 / 18:35 / 19:00 / 20:15 les JOURS d'événements
seulement. Append-only, timing estampillé (PROVISIONAL avant 18:30, FINAL après 18:35).

Exemple cron (heure serveur = UTC ; ajuster pour CET/CEST) :
    55 15 * * 1-5  python scripts/run_evening_event_capture.py --slot 17:55 --event WASDE   # si jour WASDE
    5  16 * * 1-5  python scripts/run_evening_event_capture.py --slot 18:05 --event WASDE
    ... etc.

Usage manuel :
    python scripts/run_evening_event_capture.py --slot 19:00 --event WASDE
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--slot", required=True, help="créneau CET, ex: 19:00")
    p.add_argument("--event", default="GENERIC", help="label d'événement, ex: WASDE")
    args = p.parse_args()
    from mais.collect.euronext_evening_snapshots import capture_evening_snapshot
    out = capture_evening_snapshot(args.slot, event_label=args.event, try_network=True)
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
