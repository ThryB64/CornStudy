"""V7-13 — Backtests recherche avancés (RESEARCH_ONLY_NOT_TRADING)."""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "backtests_v7.json"

HOLDOUT_CHECK_PATH = ARTEFACTS_DIR / "v7" / "holdout_lock.json"


def _check_holdout_not_used() -> bool:
    if HOLDOUT_CHECK_PATH.exists():
        lock = json.loads(HOLDOUT_CHECK_PATH.read_text())
        return not lock.get("used", True)
    return True


def _run_backtest_policy(
    signals: pd.DataFrame,
    y_forward: pd.Series,
    policy_name: str,
    confidence_threshold: float = 0.5,
    non_overlap_days: int = 40,
    cost_per_leg: float = 1.0,
) -> dict[str, Any]:
    """Backtest non-overlapping single direction."""
    valid = signals.index.intersection(y_forward.index)
    df_bt = signals.reindex(valid).join(y_forward.rename("y_fwd")).dropna()

    if len(df_bt) < 20:
        return {"verdict": "INSUFFICIENT_SIGNALS", "policy": policy_name}

    # Sélection par confiance
    selected = df_bt[df_bt.get("confidence", pd.Series(1.0, index=df_bt.index)) >= confidence_threshold]

    # Non-overlap
    trades = []
    last_exit = pd.Timestamp("2000-01-01")
    for date, row in selected.iterrows():
        if date > last_exit:
            pnl = float(row["y_fwd"]) - cost_per_leg
            trades.append({"date": str(date.date()), "pnl": pnl, "y_fwd": float(row["y_fwd"])})
            last_exit = date + pd.Timedelta(days=non_overlap_days)

    if not trades:
        return {"verdict": "NO_TRADES", "policy": policy_name}

    pnls = [t["pnl"] for t in trades]
    positive = sum(1 for p in pnls if p > 0)
    profit_factor = (
        sum(p for p in pnls if p > 0) / abs(sum(p for p in pnls if p < 0))
        if any(p < 0 for p in pnls) else float("inf")
    )
    cumulative = np.cumsum(pnls)
    max_dd = float(np.min(cumulative - np.maximum.accumulate(cumulative)))

    return {
        "policy": policy_name,
        "n_trades": len(trades),
        "hit_rate": round(positive / len(trades), 4),
        "pnl_mean": round(float(np.mean(pnls)), 4),
        "pnl_total": round(float(np.sum(pnls)), 4),
        "profit_factor": round(profit_factor, 4) if profit_factor != float("inf") else None,
        "max_drawdown": round(max_dd, 4),
        "verdict": "RESEARCH_ONLY_NOT_TRADING",
    }


def run_backtests_v7(df: pd.DataFrame) -> dict[str, Any]:
    # Vérification holdout
    if not _check_holdout_not_used():
        return {"version": "V7-13", "verdict": "HOLDOUT_ALREADY_USED"}

    # Filter out 2024 (holdout)
    df_no_holdout = df[df.index.year != 2024]

    exclude = {"y_", "Date", "date", "return_", "future_", "storage_", "prob_"}
    feat_cols = [c for c in df_no_holdout.columns
                 if not any(p in c for p in exclude)
                 and df_no_holdout[c].dtype in [np.float64, float]
                 and df_no_holdout[c].notna().mean() > 0.3][:60]

    y_col = next((c for c in ["y_up_h20", "y_up_h40", "y_up_h60"] if c in df_no_holdout.columns), None)
    if not y_col or not feat_cols:
        return {"version": "V7-13", "verdict": "NO_DATA"}

    # Générer signaux OOF
    common = df_no_holdout[feat_cols].join(df_no_holdout[y_col].rename("target")).dropna()
    if len(common) < 200:
        return {"version": "V7-13", "verdict": "INSUFFICIENT_DATA"}

    x_c = common.drop(columns=["target"]).fillna(0)
    y_c = common["target"]

    try:
        from lightgbm import LGBMClassifier
        tscv = TimeSeriesSplit(n_splits=5)
        oof = np.full(len(x_c), np.nan)
        for tr_idx, te_idx in tscv.split(x_c):
            if len(tr_idx) < 50 or y_c.iloc[tr_idx].nunique() < 2:
                continue
            clf = LGBMClassifier(n_estimators=100, seed=42, verbose=-1, n_jobs=1)
            clf.fit(x_c.iloc[tr_idx], y_c.iloc[tr_idx])
            oof[te_idx] = clf.predict_proba(x_c.iloc[te_idx])[:, 1]
    except ImportError:
        return {"version": "V7-13", "verdict": "LGBM_UNAVAILABLE"}

    oof_series = pd.Series(oof, index=x_c.index, name="confidence")
    signals_df = oof_series.to_frame()

    # Proxy forward return en EUR/t (rendement * prix EMA ou prix CBOT)
    if "ema_close" in df_no_holdout.columns:
        price = df_no_holdout["ema_close"]
    elif "cbot_eur_t" in df_no_holdout.columns:
        price = df_no_holdout["cbot_eur_t"]
    else:
        price = pd.Series(200.0, index=df_no_holdout.index)

    y_fwd = df_no_holdout[y_col].reindex(oof_series.index) * price.reindex(oof_series.index) * 0.02
    y_fwd = y_fwd.fillna(0)

    policies: dict[str, dict] = {}
    for policy_name, threshold, cost in [
        ("full_signal", 0.0, 0.5),
        ("top40", 0.6, 1.0),
        ("top20", 0.7, 1.0),
        ("top10", 0.8, 2.0),
        ("seasonal_summer", 0.55, 1.0),
    ]:
        # Pour seasonal_summer : filtrer juin-août
        if policy_name == "seasonal_summer":
            summer = signals_df[signals_df.index.month.isin([6, 7, 8])]
            signals_pol = summer
        else:
            signals_pol = signals_df

        policies[policy_name] = _run_backtest_policy(
            signals_pol, y_fwd, policy_name, threshold, non_overlap_days=40, cost_per_leg=cost
        )

    # Meilleure politique par profit_factor
    valid_policies = [(n, v) for n, v in policies.items() if v.get("n_trades", 0) >= 5 and v.get("profit_factor")]
    best_policy = max(valid_policies, key=lambda x: x[1]["profit_factor"])[0] if valid_policies else None

    return {
        "version": "V7-13",
        "holdout_respected": True,
        "n_signals": int((~np.isnan(oof)).sum()),
        "target": y_col,
        "policies": policies,
        "best_policy": best_policy,
        "verdict": "RESEARCH_ONLY_NOT_TRADING",
        "experiment_type": "BACKTEST_RESEARCH",
    }


def save_backtests_v7(df: pd.DataFrame) -> dict[str, Any]:
    result = run_backtests_v7(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-13",
        target=result.get("target", "backtest"),
        horizon=40,
        model="lgbm_oof_backtest",
        cv_protocol="time_series_split_5_no_holdout",
        embargo_days=0,
        n_oof=result.get("n_signals", 0),
        features=["lgbm_oof_signal"],
        metrics={
            "best_policy": result.get("best_policy"),
            "n_policies": len(result.get("policies", {})),
        },
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
