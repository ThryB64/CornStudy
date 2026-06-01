"""Euronext EMA curve and cross-market features."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import (
    EMA_CURVE_DAILY,
    EMA_CURVE_FEATURES,
    EMA_FRONT_ADJUSTED,
    EMA_FRONT_RAW,
    EMA_HARVEST_NOV,
    INTERIM_DIR,
    RAW_DIR,
)

BUSHEL_TO_TONNE = 39.3679
EMA_CURVE_FEATURE_COLUMNS = [
    "ema_front_price",
    "ema_second_price",
    "ema_third_price",
    "ema_harvest_nov_price",
    "ema_next_march_price",
    "ema_liquid_price",
    "ema_spread_f0_f1",
    "ema_spread_f1_f2",
    "ema_spread_f0_f2",
    "ema_spread_nov_mar",
    "ema_curve_slope_3",
    "ema_curve_slope_6",
    "ema_contango_flag",
    "ema_backwardation_flag",
    "ema_carry_front_second",
    "ema_roll_yield_ann",
    "ema_oi_total",
    "ema_volume_total",
    "ema_oi_concentration",
    "ema_liquidity_shift",
    "ema_open_interest_available",
    "ema_curve_contract_count",
    "cbot_eur_t",
    "ema_cbot_basis",
    "ema_cbot_basis_zscore_52w",
    "ema_cbot_rel_strength_20d",
    "ema_front_return_5d_adjusted",
    "ema_front_vol_20d_adjusted",
]


def build_curve_features(
    contracts: pd.DataFrame,
    front_raw: pd.DataFrame,
    harvest_nov: pd.DataFrame,
    cbot: pd.DataFrame,
    eurusd: pd.DataFrame,
    *,
    front_adjusted: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build lag-safe EMA curve features.

    The returned feature values are shifted by one row: the value attached to
    date t uses only market information observed no later than t-1.
    """
    curve = _prepare_curve(contracts)
    front = _series_price(front_raw, "ema_front_price")
    harvest = _series_price(harvest_nov, "ema_harvest_nov_price")
    dates = _base_dates([curve, front, harvest])
    raw = pd.DataFrame({"Date": dates})
    raw = raw.merge(front, on="Date", how="left")
    raw = raw.merge(harvest, on="Date", how="left")

    expiry_ranks = _rank_prices(curve, rank_col="rank_by_expiry")
    raw = raw.merge(expiry_ranks, on="Date", how="left")
    liquid = _rank_prices(curve, rank_col="rank_by_oi", ranks=(1,), prefix="liquid")
    raw = raw.merge(
        liquid[["Date", "liquid_first_price"]].rename(
            columns={"liquid_first_price": "ema_liquid_price"}
        ),
        on="Date",
        how="left",
    )

    next_march = _next_month_contract(curve, "H", "ema_next_march_price")
    raw = raw.merge(next_march, on="Date", how="left")
    six_month = _closest_dte_contract(curve, target_dte=180)
    raw = raw.merge(six_month, on="Date", how="left")

    liquidity = _liquidity_features(curve)
    raw = raw.merge(liquidity, on="Date", how="left")
    cross = _cross_market(raw[["Date", "ema_front_price"]], cbot, eurusd)
    raw = raw.merge(cross, on="Date", how="left")
    adjusted = _adjusted_return_features(front_adjusted)
    raw = raw.merge(adjusted, on="Date", how="left")

    raw["ema_spread_f0_f1"] = raw["ema_front_price"] - raw["ema_second_price"]
    raw["ema_spread_f1_f2"] = raw["ema_second_price"] - raw["ema_third_price"]
    raw["ema_spread_f0_f2"] = raw["ema_front_price"] - raw["ema_third_price"]
    raw["ema_spread_nov_mar"] = raw["ema_harvest_nov_price"] - raw["ema_next_march_price"]
    raw["ema_curve_slope_3"] = (
        (raw["ema_third_price"] - raw["ema_front_price"])
        / (raw["ema_third_dte"] - raw["ema_front_dte"]).clip(lower=1)
    )
    raw["ema_curve_slope_6"] = (
        (raw["ema_6m_price"] - raw["ema_front_price"])
        / (raw["ema_6m_dte"] - raw["ema_front_dte"]).clip(lower=1)
    )
    raw["ema_contango_flag"] = np.where(
        raw["ema_curve_contract_count"] >= 2,
        (raw["ema_second_price"] > raw["ema_front_price"]).astype(float),
        np.nan,
    )
    raw["ema_backwardation_flag"] = np.where(
        raw["ema_curve_contract_count"] >= 2,
        (raw["ema_second_price"] < raw["ema_front_price"]).astype(float),
        np.nan,
    )
    raw["ema_carry_front_second"] = raw["ema_spread_f0_f1"] / raw["ema_front_price"].replace(0, np.nan)
    raw["ema_roll_yield_ann"] = raw["ema_carry_front_second"] * (
        365.0 / (raw["ema_second_dte"] - raw["ema_front_dte"]).clip(lower=1)
    )
    raw["ema_liquidity_shift"] = raw["ema_oi_total"].pct_change()
    _mask_insufficient_curve(raw)

    out = raw[["Date"]].copy()
    for col in EMA_CURVE_FEATURE_COLUMNS:
        out[col] = raw[col].shift(1) if col in raw.columns else np.nan
    return out.sort_values("Date").reset_index(drop=True)


