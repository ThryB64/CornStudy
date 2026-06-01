"""V7-12 — Modèle P(correct) et calibration avancée."""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "p_correct_model.json"


def build_p_correct_features(df: pd.DataFrame, primary_proba: pd.Series) -> pd.DataFrame:
    """Features du modèle P(correct) : confiance, régime, qualité données."""
    feats: dict[str, pd.Series] = {}
    feats["primary_proba"] = primary_proba
    feats["primary_distance_to_05"] = (primary_proba - 0.5).abs()

    if "ema_cbot_basis_zscore_52w" in df.columns:
        feats["basis_regime_z"] = df["ema_cbot_basis_zscore_52w"]
    if "corn_realized_vol_20" in df.columns:
        feats["vol_ratio"] = df["corn_realized_vol_20"] / df.get(
            "corn_realized_vol_60", df["corn_realized_vol_20"]
        )
    if "factor_weather_belt_stress" in df.columns:
        feats["weather_stress"] = df["factor_weather_belt_stress"]
    if "cot_open_interest" in df.columns:
        coi = df["cot_open_interest"].expanding().rank(pct=True)
        feats["oi_percentile"] = coi

    return pd.DataFrame(feats, index=df.index).ffill(limit=5)


def train_p_correct_oof(
    x_meta: pd.DataFrame,
    y_correct: pd.Series,
    n_splits: int = 4,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Entraîne P(correct) en OOF strict."""
    from sklearn.metrics import brier_score_loss, roc_auc_score

    common = x_meta.join(y_correct.rename("target")).dropna()
    if len(common) < 100 or common["target"].nunique() < 2:
        return np.array([]), {"verdict": "INSUFFICIENT_DATA"}

    x_c = common.drop(columns=["target"]).fillna(0.5)
    y_c = common["target"].astype(int)
    oof = np.full(len(x_c), np.nan)
    tscv = TimeSeriesSplit(n_splits=n_splits)

    for tr_idx, te_idx in tscv.split(x_c):
        if len(tr_idx) < 30 or y_c.iloc[tr_idx].nunique() < 2:
            continue
        try:
            clf = CalibratedClassifierCV(
                LogisticRegression(C=1.0, max_iter=500), cv=3
            )
            clf.fit(x_c.iloc[tr_idx], y_c.iloc[tr_idx])
            oof[te_idx] = clf.predict_proba(x_c.iloc[te_idx])[:, 1]
        except Exception:
            pass

    valid = ~np.isnan(oof) & y_c.notna().values
    if valid.sum() < 30 or len(np.unique(y_c.values[valid])) < 2:
        return oof, {"verdict": "INSUFFICIENT_OOF"}

    brier = round(float(brier_score_loss(y_c.values[valid], oof[valid])), 4)
    auc = round(float(roc_auc_score(y_c.values[valid], oof[valid])), 4)

    return oof, {
        "n_oof": int(valid.sum()),
        "brier_score": brier,
        "auc_p_correct": auc,
        "calibration": "GOOD" if brier < 0.20 else "OK" if brier < 0.25 else "POOR",
        "verdict": "GO_RESEARCH" if auc > 0.60 and brier < 0.25 else "WATCHLIST",
    }


def run_p_correct_model(df: pd.DataFrame) -> dict[str, Any]:
    """Calcule P(correct) pour le signal principal du dataset."""
    y_col = next((c for c in ["y_up_h20", "y_up_h40", "y_up_h60"] if c in df.columns), None)
    if not y_col:
        return {"version": "V7-12", "verdict": "NO_TARGET"}

    # Simuler une proba primaire via Ridge OOF
    exclude = {"y_", "Date", "date", "return_", "future_", "storage_", "prob_"}
    feat_cols = [c for c in df.columns
                 if not any(p in c for p in exclude)
                 and df[c].dtype in [np.float64, float]
                 and df[c].notna().mean() > 0.3][:50]

    if not feat_cols:
        return {"version": "V7-12", "verdict": "NO_FEATURES"}

    try:
        from lightgbm import LGBMClassifier
        common = df[feat_cols].join(df[y_col].rename("target")).dropna()
        if len(common) < 200:
            return {"version": "V7-12", "verdict": "INSUFFICIENT_DATA"}
        x_c = common.drop(columns=["target"]).fillna(0)
        y_c = common["target"]
        tscv = TimeSeriesSplit(n_splits=4)
        primary_oof = np.full(len(x_c), np.nan)
        for tr_idx, te_idx in tscv.split(x_c):
            if len(tr_idx) < 30 or y_c.iloc[tr_idx].nunique() < 2:
                continue
            clf = LGBMClassifier(n_estimators=100, seed=42, verbose=-1, n_jobs=1)
            clf.fit(x_c.iloc[tr_idx], y_c.iloc[tr_idx])
            primary_oof[te_idx] = clf.predict_proba(x_c.iloc[te_idx])[:, 1]

        primary_series = pd.Series(primary_oof, index=common.index, name="primary_proba")
        # y_correct : 1 si la prédiction primaire était correcte
        y_pred_class = (primary_series > 0.5).astype(int)
        y_correct = (y_pred_class == y_c.astype(int)).astype(float)

        x_meta = build_p_correct_features(df.reindex(common.index), primary_series)
        oof_p_correct, metrics = train_p_correct_oof(x_meta, y_correct)
    except Exception as exc:
        return {"version": "V7-12", "verdict": "COMPUTATION_ERROR", "error": str(exc)}

    metrics.update({
        "version": "V7-12",
        "target": y_col,
        "experiment_type": "PREDICTIVE_OOF",
    })
    return metrics


def save_p_correct_model(df: pd.DataFrame) -> dict[str, Any]:
    result = run_p_correct_model(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-12",
        target=result.get("target", "p_correct"),
        horizon=20,
        model="calibrated_logistic_p_correct",
        cv_protocol="time_series_split_4",
        embargo_days=0,
        n_oof=result.get("n_oof", 0),
        features=["primary_proba", "basis_z", "vol_ratio"],
        metrics={
            "brier_score": result.get("brier_score"),
            "auc_p_correct": result.get("auc_p_correct"),
        },
        p_value=None,
        verdict=result.get("verdict", "DONE"),
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
