"""Source availability calendar for anti-leakage checks."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

import pandas as pd

SOURCE_AVAILABILITY: dict[str, dict[str, Any]] = {
    "euronext_settlement": {"lag_days": 1, "same_day_after": "18:00 CET"},
    "cbot_corn": {"lag_days": 1},
    "eurusd_rate": {"lag_days": 0},
    "cftc_cot": {"lag_days": 3, "publication_day": "friday"},
    "usda_wasde": {"lag_days": 0, "same_day_after": "18:00 ET", "frequency": "monthly"},
    "usda_fas_export_sales": {"lag_days": 0, "publication_day": "thursday"},
    "usda_nass_crop_progress": {"lag_days": 0, "publication_day": "monday"},
    "ec_mars_bulletin": {"lag_days": 30, "shift_months": 1},
    "agreste_france": {"lag_days": 7},
    "franceagrimer": {"lag_days": 30},
    "conab_brazil": {"lag_days": 30},
}


def is_available(source: str, publish_date: date | datetime, use_date: date | datetime) -> bool:
    """Return True if a source published at ``publish_date`` may be used at ``use_date``."""
    publish_dt = _as_datetime(publish_date)
    use_dt = _as_datetime(use_date)
    available_dt = first_available_datetime(source, publish_dt)
    return use_dt >= available_dt


def first_available_datetime(source: str, publish_date: date | datetime) -> datetime:
    """Return the first legal datetime at which the observation can be used."""
    rule = _rule(source)
    publish_dt = _as_datetime(publish_date)
    if "shift_months" in rule:
        shifted = pd.Timestamp(publish_dt) + pd.DateOffset(months=int(rule["shift_months"]))
        publish_dt = shifted.to_pydatetime()
    lag_days = int(rule.get("lag_days", 0))
    available_dt = publish_dt + timedelta(days=lag_days)
    same_day_after = rule.get("same_day_after")
    if lag_days == 0 and same_day_after:
        cutoff = _parse_time(str(same_day_after))
        available_dt = datetime.combine(publish_dt.date(), cutoff)
    return available_dt


def apply_availability_shift(
    df: pd.DataFrame,
    source: str,
    *,
    date_col: str = "Date",
) -> pd.DataFrame:
    """Move each row date to the first date where the observation is available."""
    if date_col not in df.columns:
        raise ValueError(f"Missing date column: {date_col}")
    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col]).map(
        lambda value: first_available_datetime(source, value.to_pydatetime()).date()
    )
    out[date_col] = pd.to_datetime(out[date_col])
    return out.sort_values(date_col).reset_index(drop=True)


def filter_available_as_of(
    df: pd.DataFrame,
    source: str,
    use_date: date | datetime,
    *,
    publish_date_col: str = "Date",
) -> pd.DataFrame:
    """Keep only rows that are legally available at ``use_date``."""
    if publish_date_col not in df.columns:
        raise ValueError(f"Missing publish date column: {publish_date_col}")
    mask = pd.to_datetime(df[publish_date_col]).map(
        lambda value: is_available(source, value.to_pydatetime(), use_date)
    )
    return df.loc[mask].copy()


def _rule(source: str) -> dict[str, Any]:
    if source not in SOURCE_AVAILABILITY:
        raise KeyError(f"Unknown availability source: {source}")
    return SOURCE_AVAILABILITY[source]


def _as_datetime(value: date | datetime) -> datetime:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    return datetime.combine(value, time.min)


def _parse_time(value: str) -> time:
    clock = value.split()[0]
    hour, minute = clock.split(":", 1)
    return time(int(hour), int(minute))


__all__ = [
    "SOURCE_AVAILABILITY",
    "apply_availability_shift",
    "filter_available_as_of",
    "first_available_datetime",
    "is_available",
]
