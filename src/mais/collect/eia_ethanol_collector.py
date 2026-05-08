"""EIA Ethanol weekly collector.

~40% of US corn goes to ethanol. Key series (EIA weekly):
  WGFRPUS2 = fuel ethanol production (thousand barrels/day)
  WGTSTUS1 = fuel ethanol stocks (thousand barrels)

API
---
Free key at https://www.eia.gov/opendata/register.php (env: EIA_API_KEY).
Falls back to the EIA public DEMO_KEY (rate-limited but functional for
one-time historical pulls via the /v2/seriesid/ backward-compat endpoint).

Output
------
data/interim/eia_ethanol.parquet
Columns: Date, ethanol_production_kbd, ethanol_stocks_kbbl,
         ethanol_production_4w_avg, ethanol_stocks_4w_avg,
         ethanol_supply_tightness (weeks of supply)
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from mais.utils import get_logger, write_parquet

log = get_logger("mais.collect.eia")

# EIA backward-compat V2 endpoint (works without paid key via DEMO_KEY)
EIA_V2_SERIESID = "https://api.eia.gov/v2/seriesid/{sid}"

SERIES_MAP = {
    "WGFRPUS2": "ethanol_production_kbd",
    "WGTSTUS1": "ethanol_stocks_kbbl",
}
DEMO_KEY = "DEMO_KEY"
PAGE_SIZE = 5000


def _fetch_series(sid: str, api_key: str) -> pd.Series | None:
    try:
        import requests
    except ImportError:
        raise NotImplementedError("requests not installed")

    url = EIA_V2_SERIESID.format(sid=sid)
    frames = []
    offset = 0

    while True:
        params = {
            "api_key": api_key,
            "length": PAGE_SIZE,
            "offset": offset,
        }
        try:
            r = requests.get(url, params=params, timeout=60)
            r.raise_for_status()
            payload = r.json().get("response", {})
        except Exception as e:
            log.warning("eia_request_failed", sid=sid, error=str(e))
            return None

        data = payload.get("data", [])
        if not data:
            break

        df_page = pd.DataFrame(data)
        frames.append(df_page)

        total = int(payload.get("total", 0))
        offset += len(data)
        if offset >= total:
            break

    if not frames:
        log.warning("eia_empty", sid=sid)
        return None

    df = pd.concat(frames, ignore_index=True)

    # The backward-compat endpoint puts the date in 'period' and value in 'value'
    date_col = next((c for c in ("period", "date", "Period") if c in df.columns), None)
    val_col = next((c for c in ("value", "Value") if c in df.columns), None)
    if not date_col or not val_col:
        log.warning("eia_missing_cols", sid=sid, cols=list(df.columns))
        return None

    df["Date"] = pd.to_datetime(df[date_col], errors="coerce")
    df["val"] = pd.to_numeric(df[val_col], errors="coerce")
    out = (
        df.dropna(subset=["Date", "val"])
        .set_index("Date")["val"]
        .sort_index()
    )
    out = out[~out.index.duplicated(keep="last")]
    log.info("eia_series_ok", sid=sid, n=len(out),
             start=str(out.index.min().date()), end=str(out.index.max().date()))
    return out


def download(out_dir: Path, src: dict | None = None) -> str:
    src = src or {}
    api_key = os.environ.get(src.get("api_key_env", "EIA_API_KEY"), "") or DEMO_KEY
    series_ids = src.get("series") or list(SERIES_MAP.keys())

    frames: dict[str, pd.Series] = {}
    for sid in series_ids:
        name = SERIES_MAP.get(sid, sid.lower())
        s = _fetch_series(sid, api_key)
        if s is not None:
            frames[name] = s

    if not frames:
        raise RuntimeError(
            "EIA returned no data. Set EIA_API_KEY (free at eia.gov/opendata) "
            "or ensure network access to api.eia.gov."
        )

    df = (
        pd.DataFrame(frames)
        .reset_index()
        .rename(columns={"index": "Date"})
        .sort_values("Date")
        .drop_duplicates("Date")
        .reset_index(drop=True)
    )
    df["Date"] = pd.to_datetime(df["Date"])

    # Rolling aggregates and supply tightness
    for col in ["ethanol_production_kbd", "ethanol_stocks_kbbl"]:
        if col in df.columns:
            df[f"{col}_4w_avg"] = df[col].rolling(4, min_periods=2).mean()

    if "ethanol_production_kbd" in df.columns and "ethanol_stocks_kbbl" in df.columns:
        prod_4w = df.get("ethanol_production_kbd_4w_avg", df["ethanol_production_kbd"])
        stocks = df["ethanol_stocks_kbbl"]
        df["ethanol_supply_tightness"] = stocks / (prod_4w * 7).replace(0, float("nan"))

    out = Path(out_dir) / "eia_ethanol.parquet"
    write_parquet(df, out)
    log.info("eia_saved", rows=len(df), cols=df.shape[1], out=str(out))
    return f"{len(df)} weekly rows, {df.shape[1]} columns"
