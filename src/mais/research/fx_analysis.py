"""V7-21 — Analyse facteur EUR/USD et régimes de change."""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import roc_auc_score

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "fx_analysis.json"


def _expandz(s: pd.Series) -> pd.Series:
    mu = s.expanding().mean()
    std = s.expanding().std()
    return ((s - mu) / std.replace(0, np.nan)).rename(s.name + "_z" if s.name else "z")


def build_fx_neutral_premium(df: pd.DataFrame) -> pd.Series:
    """Premium neutralisé FX : CBOT converti à taux de change fixe (base 2015 ou première année)."""
    if "cbot_close" not in df.columns or "ema_close" not in df.columns:
        return pd.Series(dtype=float, name="premium_fx_neutral")
    if "eurusd" not in df.columns:
        return pd.Series(dtype=float, name="premium_fx_neutral")

    # Essayer 2015 d'abord, sinon première année disponible
    mask_base = df.index.year == 2015
    if mask_base.sum() == 0:
        first_year = df.index.year.min()
        mask_base = df.index.year == first_year

    eurusd_base = float(df.loc[mask_base, "eurusd"].dropna().mean())
    if np.isnan(eurusd_base) or eurusd_base == 0:
        eurusd_base = float(df["eurusd"].dropna().mean())
    if np.isnan(eurusd_base) or eurusd_base == 0:
        return pd.Series(dtype=float, name="premium_fx_neutral")

    cbot_eur_fixed = df["cbot_close"] / eurusd_base / 36.744
    premium_fx_neutral = df["ema_close"] - cbot_eur_fixed
    return premium_fx_neutral.rename("premium_fx_neutral")


def classify_fx_regimes(df: pd.DataFrame) -> pd.Series:
    """Classifie les régimes EUR/USD : strong_eur / neutral / weak_eur."""
    if "eurusd" not in df.columns:
        return pd.Series("neutral", index=df.index, name="fx_regime")
    eurusd_z = _expandz(df["eurusd"])
    regimes = pd.Series("neutral", index=df.index, name="fx_regime")
    regimes[eurusd_z > 1.0] = "strong_eur"
    regimes[eurusd_z < -1.0] = "weak_eur"
    return regimes


def compute_fx_premium_correlation(
    df: pd.DataFrame,
    premium: pd.Series,
) -> dict[str, Any]:
    """Corrélation EUR/USD vs premium EMA/CBOT par régime."""
    if "eurusd" not in df.columns or premium.dropna().__len__() < 30:
        return {"verdict": "INSUFFICIENT_DATA"}

    fx_regimes = classify_fx_regimes(df)
    results: dict[str, Any] = {}

    for regime in ["strong_eur", "neutral", "weak_eur"]:
        mask = (fx_regimes == regime) & premium.notna() & df["eurusd"].notna()
        if mask.sum() < 30:
            results[regime] = {"n": int(mask.sum()), "verdict": "INSUFFICIENT_DATA"}
            continue
        corr = float(df.loc[mask, "eurusd"].corr(premium.loc[mask]))
        results[regime] = {
            "n": int(mask.sum()),
            "corr_fx_premium": round(corr, 4),
        }

    return results


