"""NB-EMA-06 — Étude du résidu EU : chocs européens, DA directionnel, catalyseur."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_residual_study.json"
_RESIDUAL_PARQUET = _STUDY_DIR / "ema_residual_series.parquet"
_SHOCK_THRESHOLD_SIGMA = 3.0
_MIN_EVENTS_FOR_CATALOG = 3


def _load_residuals() -> pd.DataFrame:
    df = pd.read_parquet(_RESIDUAL_PARQUET)
    df["Date"] = pd.to_datetime(df["Date"])
    return df.sort_values("Date").reset_index(drop=True)


def _residual_stats(resid: pd.Series) -> dict:
    return {
        "n": int(len(resid)),
        "mean": float(resid.mean()),
        "std": float(resid.std()),
        "skewness": float(resid.skew()),
        "kurtosis": float(resid.kurt()),
        "min": float(resid.min()),
        "max": float(resid.max()),
        "q01": float(resid.quantile(0.01)),
        "q99": float(resid.quantile(0.99)),
    }


def _extreme_events_catalog(df: pd.DataFrame, threshold_sigma: float) -> dict:
    resid = df["ema_residual"]
    mu = resid.mean()
    sigma = resid.std()
    z = (resid - mu) / sigma
    extreme_mask = z.abs() >= threshold_sigma
    events = df[extreme_mask][["Date", "ema_residual"]].copy()
    events["z_score"] = z[extreme_mask].values
    events["direction"] = np.sign(events["ema_residual"]).astype(int)
    n_events = int(len(events))

    if n_events < _MIN_EVENTS_FOR_CATALOG:
        return {
            "threshold_sigma": threshold_sigma,
            "n_events": n_events,
            "verdict": "NO_EXTREME_EVENT_ENOUGH",
            "note": f"Moins de {_MIN_EVENTS_FOR_CATALOG} événements détectés au seuil {threshold_sigma}σ",
        }

    top_pos = events[events["direction"] > 0].nlargest(5, "z_score")[["Date", "ema_residual", "z_score"]]
    top_neg = events[events["direction"] < 0].nsmallest(5, "z_score")[["Date", "ema_residual", "z_score"]]

    def _fmt(df_sub: pd.DataFrame) -> list[dict]:
        out = []
        for _, row in df_sub.iterrows():
            out.append({"date": str(row["Date"].date()), "residual": float(row["ema_residual"]), "z_score": float(row["z_score"])})
        return out

    return {
        "threshold_sigma": threshold_sigma,
        "n_events": n_events,
        "pct_extreme": float(n_events / max(len(df), 1)),
        "n_positive_shocks": int((events["direction"] > 0).sum()),
        "n_negative_shocks": int((events["direction"] < 0).sum()),
        "top5_positive": _fmt(top_pos),
        "top5_negative": _fmt(top_neg),
        "verdict": "CATALOG_BUILT",
    }


def _directional_accuracy(resid: pd.Series) -> dict:
    """DA du résidu : est-ce que le signe du résidu est prévisible depuis le passé ?"""
    # Naive persistence: does sign(resid[t]) == sign(resid[t-1]) ?
    sign_curr = np.sign(resid)
    sign_lag1 = np.sign(resid.shift(1))
    aligned = pd.concat([sign_curr, sign_lag1], axis=1).dropna()
    da_persistence = float((aligned.iloc[:, 0] == aligned.iloc[:, 1]).mean())

    # DA vs zero (fraction positive residuals)
    da_vs_zero = float((resid > 0).mean())

    # ADF on residuals
    try:
        from statsmodels.tsa.stattools import adfuller
        res = adfuller(resid.dropna(), autolag="AIC")
        adf = {"stat": float(res[0]), "p_value": float(res[1]), "verdict": "stationary" if res[1] < 0.05 else "non_stationary"}
    except ImportError:
        adf = {"error": "statsmodels_not_available"}

    return {
        "da_sign_persistence_lag1": da_persistence,
        "pct_positive_residuals": da_vs_zero,
        "interpretation": "Résidu EU = composante spécifique européenne non expliquée par CBOT+basis (contemporain).",
        "adf_residual": adf,
    }


def _rolling_residual_vol(resid: pd.Series, window: int = 60) -> dict:
    roll_std = resid.rolling(window).std().dropna()
    return {
        "window_days": window,
        "mean_rolling_vol": float(roll_std.mean()),
        "max_rolling_vol": float(roll_std.max()),
        "min_rolling_vol": float(roll_std.min()),
    }


def build_residual_study() -> dict:
    df = _load_residuals()
    resid = df["ema_residual"]

    stats = _residual_stats(resid)
    catalog_3sigma = _extreme_events_catalog(df, 3.0)
    catalog_2sigma = _extreme_events_catalog(df, 2.0)
    da_study = _directional_accuracy(resid)
    roll_vol = _rolling_residual_vol(resid)

    return {
        "n_obs": int(len(df)),
        "period_start": str(df["Date"].min().date()),
        "period_end": str(df["Date"].max().date()),
        "residual_stats": stats,
        "extreme_events_3sigma": catalog_3sigma,
        "extreme_events_2sigma": catalog_2sigma,
        "directional_study": da_study,
        "rolling_vol_60d": roll_vol,
        "key_findings": {
            "n_extreme_events_3sigma": catalog_3sigma.get("n_events"),
            "catalog_verdict_3sigma": catalog_3sigma.get("verdict"),
            "n_extreme_events_2sigma": catalog_2sigma.get("n_events"),
            "pct_extreme_3sigma": catalog_3sigma.get("pct_extreme"),
            "da_sign_persistence": da_study.get("da_sign_persistence_lag1"),
            "adf_residual_verdict": da_study.get("adf_residual", {}).get("verdict"),
            "residual_std": stats["std"],
        },
    }


def save_residual_study(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_residual_study()

    def _convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return str(obj.date())
        raise TypeError(f"Not serialisable: {type(obj)}")

    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=_convert)
    return path


if __name__ == "__main__":
    out = save_residual_study()
    print(f"Residual study saved → {out}")
