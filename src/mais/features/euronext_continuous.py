"""Continuous Euronext EMA futures series.

Raw series keep actual observed prices. Adjusted series are only for returns
and technical features; they must not be shown as farmer-facing prices.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from mais.collect.euronext_contracts_daily import normalise_contract_daily_frame
from mais.paths import (
    EMA_CONTRACT_DAILY,
    EMA_CURVE_DAILY,
    EMA_FRONT_ADJUSTED,
    EMA_FRONT_RAW,
    EMA_HARVEST_NOV,
    EMA_LIQUID_ADJUSTED,
    EMA_LIQUID_RAW,
    EMA_MOST_LIQUID,
)

PRICE_CANDIDATES = ("settlement", "close_or_last", "close", "last")


def build_curve_daily(contracts: pd.DataFrame) -> pd.DataFrame:
    """Build the daily curve table with expiry and liquidity ranks."""
    work = _prepare_contracts(contracts)
    work = work[work["price"].notna() & work["import_verdict"].eq("usable")].copy()
    if work.empty:
        return _empty_curve()

    work = work.sort_values(["date", "days_to_expiry", "contract_code"]).reset_index(drop=True)
    work["rank_by_expiry"] = work.groupby("date")["days_to_expiry"].rank(method="first").astype(int)
    oi_rank_value = work["open_interest"].fillna(-1)
    vol_rank_value = work["volume"].fillna(-1)
    work["_liquidity_sort"] = oi_rank_value * 1_000_000 + vol_rank_value
    work["rank_by_oi"] = (
        work.groupby("date")["_liquidity_sort"].rank(method="first", ascending=False).astype(int)
    )
    cols = [
        "date",
        "contract_code",
        "source_symbol",
        "source",
        "source_quality",
        "rank_by_expiry",
        "rank_by_oi",
        "price",
        "settlement",
        "close_or_last",
        "volume",
        "open_interest",
        "days_to_expiry",
        "expiry_date",
        "month_code",
        "contract_year",
    ]
    return work[cols].sort_values(["date", "rank_by_expiry"]).reset_index(drop=True)


def build_front_continuous(contracts: pd.DataFrame, min_dte: int = 15) -> pd.DataFrame:
    """Build front raw series from the nearest admissible contract."""
    curve = build_curve_daily(contracts)
    eligible = curve[(curve["days_to_expiry"] >= min_dte) & curve["price"].notna()].copy()
    if eligible.empty:
        return _empty_series()
    selected = (
        eligible.sort_values(["date", "days_to_expiry", "rank_by_expiry"])
        .groupby("date", as_index=False)
        .first()
    )
    return _add_roll_columns(selected, curve, series_name="front_raw")


def build_front_adjusted(front_raw: pd.DataFrame) -> pd.DataFrame:
    """Back-adjust front raw series for return/features use only."""
    return build_back_adjusted(front_raw, series_name="front_adjusted")


def build_liquid_continuous(
    contracts: pd.DataFrame,
    min_dte: int = 15,
    max_dte: int = 370,
) -> pd.DataFrame:
    """Build most-liquid raw series within a DTE window."""
    curve = build_curve_daily(contracts)
    eligible = curve[
        (curve["days_to_expiry"] >= min_dte)
        & (curve["days_to_expiry"] <= max_dte)
        & curve["price"].notna()
    ].copy()
    if eligible.empty:
        return _empty_series()
    eligible["liquidity_rank_source"] = np.where(
        eligible.groupby("date")["open_interest"].transform(lambda s: s.notna().any()),
        "open_interest",
        "volume",
    )
    eligible["_sort_liquidity"] = np.where(
        eligible["liquidity_rank_source"].eq("open_interest"),
        eligible["open_interest"].fillna(-1),
        eligible["volume"].fillna(-1),
    )
    selected = (
        eligible.sort_values(["date", "_sort_liquidity", "volume"], ascending=[True, False, False])
        .groupby("date", as_index=False)
        .first()
        .drop(columns=["_sort_liquidity"])
    )
    out = _add_roll_columns(selected, curve, series_name="liquid_raw")
    return out.merge(
        selected[["date", "contract_code", "liquidity_rank_source"]],
        on=["date", "contract_code"],
        how="left",
    )


def build_harvest_november(contracts: pd.DataFrame) -> pd.DataFrame:
    """Build the raw November harvest contract series, never adjusted."""
    curve = build_curve_daily(contracts)
    nov = curve[curve["month_code"].eq("X")].copy()
    if nov.empty:
        return _empty_series(series_name="harvest_nov")

    rows: list[pd.Series] = []
    for current_date, group in nov.groupby("date", sort=True):
        year = int(pd.Timestamp(current_date).year)
        same_year_code = f"EMA_X{year}"
        next_year_code = f"EMA_X{year + 1}"
        same_year = group[group["contract_code"].eq(same_year_code)]
        chosen: pd.DataFrame
        if not same_year.empty:
            expiry = pd.to_datetime(same_year.iloc[0]["expiry_date"])
            use_next = pd.Timestamp(current_date) >= expiry - pd.Timedelta(days=5)
            chosen = group[group["contract_code"].eq(next_year_code)] if use_next else same_year
        else:
            chosen = group[group["contract_code"].eq(next_year_code)]
        if not chosen.empty:
            rows.append(chosen.iloc[0])
    if not rows:
        return _empty_series(series_name="harvest_nov")
    selected = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    return _add_roll_columns(selected, curve, series_name="harvest_nov")


def build_back_adjusted(raw_series: pd.DataFrame, *, series_name: str = "adjusted") -> pd.DataFrame:
    """Back-adjust a raw series by subtracting cumulative roll gaps."""
    if raw_series.empty:
        return raw_series.copy()
    adjusted = raw_series.copy().sort_values("date").reset_index(drop=True)
    adjusted["cum_roll_adjustment"] = adjusted["roll_adjustment"].fillna(0.0).cumsum()
    adjusted["adjusted_price"] = adjusted["price"].astype(float) - adjusted["cum_roll_adjustment"]
    adjusted["series_name"] = series_name
    return adjusted


def extract_roll_log(series: pd.DataFrame) -> pd.DataFrame:
    """Extract roll events from a continuous series."""
    if series.empty or "roll_event" not in series.columns:
        return pd.DataFrame(
            columns=["date", "old_contract", "new_contract", "price_old", "price_new", "roll_gap_eur_t"]
        )
    rolls = series[series["roll_event"].astype(bool)].copy()
    if rolls.empty:
        return pd.DataFrame(
            columns=["date", "old_contract", "new_contract", "price_old", "price_new", "roll_gap_eur_t"]
        )
    return rolls.rename(
        columns={
            "prev_contract_code": "old_contract",
            "contract_code": "new_contract",
            "roll_price_old": "price_old",
            "price": "price_new",
            "roll_adjustment": "roll_gap_eur_t",
        }
    )[["date", "old_contract", "new_contract", "price_old", "price_new", "roll_gap_eur_t"]]


def build_and_save_continuous_series(
    contracts: pd.DataFrame | None = None,
    *,
    contract_path: Path = EMA_CONTRACT_DAILY,
) -> dict[str, int]:
    """Build and save all DATA-EMA-03 processed outputs."""
    source = pd.read_parquet(contract_path) if contracts is None else contracts
    curve = build_curve_daily(source)
    front_raw = build_front_continuous(source)
    front_adjusted = build_front_adjusted(front_raw)
    liquid_raw = build_liquid_continuous(source)
    liquid_adjusted = build_back_adjusted(liquid_raw, series_name="liquid_adjusted")
    harvest_nov = build_harvest_november(source)

    outputs = {
        EMA_CURVE_DAILY: curve,
        EMA_FRONT_RAW: front_raw,
        EMA_FRONT_ADJUSTED: front_adjusted,
        EMA_LIQUID_RAW: liquid_raw,
        EMA_LIQUID_ADJUSTED: liquid_adjusted,
        EMA_MOST_LIQUID: liquid_raw,
        EMA_HARVEST_NOV: harvest_nov,
    }
    for path, frame in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(path, index=False)
    return {path.name: int(len(frame)) for path, frame in outputs.items()}


def load_continuous_feature_block(dates: pd.Series | pd.DatetimeIndex) -> pd.DataFrame:
    """Load EMA continuous features for ``build_features()`` when available."""
    base = pd.DataFrame({"Date": pd.to_datetime(pd.Series(dates).unique())}).sort_values("Date")
    blocks: list[pd.DataFrame] = [base]
    for path, prefix in (
        (EMA_FRONT_ADJUSTED, "ema_front"),
        (EMA_LIQUID_ADJUSTED, "ema_liquid"),
        (EMA_HARVEST_NOV, "ema_harvest_nov"),
    ):
        if not path.exists():
            continue
        frame = pd.read_parquet(path)
        if frame.empty:
            continue
        price_col = "adjusted_price" if "adjusted_price" in frame.columns else "price"
        work = frame[["date", price_col]].rename(columns={price_col: "feature_price"}).copy()
        work["Date"] = pd.to_datetime(work["date"])
        price = pd.to_numeric(work["feature_price"], errors="coerce")
        work[f"{prefix}_price_lag1"] = price.shift(1)
        work[f"{prefix}_return_5d_lag1"] = np.log(
            price
            / price.shift(5)
        ).shift(1)
        blocks.append(work[["Date", f"{prefix}_price_lag1", f"{prefix}_return_5d_lag1"]])
    merged = blocks[0]
    for block in blocks[1:]:
        merged = merged.merge(block, on="Date", how="left")
    return merged.sort_values("Date").reset_index(drop=True)


def _prepare_contracts(contracts: pd.DataFrame) -> pd.DataFrame:
    required = {"contract_code"}
    missing = required - set(contracts.columns)
    if missing:
        raise ValueError(f"Missing EMA contract columns: {sorted(missing)}")
    work = normalise_contract_daily_frame(contracts)
    if "date" not in work.columns and "Date" in work.columns:
        work["date"] = work["Date"]
    if "date" not in work.columns:
        raise ValueError("EMA contracts require a date column")
    work["date"] = pd.to_datetime(work["date"]).dt.normalize()
    for col in PRICE_CANDIDATES:
        if col not in work.columns:
            work[col] = np.nan
    price = pd.Series(np.nan, index=work.index, dtype=float)
    for col in PRICE_CANDIDATES:
        price = price.fillna(pd.to_numeric(work[col], errors="coerce"))
    work["price"] = price
    if "close_or_last" not in work.columns:
        work["close_or_last"] = work["price"]
    if "source" not in work.columns:
        work["source"] = "unknown"
    if "source_quality" not in work.columns:
        work["source_quality"] = np.where(
            work["source"].astype(str).eq("barchart_proxy_exploratory"),
            "exploratory",
            "official_or_manual",
        )
    if "import_verdict" not in work.columns:
        work["import_verdict"] = "usable"
    if "source_symbol" not in work.columns:
        work["source_symbol"] = work["contract_code"]
    if "days_to_expiry" not in work.columns:
        if "expiry_date" in work.columns:
            expiry = pd.to_datetime(work["expiry_date"], errors="coerce")
            work["days_to_expiry"] = (expiry - work["date"]).dt.days
        else:
            work["days_to_expiry"] = np.nan
    if "open_interest" not in work.columns:
        work["open_interest"] = np.nan
    if "volume" not in work.columns:
        work["volume"] = np.nan
    if "month_code" not in work.columns:
        work["month_code"] = work["contract_code"].astype(str).str.split("_", n=1).str[1].str[0]
    if "contract_year" not in work.columns:
        work["contract_year"] = work["contract_code"].astype(str).str[-4:].astype(int)
    return work


def _add_roll_columns(selected: pd.DataFrame, curve: pd.DataFrame, *, series_name: str) -> pd.DataFrame:
    out = selected.copy().sort_values("date").reset_index(drop=True)
    out["prev_contract_code"] = out["contract_code"].shift(1)
    out["roll_event"] = out["contract_code"].ne(out["prev_contract_code"])
    out.loc[out.index[0], "roll_event"] = False
    out["roll_price_old"] = np.nan
    out["roll_adjustment"] = 0.0
    for idx, row in out[out["roll_event"]].iterrows():
        prev_contract = row["prev_contract_code"]
        same_day_old = curve[
            curve["date"].eq(row["date"]) & curve["contract_code"].eq(prev_contract)
        ]
        if same_day_old.empty:
            old_price = out.loc[idx - 1, "price"] if idx > 0 else np.nan
        else:
            old_price = same_day_old.iloc[0]["price"]
        out.loc[idx, "roll_price_old"] = old_price
        out.loc[idx, "roll_adjustment"] = float(row["price"]) - float(old_price)
    out["series_name"] = series_name
    return out[
        [
            "date",
            "series_name",
            "price",
            "contract_code",
            "source_symbol",
            "source",
            "source_quality",
            "days_to_expiry",
            "volume",
            "open_interest",
            "roll_event",
            "prev_contract_code",
            "roll_price_old",
            "roll_adjustment",
        ]
    ].reset_index(drop=True)


def _empty_curve() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "date",
            "contract_code",
            "source_symbol",
            "source",
            "source_quality",
            "rank_by_expiry",
            "rank_by_oi",
            "price",
            "settlement",
            "close_or_last",
            "volume",
            "open_interest",
            "days_to_expiry",
            "expiry_date",
            "month_code",
            "contract_year",
        ]
    )


def _empty_series(series_name: str = "") -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "date",
            "series_name",
            "price",
            "contract_code",
            "source_symbol",
            "source",
            "source_quality",
            "days_to_expiry",
            "volume",
            "open_interest",
            "roll_event",
            "prev_contract_code",
            "roll_price_old",
            "roll_adjustment",
        ]
    ).assign(series_name=series_name)
