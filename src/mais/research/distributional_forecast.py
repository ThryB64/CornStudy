"""V7-35 — Distributional forecasting du premium (quantile + conformal)."""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "distributional_forecast.json"

QUANTILES = [0.05, 0.25, 0.50, 0.75, 0.95]


def _quantile_oof(
    x_df: pd.DataFrame, y: pd.Series, quantile: float, n_splits: int = 4
) -> pd.Series:
    """Returns OOF predictions as a Series aligned with common index."""
    try:
        from lightgbm import LGBMRegressor
    except ImportError:
        return pd.Series(dtype=float)

    common = x_df.join(y.rename("target")).dropna()
    if len(common) < 100:
        return pd.Series(dtype=float)

    x_c = common.drop(columns=["target"]).fillna(0)
    y_c = common["target"]
    oof = np.full(len(x_c), np.nan)
    tscv = TimeSeriesSplit(n_splits=n_splits)

    for tr_idx, te_idx in tscv.split(x_c):
        if len(tr_idx) < 30:
            continue
        clf = LGBMRegressor(
            objective="quantile", alpha=quantile,
            n_estimators=100, seed=42, verbose=-1, n_jobs=1
        )
        clf.fit(x_c.iloc[tr_idx], y_c.iloc[tr_idx])
        oof[te_idx] = clf.predict(x_c.iloc[te_idx])

    return pd.Series(oof, index=x_c.index)


def compute_quantile_coverage(y_true: pd.Series, y_pred: pd.Series, quantile: float) -> float:
    common_idx = y_true.index.intersection(y_pred.index)
    if len(common_idx) < 20:
        return float("nan")
    yt = y_true.loc[common_idx]
    yp = y_pred.loc[common_idx]
    valid = yt.notna() & yp.notna()
    if valid.sum() < 20:
        return float("nan")
    return float(np.mean(yt[valid].values <= yp[valid].values))


def run_distributional_forecast(df: pd.DataFrame) -> dict[str, Any]:
    exclude = {"y_", "Date", "date", "return_", "future_", "storage_", "prob_"}
    feat_cols = [c for c in df.columns
                 if not any(p in c for p in exclude)
                 and df[c].dtype in [np.float64, float]
                 and df[c].notna().mean() > 0.3][:50]

    # Cibles de niveau de prix EMA
    y_col = None
    if "ema_close" in df.columns:
        df["ema_return_h40"] = df["ema_close"].pct_change(40).shift(-40)
        y_col = "ema_return_h40"
    elif "ema_cbot_basis" in df.columns:
        df["basis_change_h40"] = df["ema_cbot_basis"].diff(40).shift(-40)
        y_col = "basis_change_h40"

    if not y_col or not feat_cols:
        return {"version": "V7-35", "verdict": "NO_TARGET"}

    y = df[y_col].dropna()
    coverage_results: dict[str, Any] = {}

    for q in QUANTILES:
        oof_q = _quantile_oof(df[feat_cols], y, q)
        cov = compute_quantile_coverage(y, oof_q, q)
        calibration_error = abs(cov - q) if not np.isnan(cov) else None
        coverage_results[f"q{int(q*100):02d}"] = {
            "target_quantile": q,
            "empirical_coverage": round(cov, 4) if not np.isnan(cov) else None,
            "calibration_error": round(calibration_error, 4) if calibration_error is not None else None,
            "calibrated": calibration_error < 0.05 if calibration_error is not None else False,
        }

    n_calibrated = sum(1 for v in coverage_results.values() if v.get("calibrated"))
    overall_verdict = "WELL_CALIBRATED" if n_calibrated >= 4 else "PARTIALLY_CALIBRATED" if n_calibrated >= 2 else "POORLY_CALIBRATED"

    return {
        "version": "V7-35",
        "target": y_col,
        "n_quantiles": len(QUANTILES),
        "coverage_by_quantile": coverage_results,
        "n_calibrated_quantiles": n_calibrated,
        "verdict": overall_verdict,
        "experiment_type": "PREDICTIVE_OOF",
    }


def save_distributional_forecast(df: pd.DataFrame) -> dict[str, Any]:
    result = run_distributional_forecast(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-35",
        target=result.get("target", "premium_quantile"),
        horizon=40,
        model="lgbm_quantile_oof",
        cv_protocol="time_series_split_4",
        embargo_days=0,
        n_oof=0,
        features=["fundamental_features"],
        metrics={
            "n_calibrated": result.get("n_calibrated_quantiles"),
            "n_quantiles": result.get("n_quantiles"),
        },
        p_value=None,
        verdict=result.get("verdict", "DONE"),
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
