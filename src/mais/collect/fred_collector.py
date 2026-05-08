"""FRED collector via the official ``fredapi`` package."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.collect.fred")


def download(out_dir: Path, src: dict) -> str:
    try:
        from fredapi import Fred
    except ImportError as e:
        raise NotImplementedError("fredapi not installed - `pip install fredapi`") from e

    api_key_env = src.get("api_key_env", "FRED_API_KEY")
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise NotImplementedError(
            f"Set ${api_key_env} (free key at https://fred.stlouisfed.org/docs/api/api_key.html)"
        )
    fred = Fred(api_key=api_key)
    series_ids = src.get("series", [])
    rows = {}
    for sid in series_ids:
        try:
            s = fred.get_series(sid)
            rows[sid.lower()] = s
            log.info("fred_series_ok", sid=sid, n=len(s))
        except Exception as e:
            log.warning("fred_series_failed", sid=sid, error=str(e))
    if not rows:
        raise RuntimeError("FRED returned no series")
    df = pd.concat(rows, axis=1)
    df.index.name = "Date"
    df = df.reset_index()
    out = out_dir / "fred_macro.csv"
    df.to_csv(out, index=False)
    return f"{len(rows)} series, {len(df)} rows"