def build_and_save_curve_features(
    *,
    curve_path: Path = EMA_CURVE_DAILY,
    front_raw_path: Path = EMA_FRONT_RAW,
    front_adjusted_path: Path = EMA_FRONT_ADJUSTED,
    harvest_nov_path: Path = EMA_HARVEST_NOV,
    cbot_path: Path = INTERIM_DIR / "database.parquet",
    eurusd_path: Path = RAW_DIR / "eu_cross_assets" / "eu_cross_assets.csv",
    output_path: Path = EMA_CURVE_FEATURES,
) -> pd.DataFrame:
    """Load default project files, build EMA curve features and save parquet."""
    curve = pd.read_parquet(curve_path)
    front_raw = pd.read_parquet(front_raw_path)
    front_adjusted = pd.read_parquet(front_adjusted_path) if front_adjusted_path.exists() else None
    harvest = pd.read_parquet(harvest_nov_path)
    cbot = _read_optional_frame(cbot_path)
    eurusd = _read_optional_frame(eurusd_path)
    features = build_curve_features(
        curve,
        front_raw,
        harvest,
        cbot,
        eurusd,
        front_adjusted=front_adjusted,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(output_path, index=False)
    return features


def _prepare_curve(contracts: pd.DataFrame) -> pd.DataFrame:
    work = contracts.copy()
    if "date" not in work.columns and "Date" in work.columns:
        work["date"] = work["Date"]
    if "date" not in work.columns:
        raise ValueError("contracts require a date column")
    work["Date"] = pd.to_datetime(work["date"]).dt.normalize()
    price_col = _first_col(work, ["price", "settlement", "close_or_last", "close", "last"])
    if price_col is None:
        raise ValueError("contracts require a price, settlement or close_or_last column")
    work["price"] = pd.to_numeric(work[price_col], errors="coerce")
    if "days_to_expiry" not in work.columns:
        if "expiry_date" in work.columns:
            expiry = pd.to_datetime(work["expiry_date"], errors="coerce")
            work["days_to_expiry"] = (expiry - work["Date"]).dt.days
        else:
            work["days_to_expiry"] = np.nan
    if "rank_by_expiry" not in work.columns:
        work = work.sort_values(["Date", "days_to_expiry", "contract_code"])
        work["rank_by_expiry"] = work.groupby("Date")["days_to_expiry"].rank(method="first")
    if "rank_by_oi" not in work.columns:
        oi = (
            pd.to_numeric(work["open_interest"], errors="coerce")
            if "open_interest" in work.columns
            else pd.Series(np.nan, index=work.index)
        )
        volume = (
            pd.to_numeric(work["volume"], errors="coerce")
            if "volume" in work.columns
            else pd.Series(np.nan, index=work.index)
        )
        sort_liq = oi.fillna(-1) * 1_000_000 + volume.fillna(-1)
        work["_sort_liq"] = sort_liq
        work["rank_by_oi"] = work.groupby("Date")["_sort_liq"].rank(method="first", ascending=False)
    if "month_code" not in work.columns and "contract_code" in work.columns:
        work["month_code"] = work["contract_code"].astype(str).str.split("_", n=1).str[1].str[0]
    for col in ["volume", "open_interest"]:
        if col not in work.columns:
            work[col] = np.nan
        work[col] = pd.to_numeric(work[col], errors="coerce")
    return work[work["price"].notna()].sort_values(["Date", "rank_by_expiry"]).reset_index(drop=True)


def _series_price(frame: pd.DataFrame, output_col: str) -> pd.DataFrame:
    work = frame.copy()
    if "date" not in work.columns and "Date" in work.columns:
        work["date"] = work["Date"]
    if "date" not in work.columns:
        return pd.DataFrame(columns=["Date", output_col])
    price_col = "adjusted_price" if output_col.endswith("_adjusted") and "adjusted_price" in work.columns else "price"
    if price_col not in work.columns:
        return pd.DataFrame(columns=["Date", output_col])
    return (
        pd.DataFrame({
            "Date": pd.to_datetime(work["date"]).dt.normalize(),
            output_col: pd.to_numeric(work[price_col], errors="coerce"),
        })
        .drop_duplicates("Date", keep="last")
        .sort_values("Date")
    )


def _base_dates(frames: list[pd.DataFrame]) -> pd.Series:
    dates = []
    for frame in frames:
        if "Date" in frame.columns:
            dates.append(pd.to_datetime(frame["Date"]))
    if not dates:
        return pd.Series([], dtype="datetime64[ns]")
    return pd.Series(pd.concat(dates, ignore_index=True).dropna().drop_duplicates()).sort_values()


def _rank_prices(
    curve: pd.DataFrame,
    *,
    rank_col: str,
    ranks: tuple[int, ...] = (1, 2, 3),
    prefix: str = "ema",
) -> pd.DataFrame:
    out = pd.DataFrame({"Date": sorted(curve["Date"].dropna().unique())})
    for rank in ranks:
        sub = curve[curve[rank_col].astype(int).eq(rank)]
        keep = sub[["Date", "price", "days_to_expiry"]].rename(
            columns={
                "price": f"{prefix}_{_rank_name(rank)}_price",
                "days_to_expiry": f"{prefix}_{_rank_name(rank)}_dte",
            }
        )
        keep = keep.drop_duplicates("Date", keep="last")
        out = out.merge(keep, on="Date", how="left")
    return out.rename(
        columns={
            "ema_first_price": "ema_front_price_from_curve",
            "ema_first_dte": "ema_front_dte",
            "ema_second_price": "ema_second_price",
            "ema_second_dte": "ema_second_dte",
            "ema_third_price": "ema_third_price",
            "ema_third_dte": "ema_third_dte",
        }
    )


def _rank_name(rank: int) -> str:
    return {1: "first", 2: "second", 3: "third"}.get(rank, str(rank))


def _next_month_contract(curve: pd.DataFrame, month_code: str, output_col: str) -> pd.DataFrame:
    sub = curve[curve["month_code"].astype(str).eq(month_code) & (curve["days_to_expiry"] > 0)]
    if sub.empty:
        return pd.DataFrame({"Date": sorted(curve["Date"].dropna().unique()), output_col: np.nan})
    chosen = (
        sub.sort_values(["Date", "days_to_expiry"])
        .groupby("Date", as_index=False)
        .first()[["Date", "price"]]
        .rename(columns={"price": output_col})
    )
    return chosen


def _closest_dte_contract(curve: pd.DataFrame, *, target_dte: int) -> pd.DataFrame:
    sub = curve[curve["days_to_expiry"].notna()].copy()
    sub["_distance"] = (sub["days_to_expiry"] - target_dte).abs()
    chosen = (
        sub.sort_values(["Date", "_distance", "rank_by_expiry"])
        .groupby("Date", as_index=False)
        .first()[["Date", "price", "days_to_expiry"]]
        .rename(columns={"price": "ema_6m_price", "days_to_expiry": "ema_6m_dte"})
    )
    return chosen


def _mask_insufficient_curve(raw: pd.DataFrame) -> None:
    count = pd.to_numeric(raw["ema_curve_contract_count"], errors="coerce")
    less_than_two = count < 2
    less_than_three = count < 3
    same_as_front = raw["ema_6m_dte"].eq(raw["ema_front_dte"])

    raw.loc[
        less_than_two,
        [
            "ema_spread_f0_f1",
            "ema_spread_nov_mar",
            "ema_contango_flag",
            "ema_backwardation_flag",
            "ema_carry_front_second",
            "ema_roll_yield_ann",
        ],
    ] = np.nan
    raw.loc[
        less_than_three,
        [
            "ema_spread_f1_f2",
            "ema_spread_f0_f2",
            "ema_curve_slope_3",
        ],
    ] = np.nan
    raw.loc[same_as_front | less_than_two, "ema_curve_slope_6"] = np.nan


def _liquidity_features(curve: pd.DataFrame) -> pd.DataFrame:
    grouped = curve.groupby("Date")
    out = grouped.agg(
        ema_oi_total=("open_interest", "sum"),
        ema_volume_total=("volume", "sum"),
        ema_curve_contract_count=("contract_code", "count"),
    ).reset_index()
    max_oi = grouped["open_interest"].max().reset_index(name="_max_oi")
    out = out.merge(max_oi, on="Date", how="left")
    out["ema_oi_concentration"] = out["_max_oi"] / out["ema_oi_total"].replace(0, np.nan)
    out["ema_open_interest_available"] = (out["ema_oi_total"] > 0).astype(float)
    return out.drop(columns=["_max_oi"])


def _cross_market(front: pd.DataFrame, cbot: pd.DataFrame, eurusd: pd.DataFrame) -> pd.DataFrame:
    out = front.copy()
    if cbot.empty or eurusd.empty:
        for col in ["cbot_eur_t", "ema_cbot_basis", "ema_cbot_basis_zscore_52w", "ema_cbot_rel_strength_20d"]:
            out[col] = np.nan
        return out[["Date", "cbot_eur_t", "ema_cbot_basis", "ema_cbot_basis_zscore_52w", "ema_cbot_rel_strength_20d"]]
    cbot_col = _first_col(cbot, ["corn_close", "cbot_cents_bu", "cbot_corn_close"])
    eurusd_col = _first_col(eurusd, ["eurusd_rate", "EURUSD", "close", "Close"])
    if cbot_col is None or eurusd_col is None:
        return _cross_market(front, pd.DataFrame(), pd.DataFrame())
    c = cbot[["Date", cbot_col]].copy()
    fx = eurusd[["Date", eurusd_col]].copy()
    c["Date"] = pd.to_datetime(c["Date"]).dt.normalize()
    fx["Date"] = pd.to_datetime(fx["Date"]).dt.normalize()
    merged = out.merge(c, on="Date", how="left").merge(fx, on="Date", how="left")
    cbot_eur_t = (
        pd.to_numeric(merged[cbot_col], errors="coerce")
        / 100.0
        / pd.to_numeric(merged[eurusd_col], errors="coerce")
        * BUSHEL_TO_TONNE
    )
    merged["cbot_eur_t"] = cbot_eur_t
    merged["ema_cbot_basis"] = merged["ema_front_price"] - cbot_eur_t
    merged["ema_cbot_basis_zscore_52w"] = _rolling_zscore(merged["ema_cbot_basis"], window=260)
    merged["ema_cbot_rel_strength_20d"] = (
        merged["ema_front_price"] / merged["ema_front_price"].shift(20)
        - merged["cbot_eur_t"] / merged["cbot_eur_t"].shift(20)
    )
    return merged[["Date", "cbot_eur_t", "ema_cbot_basis", "ema_cbot_basis_zscore_52w", "ema_cbot_rel_strength_20d"]]


def _adjusted_return_features(front_adjusted: pd.DataFrame | None) -> pd.DataFrame:
    if front_adjusted is None or front_adjusted.empty:
        return pd.DataFrame(columns=["Date", "ema_front_return_5d_adjusted", "ema_front_vol_20d_adjusted"])
    work = _series_price(front_adjusted, "ema_front_price_adjusted")
    price = pd.to_numeric(work["ema_front_price_adjusted"], errors="coerce")
    work["ema_front_return_5d_adjusted"] = np.log(price / price.shift(5))
    work["ema_front_vol_20d_adjusted"] = work["ema_front_return_5d_adjusted"].rolling(20, min_periods=5).std()
    return work[["Date", "ema_front_return_5d_adjusted", "ema_front_vol_20d_adjusted"]]


def _read_optional_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def _first_col(frame: pd.DataFrame, candidates: list[str]) -> str | None:
    return next((col for col in candidates if col in frame.columns), None)


def _rolling_zscore(series: pd.Series, *, window: int) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    mean = values.rolling(window, min_periods=min(20, window)).mean()
    std = values.rolling(window, min_periods=min(20, window)).std().replace(0, np.nan)
    return (values - mean) / std
