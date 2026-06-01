"""V7-39 — Score de qualité des données par date.

Score composite [0,1] : 6 composantes pondérées reflétant la disponibilité
des sources fondamentales pour chaque observation.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "data_quality_scores.json"

QUALITY_WEIGHTS: dict[str, float] = {
    "cot": 0.25,
    "wasde": 0.20,
    "ema_price": 0.20,
    "eia": 0.15,
    "cbot_price": 0.15,
    "basis": 0.05,
}

# Colonnes candidates par composante (first non-null wins)
_COT_COLS = ["cot_net_position", "cot_noncommercial_long", "cot_commercial_long"]
_WASDE_COLS = ["wasde_stocks", "wasde_world_corn_stocks", "wasde_stocks_to_use_ratio"]
_EIA_COLS = ["eia_ethanol", "eia_ethanol_production_kbbl", "eia_corn_for_ethanol_weekly"]
_EMA_COLS = ["ema_close", "ema_barchart_proxy"]
_CBOT_COLS = ["cbot_close", "cbot_corn_close"]
_BASIS_COLS = ["ema_cbot_basis_eur", "ema_basis_zscore_252d"]


def _find_col(df: pd.DataFrame, candidates: list[str]) -> pd.Series | None:
    for col in candidates:
        if col in df.columns:
            return df[col]
    return None


def compute_data_quality_score(df: pd.DataFrame) -> pd.Series:
    """Score composite [0,1] par ligne : 6 composantes pondérées."""
    def _avail(candidates: list[str]) -> pd.Series:
        col = _find_col(df, candidates)
        if col is None:
            return pd.Series(np.zeros(len(df)), index=df.index)
        return (~col.isna()).astype(float)

    components = {
        "cot": _avail(_COT_COLS),
        "wasde": _avail(_WASDE_COLS),
        "ema_price": _avail(_EMA_COLS),
        "eia": _avail(_EIA_COLS),
        "cbot_price": _avail(_CBOT_COLS),
        "basis": _avail(_BASIS_COLS),
    }
    quality = sum(QUALITY_WEIGHTS[k] * v for k, v in components.items())
    quality.name = "data_quality_score"
    return quality


def compute_quality_report(df: pd.DataFrame) -> dict[str, Any]:
    """Rapport de qualité complet avec statistiques par composante."""
    score = compute_data_quality_score(df)

    component_stats: dict[str, Any] = {}
    for key, candidates in [
        ("cot", _COT_COLS),
        ("wasde", _WASDE_COLS),
        ("ema_price", _EMA_COLS),
        ("eia", _EIA_COLS),
        ("cbot_price", _CBOT_COLS),
        ("basis", _BASIS_COLS),
    ]:
        col = _find_col(df, candidates)
        avail_rate = float((~col.isna()).mean()) if col is not None else 0.0
        component_stats[key] = {
            "weight": QUALITY_WEIGHTS[key],
            "availability_rate": round(avail_rate, 4),
            "column_found": next((c for c in candidates if c in df.columns), None),
            "contribution_to_score": round(QUALITY_WEIGHTS[key] * avail_rate, 4),
        }

    return {
        "n_dates": len(df),
        "mean_quality_score": round(float(score.mean()), 4),
        "median_quality_score": round(float(score.median()), 4),
        "pct_high_quality": round(float((score >= 0.8).mean()), 4),
        "pct_low_quality": round(float((score < 0.5).mean()), 4),
        "components": component_stats,
        "weights": QUALITY_WEIGHTS,
    }


def compute_quality_prediction_correlation(
    df: pd.DataFrame,
    errors: pd.Series,
) -> dict[str, float]:
    """Corrélation entre score qualité et erreur de prédiction."""
    score = compute_data_quality_score(df)
    aligned = score.align(errors, join="inner")
    corr = float(aligned[0].corr(aligned[1]))
    return {
        "quality_error_correlation": round(corr, 4),
        "n_observations": int(len(aligned[0])),
        "note": "Corrélation négative attendue : haute qualité → faible erreur",
    }


def save_quality_scores(df: pd.DataFrame) -> dict[str, Any]:
    import json
    report = compute_quality_report(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    register_experiment(
        experiment_id="V7-39",
        target="data_quality_score",
        horizon=0,
        model="composite_score",
        cv_protocol="none",
        embargo_days=0,
        n_oof=0,
        features=list(QUALITY_WEIGHTS.keys()),
        metrics={
            "mean_quality": report["mean_quality_score"],
            "pct_high_quality": report["pct_high_quality"],
        },
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return report
