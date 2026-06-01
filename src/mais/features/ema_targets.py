"""Agricultural Euronext EMA targets.

Targets are future-looking by definition and must stay outside feature tables.
Raw Euronext prices are used here; adjusted prices are reserved for technical
features that cross roll dates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from mais.paths import (
    DECISION_YAML,
    EMA_FRONT_ADJUSTED,
    EMA_FRONT_RAW,
    EMA_HARVEST_NOV,
    EMA_PROCESSED_DIR,
)
from mais.utils import get_logger, write_parquet

log = get_logger("mais.features.ema_targets")

EMA_TARGETS_PARQUET = EMA_PROCESSED_DIR / "ema_targets.parquet"
DEFAULT_STORAGE_COSTS_EUR_T: dict[str, float] = {"1m": 1.5, "3m": 4.5, "6m": 9.0}
EMA_TARGET_COLUMNS: tuple[str, ...] = (
    "y_up_h20_ema",
    "y_up_h40_ema",
    "y_up_h60_ema",
    "y_up_h20_ema_raw",
    "y_up_h40_ema_raw",
    "y_up_h60_ema_raw",
    "y_up_h20_ema_adjusted",
    "y_up_h40_ema_adjusted",
    "y_up_h60_ema_adjusted",
    "y_up_h20_ema_no_roll",
    "y_up_h40_ema_no_roll",
    "y_up_h60_ema_no_roll",
    "target_crosses_roll_h20",
    "target_crosses_roll_h40",
    "target_crosses_roll_h60",
    "y_up_h20_ema_harvest",
    "y_up_h40_ema_harvest",
    "y_up_gt3pct_h40_ema",
    "y_down_gt3pct_h40_ema",
    "y_price_h20_ema",
    "y_price_h60_ema",
    "y_price_h20_ema_raw",
    "y_price_h60_ema_raw",
    "y_storage_value_1m",
    "y_storage_value_3m",
    "y_storage_value_6m",
    "y_storage_value_1m_raw",
    "y_storage_value_3m_raw",
    "y_storage_value_6m_raw",
    "y_storage_profit_3m",
)


def build_ema_targets(
    front_raw: pd.DataFrame,
    harvest_nov: pd.DataFrame,
    front_adjusted: pd.DataFrame | None = None,
    storage_costs: dict[str, float] | None = None,
    horizons: tuple[int, ...] = (20, 40, 60),
) -> pd.DataFrame:
    """Build EMA agricultural targets from raw, adjusted and no-roll price series."""
    costs = storage_costs or DEFAULT_STORAGE_COSTS_EUR_T
    front = _normalise_price_frame(
        front_raw,
        output_price_col="front_price_raw",
        price_candidates=("price", "close_or_last", "ema_close", "ema_front_price", "settlement"),
    )
    adjusted_source = front_adjusted if front_adjusted is not None else front_raw
    adjusted = _normalise_price_frame(
        adjusted_source,
        output_price_col="front_price_adjusted",
        price_candidates=("adjusted_price", "price", "close_or_last", "ema_close", "ema_front_price", "settlement"),
    )
    roll_events = _normalise_roll_events(front_raw)
    front = front.merge(adjusted, on="Date", how="left").merge(roll_events, on="Date", how="left")
    front["roll_event"] = front["roll_event"].fillna(False).astype(bool)
    harvest = _normalise_price_frame(harvest_nov, output_price_col="harvest_price")
    out = pd.DataFrame({"Date": front["Date"]})
    price_raw = front["front_price_raw"].astype(float)
    price_adjusted = front["front_price_adjusted"].astype(float)
    roll_flags = _future_roll_flags(front["roll_event"], horizons)

    for horizon in horizons:
        horizon = int(horizon)
        future_raw = price_raw.shift(-horizon)
        valid_raw = future_raw.notna() & price_raw.notna()
        future_adjusted = price_adjusted.shift(-horizon)
        valid_adjusted = future_adjusted.notna() & price_adjusted.notna()
        if horizon in (20, 40, 60):
            raw_target = _binary_target(future_raw > price_raw, valid_raw)
            out[f"y_up_h{horizon}_ema"] = raw_target
            out[f"y_up_h{horizon}_ema_raw"] = raw_target
            out[f"y_up_h{horizon}_ema_adjusted"] = _binary_target(
                future_adjusted > price_adjusted,
                valid_adjusted,
            )
            roll_col = f"target_crosses_roll_h{horizon}"
            out[roll_col] = roll_flags[horizon]
            out[f"y_up_h{horizon}_ema_no_roll"] = _binary_target(
                future_raw > price_raw,
                valid_raw & out[roll_col].eq(0.0),
            )
        if horizon in (20, 60):
            out[f"y_price_h{horizon}_ema"] = future_raw
            out[f"y_price_h{horizon}_ema_raw"] = future_raw

    future_40 = price_raw.shift(-40)
    ret_40 = np.log(future_40 / price_raw)
    valid_40 = future_40.notna() & price_raw.notna() & np.isfinite(ret_40)
    out["y_up_gt3pct_h40_ema"] = _binary_target(ret_40 > 0.03, valid_40)
    out["y_down_gt3pct_h40_ema"] = _binary_target(ret_40 < -0.03, valid_40)

    for label, horizon in (("1m", 20), ("3m", 60), ("6m", 120)):
        future = price_raw.shift(-horizon)
        value = future - price_raw - float(costs[label])
        out[f"y_storage_value_{label}"] = value
        out[f"y_storage_value_{label}_raw"] = value
    out["y_storage_profit_3m"] = _binary_target(
        out["y_storage_value_3m"] > 0,
        out["y_storage_value_3m"].notna(),
    )

    harvest_targets = _harvest_targets(front["Date"], harvest, horizons=(20, 40))
    out = out.merge(harvest_targets, on="Date", how="left")
    ordered_cols = ["Date", *EMA_TARGET_COLUMNS]
    missing = [col for col in ordered_cols if col not in out.columns]
    if missing:
        raise ValueError(f"Missing EMA target columns after build: {missing}")
    return out[ordered_cols].sort_values("Date").reset_index(drop=True)


def build_and_save_ema_targets(
    *,
    front_raw_path: Path = EMA_FRONT_RAW,
    front_adjusted_path: Path | None = EMA_FRONT_ADJUSTED,
    harvest_nov_path: Path = EMA_HARVEST_NOV,
    output_path: Path = EMA_TARGETS_PARQUET,
    decision_config_path: Path = DECISION_YAML,
) -> pd.DataFrame:
    """Load EMA continuous raw series, build targets and save the parquet output."""
    front_raw = pd.read_parquet(front_raw_path)
    front_adjusted = (
        pd.read_parquet(front_adjusted_path)
        if front_adjusted_path is not None and front_adjusted_path.exists()
        else None
    )
    harvest_nov = pd.read_parquet(harvest_nov_path)
    targets = build_ema_targets(
        front_raw,
        harvest_nov,
        front_adjusted=front_adjusted,
        storage_costs=load_ema_storage_costs(decision_config_path),
    )
    write_parquet(targets, output_path)
    log.info(
        "ema_targets_saved",
        path=str(output_path),
        rows=len(targets),
        cols=targets.shape[1],
        target_cols=len(EMA_TARGET_COLUMNS),
    )
    return targets


def assert_ema_targets_not_in_features(
    features: pd.DataFrame,
    targets: pd.DataFrame | None = None,
) -> None:
    """Raise if EMA target columns leak into a feature table."""
    forbidden = set(EMA_TARGET_COLUMNS)
    if targets is not None:
        forbidden.update(
            col for col in targets.columns if str(col).startswith("y_") and ("ema" in str(col) or "storage" in str(col))
        )
    leaked = sorted(forbidden & set(features.columns))
    if leaked:
        raise ValueError(f"EMA target leakage in features: {leaked}")


def load_ema_storage_costs(config_path: Path = DECISION_YAML) -> dict[str, float]:
    """Load EMA storage costs from decision.yaml, falling back to defaults."""
    if not config_path.exists():
        return DEFAULT_STORAGE_COSTS_EUR_T.copy()
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    raw_costs = _find_storage_costs(payload)
    costs = DEFAULT_STORAGE_COSTS_EUR_T.copy()
    for key, value in raw_costs.items():
        if key in costs:
            costs[key] = float(value)
    return costs


def _find_storage_costs(payload: dict[str, Any]) -> dict[str, Any]:
    ema_cfg = payload.get("euronext_ema", {})
    if isinstance(ema_cfg, dict):
        costs = ema_cfg.get("storage_costs_eur_per_tonne", {})
        if isinstance(costs, dict):
            return costs
    return {}


def _harvest_targets(
    base_dates: pd.Series,
    harvest: pd.DataFrame,
    *,
    horizons: tuple[int, ...],
) -> pd.DataFrame:
    harvest_work = harvest[["Date", "harvest_price"]].copy()
    harvest_work = harvest_work.sort_values("Date").drop_duplicates("Date", keep="last").reset_index(drop=True)
    price = harvest_work["harvest_price"].astype(float)
    out = pd.DataFrame({"Date": harvest_work["Date"]})
    for horizon in horizons:
        future = price.shift(-int(horizon))
        out[f"y_up_h{horizon}_ema_harvest"] = _binary_target(
            future > price,
            future.notna() & price.notna(),
        )
    base = pd.DataFrame({"Date": pd.to_datetime(base_dates)})
    return base.merge(out, on="Date", how="left")


def _normalise_price_frame(
    frame: pd.DataFrame,
    *,
    output_price_col: str,
    price_candidates: tuple[str, ...] = ("price", "close_or_last", "ema_close", "ema_front_price", "settlement"),
) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["Date", output_price_col])
    work = frame.copy()
    if "Date" not in work.columns and "date" in work.columns:
        work["Date"] = work["date"]
    if "Date" not in work.columns:
        raise ValueError("EMA target input requires Date or date column")
    price_col = _first_existing(work, price_candidates)
    if price_col is None:
        raise ValueError("EMA target input requires a raw price column")
    work["Date"] = pd.to_datetime(work["Date"]).dt.normalize()
    work[output_price_col] = pd.to_numeric(work[price_col], errors="coerce")
    return (
        work[["Date", output_price_col]]
        .dropna(subset=["Date"])
        .sort_values("Date")
        .drop_duplicates("Date", keep="last")
        .reset_index(drop=True)
    )


def _normalise_roll_events(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["Date", "roll_event"])
    work = frame.copy()
    if "Date" not in work.columns and "date" in work.columns:
        work["Date"] = work["date"]
    if "Date" not in work.columns:
        return pd.DataFrame(columns=["Date", "roll_event"])
    work["Date"] = pd.to_datetime(work["Date"]).dt.normalize()
    if "roll_event" not in work.columns:
        work["roll_event"] = False
    return (
        work[["Date", "roll_event"]]
        .dropna(subset=["Date"])
        .sort_values("Date")
        .drop_duplicates("Date", keep="last")
        .reset_index(drop=True)
    )


def _future_roll_flags(roll_event: pd.Series, horizons: tuple[int, ...]) -> dict[int, pd.Series]:
    roll = roll_event.fillna(False).astype(bool).to_numpy()
    n = len(roll)
    flags: dict[int, pd.Series] = {}
    for horizon in horizons:
        horizon = int(horizon)
        values = np.full(n, np.nan)
        for idx in range(n):
            end = idx + horizon
            if end < n:
                values[idx] = float(roll[idx + 1 : end + 1].any())
        flags[horizon] = pd.Series(values)
    return flags


def _first_existing(frame: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    for col in candidates:
        if col in frame.columns:
            return col
    return None


def _binary_target(condition: pd.Series, valid: pd.Series) -> pd.Series:
    values = condition.astype("float64")
    values.loc[~valid] = np.nan
    return values
