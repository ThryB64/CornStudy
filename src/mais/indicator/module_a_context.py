"""Module A: interpretable market-context score for the maize study."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

SIGNAL_DEFINITIONS: dict[str, dict[str, Any]] = {
    "bilan_mondial": {
        "block": "offre_mondiale",
        "columns": ["wasde_stocks_to_use_calc_z", "wasde_stocks_to_use_ratio"],
        "sign": -1.0,
        "direct_z": True,
    },
    "bilan_stocks_eu": {
        "block": "offre_mondiale",
        "columns": ["ema_cbot_basis_zscore_52w", "ema_cbot_basis"],
        "sign": -1.0,
        "direct_z": True,
    },
    "crop_condition_eu": {
        "block": "offre_mondiale",
        "columns": ["crop_ge_zscore_seasonal", "crop_ge_pct_filled", "drought_composite"],
        "sign": -1.0,
        "direct_z": True,
    },
    "brazil_supply_pressure": {
        "block": "offre_competiteurs",
        "columns": ["soy_close", "corn_soy_ratio", "wasde_production_surprise_vs_5y"],
        "sign": -1.0,
        "direct_z": False,
    },
    "ukraine_corridor": {
        "block": "offre_competiteurs",
        "columns": ["ukraine_corridor_status"],
        "sign": 1.0,
        "direct_z": False,
        "manual_default": 0.0,
    },
    "us_crop_condition": {
        "block": "offre_competiteurs",
        "columns": ["crop_ge_zscore_seasonal", "drought_composite", "drought_d2plus"],
        "sign": -1.0,
        "direct_z": True,
    },
    "china_demand": {
        "block": "demande_mondiale",
        "columns": ["export_china_pct_total", "wasde_exports_surprise_vs_5y"],
        "sign": 1.0,
        "direct_z": False,
    },
    "wasde_surprise": {
        "block": "demande_mondiale",
        "columns": ["wasde_ending_stocks_surprise_vs_5y", "wasde_supply_minus_use_surprise_vs_5y"],
        "sign": -1.0,
        "direct_z": False,
    },
    "export_pace_eu": {
        "block": "demande_mondiale",
        "columns": ["export_pace_vs_5y_avg", "export_sales_weekly_zscore", "export_momentum_4w"],
        "sign": 1.0,
        "direct_z": True,
    },
    "cot_positioning": {
        "block": "positionnement_structure",
        "columns": ["cot_mm_pct_oi_percentile", "cot_mm_net_pct_oi_y", "cot_crowding_score"],
        "sign": -1.0,
        "direct_z": False,
        "percentile": True,
    },
    "futures_structure": {
        "block": "positionnement_structure",
        "columns": ["ema_backwardation_flag", "ema_contango_flag", "ema_roll_yield_ann"],
        "sign": 1.0,
        "structure": True,
    },
    "eur_usd_competitive": {
        "block": "positionnement_structure",
        "columns": ["cbot_eur_t", "ema_cbot_rel_strength_20d"],
        "sign": 1.0,
        "direct_z": False,
    },
}

BLOCKS: tuple[str, ...] = (
    "offre_mondiale",
    "offre_competiteurs",
    "demande_mondiale",
    "positionnement_structure",
)


@dataclass(frozen=True)
class ContextEvaluation:
    da_weekly: float | None
    n_weekly: int
    availability_mean: float


def score_from_zscore(z: float | int | None, cap: float = 2.0) -> float:
    """Map a z-score to a bounded signal in [-1, +1]."""
    if z is None or pd.isna(z):
        return 0.0
    return float(np.tanh(float(z) / cap))


def score_from_stocks_use_ratio(ratio: float, mean_5y: float, std_5y: float) -> float:
    """Low stock/use is bullish, high stock/use is bearish."""
    if std_5y == 0 or pd.isna(std_5y):
        return 0.0
    z = -(float(ratio) - float(mean_5y)) / float(std_5y)
    return score_from_zscore(z)


def score_from_cot_percentile(percentile: float | int | None) -> float:
    """Contrarian COT score: crowded longs are bearish, crowded shorts bullish."""
    if percentile is None or pd.isna(percentile):
        return 0.0
    z = -(float(percentile) - 50.0) / 25.0
    return score_from_zscore(z)


def compute_context_score(row: pd.Series, features: pd.DataFrame) -> dict[str, Any]:
    """Compute the 12 Module A signals and global market orientation."""
    history = _history_until(features, row)
    signals: dict[str, dict[str, Any]] = {}
    for signal_name, definition in SIGNAL_DEFINITIONS.items():
        signal = _compute_signal(signal_name, definition, row, history)
        signals[signal_name] = signal
    available_scores = [sig["score"] for sig in signals.values() if sig["available"]]
    context_score = float(np.mean(available_scores)) if available_scores else 0.0
    block_scores = _block_scores(signals)
    availability = len(available_scores) / len(SIGNAL_DEFINITIONS)
    orientation = _orientation(context_score, availability)
    dominant = max(signals.items(), key=lambda item: abs(item[1]["score"]))[0]
    return {
        "signals": signals,
        "block_scores": block_scores,
        "context_score": context_score,
        "orientation": orientation,
        "dominant_signal": dominant,
        "data_availability_score": availability,
        "typed_uncertainty": _uncertainty_label(availability, abs(context_score)),
    }


def compute_context_timeseries(features: pd.DataFrame) -> pd.DataFrame:
    """Compute Module A context score for every row in a feature table."""
    work = features.copy()
    work["Date"] = pd.to_datetime(work["Date"]).dt.normalize()
    rows: list[dict[str, Any]] = []
    for _, row in work.sort_values("Date").iterrows():
        context = compute_context_score(row, work)
        flat = {
            "Date": row["Date"],
            "context_score": context["context_score"],
            "orientation": context["orientation"],
            "dominant_signal": context["dominant_signal"],
            "data_availability_score": context["data_availability_score"],
        }
        for name, signal in context["signals"].items():
            flat[f"signal_{name}"] = signal["score"]
        rows.append(flat)
    return pd.DataFrame(rows)


def evaluate_context_weekly_da(
    context: pd.DataFrame,
    targets: pd.DataFrame,
    *,
    target_col: str = "y_up_h20_ema",
) -> ContextEvaluation:
    """Evaluate weekly directional coherence of context_score against a binary target."""
    if target_col not in targets.columns:
        return ContextEvaluation(da_weekly=None, n_weekly=0, availability_mean=float(context["data_availability_score"].mean()))
    left = context[["Date", "context_score", "data_availability_score"]].copy()
    right = targets[["Date", target_col]].copy()
    left["Date"] = pd.to_datetime(left["Date"]).dt.normalize()
    right["Date"] = pd.to_datetime(right["Date"]).dt.normalize()
    merged = left.merge(right, on="Date", how="inner").dropna(subset=[target_col])
    if merged.empty:
        return ContextEvaluation(da_weekly=None, n_weekly=0, availability_mean=float(left["data_availability_score"].mean()))
    weekly = _one_point_per_week(merged)
    pred = weekly["context_score"].gt(0).astype(int)
    da = float(pred.eq(weekly[target_col].astype(int)).mean()) if len(weekly) else None
    return ContextEvaluation(
        da_weekly=da,
        n_weekly=int(len(weekly)),
        availability_mean=float(weekly["data_availability_score"].mean()) if len(weekly) else 0.0,
    )


def _compute_signal(
    signal_name: str,
    definition: dict[str, Any],
    row: pd.Series,
    history: pd.DataFrame,
) -> dict[str, Any]:
    if definition.get("structure"):
        score, value, col = _structure_score(row)
    else:
        col = _first_available_column(row, definition["columns"])
        if col is None:
            default = definition.get("manual_default")
            if default is None:
                return _missing_signal(signal_name, definition)
            return _signal_payload(signal_name, definition, float(default), None, "manual_default")
        value = row.get(col)
        if pd.isna(value):
            return _missing_signal(signal_name, definition, col)
        if definition.get("percentile"):
            score = score_from_cot_percentile(value)
        elif definition.get("direct_z"):
            score = score_from_zscore(float(value) * float(definition.get("sign", 1.0)))
        else:
            z = _zscore_at(history[col], value)
            score = score_from_zscore(z * float(definition.get("sign", 1.0)))
    return _signal_payload(signal_name, definition, score, value, col)


def _structure_score(row: pd.Series) -> tuple[float, float | None, str | None]:
    backward = float(row.get("ema_backwardation_flag", 0.0) or 0.0)
    contango = float(row.get("ema_contango_flag", 0.0) or 0.0)
    if backward or contango:
        raw = backward - contango
        return float(np.clip(raw, -1.0, 1.0)), raw, "ema_backwardation_flag/ema_contango_flag"
    value = row.get("ema_roll_yield_ann")
    if value is None or pd.isna(value):
        return 0.0, None, None
    return score_from_zscore(float(value)), float(value), "ema_roll_yield_ann"


def _signal_payload(
    name: str,
    definition: dict[str, Any],
    score: float,
    value: Any,
    source_col: str | None,
) -> dict[str, Any]:
    return {
        "name": name,
        "block": definition["block"],
        "score": float(np.clip(score, -1.0, 1.0)),
        "value": None if value is None or pd.isna(value) else float(value),
        "source_col": source_col,
        "available": source_col is not None,
    }


def _missing_signal(name: str, definition: dict[str, Any], source_col: str | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "block": definition["block"],
        "score": 0.0,
        "value": None,
        "source_col": source_col,
        "available": False,
    }


def _history_until(features: pd.DataFrame, row: pd.Series) -> pd.DataFrame:
    if "Date" not in features.columns or "Date" not in row:
        return features
    dates = pd.to_datetime(features["Date"]).dt.normalize()
    return features.loc[dates <= pd.Timestamp(row["Date"]).normalize()]


def _first_available_column(row: pd.Series, columns: list[str]) -> str | None:
    return next((col for col in columns if col in row.index), None)


def _zscore_at(series: pd.Series, value: Any) -> float:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if len(numeric) < 20:
        return 0.0
    std = float(numeric.std())
    if std == 0 or pd.isna(std):
        return 0.0
    return (float(value) - float(numeric.mean())) / std


def _block_scores(signals: dict[str, dict[str, Any]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for block in BLOCKS:
        values = [sig["score"] for sig in signals.values() if sig["block"] == block and sig["available"]]
        out[block] = float(np.mean(values)) if values else 0.0
    return out


def _orientation(score: float, availability: float) -> str:
    if availability < 0.50:
        return "UNCERTAIN"
    if score > 0.30:
        return "HAUSSIER"
    if score < -0.30:
        return "BAISSIER"
    return "NEUTRE"


def _uncertainty_label(availability: float, conviction: float) -> str:
    if availability < 0.50:
        return "low_data_availability"
    if conviction < 0.15:
        return "low_conviction"
    return "normal"


def _one_point_per_week(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["week_start"] = work["Date"] - pd.to_timedelta(work["Date"].dt.weekday, unit="D")
    work["_dow_distance"] = work["Date"].dt.weekday.abs()
    return (
        work.sort_values(["week_start", "_dow_distance", "Date"])
        .groupby("week_start", as_index=False)
        .first()
        .drop(columns=["week_start", "_dow_distance"])
    )
