"""V7-14 — Explicabilité et analyse des erreurs du meta-modèle."""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment
from mais.research.basis_regimes_v7 import _build_regimes

_OUTPUT = ARTEFACTS_DIR / "v7" / "error_analysis.json"


def analyze_model_errors(
    y_true: pd.Series,
    y_pred_proba: pd.Series,
    x_df: pd.DataFrame,
    regimes: pd.Series,
    threshold: float = 0.5,
) -> dict[str, Any]:
    common_idx = y_true.index.intersection(y_pred_proba.index).intersection(x_df.index)
    if len(common_idx) < 50:
        return {"verdict": "INSUFFICIENT_DATA"}

    yt = y_true.loc[common_idx]
    yp = y_pred_proba.loc[common_idx]
    y_pred_class = (yp >= threshold).astype(int)
    error_mask = yt.astype(int) != y_pred_class
    fp_mask = (y_pred_class == 1) & (yt.astype(int) == 0)
    fn_mask = (y_pred_class == 0) & (yt.astype(int) == 1)

    reg = regimes.reindex(common_idx).fillna("NORMAL")
    errors_by_regime: dict[str, Any] = {}
    for regime in reg.unique():
        r_mask = reg == regime
        total = int(r_mask.sum())
        if total == 0:
            continue
        errors_by_regime[regime] = {
            "total": total,
            "error_rate": round(float(error_mask[r_mask].mean()), 4),
            "fp_rate": round(float(fp_mask[r_mask].mean()), 4),
            "fn_rate": round(float(fn_mask[r_mask].mean()), 4),
        }

    # SHAP des erreurs
    top_error_features: list[dict] = []
    try:
        import shap
        from lightgbm import LGBMClassifier
        x_c = x_df.loc[common_idx].fillna(0)
        is_error = error_mask.astype(int)
        if is_error.nunique() > 1 and len(x_c) > 50:
            clf = LGBMClassifier(n_estimators=100, seed=42, verbose=-1, n_jobs=1)
            clf.fit(x_c, is_error)
            explainer = shap.TreeExplainer(clf)
            sv = explainer.shap_values(x_c)
            if isinstance(sv, list):
                sv = sv[1]
            mean_abs = np.abs(sv).mean(axis=0)
            top_error_features = sorted(
                [{"feature": c, "shap_importance": round(float(v), 6)}
                 for c, v in zip(x_c.columns, mean_abs, strict=False)],
                key=lambda x: -x["shap_importance"]
            )[:10]
    except Exception:
        pass

    return {
        "global_error_rate": round(float(error_mask.mean()), 4),
        "fp_rate": round(float(fp_mask.mean()), 4),
        "fn_rate": round(float(fn_mask.mean()), 4),
        "n_errors": int(error_mask.sum()),
        "errors_by_regime": errors_by_regime,
        "top10_error_features": top_error_features,
    }


def run_error_analysis(df: pd.DataFrame) -> dict[str, Any]:
    exclude = {"y_", "Date", "date", "return_", "future_", "storage_", "prob_"}
    feat_cols = [c for c in df.columns
                 if not any(p in c for p in exclude)
                 and df[c].dtype in [np.float64, float]
                 and df[c].notna().mean() > 0.3][:60]

    y_col = next((c for c in ["y_up_h20", "y_up_h40"] if c in df.columns), None)
    if not y_col or not feat_cols:
        return {"version": "V7-14", "verdict": "NO_DATA"}

    common = df[feat_cols].join(df[y_col].rename("target")).dropna()
    if len(common) < 200:
        return {"version": "V7-14", "verdict": "INSUFFICIENT_DATA"}

    x_c = common.drop(columns=["target"]).fillna(0)
    y_c = common["target"]

    try:
        from lightgbm import LGBMClassifier
        tscv = TimeSeriesSplit(n_splits=4)
        oof = np.full(len(x_c), np.nan)
        for tr_idx, te_idx in tscv.split(x_c):
            if len(tr_idx) < 30 or y_c.iloc[tr_idx].nunique() < 2:
                continue
            clf = LGBMClassifier(n_estimators=100, seed=42, verbose=-1, n_jobs=1)
            clf.fit(x_c.iloc[tr_idx], y_c.iloc[tr_idx])
            oof[te_idx] = clf.predict_proba(x_c.iloc[te_idx])[:, 1]

        oof_series = pd.Series(oof, index=x_c.index)
        valid = ~oof_series.isna()
        regimes_df = _build_regimes(df.reindex(x_c.index[valid]))
        regimes = regimes_df["regime"]

        error_result = analyze_model_errors(
            y_c[valid], oof_series[valid], x_c[valid], regimes
        )
    except Exception as exc:
        return {"version": "V7-14", "verdict": "COMPUTATION_ERROR", "error": str(exc)}

    error_result.update({"version": "V7-14", "target": y_col, "verdict": "ERROR_ANALYSIS_DONE"})
    return error_result


def save_error_analysis(df: pd.DataFrame) -> dict[str, Any]:
    result = run_error_analysis(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-14",
        target=result.get("target", "error_analysis"),
        horizon=20,
        model="lgbm_error_analysis",
        cv_protocol="time_series_split_4",
        embargo_days=0,
        n_oof=result.get("n_errors", 0),
        features=[f["feature"] for f in result.get("top10_error_features", [])[:5]],
        metrics={
            "global_error_rate": result.get("global_error_rate"),
            "n_regimes": len(result.get("errors_by_regime", {})),
        },
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
