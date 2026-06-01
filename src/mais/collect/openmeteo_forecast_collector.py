"""Collecteur météo PRÉVISIONNELLE (Open-Meteo) au format archive long, anti-leakage.

Récupère, par zone (centroïde État/région) et par date d'émission, les prévisions J+1..J+16, et les écrit
au format long attendu par `mais.features.weather_forecast` :
  forecast_issue_date | forecast_valid_date | lead_time_days | zone | variable | value

Deux modes :
- `fetch_forecast(today)` : prévision émise aujourd'hui (API Forecast, sans clé).
- `fetch_historical_forecast(start, end)` : archive « telle que connue le jour J » (Historical Forecast API)
  — indispensable pour un backtest honnête (anti-leakage).

Réseau requis -> en environnement hors-ligne, le collecteur lève proprement et le pipeline le marque SKIP.
Aucune dépendance lourde : stdlib `urllib` + `json`.
"""
from __future__ import annotations

import json
import urllib.request
from datetime import date, timedelta
from typing import Any

import pandas as pd

from mais.paths import PROJECT_ROOT as ROOT

# Centroïdes approximatifs (lat, lon) des zones de production.
US_CORN_BELT_CENTROIDS = {
    "iowa": (42.0, -93.5), "illinois": (40.0, -89.0), "nebraska": (41.5, -99.8),
    "minnesota": (46.0, -94.3), "indiana": (40.0, -86.3), "ohio": (40.3, -82.8),
    "south_dakota": (44.4, -100.2), "kansas": (38.5, -98.0), "missouri": (38.5, -92.5),
    "wisconsin": (44.5, -89.5),
}
EU_CENTROIDS = {
    "france": (47.0, 2.5), "romania": (45.9, 25.0), "hungary": (47.2, 19.5),
    "north_italy": (45.4, 9.5), "poland": (52.0, 19.5), "ukraine_west": (49.8, 24.0),
    "serbia": (44.0, 20.9),
}
DAILY_VARS = "temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration"
OUT_DIR = ROOT / "data" / "processed" / "weather_forecast"


def _http_json(url: str, timeout: int = 30) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "mais-research/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
        return json.loads(r.read().decode("utf-8"))


def _rows_from_daily(daily: dict, issue: date, zone: str) -> list[dict]:
    rows = []
    times = daily.get("time", [])
    var_map = {"temperature_2m_max": "tmax", "temperature_2m_min": "tmin",
               "precipitation_sum": "precip", "et0_fao_evapotranspiration": "et0"}
    for api_var, short in var_map.items():
        values = daily.get(api_var, [])
        for valid_str, val in zip(times, values, strict=False):
            valid = date.fromisoformat(valid_str)
            lead = (valid - issue).days
            if lead < 1 or val is None:
                continue
            rows.append({"forecast_issue_date": pd.Timestamp(issue),
                         "forecast_valid_date": pd.Timestamp(valid),
                         "lead_time_days": lead, "zone": zone, "variable": short, "value": float(val)})
    return rows


def fetch_forecast(region: str = "us", issue: date | None = None) -> pd.DataFrame:
    """Prévision émise `issue` (défaut aujourd'hui), J+1..J+16, par zone. Réseau requis."""
    issue = issue or date.today()
    centroids = US_CORN_BELT_CENTROIDS if region == "us" else EU_CENTROIDS
    rows: list[dict] = []
    for zone, (lat, lon) in centroids.items():
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
               f"&daily={DAILY_VARS}&forecast_days=16&timezone=UTC")
        try:
            data = _http_json(url)
        except Exception as exc:  # noqa: BLE001
            raise NotImplementedError(f"open-meteo forecast indisponible (réseau ?): {exc}") from exc
        rows.extend(_rows_from_daily(data.get("daily", {}), issue, zone))
    return pd.DataFrame(rows)


def fetch_historical_forecast(start: date, end: date, region: str = "us") -> pd.DataFrame:
    """Archive de prévisions « telle que connue le jour J » via Historical Forecast API. Réseau requis.

    Anti-leakage : l'API renvoie, pour chaque valid_date, la prévision issue ~1 jour avant. On reconstruit
    issue_date = valid_date − lead. Pour un vrai backtest multi-lead, itérer Previous-Runs API par run.
    """
    centroids = US_CORN_BELT_CENTROIDS if region == "us" else EU_CENTROIDS
    rows: list[dict] = []
    for zone, (lat, lon) in centroids.items():
        url = (f"https://historical-forecast-api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
               f"&start_date={start.isoformat()}&end_date={end.isoformat()}&daily={DAILY_VARS}&timezone=UTC")
        try:
            data = _http_json(url)
        except Exception as exc:  # noqa: BLE001
            raise NotImplementedError(f"open-meteo historical-forecast indisponible (réseau ?): {exc}") from exc
        daily = data.get("daily", {})
        times = daily.get("time", [])
        var_map = {"temperature_2m_max": "tmax", "temperature_2m_min": "tmin",
                   "precipitation_sum": "precip", "et0_fao_evapotranspiration": "et0"}
        for api_var, short in var_map.items():
            for valid_str, val in zip(times, daily.get(api_var, []), strict=False):
                if val is None:
                    continue
                valid = date.fromisoformat(valid_str)
                issue = valid - timedelta(days=1)  # prévision J-1 (lead 1) comme proxy archive
                rows.append({"forecast_issue_date": pd.Timestamp(issue),
                             "forecast_valid_date": pd.Timestamp(valid),
                             "lead_time_days": 1, "zone": zone, "variable": short, "value": float(val)})
    return pd.DataFrame(rows)


def save_forecast(region: str = "us") -> dict[str, Any]:
    """Tente la collecte du jour ; écrit le parquet. Renvoie un statut (OK / SKIP réseau)."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        fc = fetch_forecast(region=region)
    except NotImplementedError as exc:
        return {"status": "SKIP", "reason": str(exc), "region": region}
    path = OUT_DIR / f"{region}_corn_belt_forecast_daily.parquet"
    if path.exists():
        prev = pd.read_parquet(path)
        fc = pd.concat([prev, fc], ignore_index=True).drop_duplicates(
            subset=["forecast_issue_date", "forecast_valid_date", "zone", "variable"])
    fc.to_parquet(path, index=False)
    return {"status": "OK", "rows": int(len(fc)), "path": str(path), "region": region}
