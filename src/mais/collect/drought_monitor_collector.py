"""US Drought Monitor weekly collector (V3-06).

Public, no API key. Weekly D0-D4 corn area statistics from USDM API.
Endpoint: https://usdmdataservices.unl.edu/api/AgriculturalStatistics/GetCropImpactStateCorn
Returns corn-impacted area pct by drought level for CONUS.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.collect.drought")

BASE_URL = (
    "https://usdmdataservices.unl.edu/api/AgriculturalStatistics"
    "/GetCropImpactStateCorn"
    "?aoi=CONUS&startDate={start}&endDate={end}&statisticsType=1&format=json"
)


def _fetch_usdm(start_date: str, end_date: str, timeout: int = 30) -> list[dict]:
    url = BASE_URL.format(start=start_date, end=end_date)
    log.info("drought_fetch_start", url=url[:80])
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def _parse_records(records: list[dict]) -> pd.DataFrame:
    rows = []
    for rec in records:
        date_str = rec.get("MapDate") or rec.get("mapDate") or rec.get("releaseDate") or ""
        if not date_str:
            continue
        rows.append({
            "Date": pd.to_datetime(date_str[:10]),
            "corn_area_d0": float(rec.get("D0", rec.get("d0", 0)) or 0),
            "corn_area_d1": float(rec.get("D1", rec.get("d1", 0)) or 0),
            "corn_area_d2": float(rec.get("D2", rec.get("d2", 0)) or 0),
            "corn_area_d3": float(rec.get("D3", rec.get("d3", 0)) or 0),
            "corn_area_d4": float(rec.get("D4", rec.get("d4", 0)) or 0),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values("Date").drop_duplicates(subset=["Date"], keep="last").reset_index(drop=True)


def download(out_dir: Path, src: dict, *, start_year: int = 2000) -> str:
    """Download USDM corn area data and save to out_dir/drought_monitor.parquet."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "drought_monitor.parquet"

    end_date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    start_date = f"{start_year}-01-01"

    try:
        records = _fetch_usdm(start_date, end_date)
        df = _parse_records(records)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        log.warning("drought_fetch_failed", error=str(exc))
        if out_path.exists():
            log.info("drought_using_cached", path=str(out_path))
            return str(out_path)
        raise RuntimeError("USDM fetch failed and no cached file available") from exc

    if df.empty:
        log.warning("drought_empty_response")
        if out_path.exists():
            return str(out_path)
        df = pd.DataFrame(columns=["Date", "corn_area_d0", "corn_area_d1", "corn_area_d2", "corn_area_d3", "corn_area_d4"])

    df.to_parquet(out_path, index=False)
    log.info("drought_saved", path=str(out_path), rows=len(df))
    return str(out_path)


def build_drought_features(drought_df: pd.DataFrame) -> pd.DataFrame:
    """Build granular drought features from raw D0-D4 area data.

    Produces:
    - drought_d2plus: weighted D2+D3+D4 pct (severity-weighted)
    - drought_change_4w: change in drought_d2plus over 4 weeks (~26 days)
    - drought_extreme_flag: 1 if D3+D4 > 10% of corn area
    """
    df = drought_df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)

    for col in ("corn_area_d2", "corn_area_d3", "corn_area_d4"):
        if col not in df.columns:
            df[col] = 0.0

    df["drought_d2plus"] = (
        0.5 * pd.to_numeric(df["corn_area_d2"], errors="coerce").fillna(0)
        + 0.75 * pd.to_numeric(df["corn_area_d3"], errors="coerce").fillna(0)
        + 1.0 * pd.to_numeric(df["corn_area_d4"], errors="coerce").fillna(0)
    )
    df["drought_change_4w"] = df["drought_d2plus"].diff(4)
    d3 = pd.to_numeric(df.get("corn_area_d3", 0), errors="coerce").fillna(0)
    d4 = pd.to_numeric(df.get("corn_area_d4", 0), errors="coerce").fillna(0)
    df["drought_extreme_flag"] = ((d3 + d4) > 10.0).astype(float)

    return df[["Date", "drought_d2plus", "drought_change_4w", "drought_extreme_flag"]]
