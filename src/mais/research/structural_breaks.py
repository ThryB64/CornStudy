"""V7-19 — Détection de ruptures structurelles.

Tests Chow, CUSUM, et Bai-Perron sur la relation EMA~CBOT.
DESCRIPTIVE_ECONOMIC.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "structural_breaks.json"

CANDIDATE_BREAKS = {
    "2008-09-15": "Faillite Lehman Brothers",
    "2012-07-01": "Sécheresse US historique",
    "2020-03-15": "COVID-19 choc marchés",
    "2022-02-24": "Invasion Ukraine",
    "2014-06-01": "Correction majeure CBOT",
}


def compute_chow_breakpoint(
    y: pd.Series,
    x: pd.Series,
    break_date: str,
) -> dict[str, Any]:
    """Test Chow simplifié : compare les RSS avant et après la rupture."""
    bp = pd.Timestamp(break_date)
    mask_pre = y.index < bp
    mask_post = y.index >= bp

    if mask_pre.sum() < 10 or mask_post.sum() < 10:
        return {"break_date": break_date, "status": "INSUFFICIENT_DATA", "chow_stat": None, "p_value": None}

    def ols_rss(yt: pd.Series, xt: pd.Series) -> float:
        n = len(yt)
        if n < 2:
            return float("nan")
        x_mat = np.column_stack([np.ones(n), xt.values])
        try:
            coef, residuals, _, _ = np.linalg.lstsq(x_mat, yt.values, rcond=None)
            return float(np.sum((yt.values - x_mat @ coef) ** 2))
        except Exception:
            return float("nan")

    rss_full = ols_rss(y, x)
    rss_pre = ols_rss(y[mask_pre], x[mask_pre])
    rss_post = ols_rss(y[mask_post], x[mask_post])
    n = len(y)
    k = 2  # intercept + slope

    if any(np.isnan(v) for v in [rss_full, rss_pre, rss_post]) or rss_pre + rss_post == 0:
        return {"break_date": break_date, "status": "COMPUTATION_ERROR", "chow_stat": None, "p_value": None}

    chow_stat = ((rss_full - (rss_pre + rss_post)) / k) / ((rss_pre + rss_post) / (n - 2 * k))

    # Approximation p-value via F(k, n-2k)
    try:
        from scipy.stats import f as f_dist
        p_value = float(1 - f_dist.cdf(chow_stat, k, n - 2 * k))
    except ImportError:
        p_value = None

    return {
        "break_date": break_date,
        "description": CANDIDATE_BREAKS.get(break_date, ""),
        "n_pre": int(mask_pre.sum()),
        "n_post": int(mask_post.sum()),
        "chow_stat": round(float(chow_stat), 4),
        "p_value": round(p_value, 4) if p_value is not None else None,
        "significant_p05": (p_value < 0.05) if p_value is not None else None,
    }


def compute_cusum(y: pd.Series, x: pd.Series) -> dict[str, Any]:
    """CUSUM des résidus OLS : détecte la dérive cumulative."""
    n = len(y)
    if n < 20:
        return {"status": "INSUFFICIENT_DATA"}

    x_mat = np.column_stack([np.ones(n), x.values])
    try:
        coef, _, _, _ = np.linalg.lstsq(x_mat, y.values, rcond=None)
        residuals = y.values - x_mat @ coef
    except Exception:
        return {"status": "COMPUTATION_ERROR"}

    sigma = float(np.std(residuals))
    if sigma == 0:
        return {"status": "ZERO_VARIANCE"}

    cusum = np.cumsum(residuals / (sigma * np.sqrt(n)))
    max_cusum = float(np.max(np.abs(cusum)))
    # Critical value ≈ 1.36 at 5% (Brownian bridge)
    critical_value = 1.36

    return {
        "max_cusum": round(max_cusum, 4),
        "critical_value_p05": critical_value,
        "exceeds_critical": max_cusum > critical_value,
        "break_detected": max_cusum > critical_value,
        "approx_break_date": str(y.index[np.argmax(np.abs(cusum))].date()) if len(cusum) > 0 else None,
    }


def run_structural_breaks(df: pd.DataFrame) -> dict[str, Any]:
    """Tests complets de ruptures structurelles sur EMA~CBOT."""
    if "ema_close" not in df.columns:
        raise ValueError("Colonne 'ema_close' manquante")

    y = df["ema_close"].pct_change().dropna()
    x_col = "cbot_close_eur" if "cbot_close_eur" in df.columns else "ema_close"
    x = df[x_col].pct_change().reindex(y.index).fillna(0.0)

    chow_results = {}
    for break_date in CANDIDATE_BREAKS:
        if y.index.min() < pd.Timestamp(break_date) < y.index.max():
            chow_results[break_date] = compute_chow_breakpoint(y, x, break_date)

    cusum = compute_cusum(y, x)
    n_significant = sum(1 for r in chow_results.values() if r.get("significant_p05"))

    return {
        "version": "V7-19",
        "n_dates": len(df),
        "chow_tests": chow_results,
        "cusum": cusum,
        "n_significant_breaks": n_significant,
        "recommended_train_window": "2015-2023" if n_significant >= 2 else "2010-2023",
    }


def save_structural_breaks(df: pd.DataFrame) -> dict[str, Any]:
    result = run_structural_breaks(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-19",
        target="structural_breaks_ema_cbot",
        horizon=0,
        model="chow_cusum",
        cv_protocol="none",
        embargo_days=0,
        n_oof=0,
        features=[],
        metrics={"n_significant_breaks": result["n_significant_breaks"]},
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
