"""NB2-07 — Benchmarks directionnels EMA sur cibles relatives et européennes."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, PROJECT_ROOT
from mais.research.ema_residual_eu_v2 import _compute_oof_residuals
from mais.research.ema_residual_eu_v2 import _load_data as _load_residual_base
from mais.research.ema_utils import (
    binary_target_from_condition,
    binary_target_from_future_return,
    bootstrap_ci,
    crop_year,
)

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_direction_benchmarks_v2.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_DIRECTION_BENCHMARKS_V2.md"

_FEATURES = [
    "ema_cbot_basis",
    "ema_cbot_basis_zscore_52w",
    "ema_front_vol_20d_adjusted",
    "corn_realized_vol_20",
    "corn_logret_20d",
    "corn_gas_ratio",
    "fedfunds_level_zscore",
]


def _load_dataset() -> pd.DataFrame:
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    df = feats[feats["ema_front_price"].notna() & feats["cbot_eur_t"].notna()].copy()
    df = df.sort_values("Date").reset_index(drop=True)
    df["crop_year"] = df["Date"].apply(crop_year)
    for h in [20, 40]:
        ema_ret = df["ema_front_price"].pct_change(h).shift(-h)
        cbot_ret = df["cbot_eur_t"].pct_change(h).shift(-h)
        df[f"relative_return_h{h}"] = ema_ret - cbot_ret
        df[f"y_ema_outperforms_cbot_h{h}"] = binary_target_from_future_return(
            df[f"relative_return_h{h}"]
        )
        df[f"y_up_h{h}_ema_raw"] = binary_target_from_future_return(ema_ret)
    basis = df["ema_cbot_basis"]
    z = df["ema_cbot_basis_zscore_52w"]
    future_basis = basis.shift(-20)
    event = z.abs() >= 1.5
    reverts = ((z >= 1.5) & (future_basis < basis)) | ((z <= -1.5) & (future_basis > basis))
    df["basis_reversion_h20"] = binary_target_from_condition(
        reverts,
        event & future_basis.notna() & basis.notna() & z.notna(),
    )
    vol_future = df["ema_front_price"].pct_change().rolling(20).std().shift(-20) * np.sqrt(252)
    df["ema_vol_high_h20"] = binary_target_from_condition(vol_future > 0.25, vol_future.notna())
    resid = _compute_oof_residuals(_load_residual_base())[["Date", "ema_residual_oof"]]
    df = df.merge(resid, on="Date", how="left")
    sigma = df["ema_residual_oof"].std()
    future_resid = df["ema_residual_oof"].shift(-20)
    df["eu_residual_shock_up_h20"] = binary_target_from_condition(
        future_resid > 2 * sigma,
        future_resid.notna(),
    )
    df["eu_residual_shock_down_h20"] = binary_target_from_condition(
        future_resid < -2 * sigma,
        future_resid.notna(),
    )
    return df


def _target_map() -> dict[str, str]:
    return {
        "basis_reversion_h20": "basis_reversion_h20",
        "relative_ema_outperformance_h20": "y_ema_outperforms_cbot_h20",
        "relative_ema_outperformance_h40": "y_ema_outperforms_cbot_h40",
        "eu_residual_shock_up_h20": "eu_residual_shock_up_h20",
        "eu_residual_shock_down_h20": "eu_residual_shock_down_h20",
        "ema_vol_high_h20": "ema_vol_high_h20",
        "ema_direction_absolute_h40": "y_up_h40_ema_raw",
    }


def _bh_q_values(p_values: list[float]) -> list[float]:
    arr = np.array([1.0 if np.isnan(p) else p for p in p_values], dtype=float)
    n = len(arr)
    order = np.argsort(arr)
    q = np.empty(n)
    prev = 1.0
    for rank, idx in enumerate(order[::-1], start=1):
        true_rank = n - rank + 1
        val = min(prev, arr[idx] * n / true_rank)
        q[idx] = val
        prev = val
    return [float(x) for x in q]


def _p_value_da(successes: int, n: int) -> float:
    if n == 0:
        return float("nan")
    try:
        from scipy.stats import binomtest
        return float(binomtest(successes, n, p=0.5, alternative="greater").pvalue)
    except Exception:
        return float("nan")


def _evaluate(df: pd.DataFrame, target: str, weekly: bool = False, exclude_year: int | None = None) -> dict:
    feature_cols = [c for c in _FEATURES if c in df.columns]
    work = df.copy()
    for col in feature_cols:
        work[f"{col}_lag1"] = work[col].shift(1)
    lag_cols = [f"{c}_lag1" for c in feature_cols]
    cols = ["Date", "crop_year", target, *lag_cols]
    work = work[cols].replace([np.inf, -np.inf], np.nan).dropna()
    if exclude_year is not None:
        work = work[work["Date"].dt.year != exclude_year]
    if weekly:
        work = work.set_index("Date").resample("W-FRI").last().dropna().reset_index()
        work["crop_year"] = work["Date"].apply(crop_year)
    crop_years = sorted(work["crop_year"].unique())
    y_all: list[float] = []
    pred_all: list[float] = []
    prob_all: list[float] = []
    annual = []
    for idx in range(3, len(crop_years)):
        train = work[work["crop_year"].isin(crop_years[:idx])]
        test = work[work["crop_year"] == crop_years[idx]]
        if len(train) < 100 or len(test) < 20 or train[target].nunique() < 2:
            continue
        model = LogisticRegression(max_iter=500, class_weight="balanced", solver="liblinear")
        model.fit(train[lag_cols], train[target])
        prob = model.predict_proba(test[lag_cols])[:, 1]
        pred = (prob >= 0.5).astype(float)
        y = test[target].values
        annual.append({
            "crop_year": int(crop_years[idx]),
            "n": int(len(test)),
            "da": float(accuracy_score(y, pred)),
            "auc": float(roc_auc_score(y, prob)) if len(set(y)) > 1 else float("nan"),
            "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
            "base_rate": float(y.mean()),
        })
        y_all.extend(y.tolist())
        pred_all.extend(pred.tolist())
        prob_all.extend(prob.tolist())
    if not y_all:
        return {"target": target, "frequency": "weekly" if weekly else "daily", "error": "no_valid_folds"}
    y_arr = np.array(y_all)
    pred_arr = np.array(pred_all)
    prob_arr = np.array(prob_all)
    correct = (y_arr == pred_arr).astype(float)
    ci = bootstrap_ci(correct, np.mean, n_draws=500)
    confidence = np.abs(prob_arr - 0.5)
    top_n = max(1, int(len(confidence) * 0.20))
    top_idx = np.argsort(confidence)[-top_n:]
    cm = confusion_matrix(y_arr, pred_arr, labels=[0, 1])
    base_rate = float(y_arr.mean())
    majority_baseline_da = float(max(base_rate, 1.0 - base_rate))
    da = float(accuracy_score(y_arr, pred_arr))
    annual_da = [row["da"] for row in annual if "da" in row]
    annual_stability = float(np.mean([x >= 0.53 for x in annual_da])) if annual_da else float("nan")
    return {
        "target": target,
        "frequency": "weekly" if weekly else "daily",
        "n": int(len(y_arr)),
        "base_rate": base_rate,
        "majority_baseline_da": majority_baseline_da,
        "lift_vs_majority": float(da - majority_baseline_da),
        "da": da,
        "balanced_accuracy": float(balanced_accuracy_score(y_arr, pred_arr)),
        "auc": float(roc_auc_score(y_arr, prob_arr)) if len(set(y_arr)) > 1 else float("nan"),
        "brier": float(brier_score_loss(y_arr, prob_arr)),
        "precision": float(precision_score(y_arr, pred_arr, zero_division=0)),
        "recall": float(recall_score(y_arr, pred_arr, zero_division=0)),
        "mcc": float(matthews_corrcoef(y_arr, pred_arr)),
        "top20_da": float(accuracy_score(y_arr[top_idx], pred_arr[top_idx])),
        "annual_stability_share_da_ge_53": annual_stability,
        "ci95_da_lo": ci["ci_lo"],
        "ci95_da_hi": ci["ci_hi"],
        "p_value_da_gt_50": _p_value_da(int(correct.sum()), len(correct)),
        "confusion_matrix": cm.tolist(),
        "annual_stability": annual,
        "weekly_verdict": None if not weekly else ("WEEKLY_GO" if accuracy_score(y_arr, pred_arr) >= 0.53 else "WEEKLY_NO_GO"),
    }


def _finite_metric(row: dict, key: str, default: float = -1.0) -> float:
    value = row.get(key, default)
    if value is None:
        return default
    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return default
    return value_float if np.isfinite(value_float) else default


def _robust_signal_selection(results: list[dict], weekly_results: list[dict]) -> dict:
    weekly_by_label = {row.get("target_label"): row for row in weekly_results if "da" in row}
    candidates = []
    for row in results:
        if "da" not in row:
            continue
        label = row.get("target_label")
        weekly = weekly_by_label.get(label, {})
        score = (
            _finite_metric(row, "auc"),
            _finite_metric(row, "balanced_accuracy"),
            _finite_metric(row, "top20_da"),
            _finite_metric(weekly, "auc"),
            _finite_metric(weekly, "balanced_accuracy"),
            _finite_metric(row, "annual_stability_share_da_ge_53"),
            _finite_metric(row, "da"),
        )
        candidates.append({
            "target_label": label,
            "target": row.get("target"),
            "robust_rank_score": list(score),
            "daily_auc": row.get("auc"),
            "daily_balanced_accuracy": row.get("balanced_accuracy"),
            "daily_da": row.get("da"),
            "daily_top20_da": row.get("top20_da"),
            "weekly_auc": weekly.get("auc"),
            "weekly_balanced_accuracy": weekly.get("balanced_accuracy"),
            "weekly_da": weekly.get("da"),
            "annual_stability_share_da_ge_53": row.get("annual_stability_share_da_ge_53"),
            "majority_baseline_da": row.get("majority_baseline_da"),
            "lift_vs_majority": row.get("lift_vs_majority"),
            "mcc": row.get("mcc"),
        })
    candidates.sort(key=lambda item: tuple(item["robust_rank_score"]), reverse=True)
    for rank, item in enumerate(candidates, start=1):
        item["robust_rank"] = rank
    best = candidates[0] if candidates else {}
    return {
        "selection_rule": "Sort by AUC, balanced accuracy, top20 DA, weekly AUC, weekly balanced accuracy, annual stability, then raw DA.",
        "robust_best_signal": best,
        "ranked_signals": candidates,
    }


def build_direction_benchmarks_v2() -> dict:
    df = _load_dataset()
    results = []
    weekly_results = []
    loco = {}
    for label, target in _target_map().items():
        if target not in df.columns:
            continue
        daily = _evaluate(df, target, weekly=False)
        daily["target_label"] = label
        weekly = _evaluate(df, target, weekly=True)
        weekly["target_label"] = label
        results.append(daily)
        weekly_results.append(weekly)
        loco[label] = _evaluate(df, target, weekly=False, exclude_year=2022)
    q_values = _bh_q_values([r.get("p_value_da_gt_50", np.nan) for r in results])
    for row, q in zip(results, q_values, strict=False):
        row["bh_q_value"] = q
        row["bh_significant_5pct"] = bool(q < 0.05)
    valid = [r for r in results if "da" in r]
    best_by_da = max(valid, key=lambda r: r["da"], default={})
    robust_selection = _robust_signal_selection(results, weekly_results)
    robust_best = robust_selection.get("robust_best_signal", {})
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "protocol": "Walk-forward OOF, min 3 crop years train, features shift(1), IC95 bootstrap 500, BH FDR.",
        "targets": _target_map(),
        "daily_results": results,
        "weekly_results": weekly_results,
        "leave_one_2022_out": loco,
        "robust_signal_selection": robust_selection,
        "key_findings": {
            "best_target_label": robust_best.get("target_label"),
            "best_da": robust_best.get("daily_da"),
            "best_auc": robust_best.get("daily_auc"),
            "best_by_da_label": best_by_da.get("target_label"),
            "best_by_da": best_by_da.get("da"),
            "robust_best_signal_label": robust_best.get("target_label"),
            "robust_best_signal_auc": robust_best.get("daily_auc"),
            "robust_best_signal_balanced_accuracy": robust_best.get("daily_balanced_accuracy"),
            "robust_best_signal_weekly_auc": robust_best.get("weekly_auc"),
            "ema_absolute_h40_verdict": next((r.get("weekly_verdict") for r in weekly_results if r.get("target_label") == "ema_direction_absolute_h40"), None),
            "overall_verdict": "GO_SIGNAL" if _finite_metric(robust_best, "daily_auc", 0) >= 0.60 and _finite_metric(robust_best, "daily_balanced_accuracy", 0) >= 0.55 else "NO_GO",
        },
    }


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


def _write_markdown(data: dict, path: Path) -> None:
    k = data["key_findings"]
    lines = [
        "# EMA DIRECTION BENCHMARKS V2",
        "",
        "> Cibles EMA intelligentes : basis, relatif EMA/CBOT, résidu EU, volatilité, EMA H40.",
        "",
        "## Verdict",
        "",
        f"- Meilleure cible robuste : {k['robust_best_signal_label']}",
        f"- AUC daily robuste : {k['robust_best_signal_auc']:.3f}" if k.get("robust_best_signal_auc") == k.get("robust_best_signal_auc") else "- AUC daily robuste : N/A",
        f"- Balanced accuracy robuste : {k['robust_best_signal_balanced_accuracy']:.1%}" if k.get("robust_best_signal_balanced_accuracy") == k.get("robust_best_signal_balanced_accuracy") else "- Balanced accuracy robuste : N/A",
        f"- Meilleure cible par DA brute : {k['best_by_da_label']} ({k['best_by_da']:.1%})",
        f"- Verdict global : {k['overall_verdict']}",
        "",
        "La sélection robuste n'utilise plus la DA seule. Les cibles déséquilibrées comme `ema_vol_high_h20` doivent être rejetées si AUC, balanced accuracy, MCC ou lift vs classe majoritaire sont faibles.",
        "",
        "## Résultats daily",
        "",
        "| Cible | n | Base rate | Majority | DA | Lift maj. | AUC | Balanced acc. | MCC | q BH |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["daily_results"]:
        if "da" not in row:
            continue
        lines.append(
            f"| {row['target_label']} | {row['n']} | {row['base_rate']:.1%} | "
            f"{row['majority_baseline_da']:.1%} | {row['da']:.1%} | {row['lift_vs_majority']:.1%} | "
            f"{row['auc']:.3f} | {row['balanced_accuracy']:.1%} | {row['mcc']:.3f} | "
            f"{row.get('bh_q_value', float('nan')):.3f} |"
        )
    lines += [
        "",
        "## Classement robuste",
        "",
        "| Rang | Cible | AUC | Balanced acc. | Top20 DA | Weekly AUC | Stabilité annuelle |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in data["robust_signal_selection"]["ranked_signals"]:
        weekly_auc = row.get("weekly_auc")
        weekly_text = "N/A" if weekly_auc != weekly_auc else f"{weekly_auc:.3f}"
        lines.append(
            f"| {row['robust_rank']} | {row['target_label']} | {row['daily_auc']:.3f} | "
            f"{row['daily_balanced_accuracy']:.1%} | {row['daily_top20_da']:.1%} | "
            f"{weekly_text} | {row['annual_stability_share_da_ge_53']:.1%} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_direction_benchmarks_v2(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_direction_benchmarks_v2()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_direction_benchmarks_v2()
    print(f"Direction benchmarks v2 saved -> {out}")
