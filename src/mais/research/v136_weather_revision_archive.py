"""V136 — Archive de météo forecast historique + cadrage honnête des révisions.

But : backfiller une archive de prévisions extrêmes « telle que connue J » via l'Historical Forecast API
(Open-Meteo) pour pouvoir, à terme, étudier l'effet des RÉVISIONS de prévision sur le CBOT/basis.

RÉALITÉ HONNÊTE : l'Historical Forecast API ne renvoie qu'un lead (la prévision faite ~J-1), pas plusieurs
runs pour une même date cible. On ne peut donc PAS reconstruire une vraie révision multi-lead à partir d'elle
seule (il faudrait la Previous-Runs API, souvent rate-limitée/timeout). On en tire néanmoins une **archive
d'extrêmes historiques** (jours >32/35°C, déficit pluie) utile en soi. Les vraies révisions multi-lead sont
captées en FORWARD par V127 (journal des émissions successives).

Best-effort : timeouts fréquents → DATA_BLOCKED propre. Statut : RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V136_DIR = ARTEFACTS_DIR / "v136"
V136_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE = ROOT / "data" / "official_forward" / "weather_extremes_archive.parquet"


def _to_wide(long_df: pd.DataFrame) -> pd.DataFrame:
    """Long (valid_date, zone, variable, value) -> métriques d'extrêmes par valid_date (moyenne inter-zones)."""
    from mais.research.v127_weather_forecast_extremes import extreme_metrics
    if long_df is None or len(long_df) == 0:
        return pd.DataFrame()
    # extreme_metrics attend des colonnes forecast_valid_date/zone/variable/value
    df = long_df.rename(columns={"forecast_valid_date": "forecast_valid_date"})
    # on calcule sur l'ensemble (16 j) une seule ligne ; ici on agrège par mois d'émission pour densifier
    recs = []
    df["issue_month"] = pd.to_datetime(df["forecast_issue_date"]).dt.to_period("M").astype(str)
    for m, g in df.groupby("issue_month"):
        met = extreme_metrics(g, issue_month=int(m.split("-")[1]))
        if met:
            recs.append({"issue_month": m, **met})
    return pd.DataFrame(recs)


def run_v136_weather_archive(try_network: bool = True, days: int = 20, region: str = "us") -> dict[str, Any]:
    if not try_network:
        return {"version": "V136-WEATHER-ARCHIVE", "verdict": "OFFLINE_SKIP",
                "revisions_status": "FORWARD_ONLY_VIA_V127"}
    try:
        from mais.collect.openmeteo_forecast_collector import fetch_historical_forecast
        end = date.today() - timedelta(days=2)
        start = end - timedelta(days=days)
        long_df = fetch_historical_forecast(start, end, region=region)
    except Exception as exc:  # noqa: BLE001
        return {"version": "V136-WEATHER-ARCHIVE", "verdict": "DATA_BLOCKED",
                "reason": f"{type(exc).__name__}: {str(exc)[:90]}",
                "revisions_status": "FORWARD_ONLY_VIA_V127",
                "note": "Historical Forecast API indisponible/timeout. Révisions multi-lead = forward via V127.",
                "status": "RESEARCH_ONLY_NOT_TRADING"}
    if len(long_df) == 0:
        return {"version": "V136-WEATHER-ARCHIVE", "verdict": "DATA_BLOCKED",
                "revisions_status": "FORWARD_ONLY_VIA_V127", "status": "RESEARCH_ONLY_NOT_TRADING"}

    wide = _to_wide(long_df)
    if len(wide):
        ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
        prev = pd.read_parquet(ARCHIVE) if ARCHIVE.exists() else pd.DataFrame()
        combined = (pd.concat([prev, wide], ignore_index=True).drop_duplicates(subset="issue_month", keep="last")
                    if len(prev) else wide)
        combined.to_parquet(ARCHIVE, index=False)
        n_total = int(len(combined))
    else:
        n_total = 0

    out = {
        "version": "V136-WEATHER-ARCHIVE",
        "verdict": "WEATHER_ARCHIVE_READY",
        "region": region,
        "n_rows_fetched": int(len(long_df)),
        "n_months_archived": n_total,
        "lead_available": 1,
        "revisions_status": "FORWARD_ONLY_VIA_V127",
        "interpretation": (
            f"Archive d'extrêmes historiques construite ({region.upper()}, {len(long_df)} lignes, "
            f"{n_total} mois). L'Historical Forecast API ne donne qu'un LEAD (~J-1) -> pas de vraie révision "
            "multi-lead reconstructible ici (il faudrait Previous-Runs API). Les RÉVISIONS sont captées en "
            "FORWARD par V127 (journal des émissions successives). L'archive sert de contexte d'extrêmes passés."),
        "note": "Best-effort (timeouts fréquents). Pour révisions multi-lead historiques : Previous-Runs API "
                "(V134 WATCHLIST). DESCRIPTIF, jamais un prédicteur de timing.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V136_DIR / "v136_weather_archive.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def weather_archive_report_block() -> str:
    artefact = V136_DIR / "v136_weather_archive.json"
    if not artefact.exists():
        return ""
    try:
        s = json.loads(artefact.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    if s.get("verdict") != "WEATHER_ARCHIVE_READY":
        return ""
    return (
        "### Archive météo extrême historique (V136)\n"
        f"- {s['n_months_archived']} mois archivés ({s['region'].upper()}) · lead {s['lead_available']} "
        f"· révisions = {s['revisions_status']}\n"
        "- Historical API = 1 lead ; révisions multi-lead captées en forward (V127). RESEARCH_ONLY_NOT_TRADING.\n"
    )
