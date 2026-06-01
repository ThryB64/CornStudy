"""V7-32 — Modèle de fair value EMA/CBOT."""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import TimeSeriesSplit

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "fair_value_model.json"


def _expandz(s: pd.Series, min_periods: int = 60) -> pd.Series:
    mu = s.expanding(min_periods=min_periods).mean()
    std = s.expanding(min_periods=min_periods).std()
    return ((s - mu) / std.replace(0, np.nan)).rename(s.name + "_z" if s.name else "z")


def _build_fundamental_features(df: pd.DataFrame) -> pd.DataFrame:
    """Features fondamentales pour le modèle fair value (toutes shiftées)."""
    feats: dict[str, pd.Series] = {}

    # EUR/USD
    if "eurusd" in df.columns:
        feats["eurusd_z60"] = _expandz(df["eurusd"])
    elif "cbot_eur_t" in df.columns and "cbot_close" in df.columns:
        eurusd_derived = (df["cbot_close"] * 36.744) / df["cbot_eur_t"]
        feats["eurusd_z60"] = _expandz(eurusd_derived.replace([np.inf, -np.inf], np.nan))

    # Stocks EU (proxy via WASDE ou autres)
    if "wasde_ending_stocks" in df.columns:
        feats["eu_stocks_z"] = _expandz(df["wasde_ending_stocks"])

    # Coût transport (proxy gas ou VIX-like)
    if "gas_close" in df.columns:
        feats["transport_cost_z"] = _expandz(df["gas_close"])
    elif "factor_macro_dollar_rates" in df.columns:
        feats["macro_factor"] = df["factor_macro_dollar_rates"]

    # FOB proxy (basis EMA/CBOT comme proxy spread export)
    if "ema_cbot_basis" in df.columns:
        feats["fob_proxy_z"] = _expandz(df["ema_cbot_basis"])

    # Weather stress (impact sur production EU)
    if "factor_weather_belt_stress" in df.columns:
        feats["weather_stress"] = df["factor_weather_belt_stress"]

    result = pd.DataFrame(feats, index=df.index)
    return result.shift(1)  # anti-leakage


def compute_fair_value_oof(df: pd.DataFrame, n_splits: int = 5) -> dict[str, Any]:
    """Modèle économique linéaire OOF pour fair value premium."""
    if "ema_close" not in df.columns and "ema_cbot_basis" not in df.columns:
        return {"verdict": "INSUFFICIENT_DATA"}

    # Premium à modéliser
    if "ema_close" in df.columns and "cbot_close_eur" in df.columns:
        premium = df["ema_close"] - df["cbot_close_eur"]
    elif "ema_cbot_basis" in df.columns:
        premium = df["ema_cbot_basis"]
    else:
        return {"verdict": "NO_PREMIUM_COLUMN"}

    x_feats = _build_fundamental_features(df)
    combined = pd.DataFrame({"premium": premium}).join(x_feats).dropna()

    if len(combined) < 200:
        return {"verdict": "INSUFFICIENT_DATA", "n": len(combined)}

    x_all = combined.drop(columns=["premium"])
    y = combined["premium"]

    # OOF via TimeSeriesSplit
    tscv = TimeSeriesSplit(n_splits=n_splits)
    oof_fair_value = np.full(len(combined), np.nan)
    r2_folds = []

    for train_idx, test_idx in tscv.split(x_all):
        x_tr = x_all.iloc[train_idx]
        y_tr = y.iloc[train_idx]
        x_te = x_all.iloc[test_idx]
        mask_tr = x_tr.notna().all(axis=1) & y_tr.notna()
        if mask_tr.sum() < 20:
            continue
        reg = Ridge(alpha=1.0)
        reg.fit(x_tr[mask_tr].fillna(0), y_tr[mask_tr])
        preds = reg.predict(x_te.fillna(0))
        oof_fair_value[test_idx] = preds
        r2 = float(1 - np.var(y.iloc[test_idx] - preds) / np.var(y.iloc[test_idx]))
        r2_folds.append(r2)

    combined["fair_value"] = oof_fair_value
    combined["deviation"] = combined["premium"] - combined["fair_value"]

    # Test signal de déviation → retour futur
    y_target_col = next(
        (c for c in ["y_rel_outperform_h90", "y_up_h20_ema", "y_up_h20", "y_up_h60"] if c in df.columns),
        None,
    )
    deviation_signal: dict[str, Any] = {}

    if y_target_col is not None:
        combined_target = combined.join(df[[y_target_col]]).dropna(subset=["deviation", y_target_col])
        if len(combined_target) > 100:
            dev_z = _expandz(combined_target["deviation"].dropna())
            dev_z = dev_z.reindex(combined_target.index)
            valid = dev_z.notna() & combined_target[y_target_col].notna()
            y_true = combined_target.loc[valid, y_target_col]
            y_score = dev_z[valid]
            if len(y_true) > 50 and len(y_true.unique()) > 1:
                try:
                    auc = float(roc_auc_score(y_true, y_score))
                    deviation_signal = {
                        "n": int(valid.sum()),
                        "auc_deviation_vs_target": round(auc, 4),
                        "target": y_target_col,
                        "verdict": "GO_RESEARCH" if auc > 0.55 else "NO_GO",
                    }
                except Exception:
                    deviation_signal = {"verdict": "COMPUTATION_ERROR"}

    return {
        "n_obs": len(combined),
        "n_features": x_all.shape[1],
        "mean_r2_oof": round(float(np.mean(r2_folds)), 4) if r2_folds else None,
        "premium_mean": round(float(y.mean()), 4),
        "premium_std": round(float(y.std()), 4),
        "fair_value_mean": round(float(np.nanmean(oof_fair_value)), 4),
        "deviation_std": round(float(combined["deviation"].std()), 4),
        "deviation_signal": deviation_signal,
    }


def run_fair_value_analysis(df: pd.DataFrame) -> dict[str, Any]:
    """Analyse complète fair value EMA/CBOT."""
    oof_result = compute_fair_value_oof(df)

    verdict = oof_result.get("deviation_signal", {}).get("verdict", "NO_SIGNAL")

    return {
        "version": "V7-32",
        "experiment_type": "DESCRIPTIVE_ECONOMIC",
        "oof_analysis": oof_result,
        "verdict": verdict,
        "interpretation": (
            "La déviation premium vs fair value a une valeur predictive"
            if verdict == "GO_RESEARCH"
            else "Le fair value model economique ne predit pas bien le premium"
        ),
    }


def save_fair_value_model(df: pd.DataFrame) -> dict[str, Any]:
    result = run_fair_value_analysis(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    oof = result.get("oof_analysis", {})
    dev_sig = oof.get("deviation_signal", {})
    register_experiment(
        experiment_id="V7-32",
        target="fair_value_deviation",
        horizon=90,
        model="ridge_economic_oof",
        cv_protocol="time_series_split_5",
        embargo_days=0,
        n_oof=oof.get("n_obs", 0),
        features=["eurusd_z60", "eu_stocks_z", "transport_cost_z", "fob_proxy_z"],
        metrics={
            "mean_r2_oof": oof.get("mean_r2_oof"),
            "auc_deviation_signal": dev_sig.get("auc_deviation_vs_target"),
            "n_features": oof.get("n_features"),
        },
        p_value=None,
        verdict=result["verdict"],
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
