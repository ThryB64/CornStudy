"""V31 — Dashboard de suivi forward de l'indicateur premium (PROJET 1), séparé du module SELL_THIRDS.

L'étude principale = PROJET 1 : indicateur de prime EMA/CBOT (basis short, research forward). Le module
`daily_snapshot` (SELL_THIRDS / cash / stockage agriculteur) est un PROJET 2 distinct ; ce dashboard ne le
mélange pas. Il lit le journal forward officiel (V27) et produit un tableau lisible :
date | basis officiel | basis_z | tier | curve_shape | warnings | objectifs | statut | (PnL quand mûr).

Tant que l'historique officiel est court, le PnL réel n'est pas calculable (pas de prix de sortie officiel
encore) -> statut `open_awaiting_official_history`. Le dashboard se remplira jour après jour.

Statut : RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR

V31_DIR = ARTEFACTS_DIR / "v31"
V31_DIR.mkdir(parents=True, exist_ok=True)


def build_forward_dashboard() -> pd.DataFrame:
    from mais.research.v27_official_forward import load_forward_journal
    j = load_forward_journal()
    if j.empty:
        return j
    j = j.sort_values("price_date").reset_index(drop=True)
    today = pd.Timestamp(datetime.now().date())
    cols = ["price_date", "basis_official_eur_t", "basis_z_used", "z_source", "signal_tier",
            "curve_shape", "curve_overall", "most_liquid_contract", "warnings",
            "objective_prudent", "objective_full", "median_horizon_days", "non_reversion_risk"]
    have = [c for c in cols if c in j.columns]
    dash = j[have].copy()

    def _status(row):
        if row["signal_tier"] == "NO_SIGNAL":
            return "no_signal"
        d = pd.Timestamp(row["price_date"])
        horizon = int(row.get("median_horizon_days", 47) or 47)
        if (today - d).days < horizon:
            return "open"
        return "open_awaiting_official_history"  # pas encore de prix de sortie officiel

    dash["status"] = dash.apply(_status, axis=1)
    dash["pnl_prudent"] = None
    dash["pnl_full"] = None
    dash["compression_path"] = None
    return dash


def render_dashboard_markdown(dash: pd.DataFrame) -> str:
    lines = [
        "# Dashboard forward — Indicateur premium EMA/CBOT (PROJET 1)",
        "",
        "_Research-only. SÉPARÉ du module SELL_THIRDS / cash / stockage agriculteur (PROJET 2)._",
        f"_Généré le {datetime.now().date()}._",
        "",
    ]
    if dash.empty:
        lines.append("Aucun signal forward journalisé. Lancer le collecteur officiel en cron quotidien.")
        return "\n".join(lines)
    lines += [
        f"- Jours journalisés : **{dash['price_date'].nunique()}**",
        f"- Dernier signal : **{dash.iloc[-1]['signal_tier']}** "
        f"(basis {dash.iloc[-1].get('basis_official_eur_t')} €/t, "
        f"z {dash.iloc[-1].get('basis_z_used')}, courbe {dash.iloc[-1].get('curve_shape')})",
        "",
        "| date | basis | z | tier | courbe | warnings | obj | statut |",
        "|---|---:|---:|---|---|---|---|---|",
    ]
    for _, r in dash.iterrows():
        lines.append(
            f"| {r['price_date']} | {r.get('basis_official_eur_t')} | {r.get('basis_z_used')} | "
            f"{r.get('signal_tier')} | {r.get('curve_shape')} | {str(r.get('warnings'))[:40]} | "
            f"{r.get('objective_prudent')}/{r.get('objective_full')} | {r.get('status')} |")
    lines += [
        "",
        "## Questions de validation forward (à mesurer en accumulant)",
        "- Les signaux forward ressemblent-ils aux backtests (tier, fréquence) ?",
        "- L'officiel confirme-t-il le proxy (basis, z) ? (V37, ≥40 j puis 3/6/12 mois)",
        "- Les warnings (backwardation, ADVERSE_RISK) expliquent-ils les échecs ?",
        "",
        "_Règle figée pendant tout le forward (cf. FROZEN_BASELINE.md) : aucune modif a posteriori._",
    ]
    return "\n".join(lines)


def run_v31_dashboard() -> dict[str, Any]:
    dash = build_forward_dashboard()
    md = render_dashboard_markdown(dash)
    (V31_DIR / "forward_dashboard.md").write_text(md, encoding="utf-8")
    if not dash.empty:
        dash.to_parquet(V31_DIR / "forward_dashboard.parquet", index=False)
    out = {
        "version": "V31-FORWARD-DASHBOARD",
        "n_days": int(dash["price_date"].nunique()) if not dash.empty else 0,
        "last_tier": dash.iloc[-1]["signal_tier"] if not dash.empty else None,
        "project_separation": "PROJET 1 (premium EMA/CBOT) séparé de PROJET 2 (SELL_THIRDS/cash/stockage)",
        "dashboard_md": str(V31_DIR / "forward_dashboard.md"),
        "verdict": "DASHBOARD_BUILT",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V31_DIR / "v31_summary.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
