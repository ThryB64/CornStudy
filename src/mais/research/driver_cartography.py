"""V7-33 — Cartographie des drivers par horizon et par régime de basis."""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "driver_cartography.json"

HORIZONS = [20, 40, 60, 90, 120]

TARGET_MAP = {
    20: ["y_up_h20", "y_up_h20_ema"],
    40: ["y_rel_outperform_h40", "y_up_h40", "y_up_h40_ema"],
    60: ["y_rel_outperform_h60", "y_up_h60", "y_up_h60_ema"],
    90: ["y_rel_outperform_h90", "y_up_h90", "y_up_h90_ema"],
    120: ["y_rel_outperform_h120", "y_up_h120"],
}


def _select_target(df: pd.DataFrame, horizon: int) -> str | None:
    for col in TARGET_MAP.get(horizon, []):
        if col in df.columns and df[col].dropna().__len__() > 100:
            return col
    return None


def _get_feature_cols(df: pd.DataFrame) -> list[str]:
    """Sélectionne les features pertinentes pour la cartographie."""
    exclude_patterns = ["y_", "Date", "date", "return_", "future_", "storage_", "prob_", "sell_regret"]
    target_names = {
        col for h_targets in TARGET_MAP.values() for col in h_targets
    }
    cols = [
        c for c in df.columns
        if not any(p in c for p in exclude_patterns)
        and c not in target_names
        and df[c].dtype in [np.float64, np.float32, np.int64, np.int32, float, int]
        and df[c].notna().mean() > 0.3
    ]
    return cols[:100]  # max 100 features for speed


def compute_shap_importance_oof(
    df: pd.DataFrame,
    feature_cols: list[str],
    y: pd.Series,
    n_splits: int = 3,
) -> dict[str, float]:
    """SHAP importance OOF via LightGBM."""
    try:
        import shap
        from lightgbm import LGBMClassifier
    except ImportError:
        return _lgbm_importance_fallback(df, feature_cols, y, n_splits)

    x_all = df[feature_cols].fillna(0)
    common = x_all.join(y.rename("target")).dropna()
    if len(common) < 100:
        return {}

    x_c = common.drop(columns=["target"])
    y_c = common["target"]

    shap_vals = np.zeros(x_c.shape[1])
    tscv = TimeSeriesSplit(n_splits=n_splits)
    n_folds = 0

    for train_idx, test_idx in tscv.split(x_c):
        if len(test_idx) < 20 or len(train_idx) < 50:
            continue
        clf = LGBMClassifier(n_estimators=100, seed=42, verbose=-1, n_jobs=1)
        clf.fit(x_c.iloc[train_idx], y_c.iloc[train_idx])
        try:
            explainer = shap.TreeExplainer(clf)
            sv = explainer.shap_values(x_c.iloc[test_idx])
            if isinstance(sv, list):
                sv = sv[1]
            shap_vals += np.abs(sv).mean(axis=0)
            n_folds += 1
        except Exception:
            pass

    if n_folds == 0:
        return {}

    shap_vals /= n_folds
    importance = dict(zip(x_c.columns, shap_vals.tolist(), strict=False))
    return dict(sorted(importance.items(), key=lambda x: -x[1]))


def _lgbm_importance_fallback(
    df: pd.DataFrame,
    feature_cols: list[str],
    y: pd.Series,
    n_splits: int = 3,
) -> dict[str, float]:
    """Fallback: feature importance LightGBM sans SHAP."""
    try:
        from lightgbm import LGBMClassifier
    except ImportError:
        return {}

    x_all = df[feature_cols].fillna(0)
    common = x_all.join(y.rename("target")).dropna()
    if len(common) < 100:
        return {}

    x_c = common.drop(columns=["target"])
    y_c = common["target"]

    clf = LGBMClassifier(n_estimators=100, seed=42, verbose=-1, n_jobs=1)
    clf.fit(x_c, y_c)
    importance = dict(zip(x_c.columns, clf.feature_importances_.tolist(), strict=False))
    return dict(sorted(importance.items(), key=lambda x: -x[1]))


