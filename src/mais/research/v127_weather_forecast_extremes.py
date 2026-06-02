"""V127 — Météo FORECAST extrême (pas les moyennes) + révisions, comme WARNING de contexte.

V45 a montré que le stress RÉALISÉ ne prédit pas le CBOT (price-in par anticipation). On travaille donc le
FORECAST (anticipation) : sur la prévision 16 jours, on compte les extrêmes (jours tmax>32/35°C, déficit de
pluie, incertitude inter-zones) et on regarde la RÉVISION vs l'émission précédente (un choc d'information
leading). US -> contexte CBOT_SUPPORT ; Europe -> contexte PHYSICAL_TENSION/ADVERSE_RISK.

Anti-leakage : tout est daté à l'issue_date d'émission ; journal append-only ; jamais réindexé a posteriori.
C'est un WARNING de CONTEXTE, jamais un prédicteur de timing ni un veto.
Statut : RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V127_DIR = ARTEFACTS_DIR / "v127"
V127_DIR.mkdir(parents=True, exist_ok=True)
JOURNAL = ROOT / "data" / "official_forward" / "weather_extremes_journal.jsonl"
HEAT_32, HEAT_35 = 32.0, 35.0
DRY_TOTAL_MM = 15.0       # cumul pluie sur l'horizon en deçà = déficit
PHENO_MONTHS = (6, 7, 8)  # pollinisation / remplissage (US + EU)


def extreme_metrics(fc: pd.DataFrame, issue_month: int | None = None) -> dict[str, Any] | None:
    """Métriques d'extrêmes sur une prévision 16 j (format long : valid_date, zone, variable, value)."""
    if fc is None or len(fc) == 0 or "variable" not in fc.columns:
        return None
    tmax = fc[fc["variable"] == "tmax"]
    precip = fc[fc["variable"] == "precip"]
    if len(tmax) == 0:
        return None
    # moyenne inter-zones par jour
    by_day = tmax.groupby("forecast_valid_date")["value"].mean()
    spread_by_day = tmax.groupby("forecast_valid_date")["value"].std()
    heat_32 = int((by_day > HEAT_32).sum())
    heat_35 = int((by_day > HEAT_35).sum())
    uncertainty = round(float(spread_by_day.mean()), 2) if spread_by_day.notna().any() else None
    # déficit pluie : cumul moyen inter-zones sur l'horizon
    precip_total = None
    dry_deficit = 0
    if len(precip):
        per_zone_total = precip.groupby("zone")["value"].sum()
        precip_total = round(float(per_zone_total.mean()), 1)
        dry_deficit = int(precip_total < DRY_TOTAL_MM)
    pheno = int(issue_month in PHENO_MONTHS) if issue_month is not None else 0
    score = int(heat_32 > 0) + int(heat_35 > 0) + dry_deficit + (pheno if (heat_32 > 0 or dry_deficit) else 0)
    tier = "HIGH" if score >= 3 else ("MEDIUM" if score >= 1 else "LOW")
    return {"heat_days_gt32": heat_32, "heat_days_gt35": heat_35,
            "precip_total_mm": precip_total, "dry_deficit": dry_deficit,
            "uncertainty_tmax_std": uncertainty, "pheno_window": pheno,
            "stress_score": score, "stress_tier": tier}


def _last_journal_metrics(region: str) -> dict[str, Any] | None:
    if not JOURNAL.exists():
        return None
    last = None
    for ln in JOURNAL.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("region") == region and d.get("status") == "OK":
            last = d
    return last


def _append_journal(rec: dict[str, Any]) -> bool:
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    if JOURNAL.exists():
        for ln in JOURNAL.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(ln)
            except ValueError:
                continue
            if d.get("issue_date") == rec["issue_date"] and d.get("region") == rec["region"]:
                return False
    with JOURNAL.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, default=str) + "\n")
    return True


