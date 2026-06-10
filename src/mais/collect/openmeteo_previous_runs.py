"""V140-DATA — Collecteur Open-Meteo « Previous Runs » : révisions de prévision à lead fixe.

L'API Previous Runs expose, pour chaque date de validité, la valeur prévue telle qu'elle était connue
1..7 jours avant (`*_previous_dayN`). C'est le matériau PROPRE pour tester si une RÉVISION de prévision
(et non la météo réalisée, price-in V45) précède la détente de la prime.

Format long anti-leakage :
  issue_date | valid_date | lead_day | zone | variable | value
où issue_date = valid_date - lead_day. Une feature à l'instant d'émission `t` n'utilise QUE la valeur
au lead correspondant (connue à `t`). Réseau requis -> hors-ligne, lève proprement (WAITING_DATA).

stdlib uniquement (urllib + json). RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from mais.collect.openmeteo_forecast_collector import EU_CENTROIDS, US_CORN_BELT_CENTROIDS
from mais.paths import PROJECT_ROOT as ROOT

PREVIOUS_RUNS_URL = "https://previous-runs-api.open-meteo.com/v1/forecast"
BASE_VARS = {"temperature_2m_max": "tmax", "precipitation_sum": "precip"}
MAX_LEAD = 7
OUT_DIR = ROOT / "data" / "processed" / "weather_revisions"


def _http_json(url: str, timeout: int = 30) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "mais-research/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
        return json.loads(r.read().decode("utf-8"))


def _daily_param() -> str:
    parts = []
    for base in BASE_VARS:
        parts.append(base)
        parts += [f"{base}_previous_day{k}" for k in range(1, MAX_LEAD + 1)]
    return ",".join(parts)


def parse_previous_runs(daily: dict, zone: str) -> list[dict]:
    """Convertit la réponse API en lignes longues lead-fixe (lead 0 = run du jour de validité)."""
    times = daily.get("time", [])
    rows: list[dict] = []
    for base, short in BASE_VARS.items():
        for lead in range(0, MAX_LEAD + 1):
            key = base if lead == 0 else f"{base}_previous_day{lead}"
            vals = daily.get(key)
            if not vals:
                continue
            for valid_str, val in zip(times, vals, strict=False):
                if val is None:
                    continue
                valid = pd.Timestamp(valid_str).date()
                issue = valid - timedelta(days=lead)
                rows.append({"issue_date": str(issue), "valid_date": str(valid),
                             "lead_day": lead, "zone": zone, "variable": short, "value": float(val)})
    return rows


def fetch_previous_runs(zones: dict[str, tuple[float, float]] | None = None,
                        past_days: int = 60, write: bool = True) -> dict[str, Any]:
    """Récupère les révisions lead-fixe pour les zones données. Réseau requis."""
    zones = zones or {**US_CORN_BELT_CENTROIDS, **EU_CENTROIDS}
    rows: list[dict] = []
    errors = []
    for zone, (lat, lon) in zones.items():
        url = (f"{PREVIOUS_RUNS_URL}?latitude={lat}&longitude={lon}&daily={_daily_param()}"
               f"&past_days={past_days}&forecast_days=1&timezone=UTC")
        try:
            js = _http_json(url)
            rows += parse_previous_runs(js.get("daily", {}), zone)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{zone}: {type(e).__name__}")
    if not rows:
        return {"verdict": "WAITING_DATA", "reason": "réseau indisponible ou réponse vide",
                "errors": errors[:5]}
    df = pd.DataFrame(rows)
    if write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(OUT_DIR / "weather_revisions_long.parquet", index=False)
    return {"verdict": "REVISIONS_COLLECTED", "n_rows": int(len(df)),
            "n_zones": int(df["zone"].nunique()), "leads": sorted(df["lead_day"].unique().tolist()),
            "collected_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "n_errors": len(errors)}


def revision_tape(df_long: pd.DataFrame) -> pd.DataFrame:
    """Pour chaque (zone, variable, valid_date), révision lead k -> k-1 (rapprochement de l'échéance).

    revision_{k} = value(lead k-1) - value(lead k) : ce que la prévision a changé en se rapprochant d'un
    jour. Indexée par la date d'ÉMISSION du run le plus récent des deux (anti-leakage : connue à issue).
    """
    out: list[dict] = []
    key = ["zone", "variable", "valid_date"]
    for (zone, var, valid), g in df_long.groupby(key):
        s = g.set_index("lead_day")["value"].sort_index()
        for lead in range(1, MAX_LEAD + 1):
            if lead in s.index and (lead - 1) in s.index:
                rev = float(s[lead - 1] - s[lead])
                issue = pd.Timestamp(valid).date() - timedelta(days=lead - 1)
                out.append({"issue_date": str(issue), "valid_date": valid, "zone": zone,
                            "variable": var, "from_lead": lead, "to_lead": lead - 1, "revision": rev})
    return pd.DataFrame(out)


def load_revisions() -> pd.DataFrame:
    p = OUT_DIR / "weather_revisions_long.parquet"
    return pd.read_parquet(p) if p.exists() else pd.DataFrame()
