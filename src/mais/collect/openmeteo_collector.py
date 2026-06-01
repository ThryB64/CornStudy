"""Open-Meteo daily weather collector for the corn belt states.

Uses the free historical archive endpoint - no API key required.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

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
        params = {
            "latitude": st["lat"],
            "longitude": st["lon"],
            "start_date": "1990-01-01",
            "end_date": pd.Timestamp.utcnow().normalize().strftime("%Y-%m-%d"),
            "daily": ",".join(variables),
            "timezone": "auto",
        }
        try:
            r = requests.get(ARCHIVE_URL, params=params, timeout=120)
            r.raise_for_status()
            payload = r.json()
        except Exception as e:
            log.warning("openmeteo_failed", state=st["name"], error=str(e))
            continue
        df = pd.DataFrame(payload.get("daily", {}))
        if "time" not in df:
            continue
        df = df.rename(columns={"time": "Date"})
        df["Date"] = pd.to_datetime(df["Date"])
        out = out_dir / f"meteo_{st['name']}.csv"
        df.to_csv(out, index=False)
        n += 1
        log.info("openmeteo_state_ok", state=st["name"], rows=len(df))
    return f"{n}/{len(states)} states"
