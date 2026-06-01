"""V7-38 — Étude du model decay."""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "model_decay.json"


def analyze_model_decay(
    x_df: pd.DataFrame,
    y: pd.Series,
    n_splits: int = 5,
) -> dict[str, Any]:
    try:
        from lightgbm import LGBMClassifier
        from sklearn.metrics import roc_auc_score
    except ImportError:
        return {"error": "lgbm_unavailable"}

    common = x_df.join(y.rename("target")).dropna()
    if len(common) < 200:
        return {"error": "insufficient_data", "n": len(common)}

    x_c = common.drop(columns=["target"]).fillna(0)
    y_c = common["target"]
    tscv = TimeSeriesSplit(n_splits=n_splits)
    decay_records: list[dict] = []

    for tr_idx, te_idx in tscv.split(x_c):
        if len(tr_idx) < 50 or y_c.iloc[tr_idx].nunique() < 2:
            continue
        train_end = x_c.index[tr_idx[-1]]
        clf = LGBMClassifier(n_estimators=100, seed=42, verbose=-1, n_jobs=1)
        clf.fit(x_c.iloc[tr_idx], y_c.iloc[tr_idx])

        for i in te_idx:
            age_days = int((x_c.index[i] - train_end).days)
            pred = float(clf.predict_proba(x_c.iloc[[i]])[:, 1][0])
            decay_records.append({
                "age_days": age_days,
                "prediction": pred,
                "true_label": float(y_c.iloc[i]),
            })

    if not decay_records:
        return {"error": "no_decay_records"}

    df_decay = pd.DataFrame(decay_records)
    bins = [0, 30, 90, 180, 365, 9999]
    labels = ["0-30d", "30-90d", "90-180d", "180-365d", "365d+"]
    df_decay["age_bucket"] = pd.cut(df_decay["age_days"], bins=bins, labels=labels, right=False)

    auc_by_age: dict[str, Any] = {}
    for bucket in labels:
        sub = df_decay[df_decay["age_bucket"] == bucket]
        if len(sub) >= 20 and sub["true_label"].nunique() > 1:
            from sklearn.metrics import roc_auc_score
            auc = round(float(roc_auc_score(sub["true_label"], sub["prediction"])), 4)
            auc_by_age[bucket] = {"auc": auc, "n": len(sub)}

    # Seuil de decay
    first_auc = next((v["auc"] for v in auc_by_age.values()), None)
    decay_threshold_days: int | None = None
    if first_auc:
        for bucket, v in auc_by_age.items():
            if v["auc"] < first_auc - 0.03:
                decay_threshold_days = int(bucket.split("-")[0].replace("d", "").replace("+", ""))
                break

    recommendation = (
        f"Re-entraîner tous les {max(30, (decay_threshold_days or 180))} jours"
        if decay_threshold_days
        else "Decay faible : re-entraîner annuellement"
    )

    return {
        "n_records": len(decay_records),
        "auc_by_model_age": auc_by_age,
        "decay_threshold_days": decay_threshold_days,
        "retraining_recommendation": recommendation,
    }


def run_model_decay(df: pd.DataFrame) -> dict[str, Any]:
    exclude = {"y_", "Date", "date", "return_", "future_", "storage_", "prob_"}
    feat_cols = [c for c in df.columns
                 if not any(p in c for p in exclude)
                 and df[c].dtype in [np.float64, float]
                 and df[c].notna().mean() > 0.3][:60]

    y_col = next((c for c in ["y_up_h20", "y_up_h40"] if c in df.columns), None)
    if not y_col or not feat_cols:
        return {"version": "V7-38", "verdict": "NO_DATA"}

    decay = analyze_model_decay(df[feat_cols], df[y_col])
    decay.update({"version": "V7-38", "target": y_col, "verdict": "MODEL_DECAY_ANALYZED"})
    return decay


def save_model_decay(df: pd.DataFrame) -> dict[str, Any]:
    result = run_model_decay(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-38",
        target=result.get("target", "unknown"),
        horizon=20,
        model="lgbm_decay_study",
        cv_protocol="time_series_split_5",
        embargo_days=0,
        n_oof=result.get("n_records", 0),
        features=[],
        metrics={
            "decay_threshold_days": result.get("decay_threshold_days"),
            "n_age_buckets": len(result.get("auc_by_model_age", {})),
        },
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
