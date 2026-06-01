#!/usr/bin/env python
"""V42-03 — Collecte officielle quotidienne (serveur / GitHub Actions).

Calendar-aware : un jour NO_SESSION (week-end / férié Euronext) n'est PAS une panne, on sort proprement.
Un jour de marché : collecte EMA officiel + CBOT + FX, append au journal forward, met à jour la table de
sessions et la comparaison proxy/officiel, écrit un rapport.

Usage :
    python scripts/run_daily_collect.py            # collecte du jour
    python scripts/run_daily_collect.py --retry    # passage matinal de rattrapage (settlement tardif)

Statut : RESEARCH_ONLY_NOT_TRADING. Ne modifie jamais la baseline ni le passé du journal.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

REPORTS_DIR = ROOT / "reports" / "daily"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--retry", action="store_true", help="passage de rattrapage (settlement tardif)")
    parser.add_argument("--as-of", default=None, help="date forcée YYYY-MM-DD (tests)")
    args = parser.parse_args()

    import pandas as pd

    from mais.calendar import classify_session, is_trading_day

    as_of = pd.Timestamp(args.as_of).normalize() if args.as_of else pd.Timestamp.today().normalize()
    session = classify_session(as_of)
    status: dict[str, object] = {
        "ran_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "as_of": str(as_of.date()),
        "mode": "retry" if args.retry else "main",
        "session_today": session,
    }

    if not is_trading_day(as_of):
        status["result"] = "SKIPPED_NO_SESSION"
        status["reason"] = session
        _write(status, as_of)
        print(json.dumps(status, indent=2))
        return 0

    # 1) Snapshot officiel Euronext (append-only)
    try:
        from mais.collect.euronext_official_live import save_official_snapshot
        status["official_snapshot"] = save_official_snapshot()
    except Exception as e:  # noqa: BLE001
        status["official_snapshot"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 2) Signal forward officiel (append-only journal V27)
    try:
        from mais.research.v27_official_forward import run_v27_forward
        status["forward_journal"] = run_v27_forward()
    except Exception as e:  # noqa: BLE001
        status["forward_journal"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 3) Automatisation : sessions + couverture + proxy/officiel
    try:
        from mais.ops.official_automation import run_v42_automation
        master = None
        try:
            from mais.scripts.run_v8_phase_a import filter_out_holdout, load_master_dataset
            master = filter_out_holdout(load_master_dataset())
        except Exception:  # noqa: BLE001
            master = None
        status["automation"] = run_v42_automation(master_df=master, as_of=as_of)
    except Exception as e:  # noqa: BLE001
        status["automation"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 4) Prévisions météo forward (US+EU), append-only daté à l'émission (anti-leakage)
    try:
        from mais.research.v45_weather_crop_stress import collect_weather_forecast_forward
        status["weather_forecast"] = collect_weather_forecast_forward(try_network=True)
    except Exception as e:  # noqa: BLE001
        status["weather_forecast"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # settlement absent + passage principal -> demander un retry matinal
    snap = status.get("official_snapshot", {})
    settlement_ok = isinstance(snap, dict) and snap.get("status") == "OK"
    status["result"] = "OK" if settlement_ok else ("NEEDS_RETRY" if not args.retry else "INCOMPLETE")
    _write(status, as_of)
    print(json.dumps(status, indent=2, default=str))
    # code retour non bloquant : on ne casse pas la chaîne sur une source secondaire
    return 0


def _write(status: dict, as_of) -> None:
    (REPORTS_DIR / f"{as_of.date()}.json").write_text(json.dumps(status, indent=2, default=str), encoding="utf-8")
    (REPORTS_DIR / "latest.json").write_text(json.dumps(status, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
