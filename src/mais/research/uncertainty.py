"""Uncertainty quantification — CQR, split-conformal, probability calibration."""

from __future__ import annotations

import numpy as np
import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.research.uncertainty")


def run_split_conformal(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    alpha: float = 0.10,
) -> dict[str, float]:
    """Split-conformal prediction intervals on a calibration set.

    Assumes y_true / y_pred are the calibration fold.
    Returns the conformity score and empirical coverage.
    """
    residuals = np.abs(y_true - y_pred)
    n = len(residuals)
    q_level = np.ceil((1 - alpha) * (n + 1)) / n
    q_hat = float(np.quantile(residuals, min(q_level, 1.0)))

    # Empirical coverage (should be ≥ 1-alpha)
    covered = float(np.mean(residuals <= q_hat))
    return {"q_hat": q_hat, "coverage": covered, "alpha": alpha, "n_cal": n}


def calibrate_probabilities(
    y_true: np.ndarray,
    y_score: np.ndarray,
    method: str = "isotonic",
) -> tuple[np.ndarray, Any]:
    """Calibrate binary probability predictions.

    Returns (calibrated_probs, calibrator).
    """
    import warnings

    from sklearn.linear_model import LogisticRegression

    if method not in ("isotonic", "sigmoid"):
        raise ValueError("method must be 'isotonic' or 'sigmoid'")

    # Platt (sigmoid) via logistic regression on scores
    if method == "sigmoid":
        cal = LogisticRegression()
        cal.fit(y_score.reshape(-1, 1), y_true)
        calibrated = cal.predict_proba(y_score.reshape(-1, 1))[:, 1]
    else:
        from sklearn.isotonic import IsotonicRegression
        cal = IsotonicRegression(out_of_bounds="clip")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            calibrated = cal.fit_transform(y_score, y_true)

    return calibrated, cal


def compute_confidence_score(
    q10: np.ndarray,
    q50: np.ndarray,
    q90: np.ndarray,
    price_today: float = 1.0,
) -> np.ndarray:
    """Confidence score: 1 - (interval width / price) — tighter = more confident."""
    width = q90 - q10
    return np.clip(1.0 - width / (price_today + 1e-8), 0.0, 1.0)


def summarize_cqr_results(cqr_df: pd.DataFrame) -> pd.DataFrame:
    """Summary stats from a CQR results DataFrame."""
    required = {"horizon", "covered"}
    if not required.issubset(cqr_df.columns):
        return pd.DataFrame()

    rows = []
    for h, g in cqr_df.groupby("horizon"):
        cov = float(g["covered"].mean())
        width = float((g["q90"] - g["q10"]).mean()) if {"q90", "q10"}.issubset(g.columns) else float("nan")
        rows.append({"horizon": h, "coverage": cov, "width": width, "n": len(g)})
    return pd.DataFrame(rows)


# Stub for Any type hint without heavy import
try:
    from typing import Any
except ImportError:
    Any = object  # type: ignore
