"""EIA Ethanol weekly collector — EIA API v2 (faceted endpoints).

~40% of US corn production goes to ethanol. EIA publishes weekly (Wednesday 10:30 ET):
  * ethanol_production_kbd — Fuel Ethanol oxygenate plant production (MBBL/D)
  * ethanol_stocks_kbbl   — Fuel Ethanol ending stocks (MBBL)

API v2 endpoints used:
  Production: GET /v2/petroleum/pnp/wprode/data/  facets: duoarea=NUS, product=EPOOXE
  Stocks:     GET /v2/petroleum/stoc/wstk/data/   facets: duoarea=NUS, product=EPOOXE

Free key: https://www.eia.gov/opendata/register.php
Set EIA_API_KEY environment variable.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from mais.paths import INTERIM_DIR
from mais.utils import get_logger, write_parquet

log = get_logger("mais.collect.eia")

_SERIES = [
    {
        "path": "petroleum/pnp/wprode/data/",
        "col": "ethanol_production_kbd",
        "facets": "facets[duoarea][]=NUS&facets[product][]=EPOOXE",
    },
    {
        "path": "petroleum/stoc/wstk/data/",
        "col": "ethanol_stocks_kbbl",
        "facets": "facets[duoarea][]=NUS&facets[product][]=EPOOXE",
    },
]
_BASE = "https://api.eia.gov/v2"
_PAGE = 5000


def _fetch_series(api_key: str, path: str, facets: str) -> pd.DataFrame:
    try:
        import requests
    except ImportError as e:
        raise NotImplementedError("requests not installed") from e

    params = (
        f"api_key={api_key}&frequency=weekly&data[]=value"
        f"&{facets}&length={_PAGE}"
        "&sort[0][column]=period&sort[0][direction]=asc"
    )
    url = f"{_BASE}/{path}?{params}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    data = r.json().get("response", {}).get("data", [])
    if not data:
        return pd.DataFrame(columns=["Date", "value"])
    df = pd.DataFrame(data)[["period", "value"]].rename(columns={"period": "Date"})
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)


def download(out_dir: Path, src: dict) -> str:
    api_key = os.environ.get(src.get("api_key_env", "EIA_API_KEY"))
    if not api_key:
        raise NotImplementedError(
            "Set EIA_API_KEY (free at https://www.eia.gov/opendata/register.php)"
        )

    frames: list[pd.DataFrame] = []
    for spec in _SERIES:
        df = _fetch_series(api_key, spec["path"], spec["facets"])
        df = df.rename(columns={"value": spec["col"]})
        frames.append(df.set_index("Date"))
        log.info("eia_series_ok", col=spec["col"], n=len(df))

    if not frames:
        raise RuntimeError("EIA returned no data")

    weekly = pd.concat(frames, axis=1).reset_index()
    weekly = weekly.sort_values("Date").drop_duplicates(subset=["Date"], keep="last")

    raw_out = out_dir / "eia_ethanol.csv"
    weekly.to_csv(raw_out, index=False)

    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    interim_path = INTERIM_DIR / "eia_ethanol.parquet"
    write_parquet(weekly, interim_path)
    log.info("eia_ethanol_saved", rows=len(weekly), raw=str(raw_out), interim=str(interim_path))
    return f"{len(weekly)} weekly rows → {interim_path.name}"
