"""USDA NASS QuickStats collector.

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

PROGRESS_COLUMNS = [
    "planted_pct",
    "emerged_pct",
    "silking_pct",
    "dough_pct",
    "dented_pct",
    "mature_pct",
    "harvested_pct",
    "condition_gd_ex_pct",
    "condition_poor_vp_pct",
    "progress_gap_5y",
]


def _parse_value(value: object) -> float:
    s = str(value).strip().replace(",", "")
    if not s or s in {"(D)", "(NA)", "NA", "nan"}:
        return float("nan")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def _metric_from_row(row: pd.Series) -> str | None:
    text = " ".join(
        str(row.get(c, ""))
        for c in ("short_desc", "domaincat_desc", "prodn_practice_desc", "class_desc")
    ).upper()
    metric_map = {
        "PLANTED": "planted_pct",
        "EMERGED": "emerged_pct",
        "SILKING": "silking_pct",
        "DOUGH": "dough_pct",
        "DENTED": "dented_pct",
        "MATURE": "mature_pct",
        "HARVESTED": "harvested_pct",
        "EXCELLENT": "condition_excellent_pct",
        "GOOD": "condition_good_pct",
        "VERY POOR": "condition_very_poor_pct",
        "POOR": "condition_poor_pct",
    }
    # Check the two-word condition first so VERY POOR is not classified as POOR.
    for key in ("VERY POOR", "EXCELLENT", "GOOD", "PLANTED", "EMERGED", "SILKING", "DOUGH", "DENTED", "MATURE", "HARVESTED", "POOR"):
        if key in text:
            return metric_map[key]
    return None


def _progress_gap_5y(out: pd.DataFrame) -> pd.Series:
    progress_cols = [
        c for c in ("planted_pct", "emerged_pct", "silking_pct", "dough_pct", "dented_pct", "mature_pct", "harvested_pct")
        if c in out.columns
    ]
    if not progress_cols:
        return pd.Series(float("nan"), index=out.index)
    progress_avg = out[progress_cols].mean(axis=1, skipna=True)
    iso_week = out["Date"].dt.isocalendar().week.astype(int)
    gap = pd.Series(float("nan"), index=out.index)
    for i, (week, val) in enumerate(zip(iso_week, progress_avg, strict=False)):
        hist = progress_avg.iloc[:i][iso_week.iloc[:i] == week].tail(5)
        if hist.notna().sum() >= 2 and pd.notna(val):
            gap.iloc[i] = val - hist.mean()
    return gap


def normalize_crop_progress(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize raw QuickStats crop progress/condition rows to weekly features."""
    if df.empty:
        return pd.DataFrame(columns=["Date", *PROGRESS_COLUMNS])

    work = df.copy()
    date_col = next((c for c in ("week_ending", "Week Ending", "reference_period_desc") if c in work.columns), None)
    if date_col is None:
        raise ValueError("NASS Crop Progress data has no week_ending column")
    work["Date"] = pd.to_datetime(work[date_col], errors="coerce")
    work["metric"] = work.apply(_metric_from_row, axis=1)
    value_col = "Value" if "Value" in work.columns else "value"
    work["value_num"] = work[value_col].map(_parse_value)
    work = work.dropna(subset=["Date", "metric"])
    if work.empty:
        return pd.DataFrame(columns=["Date", *PROGRESS_COLUMNS])

    pivot = (
        work.pivot_table(index="Date", columns="metric", values="value_num", aggfunc="mean")
        .sort_index()
        .reset_index()
    )
    if {"condition_good_pct", "condition_excellent_pct"}.issubset(pivot.columns):
        pivot["condition_gd_ex_pct"] = pivot["condition_good_pct"] + pivot["condition_excellent_pct"]
    if {"condition_poor_pct", "condition_very_poor_pct"}.issubset(pivot.columns):
        pivot["condition_poor_vp_pct"] = pivot["condition_poor_pct"] + pivot["condition_very_poor_pct"]
    pivot["progress_gap_5y"] = _progress_gap_5y(pivot)

    out = pivot[["Date"] + [c for c in PROGRESS_COLUMNS if c in pivot.columns]].copy()
    for c in PROGRESS_COLUMNS:
        if c not in out.columns:
            out[c] = float("nan")
    return out[["Date", *PROGRESS_COLUMNS]]


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
    requested = str(src.get("statisticcat", "PROGRESS")).upper()
    statisticcats = ["PROGRESS", "CONDITION"] if requested in {"PROGRESS", "CONDITION"} else [requested]
    frames = []
    for statisticcat in statisticcats:
        params = {
            "key": api_key,
            "source_desc": src.get("program", "SURVEY"),
            "sector_desc": src.get("sector", "CROPS"),
            "group_desc": src.get("group", "FIELD CROPS"),
            "commodity_desc": src.get("commodity", "CORN"),
            "statisticcat_desc": statisticcat,
            "agg_level_desc": "NATIONAL",
            "format": "JSON",
        }
        try:
            r = requests.get(API_URL, params=params, timeout=120)
            r.raise_for_status()
            data = r.json().get("data", [])
        except Exception as e:
            raise RuntimeError(f"NASS request failed ({statisticcat}): {e}") from e
        if data:
            frames.append(pd.DataFrame(data))
            log.info("nass_quickstats_ok", statisticcat=statisticcat, n=len(data))

    if not frames:
        raise RuntimeError("NASS returned no data")
    raw = pd.concat(frames, ignore_index=True)
    raw_out = out_dir / f"nass_{src['name']}.csv"
    raw.to_csv(raw_out, index=False)

    normalized = normalize_crop_progress(raw)
    normalized_out = out_dir / "crop_progress.parquet"
    normalized.to_parquet(normalized_out, index=False)
    return f"{len(raw)} raw rows, {len(normalized)} weekly rows"
