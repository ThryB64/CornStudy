"""V159 — Pack d'audit dur de la vérité des données (§8bis.2 de la réflexion).

Chaque audit retourne un dict {audit, verdict: PASS/FAIL/WARN, ...} et écrit son artefact sous
artefacts/audit/. Aucune science : on vérifie que la donnée est propre AVANT toute conclusion.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.research import v27_official_forward as v27

AUDIT_DIR = ARTEFACTS_DIR / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

# Conversion CBOT corn : cents/bu -> EUR/t. 1 t de maïs = 39.3679 bu (1 bu = 25.4012 kg).
BU_PER_TONNE = 39.3679
CBOT_EUR_TOL = 0.75  # €/t : tolérance round-trip (arrondis sur cents_bu/eurusd journalisés)
SESSION_FIELDS = ("record_status", "collected_at_utc", "collected_at_paris", "effective_session_date")


def _write(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    (AUDIT_DIR / name).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return payload


def session_alignment_audit() -> dict[str, Any]:
    """Toute ligne officielle porte record_status + timestamps + effective_session_date."""
    if not v27.JOURNAL_JSONL.exists():
        return _write("session_alignment_report.json",
                      {"audit": "session_alignment", "verdict": "SKIP", "reason": "journal absent"})
    recs = [json.loads(ln) for ln in v27.JOURNAL_JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
    orphans = [r.get("price_date") for r in recs if any(r.get(f) is None for f in SESSION_FIELDS)]
    statuses: dict[str, int] = {}
    for r in recs:
        statuses[str(r.get("record_status"))] = statuses.get(str(r.get("record_status")), 0) + 1
    return _write("session_alignment_report.json", {
        "audit": "session_alignment",
        "verdict": "PASS" if not orphans else "FAIL",
        "n_lines": len(recs), "n_orphans": len(orphans), "orphan_dates": orphans,
        "session_status_counts": statuses,
    })


def finality_gate_audit() -> dict[str, Any]:
    """La vue FINAL-only existe et le résumé signale honnêtement un dernier jour provisoire."""
    summ = v27.summarize_forward_journal()
    if summ.get("verdict") == "EMPTY":
        return _write("finality_gate_report.json",
                      {"audit": "finality_gate", "verdict": "SKIP", "reason": "journal vide"})
    final_view = v27.load_forward_journal(final_only=True)
    only_final = final_view["record_status"].astype(str).isin(["FINAL", "REVISED"]).all() \
        if not final_view.empty else True
    return _write("finality_gate_report.json", {
        "audit": "finality_gate",
        "verdict": "PASS" if only_final else "FAIL",
        "n_days": summ.get("n_days"), "n_final_days": summ.get("n_final_days"),
        "last_date": summ.get("last_date"), "last_final_date": summ.get("last_final_date"),
        "last_day_provisional": summ.get("last_day_provisional"),
        "note": "Les vues premium doivent lire la vue FINAL-only ; le dernier jour peut être PROVISIONAL.",
    })


def cbot_eur_conversion_audit() -> dict[str, Any]:
    """Recalcule cbot_eur_t = cents_bu/100 * 39.3679 / eurusd et compare au journalisé."""
    j = v27.load_forward_journal()
    if j.empty or not {"cbot_cents_bu", "eurusd", "cbot_eur_t"}.issubset(j.columns):
        return _write("cbot_eur_roundtrip.json",
                      {"audit": "cbot_eur_conversion", "verdict": "SKIP", "reason": "champs absents"})
    cents = pd.to_numeric(j["cbot_cents_bu"], errors="coerce")
    fx = pd.to_numeric(j["eurusd"], errors="coerce")
    stored = pd.to_numeric(j["cbot_eur_t"], errors="coerce")
    recomputed = (cents / 100.0) * BU_PER_TONNE / fx
    err = (recomputed - stored).abs()
    max_err = float(err.max()) if len(err.dropna()) else None
    return _write("cbot_eur_roundtrip.json", {
        "audit": "cbot_eur_conversion",
        "verdict": "PASS" if (max_err is not None and max_err <= CBOT_EUR_TOL) else
                   ("SKIP" if max_err is None else "FAIL"),
        "bu_per_tonne": BU_PER_TONNE, "tolerance_eur_t": CBOT_EUR_TOL,
        "max_abs_err_eur_t": round(max_err, 4) if max_err is not None else None,
        "n_checked": int(err.notna().sum()),
    })


def contract_selection_audit() -> dict[str, Any]:
    """La règle de sélection de contrat est explicite et journalisée (front / most-liquid)."""
    j = v27.load_forward_journal()
    if j.empty:
        return _write("contract_selection_report.json",
                      {"audit": "contract_selection", "verdict": "SKIP", "reason": "journal vide"})
    has_front = "official_front_contract" in j.columns
    has_liquid = "most_liquid_contract" in j.columns
    return _write("contract_selection_report.json", {
        "audit": "contract_selection",
        "verdict": "PASS" if has_front else "FAIL",
        "front_contract_logged": has_front,
        "most_liquid_logged": has_liquid,
        "rule": "front = nearby settlement (official_front_contract) ; most_liquid_contract exposé en contexte",
        "distinct_front_contracts": sorted(j["official_front_contract"].dropna().astype(str).unique().tolist())
        if has_front else [],
    })


def run_data_truth_audit() -> dict[str, Any]:
    audits = [session_alignment_audit(), finality_gate_audit(), cbot_eur_conversion_audit(),
              contract_selection_audit()]
    verdicts = {a["audit"]: a["verdict"] for a in audits}
    failed = [k for k, v in verdicts.items() if v == "FAIL"]
    overall = "FAIL" if failed else ("WARN" if any(v == "SKIP" for v in verdicts.values()) else "PASS")
    return _write("data_truth_audit.json", {
        "version": "V159-DATA-TRUTH-AUDIT",
        "overall": overall, "failed": failed, "verdicts": verdicts,
        "status": "RESEARCH_ONLY_NOT_TRADING",
    })


if __name__ == "__main__":
    print(json.dumps(run_data_truth_audit(), indent=2))
