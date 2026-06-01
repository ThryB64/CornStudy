"""V59 — Rapport forward MENSUEL : discipline de suivi pour bâtir un vrai track record officiel.

Agrège les journaux append-only accumulés en forward (signal officiel V27, ratio MATIF V52, prévisions
météo V45) en une synthèse mensuelle : nb de jours officiels, nb de signaux par tier, basis officiel moyen,
basis_z implicite, source du z (proxy vs officiel), ratio MATIF moyen, warnings. Après 3/6/12 mois on aura
un track record. Tant que les journaux sont courts, le rapport l'indique honnêtement (THIN_DATA).

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée. Lecture seule
des journaux (aucune réécriture).
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V59_DIR = ARTEFACTS_DIR / "v59"
V59_DIR.mkdir(parents=True, exist_ok=True)
REPORT_MD = ROOT / "docs" / "FORWARD_MONTHLY_REPORT.md"

SIGNAL_JOURNAL = ROOT / "data" / "forward_journal" / "official_forward_journal.parquet"
MATIF_JOURNAL = ROOT / "data" / "official_forward" / "matif_ratio_journal.jsonl"
WEATHER_JOURNAL = ROOT / "data" / "official_forward" / "weather_forecast_journal.jsonl"


def _read_jsonl(path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return pd.DataFrame(rows)


def _month_key(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce").dt.to_period("M").astype(str)


def build_monthly(signals: pd.DataFrame, matif: pd.DataFrame) -> pd.DataFrame:
    if len(signals) == 0:
        return pd.DataFrame()
    s = signals.copy()
    s["month"] = _month_key(s["price_date"])
    matif_by_month = {}
    if len(matif) and "price_date" in matif.columns:
        m = matif.copy()
        m["month"] = _month_key(m["price_date"])
        matif_by_month = m.groupby("month")["matif_wheat_corn_ratio"].mean().round(4).to_dict()

    out = []
    for month, g in s.groupby("month"):
        active = g[g["signal_tier"].astype(str) != "NO_SIGNAL"]
        bz = pd.to_numeric(g.get("basis_z_used"), errors="coerce")
        out.append({
            "month": month,
            "n_official_days": int(len(g)),
            "n_signals": int(len(active)),
            "tiers": active["signal_tier"].value_counts().to_dict() if len(active) else {},
            "mean_basis_official_eur_t": round(float(pd.to_numeric(
                g.get("basis_official_eur_t"), errors="coerce").mean()), 2),
            "mean_basis_z_used": round(float(bz.mean()), 3) if bz.notna().any() else None,
            "z_source": g.get("z_source").mode().iloc[0] if "z_source" in g and len(g["z_source"].dropna()) else None,
            "mean_matif_wheat_corn_ratio": matif_by_month.get(month),
            "n_warnings": int((g.get("warnings").astype(str).str.len() > 0).sum())
            if "warnings" in g else 0,
        })
    return pd.DataFrame(out).sort_values("month")


def run_v59_report() -> dict[str, Any]:
    signals = pd.read_parquet(SIGNAL_JOURNAL) if SIGNAL_JOURNAL.exists() else pd.DataFrame()
    matif = _read_jsonl(MATIF_JOURNAL)
    weather = _read_jsonl(WEATHER_JOURNAL)
    monthly = build_monthly(signals, matif)

    n_signal_days = int(len(signals))
    n_months = int(monthly["month"].nunique()) if len(monthly) else 0
    thin = n_signal_days < 20 or n_months < 1

    lines = ["# Rapport forward mensuel (V59)",
             "", "Track record officiel append-only (signal V27 + MATIF V52 + météo V45). "
             "`RESEARCH_ONLY_NOT_TRADING`, lecture seule.", "",
             f"Jours de signal officiel journalisés : **{n_signal_days}** | mois couverts : **{n_months}** | "
             f"points MATIF : {len(matif)} | émissions météo : {len(weather)}.", ""]
    if thin:
        lines += ["> **THIN_DATA** : journaux encore courts. Le rapport se densifiera avec l'accumulation "
                  "forward (objectif 3/6/12 mois). Les chiffres ci-dessous sont indicatifs.", ""]
    if len(monthly):
        lines += ["| mois | jours | signaux | tiers | basis off. €/t | basis_z | source z | ratio MATIF | warns |",
                  "|---|---:|---:|---|---:|---:|---|---:|---:|"]
        def _cell(v):
            return v if (v is not None and pd.notna(v)) else "—"
        for _, r in monthly.iterrows():
            lines.append(
                f"| {r['month']} | {r['n_official_days']} | {r['n_signals']} | "
                f"{r['tiers'] or '—'} | {_cell(r['mean_basis_official_eur_t'])} | "
                f"{_cell(r['mean_basis_z_used'])} | {r['z_source'] or '—'} | "
                f"{_cell(r['mean_matif_wheat_corn_ratio'])} | {r['n_warnings']} |")
    else:
        lines += ["_Aucun signal officiel journalisé pour l'instant — le collecteur quotidien alimentera ce "
                  "rapport (settlement officiel requis)._"]
    lines += ["", "## Lecture",
              "Ce rapport est la brique de DISCIPLINE forward : il transforme les snapshots officiels en suivi "
              "mensuel reproductible. Aucune décision de trading ; on mesure la cohérence proxy/officiel, la "
              "fréquence des signaux, et le contexte (basis, z, substitution MATIF). Niveau 3 (paper trading) "
              "n'est atteignable qu'après plusieurs mois d'accumulation."]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")

    out = {
        "version": "V59-MONTHLY-FORWARD",
        "n_signal_days": n_signal_days,
        "n_months": n_months,
        "n_matif_points": int(len(matif)),
        "n_weather_emissions": int(len(weather)),
        "thin_data": bool(thin),
        "monthly": monthly.to_dict(orient="records") if len(monthly) else [],
        "report_path": str(REPORT_MD.relative_to(ROOT)) if REPORT_MD.is_relative_to(ROOT) else str(REPORT_MD),
        "verdict": "FORWARD_REPORT_THIN_DATA_ACCUMULATING" if thin else "FORWARD_REPORT_READY",
        "note": "Brique de discipline (Niveau 2→3). Track record réel après 3/6/12 mois d'accumulation.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V59_DIR / "v59_monthly_forward.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
