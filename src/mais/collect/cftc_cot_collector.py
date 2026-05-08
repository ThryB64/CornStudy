"""CFTC Commitments of Traders — disaggregated futures-only (no API key needed).

Public data, released every Friday 15:30 ET for the position as of the preceding
Tuesday. Disaggregated report available from 2009 onwards.

Sources
-------
- Current file: https://www.cftc.gov/dea/newcot/f_disagg.txt
- History zips:  https://www.cftc.gov/files/dea/history/fut_disagg_txt_{YYYY}.zip

Corn code: 002602 (Corn No. 2 CBOT).

Columns kept (all from the ``_All`` sub-report, combined futures+options omitted):
    cot_open_interest
    cot_mm_long, cot_mm_short, cot_mm_net      # Managed Money (speculators)
    cot_pm_long, cot_pm_short, cot_pm_net      # Producer/Merchant (hedgers)
    cot_sd_long, cot_sd_short, cot_sd_net      # Swap Dealers
    cot_mm_long_pct, cot_mm_short_pct          # % of open interest
    cot_mm_net_pct_oi                          # net speculative pressure
    cot_pm_net_pct_oi
"""

from __future__ import annotations

import io
import time
import zipfile
from pathlib import Path

import pandas as pd

from mais.utils import get_logger, write_parquet

log = get_logger("mais.collect.cot")

CORN_CODE = "002602"
CURRENT_URL = "https://www.cftc.gov/dea/newcot/f_disagg.txt"
HISTORY_URL = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"
FIRST_YEAR = 2009
COT_COLS = {
    "Open_Interest_All":           "cot_open_interest",
    "M_Money_Positions_Long_All":  "cot_mm_long",
    "M_Money_Positions_Short_All": "cot_mm_short",
    "Prod_Merc_Positions_Long_All":  "cot_pm_long",
    "Prod_Merc_Positions_Short_All": "cot_pm_short",
    "Swap_Positions_Long_All":      "cot_sd_long",
    "Swap__Positions_Short_All":    "cot_sd_short",
}


def _fetch_zip_df(url: str) -> pd.DataFrame | None:
    try:
        import requests
        r = requests.get(url, timeout=60)
        r.raise_for_status()
    except Exception as e:
        log.warning("cot_fetch_failed", url=url, error=str(e))
        return None
    try:
        z = zipfile.ZipFile(io.BytesIO(r.content))
        name = z.namelist()[0]
        with z.open(name) as f:
            return pd.read_csv(f, encoding="latin-1", low_memory=False)
    except Exception as e:
        log.warning("cot_parse_failed", url=url, error=str(e))
        return None


def _fetch_txt_df(url: str) -> pd.DataFrame | None:
    try:
        import requests
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        return pd.read_csv(io.StringIO(r.text), encoding="latin-1", low_memory=False)
    except Exception as e:
        log.warning("cot_txt_failed", url=url, error=str(e))
        return None


def _filter_corn(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["CFTC_Contract_Market_Code"].astype(str).str.strip() == CORN_CODE
    return df[mask].copy()


def _extract(df: pd.DataFrame) -> pd.DataFrame:
    date_col = "Report_Date_as_YYYY-MM-DD"
    if date_col not in df.columns:
        return pd.DataFrame()
    keep = [date_col] + [c for c in COT_COLS if c in df.columns]
    out = df[keep].rename(columns={"Report_Date_as_YYYY-MM-DD": "Date", **COT_COLS})
    out["Date"] = pd.to_datetime(out["Date"], errors="coerce")
    for c in list(COT_COLS.values()):
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out.dropna(subset=["Date"])


def _add_derived(df: pd.DataFrame) -> pd.DataFrame:
    if "cot_mm_long" in df.columns and "cot_mm_short" in df.columns:
        df["cot_mm_net"] = df["cot_mm_long"] - df["cot_mm_short"]
    if "cot_pm_long" in df.columns and "cot_pm_short" in df.columns:
        df["cot_pm_net"] = df["cot_pm_long"] - df["cot_pm_short"]
    if "cot_sd_long" in df.columns and "cot_sd_short" in df.columns:
        df["cot_sd_net"] = df["cot_sd_long"] - df["cot_sd_short"]
    oi = df.get("cot_open_interest")
    if oi is not None and (oi > 0).any():
        safe_oi = oi.replace(0, float("nan"))
        if "cot_mm_long" in df.columns:
            df["cot_mm_long_pct"] = df["cot_mm_long"] / safe_oi
        if "cot_mm_short" in df.columns:
            df["cot_mm_short_pct"] = df["cot_mm_short"] / safe_oi
        if "cot_mm_net" in df.columns:
            df["cot_mm_net_pct_oi"] = df["cot_mm_net"] / safe_oi
        if "cot_pm_net" in df.columns:
            df["cot_pm_net_pct_oi"] = df["cot_pm_net"] / safe_oi
    return df


def download(out_dir: Path, src: dict | None = None) -> str:
    import datetime
    current_year = datetime.date.today().year
    frames = []

    # Download historical + current year zips (zip is available for completed years)
    # Try up to current_year inclusive; years without a zip are silently skipped.
    for year in range(FIRST_YEAR, current_year + 1):
        url = HISTORY_URL.format(year=year)
        df_raw = _fetch_zip_df(url)
        if df_raw is None:
            continue
        corn = _filter_corn(df_raw)
        if corn.empty:
            continue
        extracted = _extract(corn)
        if not extracted.empty:
            frames.append(extracted)
            log.info("cot_year_ok", year=year, n=len(extracted))
        time.sleep(0.3)

    if not frames:
        raise RuntimeError("CFTC COT: no data fetched")

    combined = (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates("Date")
        .sort_values("Date")
        .reset_index(drop=True)
    )
    combined = _add_derived(combined)

    out = Path(out_dir) / "cftc_cot.parquet"
    write_parquet(combined, out)
    log.info("cot_saved", rows=len(combined), cols=combined.shape[1], out=str(out))
    return f"{len(combined)} weekly rows, {combined.shape[1]} columns"
