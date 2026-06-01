"""UTIL-EMA-01 — Fonctions utilitaires communes pour l'étude EMA."""

from __future__ import annotations

import numpy as np
import pandas as pd


def crop_year(date: pd.Timestamp) -> int:
    """Retourne l'année culturale (octobre → septembre)."""
    return date.year if date.month >= 10 else date.year - 1


def expanding_zscore(series: pd.Series, min_periods: int = 60) -> pd.Series:
    """Z-score expandant anti-leakage : utilise uniquement l'historique disponible."""
    mu = series.expanding(min_periods=min_periods).mean().shift(1)
    sigma = series.expanding(min_periods=min_periods).std().shift(1)
    return (series - mu) / sigma.replace(0, np.nan)


def bootstrap_ci(values: np.ndarray, stat_fn, n_draws: int = 1000, alpha: float = 0.05, seed: int = 42) -> dict:
    """IC bootstrap (percentile) pour une statistique quelconque."""
    rng = np.random.default_rng(seed)
    n = len(values)
    draws = [stat_fn(rng.choice(values, size=n, replace=True)) for _ in range(n_draws)]
    lo = float(np.percentile(draws, 100 * alpha / 2))
    hi = float(np.percentile(draws, 100 * (1 - alpha / 2)))
    return {"estimate": float(stat_fn(values)), "ci_lo": lo, "ci_hi": hi, "alpha": alpha, "n_draws": n_draws}


def direction_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Fraction de cas où signe(y_pred) == signe(y_true)."""
    mask = y_true != 0
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(np.sign(y_true[mask]) == np.sign(y_pred[mask])))


def binary_target_from_future_return(future_return: pd.Series) -> pd.Series:
    """Binary target that preserves unknown future returns as NaN."""
    ret = pd.to_numeric(future_return, errors="coerce")
    return pd.Series(
        np.where(ret.notna(), (ret > 0.0).astype(float), np.nan),
        index=future_return.index,
        name=future_return.name,
    )


def binary_target_from_condition(condition: pd.Series, valid: pd.Series) -> pd.Series:
    """Binary target from a boolean condition, with explicit validity mask."""
    valid_mask = valid.fillna(False).astype(bool)
    return pd.Series(
        np.where(valid_mask, condition.fillna(False).astype(bool).astype(float), np.nan),
        index=condition.index,
        name=condition.name,
    )


def walk_forward_splits(dates: pd.Series, min_train_years: int = 3, test_years: int = 1) -> list[dict]:
    """Génère les splits walk-forward par année culturale."""
    cys = dates.apply(crop_year).unique()
    cys = sorted(cys)
    splits = []
    for i in range(min_train_years, len(cys)):
        train_cys = cys[:i]
        test_cy = cys[i]
        splits.append({
            "train_crop_years": [int(c) for c in train_cys],
            "test_crop_year": int(test_cy),
            "n_train_years": len(train_cys),
        })
    return splits


def benjamini_hochberg(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    """Correction Benjamini-Hochberg pour tests multiples (FDR)."""
    n = len(p_values)
    if n == 0:
        return []
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    rejected = [False] * n
    for rank, (orig_idx, p) in enumerate(indexed, start=1):
        if p <= alpha * rank / n:
            rejected[orig_idx] = True
        else:
            break
    return rejected
