"""NB-EMA-04 — Relation EMA/CBOT : cointégration, Granger, corrélation rolling."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_cbot_cointegration.json"
_ROLLING_WINDOW = 260
_MAX_LAGS = 10


def _load_aligned() -> pd.DataFrame:
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    df = feats[feats["ema_front_price"].notna() & feats["cbot_eur_t"].notna()].copy()
    return df[["Date", "ema_front_price", "cbot_eur_t"]].sort_values("Date").reset_index(drop=True)


def _engle_granger(ema: pd.Series, cbot: pd.Series) -> dict:
    try:
        from statsmodels.tsa.stattools import coint
        stat, p_val, crit = coint(ema, cbot)
        return {
            "test": "engle_granger",
            "stat": float(stat),
            "p_value": float(p_val),
            "crit_1pct": float(crit[0]),
            "crit_5pct": float(crit[1]),
            "crit_10pct": float(crit[2]),
            "cointegrated_5pct": bool(p_val < 0.05),
        }
    except ImportError:
        return {"error": "statsmodels_not_available"}


def _johansen(ema: pd.Series, cbot: pd.Series) -> dict:
    try:
        from statsmodels.tsa.vector_ar.vecm import coint_johansen
        data = pd.concat([ema, cbot], axis=1).dropna()
        res = coint_johansen(data, det_order=0, k_ar_diff=1)
        trace_stat = res.lr1.tolist()
        trace_crit_5pct = res.cvt[:, 1].tolist()
        return {
            "test": "johansen",
            "trace_stats": [float(x) for x in trace_stat],
            "trace_crit_5pct": [float(x) for x in trace_crit_5pct],
            "n_coint_relations_5pct": int(sum(s > c for s, c in zip(trace_stat, trace_crit_5pct, strict=False))),
        }
    except ImportError:
        return {"error": "statsmodels_not_available"}


def _vecm_estimate(ema: pd.Series, cbot: pd.Series) -> dict:
    try:
        from statsmodels.tsa.vector_ar.vecm import VECM
        data = pd.concat([ema, cbot], axis=1).dropna()
        model = VECM(data, k_ar_diff=1, coint_rank=1, deterministic="n")
        fit = model.fit()
        alpha = fit.alpha.flatten().tolist()
        beta = fit.beta.flatten().tolist()
        return {
            "alpha_ema": float(alpha[0]),
            "alpha_cbot": float(alpha[1]) if len(alpha) > 1 else float("nan"),
            "beta": [float(b) for b in beta],
            "half_life_days": float(-np.log(2) / np.log(1 + alpha[0])) if alpha[0] < 0 else float("nan"),
        }
    except Exception as e:
        return {"error": str(e)[:100]}


def _granger_test(df: pd.DataFrame, cause: str, effect: str, max_lags: int) -> dict:
    try:
        from statsmodels.tsa.stattools import grangercausalitytests
        data = df[[effect, cause]].dropna()
        res = grangercausalitytests(data, maxlag=max_lags, verbose=False)
        best_lag, best_p = min(
            ((lag, r[0]["ssr_ftest"][1]) for lag, r in res.items()),
            key=lambda x: x[1],
        )
        return {
            "cause": cause,
            "effect": effect,
            "best_lag": int(best_lag),
            "best_p_value": float(best_p),
            "granger_significant_5pct": bool(best_p < 0.05),
            "all_lags_p": {str(lag): float(r[0]["ssr_ftest"][1]) for lag, r in res.items()},
        }
    except ImportError:
        return {"error": "statsmodels_not_available"}


def _rolling_correlation(ema: pd.Series, cbot: pd.Series, window: int) -> dict:
    corr = ema.rolling(window).corr(cbot).dropna()
    return {
        "window_days": window,
        "n_windows": int(len(corr)),
        "mean_corr": float(corr.mean()),
        "min_corr": float(corr.min()),
        "max_corr": float(corr.max()),
        "std_corr": float(corr.std()),
        "pct_corr_gt_08": float((corr > 0.8).mean()),
        "pct_corr_lt_05": float((corr < 0.5).mean()),
    }


def _static_corr(ema: pd.Series, cbot: pd.Series) -> dict:
    aligned = pd.concat([ema, cbot], axis=1).dropna()
    rets_ema = aligned.iloc[:, 0].pct_change().dropna()
    rets_cbt = aligned.iloc[:, 1].pct_change().dropna()
    ret_aligned = pd.concat([rets_ema, rets_cbt], axis=1).dropna()
    corr_levels = float(aligned.iloc[:, 0].corr(aligned.iloc[:, 1]))
    corr_rets = float(ret_aligned.iloc[:, 0].corr(ret_aligned.iloc[:, 1]))
    return {
        "corr_price_levels": corr_levels,
        "corr_daily_returns": corr_rets,
        "n_overlap": int(len(aligned)),
    }


def build_cbot_cointegration() -> dict:
    df = _load_aligned()
    ema = df["ema_front_price"]
    cbot = df["cbot_eur_t"]

    eg = _engle_granger(ema, cbot)
    johansen = _johansen(ema, cbot)
    vecm = _vecm_estimate(ema, cbot) if eg.get("cointegrated_5pct") else {"skipped": "not_cointegrated"}
    granger_ema_to_cbot = _granger_test(df.rename(columns={"ema_front_price": "ema", "cbot_eur_t": "cbot"}), "ema", "cbot", _MAX_LAGS)
    granger_cbot_to_ema = _granger_test(df.rename(columns={"ema_front_price": "ema", "cbot_eur_t": "cbot"}), "cbot", "ema", _MAX_LAGS)
    rolling_corr = _rolling_correlation(ema, cbot, _ROLLING_WINDOW)
    static = _static_corr(ema, cbot)

    return {
        "n_overlap_days": int(len(df)),
        "period_start": str(df["Date"].min().date()),
        "period_end": str(df["Date"].max().date()),
        "static_correlation": static,
        "engle_granger": eg,
        "johansen": johansen,
        "vecm": vecm,
        "granger_ema_to_cbot": granger_ema_to_cbot,
        "granger_cbot_to_ema": granger_cbot_to_ema,
        "rolling_corr_260d": rolling_corr,
        "key_findings": {
            "cointegrated_5pct_eg": eg.get("cointegrated_5pct"),
            "n_coint_relations_johansen": johansen.get("n_coint_relations_5pct"),
            "granger_ema_cbot_p": granger_ema_to_cbot.get("best_p_value"),
            "granger_cbot_ema_p": granger_cbot_to_ema.get("best_p_value"),
            "granger_ema_cbot_significant": granger_ema_to_cbot.get("granger_significant_5pct"),
            "granger_cbot_ema_significant": granger_cbot_to_ema.get("granger_significant_5pct"),
            "corr_price_levels": static.get("corr_price_levels"),
            "corr_daily_returns": static.get("corr_daily_returns"),
            "mean_rolling_corr_260d": rolling_corr.get("mean_corr"),
            "vecm_half_life_days": vecm.get("half_life_days"),
        },
    }


def save_cbot_cointegration(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_cbot_cointegration()

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
    out = save_cbot_cointegration()
    print(f"Cointegration saved → {out}")
