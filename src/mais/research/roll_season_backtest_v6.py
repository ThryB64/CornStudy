"""V6-04 — Roll-aware filters, seasonal experts and premium backtests."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.experiment_registry_v6 import make_record, save_registry
from mais.research.meta_model_premium_v6 import _feature_sets, _oof, build_meta_model_frame

_OUTPUT_DIR = ARTEFACTS_DIR / "v6"
_OUTPUT = _OUTPUT_DIR / "roll_season_backtest_v6.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "ROLL_SEASON_BACKTEST_V6.md"
_ROLL_PROXY_MONTHS = {2, 5, 7, 10}
_STRONG_SEASONS = {"jul_aug_yield_stress", "sep_nov_eu_harvest", "dec_import_export_arbitrage"}


def _season(month: int) -> str:
    if month in {1, 2, 3}:
        return "jan_mar_old_crop_import"
    if month in {4, 5, 6}:
        return "apr_jun_sowing_weather"
    if month in {7, 8}:
        return "jul_aug_yield_stress"
    if month in {9, 10, 11}:
        return "sep_nov_eu_harvest"
    return "dec_import_export_arbitrage"


def _annual_stability(pred: pd.DataFrame) -> float:
    years = []
    for _, group in pred.groupby("crop_year"):
        if len(group) >= 10 and group["y_true"].nunique() > 1:
            years.append(float(accuracy_score(group["y_true"], group["y_pred"]) >= 0.55))
    return float(np.mean(years)) if years else float("nan")


def _policy_mask(pred: pd.DataFrame, policy: str) -> pd.Series:
    if policy == "all":
        return pd.Series(True, index=pred.index)
    if policy == "no_roll_proxy":
        return ~pred["roll_proxy_risk"]
    if policy == "strong_season":
        return pred["season"].isin(_STRONG_SEASONS)
    if policy == "strong_season_no_roll":
        return pred["season"].isin(_STRONG_SEASONS) & ~pred["roll_proxy_risk"]
    if policy == "top40_train_only":
        return _train_only_confidence_mask(pred, coverage=0.40)
    if policy == "top20_train_only":
        return _train_only_confidence_mask(pred, coverage=0.20)
    if policy == "top40_no_roll":
        return _train_only_confidence_mask(pred, coverage=0.40) & ~pred["roll_proxy_risk"]
    raise ValueError(f"Unknown policy: {policy}")


def _train_only_confidence_mask(pred: pd.DataFrame, *, coverage: float) -> pd.Series:
    mask = pd.Series(False, index=pred.index)
    years = sorted(pred["crop_year"].dropna().unique())
    for idx, year in enumerate(years):
        train = pred[pred["crop_year"].isin(years[:idx])]
        test_idx = pred.index[pred["crop_year"].eq(year)]
        if len(train) < 40 or len(test_idx) == 0:
            continue
        threshold = train["confidence"].quantile(1.0 - coverage)
        mask.loc[test_idx] = pred.loc[test_idx, "confidence"] >= threshold
    return mask


def _evaluate_policy(pred: pd.DataFrame, policy: str) -> dict:
    mask = _policy_mask(pred, policy)
    sub = pred[mask].copy()
    row = {
        "policy": policy,
        "n": int(len(sub)),
        "coverage": float(len(sub) / len(pred)) if len(pred) else 0.0,
    }
    if len(sub) < 20 or sub["y_true"].nunique() < 2:
        return {**row, "status": "SKIPPED"}
    return {
        **row,
        "status": "OK",
        "da": float(accuracy_score(sub["y_true"], sub["y_pred"])),
        "balanced_accuracy": float(balanced_accuracy_score(sub["y_true"], sub["y_pred"])),
        "auc": float(roc_auc_score(sub["y_true"], sub["prob"])),
        "annual_stability_55": _annual_stability(sub),
    }


def _make_prediction_frame(df: pd.DataFrame, *, target: str, feature_set: str) -> pd.DataFrame:
    features = _feature_sets(df)[feature_set]
    pred = _oof(df, target, features)
    if pred.empty:
        return pred
    horizon = int(target.rsplit("_h", 1)[-1])
    value_cols = ["Date", f"relative_return_h{horizon}", "ema_front_price"]
    pred = pred.merge(df[value_cols], on="Date", how="left")
    pred["horizon"] = horizon
    pred["target"] = target
    pred["feature_set"] = feature_set
    pred["season"] = pred["month"].astype(int).map(_season)
    pred["roll_proxy_risk"] = pred["month"].astype(int).isin(_ROLL_PROXY_MONTHS)
    pred["signal"] = np.where(pred["prob"] >= 0.5, 1.0, -1.0)
    return pred.dropna(subset=[f"relative_return_h{horizon}", "ema_front_price"])


def _seasonal_expert(h40: pd.DataFrame, h90: pd.DataFrame) -> pd.DataFrame:
    h40 = h40.set_index("Date")
    h90 = h90.set_index("Date")
    rows = []
    for date in sorted(set(h40.index) | set(h90.index)):
        candidates = []
        if date in h40.index:
            candidates.append(h40.loc[date].copy())
        if date in h90.index:
            candidates.append(h90.loc[date].copy())
        if not candidates:
            continue
        month = int(candidates[0]["month"])
        preferred = 90 if _season(month) in {"jul_aug_yield_stress", "sep_nov_eu_harvest", "apr_jun_sowing_weather"} else 40
        chosen = next((row for row in candidates if int(row["horizon"]) == preferred), candidates[0])
        chosen = chosen.copy()
        chosen["Date"] = date
        chosen["expert_name"] = "seasonal_horizon_expert"
        rows.append(chosen)
    return pd.DataFrame(rows).sort_values("Date").reset_index(drop=True)


def _agreement_expert(h40: pd.DataFrame, h90: pd.DataFrame) -> pd.DataFrame:
    h40_cols = ["Date", "prob", "y_pred", "confidence", "signal"]
    h90_cols = ["Date", "y_true", "prob", "y_pred", "confidence", "signal", "relative_return_h90", "ema_front_price"]
    merged = h40[h40_cols].merge(h90[h90_cols], on="Date", suffixes=("_h40", "_h90"))
    if merged.empty:
        return merged
    context_cols = ["Date", "crop_year", "month", "season", "roll_proxy_risk"]
    context = h90[context_cols].drop_duplicates("Date")
    out = merged.merge(context, on="Date", how="left")
    out["agreement"] = out["signal_h40"].eq(out["signal_h90"])
    out = out[out["agreement"]].copy()
    out["prob"] = (out["prob_h40"] + out["prob_h90"]) / 2
    out["confidence"] = np.minimum(out["confidence_h40"], out["confidence_h90"])
    out["signal"] = out["signal_h40"]
    out["y_pred"] = (out["prob"] >= 0.5).astype(float)
    out["horizon"] = 90
    out["target"] = "h40_h90_agreement"
    out["feature_set"] = "classic_plus_meta"
    return out


def _backtest(pred: pd.DataFrame, *, policy: str, cost_per_leg: float) -> dict:
    mask = _policy_mask(pred, policy) if policy != "pre_filtered" else pd.Series(True, index=pred.index)
    candidates = pred[mask].sort_values("Date").copy()
    trades = []
    last_exit = pd.Timestamp.min
    for _, row in candidates.iterrows():
        entry = pd.Timestamp(row["Date"])
        horizon = int(row["horizon"])
        exit_date = entry + pd.Timedelta(days=horizon)
        if entry <= last_exit:
            continue
        rel_col = f"relative_return_h{horizon}"
        gross = float(row["signal"] * row[rel_col] * row["ema_front_price"])
        roll_cost = cost_per_leg if bool(row.get("roll_proxy_risk", False)) else 0.0
        net = gross - 2.0 * cost_per_leg - roll_cost
        trades.append({
            "entry_date": str(entry.date()),
            "exit_date": str(exit_date.date()),
            "crop_year": int(row["crop_year"]),
            "horizon": horizon,
            "season": row["season"],
            "gross_eur_t": gross,
            "net_eur_t": net,
            "correct": bool(row["y_pred"] == row["y_true"]),
        })
        last_exit = exit_date
    return _trade_metrics(trades, policy=policy, cost_per_leg=cost_per_leg)


def _trade_metrics(trades: list[dict], *, policy: str, cost_per_leg: float) -> dict:
    if not trades:
        return {"policy": policy, "cost_per_leg": cost_per_leg, "n_trades": 0, "status": "SKIPPED"}
    pnl = np.array([trade["net_eur_t"] for trade in trades], dtype=float)
    equity = np.cumsum(pnl)
    peak = np.maximum.accumulate(equity)
    wins = pnl[pnl > 0]
    losses = pnl[pnl <= 0]
    by_year = pd.DataFrame(trades).groupby("crop_year")["net_eur_t"].sum()
    return {
        "policy": policy,
        "cost_per_leg": float(cost_per_leg),
        "n_trades": int(len(trades)),
        "status": "OK",
        "hit_rate": float(np.mean(pnl > 0)),
        "signal_accuracy": float(np.mean([trade["correct"] for trade in trades])),
        "pnl_total_eur_t": float(pnl.sum()),
        "pnl_mean_eur_t": float(pnl.mean()),
        "profit_factor": float(wins.sum() / abs(losses.sum())) if len(losses) and losses.sum() < 0 else float("inf"),
        "max_drawdown_eur_t": float(np.min(equity - peak)),
        "positive_year_share": float((by_year > 0).mean()),
        "trades": trades,
    }


@lru_cache(maxsize=1)
def build_roll_season_backtest_v6() -> dict:
    df = build_meta_model_frame()
    h40 = _make_prediction_frame(df, target="y_rel_outperform_h40", feature_set="classic_plus_meta")
    h90 = _make_prediction_frame(df, target="y_rel_outperform_h90", feature_set="classic_plus_meta")
    seasonal = _seasonal_expert(h40, h90)
    agreement = _agreement_expert(h40, h90)

    scenarios = {
        "h40": h40,
        "h90": h90,
        "seasonal_expert": seasonal,
        "h40_h90_agreement": agreement,
    }
    policies = ["all", "no_roll_proxy", "strong_season", "strong_season_no_roll", "top40_train_only", "top20_train_only", "top40_no_roll"]
    policy_results = []
    backtests = []
    for name, pred in scenarios.items():
        if pred.empty:
            continue
        for policy in policies:
            row = _evaluate_policy(pred, policy)
            policy_results.append({"scenario": name, **row})
        bt_policy = "top40_no_roll" if name != "h40_h90_agreement" else "pre_filtered"
        for cost in [1.0, 2.0, 3.0, 5.0, 8.0]:
            backtests.append({"scenario": name, **_backtest(pred, policy=bt_policy, cost_per_leg=cost)})

    ok_policies = [row for row in policy_results if row.get("status") == "OK"]
    ok_backtests = [row for row in backtests if row.get("status") == "OK"]
    best_policy = max(ok_policies, key=lambda row: (row["balanced_accuracy"], row["coverage"]), default={})
    best_backtest = max(ok_backtests, key=lambda row: (row["pnl_total_eur_t"], row["profit_factor"]), default={})
    records = [
        make_record(
            experiment_id=f"V6-04-{row['scenario']}-{row['policy']}",
            feature_set=row["scenario"],
            target="premium_policy",
            horizon=str(row.get("scenario")),
            model="roll_season_filter",
            cv_protocol="oof_plus_train_only_thresholds",
            metrics={k: row[k] for k in ("auc", "balanced_accuracy", "coverage") if k in row},
            verdict="PROMISING" if row.get("balanced_accuracy", 0) >= 0.70 else "WATCHLIST",
            artefact_paths=["artefacts/v6/roll_season_backtest_v6.json"],
        )
        for row in ok_policies
    ]
    registry = save_registry(records) if records else {}
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "production_verdict": "RESEARCH_ONLY_NOT_TRADING",
        "policy_results": policy_results,
        "backtests": backtests,
        "registry": registry,
        "key_findings": {
            "best_policy": best_policy,
            "best_backtest": {k: v for k, v in best_backtest.items() if k != "trades"},
            "interpretation": _interpretation(best_policy, best_backtest),
        },
    }


def _interpretation(best_policy: dict, best_backtest: dict) -> str:
    if best_policy.get("balanced_accuracy", 0) >= 0.75 and best_backtest.get("pnl_total_eur_t", 0) > 0:
        return "Roll-aware and seasonal filters materially improve selectivity in research-only spread tests."
    if best_policy.get("balanced_accuracy", 0) >= 0.68:
        return "Filters improve classification quality, but economic robustness remains limited."
    return "Roll-aware and seasonal filters do not yet improve enough over the V6-03 meta-model."


def _json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return str(obj.date())
    if isinstance(obj, bool):
        return bool(obj)
    raise TypeError(f"Not serialisable: {type(obj)}")


def _write_doc(data: dict, path: Path) -> None:
    lines = [
        "# ROLL SEASON BACKTEST V6",
        "",
        "> Tests roll-aware, experts saisonniers et backtests research-only EMA/CBOT.",
        "",
        f"- Source quality : `{data['source_quality']}`",
        f"- Production verdict : `{data['production_verdict']}`",
        f"- Best policy : `{data['key_findings']['best_policy'].get('scenario')}` / `{data['key_findings']['best_policy'].get('policy')}`",
        f"- Best backtest : `{data['key_findings']['best_backtest'].get('scenario')}` / `{data['key_findings']['best_backtest'].get('policy')}`",
        f"- Lecture : {data['key_findings']['interpretation']}",
        "",
        "## Policy Results",
        "",
        "| Scenario | Policy | n | Coverage | AUC | BA | DA | Stability |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["policy_results"]:
        lines.append(
            f"| `{row['scenario']}` | `{row['policy']}` | {row.get('n', 0)} | {row.get('coverage', float('nan')):.3f} | "
            f"{row.get('auc', float('nan')):.3f} | {row.get('balanced_accuracy', float('nan')):.3f} | "
            f"{row.get('da', float('nan')):.3f} | {row.get('annual_stability_55', float('nan')):.3f} |"
        )
    lines += ["", "## Backtests Research Only", "", "| Scenario | Policy | Cost | Trades | Hit | PnL | PF | DD |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for row in data["backtests"]:
        lines.append(
            f"| `{row['scenario']}` | `{row['policy']}` | {row.get('cost_per_leg', float('nan')):.1f} | {row.get('n_trades', 0)} | "
            f"{row.get('hit_rate', float('nan')):.3f} | {row.get('pnl_total_eur_t', float('nan')):.2f} | "
            f"{row.get('profit_factor', float('nan')):.2f} | {row.get('max_drawdown_eur_t', float('nan')):.2f} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_roll_season_backtest_v6(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_roll_season_backtest_v6()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_doc(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_roll_season_backtest_v6()
    print(f"Roll season backtest V6 saved -> {out}")
