"""Probability calibration for the Maize Direction Indicator.

Fits Platt (logistic regression) and Isotonic regression calibrators on
train/validation splits (pre-2023 only). Never touches 2023–2025 data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.indicator.calibration")


def ece(y_prob: np.ndarray, y_true: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error."""
    bins = np.linspace(0, 1, n_bins + 1)
    total = len(y_prob)
    result = 0.0
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (y_prob >= lo) & (y_prob < hi)
        if mask.sum() == 0:
            continue
        result += (mask.sum() / total) * abs(y_true[mask].mean() - y_prob[mask].mean())
    return float(result)


def brier(y_prob: np.ndarray, y_true: np.ndarray) -> float:
    return float(np.mean((y_prob - y_true) ** 2))


def reliability_curve(
    y_prob: np.ndarray, y_true: np.ndarray, n_bins: int = 10
) -> pd.DataFrame:
    bins = np.linspace(0, 1, n_bins + 1)
    rows = []
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (y_prob >= lo) & (y_prob < hi)
        n = int(mask.sum())
        if n == 0:
            continue
        rows.append({
            "bin_low": lo,
            "bin_high": hi,
            "bin_mid": (lo + hi) / 2,
            "mean_pred": float(y_prob[mask].mean()),
            "fraction_positive": float(y_true[mask].mean()),
            "n": n,
        })
    return pd.DataFrame(rows)


def fit_p_correct_model(*args, **kwargs):
    """Fit the R&D-07 calibrated P(correct) model.

    Kept in indicator.calibration as the production-facing entry point while
    the implementation lives in mais.research.p_correct_model.
    """
    from mais.research.p_correct_model import fit_p_correct_model as _fit_p_correct_model

    return _fit_p_correct_model(*args, **kwargs)


class PlattCalibrator:
    """Logistic regression (Platt scaling) calibrator."""

    def __init__(self, c: float = 1.0) -> None:
        self.c = float(c)
        self._a: float = 1.0
        self._b: float = 0.0

    def fit(self, y_prob: np.ndarray, y_true: np.ndarray) -> PlattCalibrator:
        try:
            from sklearn.linear_model import LogisticRegression

            lr = LogisticRegression(C=self.c, solver="lbfgs", max_iter=1000)
            lr.fit(y_prob.reshape(-1, 1), y_true)
            self._a = float(lr.coef_[0][0])
            self._b = float(lr.intercept_[0])
        except ImportError:
            log.warning("sklearn_not_available", fallback="identity calibrator")
        return self

    def transform(self, y_prob: np.ndarray) -> np.ndarray:
        z = np.clip(self._a * y_prob + self._b, -50.0, 50.0)
        return 1.0 / (1.0 + np.exp(-z))


def compare_platt_c_values(
    y_prob_train: np.ndarray,
    y_true_train: np.ndarray,
    y_prob_val: np.ndarray,
    y_true_val: np.ndarray,
    c_values: tuple[float, ...] = (1e10, 1.0, 0.1),
) -> pd.DataFrame:
    """Compare Platt regularisation strengths on validation data."""
    rows = []
    for c in c_values:
        y_cal = PlattCalibrator(c=c).fit(y_prob_train, y_true_train).transform(y_prob_val)
        rows.append(
            {
                "method": "platt",
                "C": float(c),
                "ece": ece(y_cal, y_true_val),
                "brier": brier(y_cal, y_true_val),
                "prob_std": float(np.std(y_cal)),
                "prob_distance_mean": float(np.mean(np.abs(y_cal - 0.5) * 2.0)),
            }
        )
    return pd.DataFrame(rows)


class IsotonicCalibrator:
    """Isotonic regression calibrator."""

    def __init__(self) -> None:
        self._ir = None

    def fit(self, y_prob: np.ndarray, y_true: np.ndarray) -> IsotonicCalibrator:
        try:
            from sklearn.isotonic import IsotonicRegression
            self._ir = IsotonicRegression(out_of_bounds="clip")
            self._ir.fit(y_prob, y_true)
        except ImportError:
            log.warning("sklearn_not_available", fallback="identity calibrator")
        return self

    def transform(self, y_prob: np.ndarray) -> np.ndarray:
        if self._ir is None:
            return y_prob
        return np.array(self._ir.transform(y_prob), dtype=float)


