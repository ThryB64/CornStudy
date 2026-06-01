"""Calibrated P(correct) model for direction and economic decisions."""

from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss

from mais.indicator.calibration import ece, reliability_curve

META_FEATURES: tuple[str, ...] = (
    "prob_distance",
    "disagreement",
    "signal_stability_5d",
    "regime_score",
    "month",
    "days_since_wasde",
    "wasde_surprise_abs",
    "cot_extreme_flag",
)

FORBIDDEN_FEATURE_TOKENS: tuple[str, ...] = (
    "actual",
    "future",
    "target",
    "gain",
    "profit",
    "forward",
    "max_price",
)


@dataclass
class PCorrectModel:
    """Small serializable wrapper around the fitted P(correct) estimator."""

    features: tuple[str, ...]
    impute_values: dict[str, float]
    estimator: LogisticRegression | None = None
    constant_probability: float | None = None

    def predict_proba(self, frame: pd.DataFrame) -> np.ndarray:
        """Return calibrated P(correct) for each row."""
        x = _feature_matrix(frame, self.features, self.impute_values)
        if self.constant_probability is not None:
            return np.full(len(x), float(self.constant_probability), dtype=float)
        if self.estimator is None:
            raise ValueError("PCorrectModel is not fitted")
        return self.estimator.predict_proba(x)[:, 1]


def build_p_correct_frame(
    consensus: pd.DataFrame,
    *,
    profitability: pd.DataFrame | None = None,
    proba_col: str = "consensus_proba",
    actual_col: str = "actual_up_majority",
    signal_col: str = "signal",
) -> pd.DataFrame:
    """Build target/meta-feature frame from consensus OOF and optional profit data."""
    required = {"Date", proba_col, actual_col}
    missing = required - set(consensus.columns)
    if missing:
        raise ValueError(f"Missing required consensus columns: {sorted(missing)}")
    frame = consensus.copy()
    frame["Date"] = pd.to_datetime(frame["Date"])
    if signal_col not in frame.columns:
        frame[signal_col] = np.where(frame[proba_col] >= 0.5, "BULLISH", "BEARISH")

    frame["prob_distance"] = (frame[proba_col].astype(float) - 0.5).abs() * 2.0
    if "disagreement" not in frame.columns:
        frame["disagreement"] = 0.0
    frame["pred_direction_up"] = np.where(
        frame[signal_col].eq("BULLISH"),
        1,
        np.where(frame[signal_col].eq("BEARISH"), 0, (frame[proba_col] >= 0.5).astype(int)),
    )
    frame["y_direction_correct"] = (frame["pred_direction_up"].astype(int) == frame[actual_col].astype(int)).astype(int)
    frame["signal_stability_5d"] = _signal_stability(frame[signal_col])
    frame["month"] = frame["Date"].dt.month.astype(int)
    for col in ("regime_score", "days_since_wasde", "wasde_surprise_abs", "cot_extreme_flag"):
        if col not in frame.columns:
            frame[col] = 0.0

    if profitability is not None:
        profit = profitability.copy()
        profit["Date"] = pd.to_datetime(profit["Date"])
        frame = frame.merge(profit, on="Date", how="left", suffixes=("", "_profit"))
    profit_col = _find_profit_column(frame)
    if profit_col is not None:
        frame["y_decision_profitable"] = (frame[profit_col].astype(float) > 0.0).astype(int)

    return frame