def compare_fx_neutral_vs_raw(
    df: pd.DataFrame,
    y_target: pd.Series,
) -> dict[str, Any]:
    """Compare AUC modèle FX-neutralisé vs modèle complet."""
    if "eurusd" not in df.columns or "ema_close" not in df.columns:
        return {"verdict": "INSUFFICIENT_DATA"}

    premium_raw = (df["ema_close"] - df.get("cbot_close_eur", df["ema_close"].rolling(60).mean()))
    premium_neutral = build_fx_neutral_premium(df)

    if premium_raw.dropna().__len__() < 100 or premium_neutral.dropna().__len__() < 100:
        return {"verdict": "INSUFFICIENT_DATA"}

    common = pd.DataFrame({
        "premium_raw": premium_raw,
        "premium_neutral": premium_neutral,
        "y": y_target,
    }).dropna()

    if len(common) < 100:
        return {"verdict": "INSUFFICIENT_DATA", "n": len(common)}

    # Simple OOF: first 70% train, last 30% test
    n_train = int(len(common) * 0.7)
    x_raw_tr = common["premium_raw"].values[:n_train].reshape(-1, 1)
    x_raw_te = common["premium_raw"].values[n_train:].reshape(-1, 1)
    x_neu_tr = common["premium_neutral"].values[:n_train].reshape(-1, 1)
    x_neu_te = common["premium_neutral"].values[n_train:].reshape(-1, 1)
    y_tr = common["y"].values[:n_train]
    y_te = common["y"].values[n_train:]

    if len(np.unique(y_te)) < 2:
        return {"verdict": "INSUFFICIENT_DATA", "reason": "only_one_class_in_test"}

    try:
        r = Ridge(alpha=1.0)
        r.fit(x_raw_tr, y_tr)
        auc_raw = float(roc_auc_score(y_te, r.predict(x_raw_te)))

        r2 = Ridge(alpha=1.0)
        r2.fit(x_neu_tr, y_tr)
        auc_neutral = float(roc_auc_score(y_te, r2.predict(x_neu_te)))
    except Exception:
        return {"verdict": "COMPUTATION_ERROR"}

    return {
        "n_train": n_train,
        "n_test": len(y_te),
        "auc_raw_premium": round(auc_raw, 4),
        "auc_fx_neutral_premium": round(auc_neutral, 4),
        "delta_auc": round(auc_raw - auc_neutral, 4),
        "interpretation": (
            "FX explique une partie du signal" if abs(auc_raw - auc_neutral) > 0.02
            else "FX influence limitee sur le premium"
        ),
    }


def run_fx_analysis(df: pd.DataFrame) -> dict[str, Any]:
    """Analyse complète FX / régimes de change."""
    # Premium brut
    if "ema_close" in df.columns and "cbot_close_eur" in df.columns:
        premium = df["ema_close"] - df["cbot_close_eur"]
    elif "ema_cbot_basis" in df.columns:
        premium = df["ema_cbot_basis"]
    else:
        premium = pd.Series(dtype=float)

    corr_by_regime = compute_fx_premium_correlation(df, premium)

    # Cible pour comparaison modèles
    y_col = next(
        (c for c in ["y_rel_outperform_h40", "y_up_h20_ema", "y_up_h20"] if c in df.columns),
        None,
    )
    model_comparison: dict[str, Any] = {}
    if y_col:
        model_comparison = compare_fx_neutral_vs_raw(df, df[y_col])

    # Corrélation directe EUR/USD vs premium
    global_corr: float | None = None
    if "eurusd" in df.columns and len(premium.dropna()) > 100:
        common = pd.DataFrame({"fx": df["eurusd"], "premium": premium}).dropna()
        if len(common) > 50:
            global_corr = round(float(common["fx"].corr(common["premium"])), 4)

    # Stats régimes
    if "eurusd" in df.columns:
        fx_regimes = classify_fx_regimes(df)
        regime_counts = fx_regimes.value_counts().to_dict()
    else:
        regime_counts = {}

    return {
        "version": "V7-21",
        "n_dates": len(df),
        "has_eurusd": "eurusd" in df.columns,
        "global_corr_fx_premium": global_corr,
        "regime_counts": regime_counts,
        "correlation_by_regime": corr_by_regime,
        "fx_neutral_model_comparison": model_comparison,
        "verdict": "FX_ANALYSIS_DONE",
        "experiment_type": "PREDICTIVE_OOF",
    }


def save_fx_analysis(df: pd.DataFrame) -> dict[str, Any]:
    result = run_fx_analysis(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    mc = result.get("fx_neutral_model_comparison", {})
    register_experiment(
        experiment_id="V7-21",
        target="fx_regime_premium",
        horizon=40,
        model="ridge_fx_neutral",
        cv_protocol="holdout_70_30",
        embargo_days=0,
        n_oof=mc.get("n_test", 0),
        features=["eurusd", "premium_raw", "premium_fx_neutral"],
        metrics={
            "auc_raw": mc.get("auc_raw_premium"),
            "auc_fx_neutral": mc.get("auc_fx_neutral_premium"),
            "delta_auc": mc.get("delta_auc"),
            "global_corr_fx_premium": result.get("global_corr_fx_premium"),
        },
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
