"""NOAA CPC Oceanic Nino Index collector."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.collect.enso")

ONI_URL = "https://origin.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php"
SEASONS = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]


class CollectorError(RuntimeError):
    """Raised when the NOAA page format is not parseable."""


class DataQualityError(RuntimeError):
    """Raised when parsed ONI coverage is insufficient."""


def parse_oni_table(html_or_tables: str | list[pd.DataFrame]) -> pd.DataFrame:
    """Parse the NOAA ONI seasonal table into monthly rows."""
    tables = pd.read_html(html_or_tables) if isinstance(html_or_tables, str) else html_or_tables
    table = _find_oni_table(tables)
    if table is None:
        raise CollectorError("ENSO NOAA format changed: ONI table not found")

    work = table.copy()
    work.columns = [str(col).strip().upper() for col in work.columns]
    year_col = next((col for col in work.columns if col in {"YR", "YEAR"}), None)
    if year_col is None or not set(SEASONS).issubset(work.columns):
        raise CollectorError("ENSO NOAA format changed: missing Year/season columns")

    rows = []
    for _, row in work.iterrows():
        year = pd.to_numeric(row[year_col], errors="coerce")
        if pd.isna(year):
            continue
        for month, season in enumerate(SEASONS, start=1):
            value = pd.to_numeric(row[season], errors="coerce")
            if pd.notna(value):
                rows.append({"Date": pd.Timestamp(int(year), month, 1), "enso_oni_index": float(value)})
    out = pd.DataFrame(rows).sort_values("Date").drop_duplicates("Date").reset_index(drop=True)
    if out.empty:
        raise CollectorError("ENSO NOAA format changed: parsed table is empty")
    return out


def validate_oni_coverage(df: pd.DataFrame, start: str = "2010-01-01", end: str = "2022-12-31") -> None:
    """Require at least 90% monthly ONI coverage over the R&D period."""
    work = df.copy()
    work["Date"] = pd.to_datetime(work["Date"])
    months = pd.date_range(start, end, freq="MS")
    covered = work.set_index("Date").reindex(months)["enso_oni_index"].notna().mean()
    if covered < 0.90:
        raise DataQualityError(f"ENSO ONI coverage too low: {covered:.1%}")


def build_enso_features(monthly_oni: pd.DataFrame, out_dates: pd.Series | pd.DatetimeIndex) -> pd.DataFrame:
    """Map monthly ONI observations to daily feature rows with shift(1)."""
    oni = monthly_oni.copy()
    oni["Date"] = pd.to_datetime(oni["Date"])
    oni = oni.sort_values("Date").drop_duplicates("Date")
    if oni["enso_oni_index"].notna().sum() == 0:
        raise DataQualityError("ENSO ONI series is entirely empty")

    oni["enso_regime"] = np.select(
        [oni["enso_oni_index"] >= 0.5, oni["enso_oni_index"] <= -0.5],
        [1.0, -1.0],
        default=0.0,
    )
    oni["enso_lag3_oni"] = oni["enso_oni_index"].shift(3)
    oni["enso_accumulated_6m"] = oni["enso_oni_index"].rolling(6, min_periods=1).sum()
    oni["enso_el_nino_flag"] = _phase_flag(oni["enso_oni_index"], sign=1)
    oni["enso_la_nina_flag"] = _phase_flag(oni["enso_oni_index"], sign=-1)

    base = pd.DataFrame({"Date": pd.to_datetime(pd.Series(out_dates).unique())}).sort_values("Date")
    merged = pd.merge_asof(base, oni, on="Date", direction="backward")
    feature_cols = [
        "enso_oni_index",
        "enso_regime",
        "enso_lag3_oni",
        "enso_accumulated_6m",
        "enso_el_nino_flag",
        "enso_la_nina_flag",
    ]
    out = merged[["Date"] + feature_cols].copy()
    out[feature_cols] = out[feature_cols].shift(1)
    return out


def download(out_dir: Path, src: dict | None = None) -> str:
    """Download NOAA ONI and save ``enso_oni.parquet``."""
    import requests

    url = (src or {}).get("url", ONI_URL)
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    parsed = parse_oni_table(response.text)
    validate_oni_coverage(parsed)
    out_dir.mkdir(parents=True, exist_ok=True)
    parsed.to_parquet(out_dir / "enso_oni.parquet", index=False)
    log.info("enso_oni_written", rows=len(parsed), path=str(out_dir / "enso_oni.parquet"))
    return f"{len(parsed)} monthly ONI rows"


def _find_oni_table(tables: list[pd.DataFrame]) -> pd.DataFrame | None:
    for table in tables:
        cols = {str(col).strip().upper() for col in table.columns}
        if ("YR" in cols or "YEAR" in cols) and set(SEASONS).issubset(cols):
            return table
    return None


def _phase_flag(series: pd.Series, *, sign: int) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    condition = values >= 0.5 if sign > 0 else values <= -0.5
    rolling = condition.rolling(5, min_periods=5).sum()
    return (rolling >= 5).astype(float)
