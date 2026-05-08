"""Synthetic USDA report calendar (Phase 1 NEW).

No download - we generate the table locally from the cadence rules in
sources.yaml. Outputs binary indicators and days_to/since for each
report type. These features capture the well-documented event-day
risk premium around WASDE / Grain Stocks / Acreage.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.collect.calendar")


def _wasde_dates(start: pd.Timestamp, end: pd.Timestamp) -> list[pd.Timestamp]:
    """WASDE is published around the 8-12th of each month at 12:00 ET.
    We approximate by the 10th of each month between start and end."""
    months = pd.date_range(start, end, freq="MS")
    return [m + pd.Timedelta(days=9) for m in months]  # 10th of month


def _quarterly_grain_stocks(start: pd.Timestamp, end: pd.Timestamp) -> list[pd.Timestamp]:
    """Released ~end of Mar / Jun / Sep / Dec (NASS Grain Stocks)."""
    out = []
    for y in range(start.year, end.year + 1):
        for m, d in [(3, 30), (6, 30), (9, 30), (12, 22)]:
            try:
                out.append(pd.Timestamp(year=y, month=m, day=d))
            except Exception:
                pass
    return [d for d in out if start <= d <= end]


def _annual_acreage(start: pd.Timestamp, end: pd.Timestamp) -> list[pd.Timestamp]:
    """Acreage report - last day of June each year."""
    return [pd.Timestamp(year=y, month=6, day=30) for y in range(start.year, end.year + 1)]


def download(out_dir: Path, src: dict) -> str:
    start = pd.Timestamp("2000-01-01")
    end = pd.Timestamp.utcnow().normalize()
    daily_index = pd.bdate_range(start, end)
    df = pd.DataFrame({"Date": daily_index})

    wasde = _wasde_dates(start, end)
    df["is_wasde_day"] = df["Date"].isin(wasde).astype(int)
    df["days_to_next_wasde"] = _days_to_next(df["Date"], wasde)
    df["days_since_last_wasde"] = _days_since_last(df["Date"], wasde)

    gs = _quarterly_grain_stocks(start, end)
    df["is_grain_stocks_day"] = df["Date"].isin(gs).astype(int)
    df["days_to_next_grain_stocks"] = _days_to_next(df["Date"], gs)

    acr = _annual_acreage(start, end)
    df["is_acreage_day"] = df["Date"].isin(acr).astype(int)
    df["days_to_next_acreage"] = _days_to_next(df["Date"], acr)

    out = out_dir / "usda_calendar.csv"
    df.to_csv(out, index=False)
    return f"{len(df)} rows"


def _days_to_next(dates: pd.Series, events: list[pd.Timestamp]) -> pd.Series:
    events = sorted(events)
    out = []
    for d in dates:
        nxt = next((e for e in events if e >= d), None)
        out.append((nxt - d).days if nxt is not None else 365)
    return pd.Series(out, index=dates.index)


def _days_since_last(dates: pd.Series, events: list[pd.Timestamp]) -> pd.Series:
    events = sorted(events)
    out = []
    for d in dates:
        prev = None
        for e in events:
            if e <= d:
                prev = e
            else:
                break
        out.append((d - prev).days if prev is not None else 365)
    return pd.Series(out, index=dates.index)
