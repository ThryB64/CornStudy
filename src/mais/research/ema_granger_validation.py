"""VALID-GRANGER-01 — Validation robustesse Granger EMA→CBOT (5 tests)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_granger_validation.json"
_MAX_LAGS = 10


def _load_data() -> pd.DataFrame:
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    df = feats[feats["ema_front_price"].notna() & feats["cbot_eur_t"].notna()].copy()
    df = df[["Date", "ema_front_price", "cbot_eur_t"]].sort_values("Date").reset_index(drop=True)
    df["ema_ret"] = df["ema_front_price"].pct_change()
    df["cbot_ret"] = df["cbot_eur_t"].pct_change()
    return df.dropna()


def _granger_p(df: pd.DataFrame, cause: str, effect: str, max_lags: int = _MAX_LAGS) -> dict:
    try:
        from statsmodels.tsa.stattools import grangercausalitytests
        data = df[[effect, cause]].dropna()
        res = grangercausalitytests(data, maxlag=max_lags, verbose=False)
        lag_ps = {int(lag): float(r[0]["ssr_ftest"][1]) for lag, r in res.items()}
        best_lag = min(lag_ps, key=lag_ps.get)
        return {"best_lag": int(best_lag), "best_p": float(lag_ps[best_lag]), "all_lags_p": lag_ps}
    except ImportError:
        return {"error": "statsmodels_not_available"}


def _test1_temporal_robustness(df: pd.DataFrame) -> dict:
    """Test 1 : robustesse temporelle — Granger EMA→CBOT sur 3 sous-périodes."""
    n = len(df)
    thirds = [df.iloc[:n // 3], df.iloc[n // 3:2 * n // 3], df.iloc[2 * n // 3:]]
    labels = ["period_1_early", "period_2_mid", "period_3_late"]
    results = {}
    significant_count = 0
    for label, sub in zip(labels, thirds, strict=False):
        r = _granger_p(sub[["ema_ret", "cbot_ret"]], "ema_ret", "cbot_ret")
        results[label] = {"start": str(sub["Date"].min().date()), "end": str(sub["Date"].max().date()), **r}
        if r.get("best_p", 1.0) < 0.05:
            significant_count += 1
    verdict = "ROBUST" if significant_count >= 2 else ("PARTIAL" if significant_count == 1 else "NOT_ROBUST")
    return {"name": "temporal_robustness", "n_periods_significant": significant_count, "verdict": verdict, "periods": results}


def _test2_lag_robustness(df: pd.DataFrame) -> dict:
    """Test 2 : robustesse aux lags — Granger EMA→CBOT pour max_lag in [1,3,5,10]."""
    results = {}
    sig_count = 0
    for ml in [1, 3, 5, 10]:
        r = _granger_p(df[["ema_ret", "cbot_ret"]], "ema_ret", "cbot_ret", max_lags=ml)
        results[f"max_lag_{ml}"] = r
        if r.get("best_p", 1.0) < 0.05:
            sig_count += 1
    verdict = "ROBUST" if sig_count >= 3 else ("PARTIAL" if sig_count >= 2 else "NOT_ROBUST")
    return {"name": "lag_robustness", "n_configs_significant": sig_count, "verdict": verdict, "configs": results}


def _test3_eur_usd_neutralization(df: pd.DataFrame) -> dict:
    """Test 3 : neutralisation EUR/USD — Granger sur retours en USD (approx via dénominateur commun).
    Comme nous n'avons pas de série EUR/USD directe, nous testons sur les niveaux de prix bruts
    et sur les retours log pour contrôler l'effet FX.
    """
    # Proxy: utiliser log returns pour neutraliser partiellement les effets FX
    sub = df.copy()
    sub["ema_logret"] = np.log(sub["ema_front_price"]).diff()
    sub["cbot_logret"] = np.log(sub["cbot_eur_t"]).diff()
    sub = sub.dropna()

    r_logret = _granger_p(sub[["ema_logret", "cbot_logret"]], "ema_logret", "cbot_logret")
    r_pctret = _granger_p(df[["ema_ret", "cbot_ret"]], "ema_ret", "cbot_ret")

    sig_log = r_logret.get("best_p", 1.0) < 0.05
    sig_pct = r_pctret.get("best_p", 1.0) < 0.05
    consistent = sig_log == sig_pct

    return {
        "name": "eur_usd_neutralization",
        "note": "FX direct non disponible. Proxy via log returns vs pct returns.",
        "granger_pct_returns": r_pctret,
        "granger_log_returns": r_logret,
        "consistent_across_transformations": consistent,
        "verdict": "ROBUST" if (sig_log and sig_pct) else ("PARTIAL" if (sig_log or sig_pct) else "NOT_ROBUST"),
    }


def _test4_oof_validation(df: pd.DataFrame) -> dict:
    """Test 4 : validation OOF — entraîner Granger sur première moitié, vérifier p sur seconde."""
    n = len(df)
    train = df.iloc[:n // 2]
    test = df.iloc[n // 2:]

    r_train = _granger_p(train[["ema_ret", "cbot_ret"]], "ema_ret", "cbot_ret")
    r_test = _granger_p(test[["ema_ret", "cbot_ret"]], "ema_ret", "cbot_ret")

    sig_train = r_train.get("best_p", 1.0) < 0.05
    sig_test = r_test.get("best_p", 1.0) < 0.05
    verdict = "OOF_CONFIRMED" if (sig_train and sig_test) else ("TRAIN_ONLY" if sig_train else "NOT_SIGNIFICANT")

    return {
        "name": "oof_validation",
        "train_period": {"start": str(train["Date"].min().date()), "end": str(train["Date"].max().date())},
        "test_period": {"start": str(test["Date"].min().date()), "end": str(test["Date"].max().date())},
        "granger_train": r_train,
        "granger_test": r_test,
        "significant_in_train": sig_train,
        "significant_in_test": sig_test,
        "verdict": verdict,
    }


def _test5_exclude_2022(df: pd.DataFrame) -> dict:
    """Test 5 : exclusion 2022 — est-ce que Granger tient hors période Ukraine ?"""
    df_no22 = df[~df["Date"].dt.year.isin([2022])].copy()
    df_only22 = df[df["Date"].dt.year == 2022].copy()

    r_no22 = _granger_p(df_no22[["ema_ret", "cbot_ret"]], "ema_ret", "cbot_ret")
    r_full = _granger_p(df[["ema_ret", "cbot_ret"]], "ema_ret", "cbot_ret")

    sig_no22 = r_no22.get("best_p", 1.0) < 0.05
    sig_full = r_full.get("best_p", 1.0) < 0.05

    return {
        "name": "exclude_2022",
        "n_obs_excl_2022": int(len(df_no22)),
        "n_obs_2022_only": int(len(df_only22)),
        "granger_full": r_full,
        "granger_excl_2022": r_no22,
        "significant_full": sig_full,
        "significant_excl_2022": sig_no22,
        "verdict": "ROBUST" if (sig_full and sig_no22) else ("2022_DRIVEN" if (sig_full and not sig_no22) else "NOT_SIGNIFICANT"),
    }


def build_granger_validation() -> dict:
    df = _load_data()

    t1 = _test1_temporal_robustness(df)
    t2 = _test2_lag_robustness(df)
    t3 = _test3_eur_usd_neutralization(df)
    t4 = _test4_oof_validation(df)
    t5 = _test5_exclude_2022(df)

    verdicts = [t1["verdict"], t2["verdict"], t3["verdict"], t4["verdict"], t5["verdict"]]
    n_robust = sum(v in ("ROBUST", "OOF_CONFIRMED") for v in verdicts)
    overall = "CONFIRMED" if n_robust >= 4 else ("PARTIAL" if n_robust >= 2 else "REJECTED")

    return {
        "n_obs_total": int(len(df)),
        "period": {"start": str(df["Date"].min().date()), "end": str(df["Date"].max().date())},
        "test1_temporal_robustness": t1,
        "test2_lag_robustness": t2,
        "test3_eur_usd_neutralization": t3,
        "test4_oof_validation": t4,
        "test5_exclude_2022": t5,
        "summary": {
            "verdicts": dict(zip(["t1", "t2", "t3", "t4", "t5"], verdicts, strict=False)),
            "n_robust_or_confirmed": n_robust,
            "overall_verdict": overall,
            "note": "Granger EMA→CBOT. Confirmé si ≥4/5 tests robustes.",
        },
    }


def save_granger_validation(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_granger_validation()

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
    out = save_granger_validation()
    print(f"Granger validation saved → {out}")
