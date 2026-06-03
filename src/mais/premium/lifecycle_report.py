"""V145 — Rapport du cycle de vie du signal actif (combine V124 santé + V139 machine d'état).

Produit un markdown clair : où en est le signal (état), depuis combien de temps, compression/MFE/MAE,
distances aux objectifs, et la lecture du cycle de vie. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from mais.paths import ARTEFACTS_DIR, DATA_DIR

V_DIR = ARTEFACTS_DIR / "lifecycle_report"
V_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR = DATA_DIR / "premium"


def run_v145_lifecycle() -> dict[str, Any]:
    from mais.premium.state_machine import run_v139_state_machine
    from mais.research.v124_active_monitoring_v2 import monitor_active_signal_v2
    mon = monitor_active_signal_v2()
    sm = run_v139_state_machine()
    if mon.get("verdict") != "ACTIVE_MONITORING_READY":
        return {"version": "V145-LIFECYCLE", "verdict": "NO_ACTIVE_SIGNAL"}

    out = {
        "version": "V145-LIFECYCLE",
        "verdict": "LIFECYCLE_REPORT_BUILT",
        "as_of": mon.get("current_date"),
        "headline_state": sm.get("headline_state"),
        "prime_nature": sm.get("prime_nature"),
        "lifecycle_state": sm.get("lifecycle_state"),
        "days_since_entry": mon.get("days_since_entry"),
        "compression_realized_eur_t": mon.get("compression_realized_eur_t"),
        "mfe_eur_t": mon.get("mfe_eur_t"), "mae_eur_t": mon.get("mae_eur_t"),
        "distance_to_z05": mon.get("distance_to_z05"), "distance_to_z0": mon.get("distance_to_z0"),
        "health_status": mon.get("status"),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V_DIR / "v145_lifecycle.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    _write_md(out)
    return out


def _write_md(s: dict[str, Any]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    md = [
        f"# Cycle de vie du signal actif — {s['as_of']}",
        f"_Généré {s['generated_at']} · RESEARCH_ONLY_NOT_TRADING_", "",
        f"- **État** : {s['headline_state']} (nature {s['prime_nature']}, cycle {s['lifecycle_state']})",
        f"- **Âge** : {s['days_since_entry']} j · santé {s['health_status']}",
        f"- **Compression** : {s['compression_realized_eur_t']} €/t · MFE {s['mfe_eur_t']} · MAE {s['mae_eur_t']}",
        f"- **Distance** : z→0.5 {s['distance_to_z05']} · z→0 {s['distance_to_z0']}",
    ]
    (REPORTS_DIR / "lifecycle.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def lifecycle_report_block() -> str:
    s = run_v145_lifecycle()
    if s.get("verdict") != "LIFECYCLE_REPORT_BUILT":
        return ""
    return (
        "### Cycle de vie du signal (V145)\n"
        f"- **{s['headline_state']}** ({s['lifecycle_state']}, {s['prime_nature']}) · {s['days_since_entry']} j · "
        f"santé {s['health_status']}\n"
        f"- compression {s['compression_realized_eur_t']} · MFE {s['mfe_eur_t']} · dist z→0.5 {s['distance_to_z05']}\n"
        "- Rapport : data/premium/lifecycle.md. RESEARCH_ONLY_NOT_TRADING.\n"
    )
