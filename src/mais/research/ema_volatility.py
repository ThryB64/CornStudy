"""NB-EMA-11 — Modélisation de la volatilité EMA : HAR et statistiques descriptives."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_volatility.json"


def _load_returns() -> pd.DataFrame:
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    df = feats[feats["ema_front_price"].notna()].copy()
    df = df[["Date", "ema_front_price"]].sort_values("Date").reset_index(drop=True)
    df["ema_ret"] = df["ema_front_price"].pct_change()
    df["rv_1d"] = df["ema_ret"].abs()
    df["rv_5d"] = df["ema_ret"].rolling(5).std() * np.sqrt(252)
    df["rv_20d"] = df["ema_ret"].rolling(20).std() * np.sqrt(252)
    df["rv_60d"] = df["ema_ret"].rolling(60).std() * np.sqrt(252)
    return df.dropna().reset_index(drop=True)


def _vol_descriptive(df: pd.DataFrame) -> dict:
    rv = df["rv_20d"]
    return {
        "mean_ann_vol_20d": float(rv.mean()),
        "std_ann_vol_20d": float(rv.std()),
        "min_ann_vol_20d": float(rv.min()),
        "max_ann_vol_20d": float(rv.max()),
        "pct_vol_gt_20pct": float((rv > 0.20).mean()),
        "pct_vol_gt_30pct": float((rv > 0.30).mean()),
        "n": int(len(rv)),
    }


def _har_model(df: pd.DataFrame) -> dict:
    """HAR-RV : RV_d = c + β_d*RV_{d-1} + β_w*RV_{5d,d-1} + β_m*RV_{20d,d-1} + ε."""
    df2 = df.copy()
    df2["rv_daily"] = df2["rv_1d"]
    df2["rv_weekly_lag"] = df2["rv_5d"].shift(1)
    df2["rv_monthly_lag"] = df2["rv_20d"].shift(1)
    df2["rv_daily_lag"] = df2["rv_daily"].shift(1)
    sub = df2[["rv_daily", "rv_daily_lag", "rv_weekly_lag", "rv_monthly_lag"]].dropna()
    y = sub["rv_daily"].values
    x_har = sub[["rv_daily_lag", "rv_weekly_lag", "rv_monthly_lag"]].values
    xc = np.column_stack([np.ones(len(y)), x_har])
    coefs, _, _, _ = np.linalg.lstsq(xc, y, rcond=None)
    y_hat = xc @ coefs
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = float(1 - ss_res / ss_tot)
    intercept, beta_d, beta_w, beta_m = coefs.tolist()
    return {
        "model": "HAR-RV",
        "intercept": float(intercept),
        "beta_daily": float(beta_d),
        "beta_weekly": float(beta_w),
        "beta_monthly": float(beta_m),
        "r2": r2,
        "n": int(len(y)),
        "note": "HAR-RV in-sample. Validation OOF non effectuée.",
    }


def _garch_attempt(ret: pd.Series) -> dict:
    try:
        from arch import arch_model
        am = arch_model(ret * 100, vol="Garch", p=1, q=1, dist="normal")
        res = am.fit(disp="off")
        return {
            "model": "GARCH(1,1)",
            "omega": float(res.params.get("omega", float("nan"))),
            "alpha[1]": float(res.params.get("alpha[1]", float("nan"))),
            "beta[1]": float(res.params.get("beta[1]", float("nan"))),
            "persistence": float(res.params.get("alpha[1]", 0) + res.params.get("beta[1]", 0)),
            "aic": float(res.aic),
            "log_likelihood": float(res.loglikelihood),
        }
    except ImportError:
        return {"error": "arch_not_available"}
    except Exception as e:
        return {"error": str(e)[:80]}


def _vol_regime_stats(df: pd.DataFrame) -> dict:
    rv = df["rv_20d"]
    q33 = rv.quantile(0.33)
    q67 = rv.quantile(0.67)
    low = df[rv <= q33]["ema_ret"]
    mid = df[(rv > q33) & (rv <= q67)]["ema_ret"]
    high = df[rv > q67]["ema_ret"]
    return {
        "low_vol_threshold": float(q33),
        "high_vol_threshold": float(q67),
        "low_vol_n": int(len(low)),
        "mid_vol_n": int(len(mid)),
        "high_vol_n": int(len(high)),
        "low_vol_mean_ret": float(low.mean()),
        "high_vol_mean_ret": float(high.mean()),
        "low_vol_std": float(low.std()),
        "high_vol_std": float(high.std()),
    }


def build_volatility() -> dict:
    df = _load_returns()
    desc = _vol_descriptive(df)
    har = _har_model(df)
    garch = _garch_attempt(df["ema_ret"])
    regime = _vol_regime_stats(df)

    return {
        "n_obs": int(len(df)),
        "period_start": str(df["Date"].min().date()),
        "period_end": str(df["Date"].max().date()),
        "descriptive_vol": desc,
        "har_model": har,
        "garch_model": garch,
        "vol_regime_stats": regime,
        "key_findings": {
            "mean_ann_vol": desc["mean_ann_vol_20d"],
            "max_ann_vol": desc["max_ann_vol_20d"],
            "pct_high_vol_days": desc["pct_vol_gt_20pct"],
            "har_r2": har["r2"],
            "har_persistence": float(har["beta_daily"] + har["beta_weekly"] + har["beta_monthly"]),
            "garch_available": "error" not in garch,
        },
    }


def save_volatility(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_volatility()

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
    out = save_volatility()
    print(f"Volatility saved → {out}")
