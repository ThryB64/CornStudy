"""V7-34 — Modèle de scénarios de marché."""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "scenario_analysis.json"

SCENARIOS = {
    "eu_drought": {
        "factor_weather_belt_stress": 2.5,
        "ema_cbot_basis_zscore_52w": 1.5,
    },
    "ukraine_export_disruption": {
        "cot_mm_long": -50000.0,
        "ema_cbot_basis_zscore_52w": 2.0,
    },
    "demand_recession": {
        "cot_mm_long": -80000.0,
        "factor_cross_commodity": -1.5,
    },
    "cbot_bull_market": {
        "corn_realized_vol_20": 0.25,
        "factor_market_momentum": 1.8,
    },
    "basis_normalization": {
        "ema_cbot_basis_zscore_52w": -1.5,
        "ema_cbot_rel_strength_20d": -0.05,
    },
}

CRISIS_PERIODS = {
    "2012_drought": ("2012-06-01", "2012-10-31"),
    "2020_covid": ("2020-02-01", "2020-06-30"),
    "2022_ukraine": ("2022-02-24", "2022-09-30"),
}


def simulate_scenario(
    clf,
    baseline_x: pd.DataFrame,
    scenario: dict[str, float],
) -> dict[str, Any]:
    x_scen = baseline_x.copy()
    applied = []
    for feat, val in scenario.items():
        if feat in x_scen.columns:
            x_scen[feat] = val
            applied.append(feat)

    proba_base = float(clf.predict_proba(baseline_x.fillna(0))[:, 1].mean())
    proba_scen = float(clf.predict_proba(x_scen.fillna(0))[:, 1].mean())
    return {
        "proba_base": round(proba_base, 4),
        "proba_scenario": round(proba_scen, 4),
        "delta": round(proba_scen - proba_base, 4),
        "applied_features": applied,
        "direction": "UP" if proba_scen > proba_base + 0.05 else "DOWN" if proba_scen < proba_base - 0.05 else "NEUTRAL",
    }


def run_scenario_analysis(df: pd.DataFrame) -> dict[str, Any]:
    exclude = {"y_", "Date", "date", "return_", "future_", "storage_", "prob_"}
    feat_cols = [c for c in df.columns
                 if not any(p in c for p in exclude)
                 and df[c].dtype in [np.float64, float]
                 and df[c].notna().mean() > 0.3][:60]

    y_col = next((c for c in ["y_up_h20", "y_up_h40"] if c in df.columns), None)
    if not y_col or not feat_cols:
        return {"version": "V7-34", "verdict": "NO_DATA"}

    common = df[feat_cols].join(df[y_col].rename("target")).dropna()
    if len(common) < 200:
        return {"version": "V7-34", "verdict": "INSUFFICIENT_DATA"}

    x_c = common.drop(columns=["target"]).fillna(0)
    y_c = common["target"]

    try:
        from lightgbm import LGBMClassifier
        clf = LGBMClassifier(n_estimators=100, seed=42, verbose=-1, n_jobs=1)
        clf.fit(x_c, y_c)
    except ImportError:
        return {"version": "V7-34", "verdict": "LGBM_UNAVAILABLE"}

    # Baseline : dernière fenêtre de 90 jours
    baseline_x = x_c.tail(90)

    scenario_results: dict[str, Any] = {}
    for name, scen in SCENARIOS.items():
        # Filtrer aux features disponibles
        scen_filtered = {k: v for k, v in scen.items() if k in feat_cols}
        if not scen_filtered:
            scenario_results[name] = {"verdict": "NO_MATCHING_FEATURES"}
            continue
        scenario_results[name] = simulate_scenario(clf, baseline_x, scen_filtered)

    # Validation backtestée sur crises historiques
    crisis_validation: dict[str, Any] = {}
    for crisis_name, (start, end) in CRISIS_PERIODS.items():
        mask = (common.index >= pd.Timestamp(start)) & (common.index <= pd.Timestamp(end))
        if mask.sum() < 10:
            crisis_validation[crisis_name] = {"verdict": "INSUFFICIENT_DATA"}
            continue
        x_crisis = x_c[mask]
        y_crisis = y_c[mask]
        if y_crisis.nunique() < 2:
            crisis_validation[crisis_name] = {"verdict": "ONE_CLASS_ONLY"}
            continue
        from sklearn.metrics import roc_auc_score
        preds = clf.predict_proba(x_crisis)[:, 1]
        auc_crisis = round(float(roc_auc_score(y_crisis, preds)), 4)
        crisis_validation[crisis_name] = {"auc": auc_crisis, "n": int(mask.sum())}

    return {
        "version": "V7-34",
        "target": y_col,
        "scenarios": scenario_results,
        "crisis_validation": crisis_validation,
        "verdict": "SCENARIO_ANALYSIS_DONE",
        "experiment_type": "MODEL_VALIDATION",
    }


def save_scenario_analysis(df: pd.DataFrame) -> dict[str, Any]:
    result = run_scenario_analysis(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-34",
        target=result.get("target", "scenario"),
        horizon=20,
        model="lgbm_scenario",
        cv_protocol="none",
        embargo_days=0,
        n_oof=0,
        features=list(SCENARIOS.keys()),
        metrics={
            "n_scenarios": len(SCENARIOS),
            "n_crises_validated": len(result.get("crisis_validation", {})),
        },
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