def analyze_calibration(
    calib_preds: pd.DataFrame,
    horizon: int = 20,
    model: str = "ridge_factors",
    train_folds: list[int] | None = None,
    val_folds: list[int] | None = None,
    max_date: str = "2022-12-31",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calibration analysis for a given model and horizon.

    Returns (results_df, reliability_df). Calibrators are trained on train_folds
    and evaluated on val_folds — never on data after max_date (reserved for IND-08).
    """
    sub = calib_preds[
        (calib_preds["model"] == model)
        & (calib_preds["horizon"] == horizon)
        & (calib_preds["Date"] <= pd.Timestamp(max_date))
    ].copy()

    p_col = f"p_up_h{horizon}"
    if p_col not in sub.columns or sub[p_col].isna().all():
        log.warning("p_up_col_missing_or_all_nan", col=p_col, model=model)
        return pd.DataFrame(), pd.DataFrame()

    sub = sub[sub[p_col].notna()].copy()
    sub["Date"] = pd.to_datetime(sub["Date"])
    sub["y_binary"] = (sub["y_true"] > 0).astype(float)

    all_folds = sorted(sub["fold"].unique())
    if train_folds is None:
        n_train = max(1, len(all_folds) - 2)
        train_folds = all_folds[:n_train]
        val_folds = all_folds[n_train:]

    train = sub[sub["fold"].isin(train_folds)]
    val = sub[sub["fold"].isin(val_folds)]

    if len(train) < 50 or len(val) < 50:
        log.warning(
            "calibration_insufficient_data", n_train=len(train), n_val=len(val)
        )
        return pd.DataFrame(), pd.DataFrame()

    y_prob_tr = train[p_col].values.astype(float)
    y_true_tr = train["y_binary"].values.astype(float)
    y_prob_val = val[p_col].values.astype(float)
    y_true_val = val["y_binary"].values.astype(float)

    def _row(method: str, y_prob: np.ndarray) -> dict:
        return {
            "method": method,
            "ece": ece(y_prob, y_true_val),
            "brier": brier(y_prob, y_true_val),
            "n_train": len(train),
            "n_val": len(val),
            "horizon": horizon,
            "model": model,
        }

    # Baseline (uncalibrated)
    results = [_row("uncalibrated", y_prob_val)]
    rel_curves = [reliability_curve(y_prob_val, y_true_val)]
    rel_curves[0]["method"] = "uncalibrated"

    # Platt — V3 keeps C=1.0 as the regularized production compromise.
    platt_grid = compare_platt_c_values(y_prob_tr, y_true_tr, y_prob_val, y_true_val)
    if not platt_grid.empty:
        chosen = platt_grid[platt_grid["C"] == 1.0]
        best = chosen.iloc[0] if not chosen.empty else platt_grid.iloc[0]
        y_platt = PlattCalibrator(c=float(best["C"])).fit(y_prob_tr, y_true_tr).transform(y_prob_val)
        platt_row = _row("platt", y_platt)
        platt_row["C"] = float(best["C"])
        platt_row["prob_std"] = float(np.std(y_platt))
        results.append(platt_row)
        rc_platt = reliability_curve(y_platt, y_true_val)
        rc_platt["method"] = "platt"
        rc_platt["C"] = float(best["C"])
        rel_curves.append(rc_platt)

    # Isotonic
    y_iso = IsotonicCalibrator().fit(y_prob_tr, y_true_tr).transform(y_prob_val)
    results.append(_row("isotonic", y_iso))
    rc_iso = reliability_curve(y_iso, y_true_val)
    rc_iso["method"] = "isotonic"
    rel_curves.append(rc_iso)

    results_df = pd.DataFrame(results)
    reliability_df = pd.concat(rel_curves, ignore_index=True)
    reliability_df["horizon"] = horizon
    reliability_df["model"] = model

    log.info(
        "calibration_done",
        model=model,
        horizon=horizon,
        ece_before=round(results[0]["ece"], 4),
        ece_platt=round(results[1]["ece"], 4),
        ece_iso=round(results[2]["ece"], 4),
    )
    return results_df, reliability_df
