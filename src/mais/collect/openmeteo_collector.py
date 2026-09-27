"""Open-Meteo daily weather collector for the corn belt states.

Uses the free historical archive endpoint - no API key required.
Incrémental (reprend 10 j avant la dernière date du CSV) + backoff sur 429, puis reconstruit
data/interim/meteo.parquet (colonnes wx_<state>_<variable>, agrégées par features/weather_belt).
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from mais.paths import INTERIM_DIR
from mais.utils import get_logger

log = get_logger("mais.collect.openmeteo")

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def download(out_dir: Path, src: dict) -> str:
    try:
        import requests
    except ImportError as e:
        raise NotImplementedError("requests not installed") from e

    states = src.get("states", [])
    variables = src.get("variables", [])
    if not states or not variables:
        raise ValueError("openmeteo source needs states + variables")

    n = 0
    for st in states:
        out = out_dir / f"meteo_{st['name']}.csv"
        old = pd.read_csv(out, parse_dates=["Date"]) if out.exists() else None
        start = "1990-01-01"
        if old is not None and not old.empty and set(variables) <= set(old.columns):
            start = (old["Date"].max() - pd.Timedelta(days=10)).strftime("%Y-%m-%d")
        params = {
            "latitude": st["lat"],
            "longitude": st["lon"],
            "start_date": start,
            "end_date": pd.Timestamp.utcnow().normalize().strftime("%Y-%m-%d"),
            "daily": ",".join(variables),
            "timezone": "auto",
        }
        payload = None
        for attempt in range(5):
            try:
                r = requests.get(ARCHIVE_URL, params=params, timeout=120)
                if r.status_code == 429:
                    time.sleep(30 * (attempt + 1))
                    continue
                r.raise_for_status()
                payload = r.json()
                break
            except Exception as e:
                log.warning("openmeteo_failed", state=st["name"], attempt=attempt, error=str(e))
                time.sleep(5 * (attempt + 1))
        if payload is None:
            continue
        df = pd.DataFrame(payload.get("daily", {}))
        if "time" not in df:
            continue
        df = df.rename(columns={"time": "Date"})
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.dropna(subset=[v for v in variables if v in df.columns], how="all")
        if old is not None and start != "1990-01-01":
            df = pd.concat([old, df]).drop_duplicates("Date", keep="last").sort_values("Date")
        df.to_csv(out, index=False)
        n += 1
        log.info("openmeteo_state_ok", state=st["name"], rows=len(df), last=str(df["Date"].max().date()))
        time.sleep(1.0)
    build_meteo_interim(out_dir)
    return f"{n}/{len(states)} states"


def build_meteo_interim(raw_dir: Path) -> Path:
    frames = []
    for f in sorted(Path(raw_dir).glob("meteo_*.csv")):
        state = f.stem.removeprefix("meteo_").lower()
        df = pd.read_csv(f, parse_dates=["Date"])
        frames.append(df.set_index("Date").add_prefix(f"wx_{state}_"))
    meteo = pd.concat(frames, axis=1).sort_index().reset_index()
    path = INTERIM_DIR / "meteo.parquet"
    meteo.to_parquet(path, index=False)
    log.info("meteo_interim_saved", states=len(frames), rows=len(meteo), last=str(meteo["Date"].max().date()))
    return path
