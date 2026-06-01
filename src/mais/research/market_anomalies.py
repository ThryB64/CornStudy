"""V7-25 — Tests des anomalies de marché.

8 anomalies testées sur le premium EMA/CBOT avec correction BH.
DESCRIPTIVE_ECONOMIC.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment
from mais.research.multiple_testing import bh_correction

_OUTPUT = ARTEFACTS_DIR / "v7" / "market_anomalies.json"

ANOMALY_TESTS: dict[str, Any] = {
    "momentum_20d": lambda r: (r.rolling(20, min_periods=5).mean() > 0).astype(float),
    "momentum_60d": lambda r: (r.rolling(60, min_periods=20).mean() > 0).astype(float),
    "mean_reversion_20d": lambda r: (r.rolling(20, min_periods=5).mean() < 0).astype(float),
    "day_of_week_monday": lambda r: (r.index.dayofweek == 0).astype(float),
    "month_seasonality_q1": lambda r: (r.index.month.isin([1, 2, 3])).astype(float),
    "month_seasonality_q3": lambda r: (r.index.month.isin([7, 8, 9])).astype(float),
    "post_wasde_5d": lambda r: (r.index.day <= 7).astype(float),
    "volatility_mean_reversion": lambda r: (
        r.rolling(5, min_periods=2).std() > r.rolling(60, min_periods=20).std()
    ).astype(float),
}


def compute_anomaly_pvalue(
    returns: pd.Series,
    y_true: pd.Series,
    anomaly_fn: Any,
    n_permutations: int = 500,
    seed: int = 42,
) -> dict[str, Any]:
    """Teste une anomalie et retourne p-value par permutation."""
    try:
        signal = anomaly_fn(returns).reindex(y_true.index).fillna(0.5)
    except Exception as e:
        return {"status": "ERROR", "error": str(e), "p_value": None}

    # Corrélation signal/cible = mesure d'effet
    valid = y_true.notna() & signal.notna()
    if valid.sum() < 20:
        return {"status": "INSUFFICIENT_DATA", "p_value": None}

    obs_corr = float(signal[valid].corr(y_true[valid]))
    if np.isnan(obs_corr):
        return {"status": "NAN_CORRELATION", "p_value": None}

    rng = np.random.default_rng(seed)
    null_corrs = np.array([
        rng.permutation(signal[valid].values).dot(y_true[valid].values) / valid.sum()
        for _ in range(n_permutations)
    ])
    p_value = float((np.abs(null_corrs) >= np.abs(obs_corr)).mean())

    return {
        "observed_correlation": round(obs_corr, 4),
        "p_value": round(p_value, 4),
        "n_valid": int(valid.sum()),
        "status": "OK",
    }


def run_market_anomalies(
    returns: pd.Series,
    y_true: pd.Series,
    n_permutations: int = 500,
) -> dict[str, Any]:
    """Teste 8 anomalies avec correction BH."""
    results: dict[str, dict] = {}
    for name, fn in ANOMALY_TESTS.items():
        results[name] = compute_anomaly_pvalue(returns, y_true, fn, n_permutations)

    # BH correction
    p_values = [
        r["p_value"] for r in results.values()
        if r.get("p_value") is not None
    ]
    testable_names = [
        name for name, r in results.items()
        if r.get("p_value") is not None
    ]

    if p_values:
        bh = bh_correction(p_values)
        for name, bh_res in zip(testable_names, bh["results"], strict=True):
            results[name]["q_bh"] = round(bh_res["q_bh"], 4)
            results[name]["significant_after_bh"] = bh_res["rejected"]
    else:
        for name in results:
            results[name]["q_bh"] = None
            results[name]["significant_after_bh"] = False

    n_significant = sum(1 for r in results.values() if r.get("significant_after_bh"))
    return {
        "version": "V7-25",
        "n_anomalies_tested": len(ANOMALY_TESTS),
        "n_significant_after_bh": n_significant,
        "alpha": 0.05,
        "results": results,
    }


def save_market_anomalies(
    returns: pd.Series,
    y_true: pd.Series,
) -> dict[str, Any]:
    result = run_market_anomalies(returns, y_true)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-25",
        target="market_anomalies",
        horizon=0,
        model="anomaly_bh_correction",
        cv_protocol="none",
        embargo_days=0,
        n_oof=0,
        features=list(ANOMALY_TESTS.keys()),
        metrics={"n_significant_after_bh": result["n_significant_after_bh"]},
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
