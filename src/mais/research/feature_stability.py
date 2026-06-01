"""V7-37 — Analyse de stabilité des features (SHAP rolling)."""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "feature_stability.json"


def compute_rolling_feature_stability(
    x_df: pd.DataFrame,
    y: pd.Series,
    window_years: int = 2,
    stride_months: int = 6,
    max_features: int = 30,
) -> dict[str, Any]:
    try:
        import shap
        from lightgbm import LGBMClassifier
    except ImportError:
        return {"error": "lgbm_or_shap_unavailable"}

    feat_cols = x_df.columns.tolist()[:max_features]
    x_df = x_df[feat_cols]
    common = x_df.join(y.rename("target")).dropna()
    if len(common) < 200:
        return {"error": "insufficient_data", "n": len(common)}

    shap_windows: list[dict] = []
    start = common.index[0]
    end = common.index[-1]
    window = pd.DateOffset(years=window_years)
    stride = pd.DateOffset(months=stride_months)
    current = start

    while current + window <= end:
        mask = (common.index >= current) & (common.index < current + window)
        if mask.sum() < 50:
            current += stride
            continue
        x_w = common.loc[mask, feat_cols]
        y_w = common.loc[mask, "target"]
        if y_w.nunique() < 2:
            current += stride
            continue
        clf = LGBMClassifier(n_estimators=100, seed=42, verbose=-1, n_jobs=1)
        clf.fit(x_w, y_w)
        try:
            explainer = shap.TreeExplainer(clf)
            sv = explainer.shap_values(x_w)
            if isinstance(sv, list):
                sv = sv[1]
            vals = np.abs(sv).mean(axis=0)
            entry: dict[str, Any] = {"window_start": str(current.date())}
            entry.update(dict(zip(feat_cols, vals.tolist(), strict=False)))
            shap_windows.append(entry)
        except Exception:
            pass
        current += stride

    if not shap_windows:
        return {"error": "no_windows_computed"}

    df_stability = pd.DataFrame(shap_windows).set_index("window_start")
    df_stability = df_stability.astype(float)

    metrics: dict[str, dict] = {}
    for col in feat_cols:
        if col not in df_stability.columns:
            continue
        s = df_stability[col]
        mean_imp = float(s.mean())
        std_imp = float(s.std()) if len(s) > 1 else 0.0
        cv = std_imp / (mean_imp + 1e-9)
        metrics[col] = {
            "mean_importance": round(mean_imp, 6),
            "std_importance": round(std_imp, 6),
            "cv_importance": round(cv, 4),
        }

    sorted_by_cv = sorted(metrics.items(), key=lambda x: x[1]["cv_importance"])
    top20_stable = [{"feature": f, **v} for f, v in sorted_by_cv[:20]]
    top20_unstable = [{"feature": f, **v} for f, v in sorted_by_cv[-20:]]

    return {
        "n_windows": len(shap_windows),
        "n_features": len(feat_cols),
        "top20_stable": top20_stable,
        "top20_unstable": top20_unstable,
    }


def run_feature_stability(df: pd.DataFrame) -> dict[str, Any]:
    exclude = {"y_", "Date", "date", "return_", "future_", "storage_", "prob_"}
    feat_cols = [c for c in df.columns
                 if not any(p in c for p in exclude)
                 and df[c].dtype in [np.float64, float]
                 and df[c].notna().mean() > 0.3][:40]

    y_col = next((c for c in ["y_up_h20", "y_up_h40", "y_up_h60"] if c in df.columns), None)
    if not y_col or not feat_cols:
        return {"version": "V7-37", "verdict": "NO_DATA"}

    stability = compute_rolling_feature_stability(df[feat_cols], df[y_col])
    stability.update({"version": "V7-37", "target": y_col, "verdict": "STABILITY_ANALYZED"})
    return stability


def save_feature_stability(df: pd.DataFrame) -> dict[str, Any]:
    result = run_feature_stability(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-37",
        target=result.get("target", "unknown"),
        horizon=0,
        model="lgbm_shap_rolling",
        cv_protocol="rolling_window_2y",
        embargo_days=0,
        n_oof=result.get("n_windows", 0),
        features=[f["feature"] for f in result.get("top20_stable", [])[:5]],
        metrics={
            "n_windows": result.get("n_windows"),
            "n_stable_features": len(result.get("top20_stable", [])),
        },
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
