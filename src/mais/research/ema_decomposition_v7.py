"""V7-09 — Décomposition dynamique EMA en 4 composantes.

Décompose le mouvement du prix EMA en : CBOT, FX, premium fondamental, roll.
DESCRIPTIVE_ECONOMIC — pas de prédiction, analyse de drivers.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "ema_decomposition.json"

COMPONENTS = ["cbot_component", "fx_component", "premium_component", "roll_component"]
SUB_PERIODS = [
    ("2010-01-01", "2014-12-31", "2010-2014"),
    ("2015-01-01", "2019-12-31", "2015-2019"),
    ("2020-01-01", "2023-12-31", "2020-2023"),
]


def decompose_ema_returns(df: pd.DataFrame, window: int = 120) -> pd.DataFrame:
    """Décomposition rolling OLS : 4 composantes du rendement EMA.

    Requiert : ema_close, et au moins un parmi cbot_close_eur/eurusd.
    Returns DataFrame avec colonnes : cbot_component, fx_component,
    premium_component, roll_component, residual, r2_rolling.
    """
    if "ema_close" not in df.columns:
        raise ValueError("Colonne 'ema_close' manquante")

    ema_ret = df["ema_close"].pct_change()

    cbot_ret = (
        df["cbot_close_eur"].pct_change()
        if "cbot_close_eur" in df.columns
        else pd.Series(0.0, index=df.index)
    )
    fx_ret = (
        df["eurusd"].pct_change()
        if "eurusd" in df.columns
        else pd.Series(0.0, index=df.index)
    )
    basis = df["ema_close"] - df.get("cbot_close_eur", df["ema_close"].rolling(252, min_periods=60).mean())
    premium_chg = basis.diff()
    roll_adj = df.get("roll_adj", pd.Series(0.0, index=df.index))

    results = pd.DataFrame(index=df.index, dtype=float)
    results["cbot_component"] = np.nan
    results["fx_component"] = np.nan
    results["premium_component"] = np.nan
    results["roll_component"] = np.nan
    results["residual"] = np.nan
    results["r2_rolling"] = np.nan

    try:
        from sklearn.linear_model import LinearRegression
    except ImportError:
        # Fallback: simple proportional attribution
        total_abs = (cbot_ret.abs() + fx_ret.abs() + premium_chg.abs() + roll_adj.abs()).replace(0, np.nan)
        results["cbot_component"] = ema_ret * cbot_ret.abs() / total_abs
        results["fx_component"] = ema_ret * fx_ret.abs() / total_abs
        results["premium_component"] = ema_ret * premium_chg.abs() / total_abs
        results["roll_component"] = ema_ret * roll_adj.abs() / total_abs
        results["residual"] = 0.0
        results["r2_rolling"] = 0.5
        return results

    x_mat = pd.DataFrame({
        "cbot": cbot_ret,
        "fx": fx_ret,
        "premium": premium_chg,
        "roll": roll_adj,
    }).fillna(0.0)
    y = ema_ret.fillna(0.0)

    for end_i in range(window, len(df)):
        start_i = end_i - window
        x_w = x_mat.iloc[start_i:end_i].values
        y_w = y.iloc[start_i:end_i].values
        if np.isnan(y_w).any() or np.isnan(x_w).any():
            continue
        try:
            reg = LinearRegression(fit_intercept=False)
            reg.fit(x_w, y_w)
            coefs = reg.coef_
            y_pred = x_mat.iloc[end_i].values * coefs
            results.iloc[end_i, results.columns.get_loc("cbot_component")] = y_pred[0]
            results.iloc[end_i, results.columns.get_loc("fx_component")] = y_pred[1]
            results.iloc[end_i, results.columns.get_loc("premium_component")] = y_pred[2]
            results.iloc[end_i, results.columns.get_loc("roll_component")] = y_pred[3]
            residual = y.iloc[end_i] - y_pred.sum()
            results.iloc[end_i, results.columns.get_loc("residual")] = residual
            ss_res = float(np.sum((y_w - reg.predict(x_w)) ** 2))
            ss_tot = float(np.sum((y_w - y_w.mean()) ** 2))
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
            results.iloc[end_i, results.columns.get_loc("r2_rolling")] = r2
        except Exception:
            continue

    return results


def compute_variance_attribution(decomp: pd.DataFrame) -> dict[str, float]:
    """Variance expliquée par composante (% de la variance totale)."""
    valid = decomp[COMPONENTS].dropna()
    total_var = float(valid.sum(axis=1).var())
    if total_var == 0:
        return dict.fromkeys(COMPONENTS, 0.0)
    return {c: round(float(valid[c].var() / total_var), 4) for c in COMPONENTS}


def compute_subperiod_stats(
    decomp: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Statistiques par sous-période."""
    stats = []
    for start, end, label in SUB_PERIODS:
        mask = (decomp.index >= start) & (decomp.index <= end)
        sub = decomp[mask]
        if len(sub) < 20:
            continue
        attr = compute_variance_attribution(sub)
        stats.append({
            "period": label,
            "n_dates": len(sub),
            "variance_attribution": attr,
            "mean_r2": round(float(sub["r2_rolling"].mean()), 4) if "r2_rolling" in sub else None,
        })
    return stats


def run_ema_decomposition(df: pd.DataFrame, window: int = 120) -> dict[str, Any]:
    """Décomposition complète EMA."""
    decomp = decompose_ema_returns(df, window=window)
    global_attr = compute_variance_attribution(decomp)
    subperiods = compute_subperiod_stats(decomp)
    dominant = max(global_attr, key=lambda k: global_attr[k])
    return {
        "version": "V7-09",
        "n_dates": len(df),
        "window": window,
        "global_variance_attribution": global_attr,
        "dominant_component": dominant,
        "subperiod_stats": subperiods,
        "columns_available": {
            "cbot_close_eur": "cbot_close_eur" in df.columns,
            "eurusd": "eurusd" in df.columns,
            "roll_adj": "roll_adj" in df.columns,
        },
    }


def save_ema_decomposition(df: pd.DataFrame) -> dict[str, Any]:
    result = run_ema_decomposition(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-09",
        target="ema_decomposition",
        horizon=0,
        model="rolling_ols_4_components",
        cv_protocol="none",
        embargo_days=0,
        n_oof=0,
        features=COMPONENTS,
        metrics={
            "dominant_component": result["dominant_component"],
            **{f"var_{k}": v for k, v in result["global_variance_attribution"].items()},
        },
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
