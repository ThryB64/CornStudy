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

    # 5) Ratio MATIF blé/maïs (substitution EU), append-only forward (V52)
    try:
        from mais.research.v52_matif_substitution import append_matif_journal
        status["matif_ratio"] = append_matif_journal()
    except Exception as e:  # noqa: BLE001
        status["matif_ratio"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 6) Refresh du contexte CBOT live 2026 (V107) — persiste l'artefact lu par le rapport
    try:
        from mais.research.v107_live_context_refresh import run_v107_context_refresh
        status["context_refresh"] = run_v107_context_refresh(try_network=True)
    except Exception as e:  # noqa: BLE001
        status["context_refresh"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 7) Reconstruction basis live + ADVERSE_RISK live (V108)
    try:
        from mais.research.v108_live_basis_reconstruction import run_v108_live_basis
        status["live_basis"] = run_v108_live_basis(try_network=True)
    except Exception as e:  # noqa: BLE001
        status["live_basis"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 8) Courbe EMA officielle live -> PHYSICAL_TENSION live (V109)
    try:
        from mais.research.v109_ema_curve_live_tension import run_v109_curve_tension
        status["curve_tension"] = run_v109_curve_tension(try_network=True)
    except Exception as e:  # noqa: BLE001
        status["curve_tension"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 9) Accumulation de la courbe EMA + tendance de tension (V125)
    try:
        from mais.research.v125_curve_accumulation import run_v125_curve_accumulation
        status["curve_accumulation"] = run_v125_curve_accumulation()
    except Exception as e:  # noqa: BLE001
        status["curve_accumulation"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 9b) Historique ratio MATIF blé/maïs (substitution EU) -> parquet structuré (V126)
    try:
        from mais.research.v126_matif_substitution_v2 import run_v126_substitution
        status["substitution_v2"] = run_v126_substitution()
    except Exception as e:  # noqa: BLE001
        status["substitution_v2"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 9c) Météo forecast extrême US + EU (warning de contexte, append-only) (V127)
    try:
        from mais.research.v127_weather_forecast_extremes import run_v127_weather
        status["weather_extremes"] = {r: run_v127_weather(try_network=True, region=r) for r in ("us", "eu")}
    except Exception as e:  # noqa: BLE001
        status["weather_extremes"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 9d) Probe + accumulation du basis aligné intraday (WATCHLIST) (V128)
    try:
        from mais.research.v128_intraday_aligned_probe import run_v128_intraday
        status["intraday_align"] = run_v128_intraday(try_network=True)
    except Exception as e:  # noqa: BLE001
        status["intraday_align"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 10) Révision auditée du jour courant + cohérence des couches (V122)
    try:
        from mais.research.v122_journal_consistency import run_v122
        fj = status.get("forward_journal") or {}
        recomputed = fj.get("signal") if isinstance(fj, dict) else None
        status["consistency"] = run_v122(as_of=as_of, revise_with=recomputed)
    except Exception as e:  # noqa: BLE001
        status["consistency"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 11) Suivi du signal actif v2 (V124) + gate de fraîcheur (V123)
    try:
        from mais.research.v124_active_monitoring_v2 import monitor_active_signal_v2
        status["active_monitoring_v2"] = monitor_active_signal_v2()
    except Exception as e:  # noqa: BLE001
        status["active_monitoring_v2"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}
    try:
        from mais.research.v123_freshness_gate import run_v123_freshness
        status["freshness"] = run_v123_freshness()
    except Exception as e:  # noqa: BLE001
        status["freshness"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 12) Synthèse de l'indicateur research v3 (vue intégrée) (V132)
    try:
        from mais.research.v132_indicator_synthesis_v3 import run_v132_synthesis
        status["indicator_v3"] = run_v132_synthesis()
    except Exception as e:  # noqa: BLE001
        status["indicator_v3"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 12b) Forecast revision tape (VN-C4, lit le journal météo V127)
    try:
        from mais.research.v_forecast_revision_tape import run_v_revision_tape
        status["revision_tape"] = run_v_revision_tape()
    except Exception as e:  # noqa: BLE001
        status["revision_tape"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 12c) Moteur météo -> canaux (V140)
    try:
        from mais.research.v140_weather_revision_engine import run_v140_weather_engine
        status["weather_engine"] = run_v140_weather_engine()
    except Exception as e:  # noqa: BLE001
        status["weather_engine"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 12d) Machine d'état de l'indicateur (V139) — avant le head qui la consomme
    try:
        from mais.premium.state_machine import run_v139_state_machine
        status["state_machine"] = run_v139_state_machine()
    except Exception as e:  # noqa: BLE001
        status["state_machine"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 13) Single source of truth premium (VN-A1) — le head autoritatif
    try:
        from mais.premium.head import build_premium_head
        status["premium_head"] = build_premium_head()
    except Exception as e:  # noqa: BLE001
        status["premium_head"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 14) Cycle de vie (V145), jalons (V147), dashboard v4 (V146)
    try:
        from mais.premium.dashboard_v4 import run_v146_dashboard
        from mais.premium.forward_milestones import run_v147_milestones
        from mais.premium.lifecycle_report import run_v145_lifecycle
        status["lifecycle"] = run_v145_lifecycle()
        status["milestones"] = run_v147_milestones()
        status["dashboard_v4"] = run_v146_dashboard()
    except Exception as e:  # noqa: BLE001
        status["dashboard_v4"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 15) Rapport mensuel v2 (V133) — régénéré chaque jour pour que reports/monthly/latest.md
    # reste aligné sur le head (V152-SYNC : une seule vérité, commitée par le CI)
    try:
        from mais.research.v133_monthly_forward_report_v2 import run_v133_monthly_v2
        status["monthly_report"] = run_v133_monthly_v2()
    except Exception as e:  # noqa: BLE001
        status["monthly_report"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 15bis) Révisions météo previous-runs (V140-DATA) — append quotidien dans l'archive committée
    # (l'API ne remonte qu'à ~92 j ; l'accumulation append-only construit l'historique long)
    try:
        from mais.collect.openmeteo_previous_runs import fetch_previous_runs
        status["weather_previous_runs"] = fetch_previous_runs(past_days=10)
    except Exception as e:  # noqa: BLE001
        status["weather_previous_runs"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 15ter) Taux BCE horodaté (V174) — archive committée + audit de la règle FX
    try:
        from mais.audit.fx_bce import run_fx_bce_audit
        from mais.collect.ecb_fx_collector import fetch_ecb_eurusd
        status["ecb_fx"] = fetch_ecb_eurusd(start="2026-05-25")
        status["fx_bce_audit"] = {k: v for k, v in run_fx_bce_audit().items() if k != "per_day"}
    except Exception as e:  # noqa: BLE001
        status["ecb_fx"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 15quater) Prix unitaires COMEXT (V161) — mensuel, appel léger, append-dedup dans l'archive
    try:
        from mais.collect.comext_unit_value import fetch_comext_unit_values
        status["comext_unit_values"] = fetch_comext_unit_values(since="2025-01")
    except Exception as e:  # noqa: BLE001
        status["comext_unit_values"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 15quinquies) Quote proxy Barchart du front officiel (V144-DATA) — construit l'overlap
    # proxy<->officiel en forward (1 paire/jour ; V144 démarre à ~40 paires)
    try:
        from mais.collect.proxy_forward_quote import run_proxy_forward_quote
        status["proxy_forward_quote"] = run_proxy_forward_quote()
    except Exception as e:  # noqa: BLE001
        status["proxy_forward_quote"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 15sexies) Validations forward courbe/MATIF (V141/V142) — gate 40 j, mûrit automatiquement
    try:
        from mais.research.v141_v142_forward_validation import run_v141_v142_forward
        status["forward_validation_v141_v142"] = run_v141_v142_forward()
    except Exception as e:  # noqa: BLE001
        status["forward_validation_v141_v142"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 15septies) Lecture live du composite V176 (stratification descriptive ; head intouché)
    try:
        from mais.research.v176_composite_indicator import run_v176_live
        status["composite_v176"] = run_v176_live()
    except Exception as e:  # noqa: BLE001
        status["composite_v176"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 15octies) Re-runs data-gated (V177) — V166-officiel/V168-MATIF/V155-été mûrissent seuls
    try:
        from mais.research.v177_data_gated_reruns import run_v177_data_gated
        status["data_gated_reruns"] = {g["rerun"]: f'{g["status"]} {g["n"]}/{g["gate"]}'
                                       for g in run_v177_data_gated()["gates"]}
    except Exception as e:  # noqa: BLE001
        status["data_gated_reruns"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

    # 16) Audit de cohérence source unique (V152-SYNC) — head/dashboard/lifecycle/monthly/latest
    try:
        from mais.audit.single_source import run_single_source_audit
        status["single_source_audit"] = run_single_source_audit()
    except Exception as e:  # noqa: BLE001
        status["single_source_audit"] = {"status": "FAIL", "error": f"{type(e).__name__}: {e}"}

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
