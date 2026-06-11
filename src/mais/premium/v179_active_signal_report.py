"""V179 — Rapport complet du signal actif (entrée 2026-05-29).

Assemble en UN document la trajectoire quotidienne du signal actif et tout son contexte :
cœur V124 (compression réalisée, MFE/MAE, distance z→0.5, statut HEALTHY/SLOW/ADVERSE_LIKE/
DELAYED), table jour par jour depuis l'entrée (basis, z, tier, CBOT EUR/t, courbe, MATIF),
diagnostics du head (météo, substitution, tension physique) et machine d'état V139.

Lecture seule de toutes les couches — ne modifie ni head, ni state machine, ni journal.
Sorties : artefact JSON + rapport Markdown `reports/active_signal/latest.md`.
RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT
from mais.premium.v178_official_validation import _load_official

V179_DIR = ARTEFACTS_DIR / "v179"
V179_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR = ROOT / "reports" / "active_signal"
CURVE_HISTORY = ROOT / "data" / "official_forward" / "ema_curve_history.parquet"
MATIF_HISTORY = ROOT / "data" / "official_forward" / "matif_ratio_history.parquet"
HEAD = ROOT / "data" / "premium" / "premium_daily_head.json"
STATE_MACHINE = ARTEFACTS_DIR / "state_machine" / "state_machine.json"


def _read_json(path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _daily_table(journal: pd.DataFrame, entry_date: str) -> pd.DataFrame:
    ep = journal[journal["price_date"] >= entry_date].copy()
    cols = {"price_date": "date", "basis_official_eur_t": "basis", "basis_z_used": "z",
            "signal_tier": "tier", "cbot_eur_t": "cbot_eur_t", "record_status": "session"}
    ep = ep[[c for c in cols if c in ep.columns]].rename(columns=cols)
    for extra_path, key, rename in ((CURVE_HISTORY, "front_next_spread", "curve_spread"),
                                    (CURVE_HISTORY, "curve_shape", "curve_shape"),
                                    (MATIF_HISTORY, "ratio", "matif_wheat_corn")):
        if extra_path.exists():
            x = pd.read_parquet(extra_path)
            x["price_date"] = pd.to_datetime(x["price_date"]).dt.strftime("%Y-%m-%d")
            if key in x.columns:
                ep = ep.merge(x[["price_date", key]].rename(columns={key: rename}),
                              left_on="date", right_on="price_date", how="left").drop(
                                  columns="price_date")
    return ep


def run_v179_active_signal_report() -> dict[str, Any]:
    try:
        from mais.research.v124_active_monitoring_v2 import monitor_active_signal_v2
        core = monitor_active_signal_v2()
    except Exception as e:  # noqa: BLE001
        core = {"verdict": "MONITORING_UNAVAILABLE", "error": f"{type(e).__name__}: {e}"}
    if core.get("verdict") not in ("ACTIVE_MONITORING_READY",):
        out = {"version": "V179-ACTIVE-SIGNAL-REPORT", "verdict": core.get("verdict"),
               "status": "RESEARCH_ONLY_NOT_TRADING"}
        (V179_DIR / "v179_active_signal.json").write_text(
            json.dumps(out, indent=2, default=str), encoding="utf-8")
        return out

    journal = _load_official()
    table = _daily_table(journal, core["entry_date"]) if journal is not None else pd.DataFrame()
    head = _read_json(HEAD) or {}
    sm = _read_json(STATE_MACHINE) or {}
    diags = head.get("diagnostics", {})

    out = {
        "version": "V179-ACTIVE-SIGNAL-REPORT",
        "verdict": "REPORT_BUILT",
        "signal_status": core.get("status"),
        "core": {k: core.get(k) for k in
                 ("entry_date", "current_date", "days_since_entry", "entry_tier", "current_tier",
                  "entry_z", "current_z", "entry_basis_eur_t", "current_basis_eur_t",
                  "compression_realized_eur_t", "mfe_eur_t", "mae_eur_t", "distance_to_z05",
                  "distance_to_z0", "median_horizon_days")},
        "state_machine": {k: sm.get(k) for k in
                          ("prime_nature", "lifecycle_state", "signal_tier", "basis_z")},
        "context": {
            "objective": head.get("TARGET_RECOMMENDATION"),
            "signal_quality": head.get("SIGNAL_QUALITY"),
            "composite_score": head.get("COMPOSITE_SCORE"),
            "weather_us": (diags.get("WEATHER_WARNING_US") or {}).get("value"),
            "weather_eu": (diags.get("WEATHER_WARNING_EU") or {}).get("value"),
            "physical_tension": (diags.get("PHYSICAL_TENSION") or {}).get("value"),
            "curve_trend": (diags.get("CURVE_TREND") or {}).get("value"),
            "cbot_support": (diags.get("CBOT_SUPPORT") or {}).get("value"),
            "adverse_risk": (diags.get("ADVERSE_RISK") or {}).get("value"),
        },
        "daily_table": table.to_dict(orient="records"),
        "warnings": head.get("warnings"),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V179_DIR / "v179_active_signal.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8")
    _write_markdown(out, table)
    return out


def _write_markdown(out: dict[str, Any], table: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    c, ctx, sm = out["core"], out["context"], out["state_machine"]
    lines = [
        "# Signal actif — rapport V179", "",
        f"_Généré au {c.get('current_date')} · RESEARCH_ONLY_NOT_TRADING_", "",
        f"**Statut : {out['signal_status']}** · entrée {c.get('entry_date')} "
        f"({c.get('entry_tier')}, z {c.get('entry_z')}) · {c.get('days_since_entry')} j", "",
        "## Trajectoire",
        f"- basis {c.get('entry_basis_eur_t')} → {c.get('current_basis_eur_t')} €/t "
        f"(compression réalisée **{c.get('compression_realized_eur_t')} €/t**)",
        f"- z {c.get('entry_z')} → {c.get('current_z')} · distance z→0.5 : "
        f"**{c.get('distance_to_z05')}** · z→0 : {c.get('distance_to_z0')}",
        f"- MFE {c.get('mfe_eur_t')} €/t · MAE {c.get('mae_eur_t')} €/t · horizon médian "
        f"{c.get('median_horizon_days')} j", "",
        "## Machine d'état & contexte",
        f"- nature : **{sm.get('prime_nature')}** · cycle : **{sm.get('lifecycle_state')}**",
        f"- objectif : {ctx.get('objective')} · qualité : {ctx.get('signal_quality')} · "
        f"composite : {ctx.get('composite_score')}",
        f"- courbe : {ctx.get('curve_trend')} · tension physique : {ctx.get('physical_tension')} "
        f"· CBOT support : {ctx.get('cbot_support')} · ADVERSE : {ctx.get('adverse_risk')}",
        f"- météo US : {ctx.get('weather_us')} · météo EU : {ctx.get('weather_eu')}", "",
    ]
    if len(table):
        lines.append("## Jour par jour (sessions officielles)")
        cols = [c2 for c2 in ("date", "session", "basis", "z", "tier", "cbot_eur_t",
                              "curve_spread", "curve_shape", "matif_wheat_corn")
                if c2 in table.columns]
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("|" + "---|" * len(cols))
        for _, r in table.iterrows():
            lines.append("| " + " | ".join(
                "" if pd.isna(r[c2]) else (f"{r[c2]:.2f}" if isinstance(r[c2], float) else str(r[c2]))
                for c2 in cols) + " |")
    if out.get("warnings"):
        lines += ["", "## Warnings"] + [f"- {w}" for w in out["warnings"]]
    (REPORT_DIR / "latest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
