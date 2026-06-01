"""V7-27 — Modèles multi-facteurs conditionnels par régime de basis."""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment
from mais.research.basis_regimes_v7 import REGIME_NAMES, _build_regimes

_OUTPUT = ARTEFACTS_DIR / "v7" / "conditional_models.json"


def _oof_auc_on_subset(
    x_df: pd.DataFrame, y: pd.Series, mask: pd.Series, n_splits: int = 3
) -> dict[str, Any]:
    try:
        from lightgbm import LGBMClassifier
        from sklearn.metrics import roc_auc_score
    except ImportError:
        return {"verdict": "LGBM_UNAVAILABLE"}

    regime_x = x_df[mask]
    regime_y = y[mask]
    common = regime_x.join(regime_y.rename("target")).dropna()
    if len(common) < 30 or common["target"].nunique() < 2:
        return {"verdict": "TOO_FEW_SAMPLES", "n": len(common)}

    x_c = common.drop(columns=["target"]).fillna(0)
    y_c = common["target"]

    tscv = TimeSeriesSplit(n_splits=n_splits)
    oof = np.full(len(x_c), np.nan)
    for tr_idx, te_idx in tscv.split(x_c):
        if len(tr_idx) < 10 or y_c.iloc[tr_idx].nunique() < 2:
            continue
        clf = LGBMClassifier(n_estimators=100, seed=42, verbose=-1, n_jobs=1)
        clf.fit(x_c.iloc[tr_idx], y_c.iloc[tr_idx])
        oof[te_idx] = clf.predict_proba(x_c.iloc[te_idx])[:, 1]

    valid = ~np.isnan(oof) & y_c.notna().values
    if valid.sum() < 20 or len(np.unique(y_c.values[valid])) < 2:
        return {"verdict": "INSUFFICIENT_OOF", "n_valid": int(valid.sum())}

    from sklearn.metrics import roc_auc_score
    return {"auc": round(float(roc_auc_score(y_c.values[valid], oof[valid])), 4),
            "n": int(valid.sum()), "verdict": "OK"}


def run_conditional_models(df: pd.DataFrame) -> dict[str, Any]:
    regimes_df = _build_regimes(df)
    regimes = regimes_df["regime"]

    exclude = {"y_", "Date", "date", "return_", "future_", "storage_", "prob_"}
    feat_cols = [c for c in df.columns
                 if not any(p in c for p in exclude)
                 and df[c].dtype in [np.float64, float]
                 and df[c].notna().mean() > 0.3][:60]

    y_col = next((c for c in ["y_up_h20", "y_up_h40", "y_up_h60"] if c in df.columns), None)
    if not y_col or not feat_cols:
        return {"version": "V7-27", "verdict": "NO_DATA"}

    y = df[y_col]

    # Global model
    global_result = _oof_auc_on_subset(df[feat_cols], y, pd.Series(True, index=df.index))

    regime_results: dict[str, Any] = {}
    for regime in REGIME_NAMES:
        mask = regimes.reindex(df.index).fillna("NORMAL") == regime
        regime_results[regime] = _oof_auc_on_subset(df[feat_cols], y, mask)

    gains = {
        r: round((v.get("auc") or 0) - (global_result.get("auc") or 0), 4)
        for r, v in regime_results.items()
        if "auc" in v
    }
    best_regime = max(gains, key=lambda r: gains[r]) if gains else None

    return {
        "version": "V7-27",
        "target": y_col,
        "global_auc": global_result.get("auc"),
        "regime_results": regime_results,
        "delta_vs_global": gains,
        "best_regime": best_regime,
        "experiment_type": "PREDICTIVE_OOF",
        "verdict": "CONDITIONAL_MODELS_DONE",
    }


def save_conditional_models(df: pd.DataFrame) -> dict[str, Any]:
    result = run_conditional_models(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-27",
        target=result.get("target", "unknown"),
        horizon=40,
        model="lgbm_regime_conditional",
        cv_protocol="time_series_split_3",
        embargo_days=0,
        n_oof=0,
        features=["regime_conditional"],
        metrics={
            "global_auc": result.get("global_auc"),
            "best_regime": result.get("best_regime"),
            "n_regimes": len(REGIME_NAMES),
        },
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
