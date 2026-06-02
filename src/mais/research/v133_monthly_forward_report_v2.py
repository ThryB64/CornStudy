"""V133 — Rapport forward mensuel v2 : un bilan clair de l'accumulation officielle.

Étend V59 en regroupant tout ce qui s'accumule en forward : jours officiels, signaux, cohérence
latest/journal (V122), proxy vs officiel (V103), basis_z, objectifs, MFE/MAE du signal actif (V124),
météo (V127), ratio MATIF (V126), tension de courbe (V125/V109), et l'état du signal actif. Produit un
markdown daté dans reports/monthly/.

Lecture seule des journaux/artefacts. Statut : RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V133_DIR = ARTEFACTS_DIR / "v133"
V133_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR = ROOT / "reports" / "monthly"
OFFICIAL_JOURNAL = ROOT / "data" / "forward_journal" / "official_forward_journal.parquet"


def _read(rel) -> dict[str, Any]:
    try:
        return json.loads((ARTEFACTS_DIR / rel).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def run_v133_monthly_v2() -> dict[str, Any]:
    if not OFFICIAL_JOURNAL.exists():
        return {"version": "V133-MONTHLY-V2", "verdict": "NO_JOURNAL"}
    j = pd.read_parquet(OFFICIAL_JOURNAL).sort_values("price_date")
    if len(j) == 0:
        return {"version": "V133-MONTHLY-V2", "verdict": "EMPTY_JOURNAL"}

    j["month"] = pd.to_datetime(j["price_date"]).dt.to_period("M").astype(str)
    tier_counts = j["signal_tier"].value_counts().to_dict()
    basis = pd.to_numeric(j["basis_official_eur_t"], errors="coerce").dropna()
    by_month = {}
    for m, g in j.groupby("month"):
        b = pd.to_numeric(g["basis_official_eur_t"], errors="coerce").dropna()
        by_month[m] = {"days": int(len(g)),
                       "tiers": {str(k): int(v) for k, v in g["signal_tier"].value_counts().items()},
                       "basis_mean": round(float(b.mean()), 2) if len(b) else None,
                       "basis_last": round(float(b.iloc[-1]), 2) if len(b) else None}

    consistency = _read("v122/v122_consistency.json")
    monitoring = _read("v124/v124_active_monitoring.json")
    weather_us = _read("v127/v127_weather_us.json")
    matif = _read("v126/v126_substitution.json")
    curve = _read("v125/v125_curve_accumulation.json")
    dashboard = _read("v103/v103_dashboard.json") or _read("v103/proxy_official_dashboard.json")

    out = {
        "version": "V133-MONTHLY-V2",
        "verdict": "MONTHLY_REPORT_V2_BUILT",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "n_official_days": int(j["price_date"].nunique()),
        "first_date": str(j["price_date"].iloc[0]),
        "last_date": str(j["price_date"].iloc[-1]),
        "tier_counts": {str(k): int(v) for k, v in tier_counts.items()},
        "basis_mean_eur_t": round(float(basis.mean()), 2) if len(basis) else None,
        "basis_last_eur_t": round(float(basis.iloc[-1]), 2) if len(basis) else None,
        "by_month": by_month,
        "consistency_verdict": consistency.get("verdict"),
        "active_signal_status": monitoring.get("status"),
        "active_signal_mfe": monitoring.get("mfe_eur_t"),
        "active_signal_mae": monitoring.get("mae_eur_t"),
        "weather_us_tier": weather_us.get("stress_tier"),
        "matif_ratio_last": matif.get("matif_ratio_last"),
        "curve_trend": curve.get("spread_trend"),
        "curve_tension_tier": curve.get("physical_tension_tier"),
        "proxy_official_dashboard": dashboard.get("verdict") if dashboard else None,
        "months_to_serious_review": round(max(0.0, 6 - j["price_date"].nunique() / 21), 1),
        "note": "Bilan forward sérieux à ≥6 mois officiels. Journal append-only, passé jamais réécrit. "
                "Lecture seule. RESEARCH_ONLY_NOT_TRADING.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V133_DIR / "v133_monthly_v2.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    _write_markdown(out)
    return out


def _write_markdown(s: dict[str, Any]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Rapport forward mensuel v2 — {s['last_date']}",
        "",
        f"_Généré {s['generated_at']} · RESEARCH_ONLY_NOT_TRADING_",
        "",
        f"- **Jours officiels** : {s['n_official_days']} ({s['first_date']} → {s['last_date']})",
        f"- **Tiers** : {s['tier_counts']}",
        f"- **Basis officiel** : moy {s['basis_mean_eur_t']} · dernier {s['basis_last_eur_t']} €/t",
        f"- **Cohérence signal (V122)** : {s['consistency_verdict']}",
        f"- **Signal actif (V124)** : {s['active_signal_status']} · MFE {s['active_signal_mfe']} · "
        f"MAE {s['active_signal_mae']}",
        f"- **Courbe (V125)** : tendance {s['curve_trend']} · tension {s['curve_tension_tier']}",
        f"- **Substitution MATIF (V126)** : ratio {s['matif_ratio_last']}",
        f"- **Météo US (V127)** : {s['weather_us_tier']}",
        f"- **Proxy/officiel (V103)** : {s['proxy_official_dashboard']}",
        f"- **Avant bilan sérieux** : ~{s['months_to_serious_review']} mois",
        "",
        "## Par mois",
        "",
        "| Mois | Jours | Tiers | Basis moy | Basis dernier |",
        "|------|-------|-------|-----------|---------------|",
    ]
    for m, v in s["by_month"].items():
        lines.append(f"| {m} | {v['days']} | {v['tiers']} | {v['basis_mean']} | {v['basis_last']} |")
    (REPORTS_DIR / f"{s['last_date']}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (REPORTS_DIR / "latest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def monthly_v2_report_block() -> str:
    artefact = V133_DIR / "v133_monthly_v2.json"
    if not artefact.exists():
        return ""
    try:
        s = json.loads(artefact.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    if s.get("verdict") != "MONTHLY_REPORT_V2_BUILT":
        return ""
    return (
        "### Bilan forward mensuel v2 (V133)\n"
        f"- {s['n_official_days']} jours officiels ({s['first_date']}→{s['last_date']}) · tiers "
        f"{s['tier_counts']} · basis dernier {s['basis_last_eur_t']} €/t\n"
        f"- Cohérence {s['consistency_verdict']} · signal actif {s['active_signal_status']} · "
        f"avant bilan sérieux ~{s['months_to_serious_review']} mois\n"
        "- Rapport complet : reports/monthly/latest.md. RESEARCH_ONLY_NOT_TRADING.\n"
    )
