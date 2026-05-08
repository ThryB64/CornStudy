"""USDA NASS QuickStats collector (Phase 1 NEW).

Free API, key required: https://quickstats.nass.usda.gov/api
Set NASS_API_KEY environment variable.

Used for:
  - Crop Progress (weekly, planted/emerged/silking/dough/dented/mature/harvested pct)
  - Crop Condition (weekly, very poor / poor / fair / good / excellent pct)
  - State-level yield (monthly)
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.collect.nass")

API_URL = "https://quickstats.nass.usda.gov/api/api_GET/"


def download(out_dir: Path, src: dict) -> str:
    try:
        import requests
    except ImportError as e:
        raise NotImplementedError("requests not installed") from e

    api_key = os.environ.get(src.get("api_key_env", "NASS_API_KEY"))
    if not api_key:
        raise NotImplementedError(
            "Set NASS_API_KEY (free key at https://quickstats.nass.usda.gov/api)"
        )
    params = {
        "key": api_key,
        "source_desc": src.get("program", "SURVEY"),
        "sector_desc": src.get("sector", "CROPS"),
        "group_desc":  src.get("group", "FIELD CROPS"),
        "commodity_desc": src.get("commodity", "CORN"),
        "statisticcat_desc": src.get("statisticcat", "PROGRESS"),
        "agg_level_desc": "NATIONAL",
        "format": "JSON",
    }
    try:
        r = requests.get(API_URL, params=params, timeout=120)
        r.raise_for_status()
        data = r.json().get("data", [])
    except Exception as e:
        raise RuntimeError(f"NASS request failed: {e}") from e
    if not data:
        raise RuntimeError("NASS returned no data")
    df = pd.DataFrame(data)
    out = out_dir / f"nass_{src['name']}.csv"
    df.to_csv(out, index=False)
    return f"{len(df)} rows"
