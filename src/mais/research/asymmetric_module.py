"""Asymmetric downside risk and upside opportunity module."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score


@dataclass(frozen=True)
class AsymmetricThresholds:
    lambda_value: float
    threshold_down: float
    threshold_up: float


def evaluate_asymmetric_module(
    frame: pd.DataFrame,
    *,
    feature_cols: list[str],
    down_target_col: str = "y_down_gt_5pct_h40",
    up_target_col: str = "y_up_gt_5pct_h40",
    economic_col: str = "move_cents_h40",
    output_path: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fit separate downside/upside models, calibrate thresholds, return metrics."""
    _validate_columns(frame, feature_cols + [down_target_col, up_target_col])
    work = frame.copy()
    if "Date" in work.columns:
        work["Date"] = pd.to_datetime(work["Date"])
        work = work.sort_values("Date")
    work = work.dropna(subset=[down_target_col, up_target_col]).reset_index(drop=True)
    train, valid = _chronological_split(work)
    imputes = _impute_values(train, feature_cols)

    down_model = _fit_classifier(train, feature_cols, down_target_col, imputes)
    up_model = _fit_classifier(train, feature_cols, up_target_col, imputes)

    scored = valid.copy()
    scored["downside_risk_score"] = _predict_probability(down_model, valid, feature_cols, imputes)
    scored["upside_opportunity_score"] = _predict_probability(up_model, valid, feature_cols, imputes)
    down_auc = _safe_auc(scored[down_target_col], scored["downside_risk_score"])
    up_auc = _safe_auc(scored[up_target_col], scored["upside_opportunity_score"])
    thresholds, threshold_curve = calibrate_asymmetric_thresholds(
        scored,
        down_score_col="downside_risk_score",
        up_score_col="upside_opportunity_score",
        down_target_col=down_target_col,
        up_target_col=up_target_col,
        economic_col=economic_col,
    )
    scored["action"] = assign_asymmetric_actions(
        scored["downside_risk_score"],
        scored["upside_opportunity_score"],
        thresholds=thresholds,
    )
    economic = economic_evaluation(
        scored,
        down_target_col=down_target_col,
        up_target_col=up_target_col,
        economic_col=economic_col,
    )
    metrics = {
        "downside_auc": down_auc,
        "downside_auc_ci95": _bootstrap_auc_ci(scored[down_target_col], scored["downside_risk_score"]),
        "upside_auc": up_auc,
        "upside_auc_ci95": _bootstrap_auc_ci(scored[up_target_col], scored["upside_opportunity_score"]),
        "thresholds": {
            "lambda_value": thresholds.lambda_value,
            "threshold_down": thresholds.threshold_down,
            "threshold_up": thresholds.threshold_up,
        },
        "threshold_curve": threshold_curve,
        "economic_evaluation": economic,
        "verdict": _verdict(down_auc, up_auc, economic),
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    return scored, metrics


def calibrate_asymmetric_thresholds(
    frame: pd.DataFrame,
    *,
    down_score_col: str = "downside_risk_score",
    up_score_col: str = "upside_opportunity_score",
    down_target_col: str = "y_down_gt_5pct_h40",
    up_target_col: str = "y_up_gt_5pct_h40",
    economic_col: str = "move_cents_h40",
    lambda_grid: tuple[float, ...] = (1.5, 2.0, 2.5, 3.0),
) -> tuple[AsymmetricThresholds, list[dict[str, float]]]:
    """Calibrate lambda and upside threshold on validation economics."""
    best_score = -np.inf
    best = AsymmetricThresholds(lambda_value=lambda_grid[0], threshold_down=lambda_grid[0] / (1.0 + lambda_grid[0]), threshold_up=0.5)
    rows: list[dict[str, float]] = []
    for lambda_value in lambda_grid:
        threshold_down = float(lambda_value / (1.0 + lambda_value))
        threshold_up, up_curve = calibrate_threshold(
            frame[up_score_col],
            frame[up_target_col],
            economic_values=frame[economic_col] if economic_col in frame.columns else None,
        )
        actions = assign_asymmetric_actions(
            frame[down_score_col],
            frame[up_score_col],
            thresholds=AsymmetricThresholds(lambda_value, threshold_down, threshold_up),
        )
        score = _economic_score(frame, actions, down_target_col, up_target_col, economic_col)
        rows.append(
            {
                "lambda_value": float(lambda_value),
                "threshold_down": threshold_down,
                "threshold_up": threshold_up,
                "economic_score": float(score),
                "up_curve_best_score": float(max(row["score"] for row in up_curve)),
            }
        )
        if score > best_score:
            best_score = score
            best = AsymmetricThresholds(lambda_value=float(lambda_value), threshold_down=threshold_down, threshold_up=threshold_up)
    return best, rows


def calibrate_threshold(
    score: pd.Series,
    target: pd.Series,
    *,
    economic_values: pd.Series | None = None,
    thresholds: np.ndarray | None = None,
) -> tuple[float, list[dict[str, float]]]:
    """Calibrate an upside threshold by economic objective, not by constant."""
    grid = thresholds if thresholds is not None else np.round(np.arange(0.40, 0.86, 0.05), 2)
    econ = pd.Series(1.0, index=target.index) if economic_values is None else economic_values.abs().fillna(0.0)
    rows: list[dict[str, float]] = []
    best_threshold = float(grid[0])
    best_score = -np.inf
    for threshold in grid:
        selected = score >= threshold
        true_positive = selected & (target.astype(int) == 1)
        false_positive = selected & (target.astype(int) == 0)
        objective = float(econ[true_positive].mean() if true_positive.any() else 0.0)
        penalty = float(econ[false_positive].mean() if false_positive.any() else 0.0)
        actionability = float(selected.mean())
        value = objective - 0.5 * penalty + 0.05 * actionability
        rows.append({"threshold": float(threshold), "score": value, "actionability": actionability})
        if value > best_score:
            best_score = value
            best_threshold = float(threshold)
    return best_threshold, rows


def assign_asymmetric_actions(
    downside_risk_score: pd.Series | np.ndarray,
    upside_opportunity_score: pd.Series | np.ndarray,
    *,
    thresholds: AsymmetricThresholds,
) -> pd.Series:
    """Apply fractional farmer decision rules from calibrated thresholds."""
    down = pd.Series(downside_risk_score, dtype=float).reset_index(drop=True)
    up = pd.Series(upside_opportunity_score, dtype=float).reset_index(drop=True)
    action = pd.Series("ATTENDRE", index=down.index, dtype=object)
    action[down > thresholds.threshold_down] = "VENDRE_MAINTENANT"
    action[(down <= thresholds.threshold_down) & (up > thresholds.threshold_up)] = "STOCKER"
    action[(down > 0.50) & (up < 0.45) & (action == "ATTENDRE")] = "VENDRE_PARTIEL_50PCT"
    return action


def economic_evaluation(
    frame: pd.DataFrame,
    *,
    down_target_col: str,
    up_target_col: str,
    economic_col: str = "move_cents_h40",
) -> dict[str, Any]:
    """Summarize avoided loss, missed gain and regret by crop year."""
    work = frame.copy()
    if economic_col not in work.columns:
        work[economic_col] = 0.0
    move_abs = work[economic_col].abs().astype(float)
    sell_now = work["action"].isin(["VENDRE_MAINTENANT", "VENDRE_PARTIEL_50PCT"])
    stock = work["action"].eq("STOCKER")
    work["perte_evitee_cents"] = np.where(sell_now & (work[down_target_col].astype(int) == 1), move_abs, 0.0)
    work["gain_manque_cents"] = np.where(sell_now & (work[up_target_col].astype(int) == 1), move_abs, 0.0)
    work["regret_cents"] = np.where(stock & (work[down_target_col].astype(int) == 1), move_abs, work["gain_manque_cents"])
    if "Date" in work.columns:
        year = pd.to_datetime(work["Date"]).dt.year
    elif "crop_year" in work.columns:
        year = work["crop_year"].astype(int)
    else:
        year = pd.Series(0, index=work.index)
    work["crop_year"] = year
    by_year = {
        str(int(crop_year)): {
            "perte_evitee_mean": float(sub["perte_evitee_cents"].mean()),
            "gain_manque_mean": float(sub["gain_manque_cents"].mean()),
            "regret_moyen": float(sub["regret_cents"].mean()),
            "n_actions": int((sub["action"] != "ATTENDRE").sum()),
        }
        for crop_year, sub in work.groupby("crop_year")
    }
    return {
        "perte_evitee_mean": float(work["perte_evitee_cents"].mean()),
        "gain_manque_mean": float(work["gain_manque_cents"].mean()),
        "regret_moyen": float(work["regret_cents"].mean()),
        "actions_distribution": {str(k): int(v) for k, v in work["action"].value_counts().to_dict().items()},
        "by_crop_year": by_year,
    }


def _validate_columns(frame: pd.DataFrame, columns: list[str]) -> None:
    missing = [col for col in columns if col not in frame.columns]
    if missing:
        raise ValueError(f"Missing columns for asymmetric module: {missing}")


def _chronological_split(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    split = max(1, int(len(frame) * 0.65))
    if len(frame) - split < 5:
        split = max(5, len(frame) - 5)
    return frame.iloc[:split].copy(), frame.iloc[split:].copy()


def _impute_values(frame: pd.DataFrame, feature_cols: list[str]) -> dict[str, float]:
    values = {}
    for col in feature_cols:
        median = pd.to_numeric(frame[col], errors="coerce").median()
        values[col] = 0.0 if pd.isna(median) else float(median)
    return values


def _feature_matrix(frame: pd.DataFrame, feature_cols: list[str], imputes: dict[str, float]) -> np.ndarray:
    x = pd.DataFrame(index=frame.index)
    for col in feature_cols:
        x[col] = pd.to_numeric(frame[col], errors="coerce").fillna(imputes[col])
    return x.to_numpy(dtype=float)


def _fit_classifier(frame: pd.DataFrame, feature_cols: list[str], target_col: str, imputes: dict[str, float]) -> Any:
    y = frame[target_col].astype(int).to_numpy()
    if len(np.unique(y)) < 2:
        return float(np.mean(y))
    model = LogisticRegression(C=1.0, max_iter=1000)
    model.fit(_feature_matrix(frame, feature_cols, imputes), y)
    return model


def _predict_probability(model: Any, frame: pd.DataFrame, feature_cols: list[str], imputes: dict[str, float]) -> np.ndarray:
    if isinstance(model, float):
        return np.full(len(frame), model, dtype=float)
    return model.predict_proba(_feature_matrix(frame, feature_cols, imputes))[:, 1]


def _safe_auc(y_true: pd.Series, score: pd.Series) -> float | None:
    y = y_true.astype(int)
    if y.nunique() < 2:
        return None
    return float(roc_auc_score(y, score))


def _bootstrap_auc_ci(y_true: pd.Series, score: pd.Series, n_boot: int = 200) -> list[float | None]:
    y = y_true.astype(int).reset_index(drop=True)
    s = pd.Series(score, dtype=float).reset_index(drop=True)
    if y.nunique() < 2:
        return [None, None]
    rng = np.random.default_rng(42)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(y), size=len(y))
        if y.iloc[idx].nunique() < 2:
            continue
        vals.append(roc_auc_score(y.iloc[idx], s.iloc[idx]))
    if not vals:
        return [None, None]
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return [float(lo), float(hi)]


def _economic_score(frame: pd.DataFrame, actions: pd.Series, down_target_col: str, up_target_col: str, economic_col: str) -> float:
    work = frame.copy()
    work["action"] = actions.to_numpy()
    econ = economic_evaluation(work, down_target_col=down_target_col, up_target_col=up_target_col, economic_col=economic_col)
    return float(econ["perte_evitee_mean"] - econ["gain_manque_mean"] - 0.25 * econ["regret_moyen"])


def _verdict(down_auc: float | None, up_auc: float | None, economic: dict[str, Any]) -> str:
    aucs = [v for v in (down_auc, up_auc) if v is not None]
    if not aucs:
        return "INCONCLU"
    score = economic["perte_evitee_mean"] - economic["gain_manque_mean"]
    if min(aucs) >= 0.65 and score > 0:
        return "CONFIRMÉ"
    if min(aucs) >= 0.60 or score > 0:
        return "PROMETTEUR"
    if max(aucs) < 0.55 and score <= 0:
        return "REJETÉ"
    return "NEUTRE"