def run_v127_weather(try_network: bool = True, region: str = "us") -> dict[str, Any]:
    if not try_network:
        return {"version": "V127-WEATHER-EXTREMES", "verdict": "OFFLINE_SKIP", "region": region}
    try:
        from mais.collect.openmeteo_forecast_collector import fetch_forecast
        fc = fetch_forecast(region=region)
    except Exception as exc:  # noqa: BLE001
        return {"version": "V127-WEATHER-EXTREMES", "verdict": "NO_FORECAST_DATA", "region": region,
                "reason": f"{type(exc).__name__}: {str(exc)[:80]}"}
    issue = pd.Timestamp(fc["forecast_issue_date"].iloc[0]) if len(fc) else pd.Timestamp.today()
    metrics = extreme_metrics(fc, issue_month=int(issue.month))
    if metrics is None:
        return {"version": "V127-WEATHER-EXTREMES", "verdict": "NO_FORECAST_DATA", "region": region}

    prev = _last_journal_metrics(region)
    revision = None
    if prev:
        revision = {"d_heat32": metrics["heat_days_gt32"] - prev.get("heat_days_gt32", 0),
                    "d_heat35": metrics["heat_days_gt35"] - prev.get("heat_days_gt35", 0),
                    "d_score": metrics["stress_score"] - prev.get("stress_score", 0),
                    "since_issue": prev.get("issue_date")}

    rec = {"status": "OK", "region": region, "issue_date": str(issue.date()), **metrics,
           "logged_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
    appended = _append_journal(rec)

    channel = "CBOT_SUPPORT" if region == "us" else "PHYSICAL_TENSION/ADVERSE_RISK"
    out = {
        "version": "V127-WEATHER-EXTREMES",
        "verdict": "WEATHER_WARNING_READY",
        "region": region,
        "issue_date": str(issue.date()),
        **metrics,
        "revision_vs_prev": revision,
        "revision_status": "OK" if revision is not None else "NO_PREVIOUS_ISSUE",
        "channel": channel,
        "journal_appended": appended,
        "interpretation": (
            f"Prévision 16 j ({region.upper()}) émise {issue.date()} : {metrics['heat_days_gt32']} j >32°C, "
            f"{metrics['heat_days_gt35']} j >35°C, pluie {metrics['precip_total_mm']} mm "
            f"(déficit={metrics['dry_deficit']}), incertitude {metrics['uncertainty_tmax_std']}°C. "
            f"WEATHER_WARNING **{metrics['stress_tier']}** -> canal {channel}. "
            + (f"Révision vs {revision['since_issue']} : Δscore {revision['d_score']}. " if revision else "")
            + "Rappel V45 : le réalisé ne prédit pas le CBOT -> ceci est un WARNING d'anticipation, jamais un "
              "prédicteur de timing ni un veto."),
        "note": "Forecast daté à l'émission, anti-leakage, append-only. Révisions = Δ vs émission précédente "
                "(archive multi-lead via historical-forecast = best-effort, souvent DATA_BLOCKED par timeout).",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V127_DIR / f"v127_weather_{region}.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def weather_warning_report_block() -> str:
    blocks = []
    for region in ("us", "eu"):
        artefact = V127_DIR / f"v127_weather_{region}.json"
        if not artefact.exists():
            continue
        try:
            s = json.loads(artefact.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if s.get("verdict") != "WEATHER_WARNING_READY":
            continue
        rev = s.get("revision_vs_prev")
        rev_txt = f" · révision Δscore {rev['d_score']}" if rev else ""
        blocks.append(
            f"- **{region.upper()}** ({s['issue_date']}) : {s['heat_days_gt32']} j>32°C, {s['heat_days_gt35']} j>35°C, "
            f"pluie {s['precip_total_mm']}mm (déficit={s['dry_deficit']}) → warning **{s['stress_tier']}** "
            f"[{s['channel']}]{rev_txt}")
    if not blocks:
        return ""
    return ("### Météo forecast extrême (V127 — WARNING de contexte)\n" + "\n".join(blocks)
            + "\n- Anticipation, jamais un prédicteur de timing ni un veto. RESEARCH_ONLY_NOT_TRADING.\n")
