"""NB-EMA-03 — Validation et analyse des séries continues EMA (raw vs adjusted)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, EMA_FRONT_ADJUSTED, EMA_FRONT_RAW

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_continuous_series.json"
_INVARIANT_TOL = 0.01


def _load(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def _invariant_check(adj: pd.DataFrame) -> dict:
    """Vérifie raw_price - adjusted_price == cum_roll_adjustment (tolérance < 0.01)."""
    residual = (adj["price"] - adj["adjusted_price"] - adj["cum_roll_adjustment"]).abs()
    n_violations = int((residual > _INVARIANT_TOL).sum())
    return {
        "invariant": "price - adjusted_price == cum_roll_adjustment",
        "tolerance": _INVARIANT_TOL,
        "max_residual": float(residual.max()),
        "mean_residual": float(residual.mean()),
        "n_violations": n_violations,
        "invariant_holds": n_violations == 0,
    }


def _trading_day_gaps(df: pd.DataFrame) -> dict:
    dates = df["date"].drop_duplicates().sort_values()
    bdays = pd.bdate_range(dates.min(), dates.max())
    missing = bdays.difference(dates)
    n_missing = int(len(missing))
    n_total = int(len(bdays))
    coverage = float(len(dates) / max(n_total, 1))
    # Identify gap periods ≥ 5 consecutive missing bdays
    gaps = []
    if n_missing > 0:
        gs = missing[0]
        prev = missing[0]
        for d in missing[1:]:
            if (d - prev).days > 3:
                gaps.append({"start": str(gs.date()), "end": str(prev.date()), "n": int((prev - gs).days + 1)})
                gs = d
            prev = d
        gaps.append({"start": str(gs.date()), "end": str(prev.date()), "n": int((prev - gs).days + 1)})
        gaps = [g for g in gaps if g["n"] >= 5]
    return {
        "n_total_bdays": n_total,
        "n_observed": int(len(dates)),
        "n_missing": n_missing,
        "coverage_rate": coverage,
        "n_gaps_ge5": len(gaps),
        "gaps": gaps,
    }


def _return_stats(series: pd.Series, label: str) -> dict:
    rets = series.pct_change().dropna()
    if len(rets) == 0:
        return {"label": label, "error": "no_data"}
    return {
        "label": label,
        "n": int(len(rets)),
        "mean_daily_ret": float(rets.mean()),
        "std_daily_ret": float(rets.std()),
        "skewness": float(rets.skew()),
        "kurtosis": float(rets.kurt()),
        "min_ret": float(rets.min()),
        "max_ret": float(rets.max()),
        "annualized_vol": float(rets.std() * np.sqrt(252)),
    }


def _adf_on_returns(series: pd.Series) -> dict:
    try:
        from statsmodels.tsa.stattools import adfuller
        rets = series.pct_change().dropna()
        res = adfuller(rets, autolag="AIC")
        return {
            "adf_stat": float(res[0]),
            "p_value": float(res[1]),
            "n_lags": int(res[2]),
            "verdict": "stationary" if res[1] < 0.05 else "non_stationary",
        }
    except ImportError:
        return {"error": "statsmodels_not_available"}


def _price_level_stats(series: pd.Series, label: str) -> dict:
    return {
        "label": label,
        "n_days": int(len(series)),
        "period_start": str(series.index.min().date()) if hasattr(series.index.min(), "date") else str(series.index.min()),
        "period_end": str(series.index.max().date()) if hasattr(series.index.max(), "date") else str(series.index.max()),
        "mean": float(series.mean()),
        "std": float(series.std()),
        "min": float(series.min()),
        "max": float(series.max()),
        "median": float(series.median()),
    }


def _divergence_raw_vs_adj(raw: pd.DataFrame, adj: pd.DataFrame) -> dict:
    merged = pd.merge(
        raw[["date", "price"]].rename(columns={"price": "raw"}),
        adj[["date", "adjusted_price"]].rename(columns={"adjusted_price": "adj"}),
        on="date", how="inner",
    )
    if len(merged) < 10:
        return {"error": "insufficient_overlap"}
    diff = (merged["raw"] - merged["adj"]).abs()
    rets_raw = merged["raw"].pct_change().dropna()
    rets_adj = merged["adj"].pct_change().dropna()
    aligned = pd.concat([rets_raw.rename("r"), rets_adj.rename("a")], axis=1).dropna()
    corr_ret = float(aligned["r"].corr(aligned["a"])) if len(aligned) > 1 else float("nan")
    sign_agree = float((np.sign(aligned["r"]) == np.sign(aligned["a"])).mean()) if len(aligned) > 1 else float("nan")
    return {
        "n_overlap": int(len(merged)),
        "mean_abs_price_diff": float(diff.mean()),
        "max_abs_price_diff": float(diff.max()),
        "corr_daily_returns": corr_ret,
        "direction_agreement": sign_agree,
    }


def build_continuous_series() -> dict:
    raw = _load(EMA_FRONT_RAW)
    adj = _load(EMA_FRONT_ADJUSTED)

    invariant = _invariant_check(adj)
    gaps_raw = _trading_day_gaps(raw)
    gaps_adj = _trading_day_gaps(adj)

    raw_indexed = raw.set_index("date")["price"]
    adj_indexed = adj.set_index("date")["adjusted_price"]

    price_stats_raw = _price_level_stats(raw_indexed, "raw")
    price_stats_adj = _price_level_stats(adj_indexed, "adjusted")

    ret_stats_raw = _return_stats(raw_indexed, "raw")
    ret_stats_adj = _return_stats(adj_indexed, "adjusted")

    adf_raw = _adf_on_returns(raw_indexed)
    adf_adj = _adf_on_returns(adj_indexed)

    divergence = _divergence_raw_vs_adj(raw, adj)

    return {
        "invariant_check": invariant,
        "gaps_raw": gaps_raw,
        "gaps_adjusted": gaps_adj,
        "price_stats_raw": price_stats_raw,
        "price_stats_adjusted": price_stats_adj,
        "return_stats_raw": ret_stats_raw,
        "return_stats_adjusted": ret_stats_adj,
        "adf_returns_raw": adf_raw,
        "adf_returns_adjusted": adf_adj,
        "divergence_raw_vs_adjusted": divergence,
        "key_findings": {
            "invariant_holds": invariant["invariant_holds"],
            "max_invariant_residual": invariant["max_residual"],
            "coverage_rate_raw": gaps_raw["coverage_rate"],
            "coverage_rate_adj": gaps_adj["coverage_rate"],
            "n_gaps_ge5_raw": gaps_raw["n_gaps_ge5"],
            "direction_agreement_raw_adj": divergence.get("direction_agreement"),
            "adf_returns_adj_verdict": adf_adj.get("verdict"),
        },
    }


def save_continuous_series(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_continuous_series()

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
    out = save_continuous_series()
    print(f"Continuous series saved → {out}")