def compute_rolling_importance(
    df: pd.DataFrame,
    feature_cols: list[str],
    y: pd.Series,
    window_years: int = 3,
) -> dict[str, Any]:
    """Feature importance roulante par fenêtre de 3 ans."""
    try:
        from lightgbm import LGBMClassifier
    except ImportError:
        return {}

    x_all = df[feature_cols].fillna(0)
    combined = x_all.join(y.rename("target")).dropna()
    years = combined.index.year.unique()
    rolling = {}

    for year in sorted(years):
        start_y = year - window_years
        mask = (combined.index.year >= start_y) & (combined.index.year <= year)
        if mask.sum() < 50:
            continue
        x_w = combined.loc[mask].drop(columns=["target"])
        y_w = combined.loc[mask, "target"]
        if len(y_w.unique()) < 2:
            continue
        clf = LGBMClassifier(n_estimators=50, seed=42, verbose=-1, n_jobs=1)
        clf.fit(x_w, y_w)
        top3 = sorted(zip(x_w.columns, clf.feature_importances_, strict=False), key=lambda x: -x[1])[:3]
        rolling[str(year)] = [{"feature": f, "importance": float(v)} for f, v in top3]

    return rolling


def run_driver_cartography(df: pd.DataFrame) -> dict[str, Any]:
    """Cartographie complète des drivers par horizon."""
    feature_cols = _get_feature_cols(df)
    results_by_horizon: dict[str, Any] = {}

    for horizon in HORIZONS:
        y_col = _select_target(df, horizon)
        if y_col is None:
            results_by_horizon[f"H{horizon}"] = {"verdict": "NO_TARGET"}
            continue

        y = df[y_col].dropna()
        n_available = len(y)
        if n_available < 100:
            results_by_horizon[f"H{horizon}"] = {"verdict": "TOO_FEW_SAMPLES", "n": n_available}
            continue

        # SHAP importance OOF
        importance = compute_shap_importance_oof(df, feature_cols, y, n_splits=3)
        top10 = list(importance.items())[:10] if importance else []

        # Rolling importance
        rolling = compute_rolling_importance(df, feature_cols[:30], y)

        results_by_horizon[f"H{horizon}"] = {
            "target": y_col,
            "n_obs": n_available,
            "top10_drivers": [{"feature": f, "importance": round(float(v), 6)} for f, v in top10],
            "rolling_top3": rolling,
            "n_features_used": len(feature_cols),
        }

    # Stabilité des top features sur les horizons disponibles
    all_top_features: dict[str, int] = {}
    for h_result in results_by_horizon.values():
        for item in h_result.get("top10_drivers", []):
            f = item["feature"]
            all_top_features[f] = all_top_features.get(f, 0) + 1

    stable_features = [f for f, cnt in sorted(all_top_features.items(), key=lambda x: -x[1]) if cnt >= 2]

    return {
        "version": "V7-33",
        "n_horizons": len(HORIZONS),
        "n_features": len(feature_cols),
        "results_by_horizon": results_by_horizon,
        "stable_across_horizons": stable_features[:10],
        "experiment_type": "DESCRIPTIVE_ECONOMIC",
        "verdict": "DRIVER_CARTOGRAPHY_DONE",
    }


def save_driver_cartography(df: pd.DataFrame) -> dict[str, Any]:
    result = run_driver_cartography(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-33",
        target="driver_cartography",
        horizon=0,
        model="lgbm_shap_oof",
        cv_protocol="time_series_split_3",
        embargo_days=0,
        n_oof=0,
        features=result.get("stable_across_horizons", [])[:5],
        metrics={
            "n_horizons": result["n_horizons"],
            "n_stable_features": len(result.get("stable_across_horizons", [])),
        },
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