def fit_p_correct_model(
    frame: pd.DataFrame,
    *,
    target_col: str = "y_direction_correct",
    meta_features: tuple[str, ...] | list[str] = META_FEATURES,
    n_bins: int = 10,
    output_model_path: Path | None = None,
    output_reliability_path: Path | None = None,
) -> tuple[PCorrectModel, dict[str, Any], pd.DataFrame]:
    """Fit a logistic P(correct) model and return model, metrics, reliability."""
    if target_col not in frame.columns:
        raise ValueError(f"Missing target column: {target_col}")
    features = tuple(meta_features)
    validate_meta_features_no_leakage(features)
    work = frame.copy()
    if "Date" in work.columns:
        work["Date"] = pd.to_datetime(work["Date"])
        work = work.sort_values("Date")
    work = work.dropna(subset=[target_col]).reset_index(drop=True)
    if len(work) < 10:
        raise ValueError("At least 10 observations are required to fit P(correct)")

    train, eval_frame = _chronological_split(work)
    impute_values = _impute_values(train, features)
    y_train = train[target_col].astype(int).to_numpy()
    y_eval = eval_frame[target_col].astype(int).to_numpy()

    if len(np.unique(y_train)) < 2:
        model = PCorrectModel(
            features=features,
            impute_values=impute_values,
            constant_probability=float(np.mean(y_train)),
        )
    else:
        estimator = LogisticRegression(C=1.0, max_iter=1000)
        estimator.fit(_feature_matrix(train, features, impute_values), y_train)
        model = PCorrectModel(features=features, impute_values=impute_values, estimator=estimator)

    p_eval = np.clip(model.predict_proba(eval_frame), 1e-6, 1.0 - 1e-6)
    reliability = reliability_curve(p_eval, y_eval, n_bins=n_bins)
    metrics = {
        "target": target_col,
        "n_train": int(len(train)),
        "n_eval": int(len(eval_frame)),
        "ece": ece(p_eval, y_eval, n_bins=n_bins),
        "brier_score": float(brier_score_loss(y_eval, p_eval)),
        "log_loss": float(log_loss(y_eval, p_eval, labels=[0, 1])),
        "sharpness": float(np.std(p_eval)),
        "monotone": _is_reliability_monotone(reliability),
        "features": list(features),
    }
    _maybe_write_outputs(model, metrics, reliability, output_model_path, output_reliability_path)
    return model, metrics, reliability


def validate_meta_features_no_leakage(features: tuple[str, ...] | list[str]) -> None:
    """Reject target/economic realization columns as model inputs."""
    bad = []
    for feature in features:
        name = feature.lower()
        if name.startswith("y_") or any(token in name for token in FORBIDDEN_FEATURE_TOKENS):
            bad.append(feature)
    if bad:
        raise ValueError(f"Forbidden leakage-prone P(correct) features: {bad}")


def _signal_stability(signal: pd.Series) -> pd.Series:
    mapped = signal.map({"BULLISH": 1.0, "BEARISH": -1.0}).fillna(0.0)
    return mapped.rolling(5, min_periods=1).apply(lambda values: float(np.mean(values == values[-1])), raw=True)


def _find_profit_column(frame: pd.DataFrame) -> str | None:
    for col in ("gain_net_signal", "gain_vs_sell_harvest", "net_gain", "profit"):
        if col in frame.columns:
            return col
    return None


def _chronological_split(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    split = max(1, int(len(frame) * 0.65))
    if len(frame) - split < 5:
        split = max(5, len(frame) - 5)
    return frame.iloc[:split].copy(), frame.iloc[split:].copy()


def _impute_values(frame: pd.DataFrame, features: tuple[str, ...]) -> dict[str, float]:
    values: dict[str, float] = {}
    for feature in features:
        if feature not in frame.columns:
            values[feature] = 0.0
            continue
        median = pd.to_numeric(frame[feature], errors="coerce").median()
        values[feature] = 0.0 if pd.isna(median) else float(median)
    return values


def _feature_matrix(frame: pd.DataFrame, features: tuple[str, ...], impute_values: dict[str, float]) -> np.ndarray:
    matrix = pd.DataFrame(index=frame.index)
    for feature in features:
        if feature in frame.columns:
            matrix[feature] = pd.to_numeric(frame[feature], errors="coerce")
        else:
            matrix[feature] = np.nan
        matrix[feature] = matrix[feature].fillna(impute_values.get(feature, 0.0))
    return matrix.to_numpy(dtype=float)


def _is_reliability_monotone(curve: pd.DataFrame) -> bool:
    if curve.empty or "fraction_positive" not in curve.columns:
        return False
    values = curve.sort_values("mean_pred")["fraction_positive"].to_numpy(dtype=float)
    return bool(np.all(np.diff(values) >= -0.05))


def _maybe_write_outputs(
    model: PCorrectModel,
    metrics: dict[str, Any],
    reliability: pd.DataFrame,
    output_model_path: Path | None,
    output_reliability_path: Path | None,
) -> None:
    if output_model_path is not None:
        output_model_path.parent.mkdir(parents=True, exist_ok=True)
        with output_model_path.open("wb") as file:
            pickle.dump(model, file)
    if output_reliability_path is not None:
        output_reliability_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {**metrics, "reliability_curve": reliability.to_dict(orient="records")}
        output_reliability_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
