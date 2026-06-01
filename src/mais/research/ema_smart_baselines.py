"""FIX-EMA-06 — Baselines intelligentes pour les cibles EMA."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_direction_benchmarks_v2 import _load_dataset, build_direction_benchmarks_v2
from mais.research.ema_utils import bootstrap_ci, crop_year

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_smart_baselines.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_SMART_BASELINES.md"

_TARGETS = {
    "relative_ema_outperformance_h40": "y_ema_outperforms_cbot_h40",
    "ema_direction_absolute_h40": "y_up_h40_ema_raw",
}


def _base_frame() -> pd.DataFrame:
    df = _load_dataset().copy()
    df["crop_year"] = df["Date"].apply(crop_year)
    df["month"] = df["Date"].dt.month
    df["ema_momentum_20d"] = (df["ema_front_price"].pct_change(20) > 0).astype(float)
    df["cbot_momentum_20d"] = (df["cbot_eur_t"].pct_change(20) > 0).astype(float)
    df["basis_z_rule"] = (df["ema_cbot_basis_zscore_52w"] < 0).astype(float)
    return df


def _eligible_oof(frame: pd.DataFrame) -> pd.DataFrame:
    years = sorted(frame["crop_year"].dropna().unique())
    if len(years) <= 3:
        return frame.iloc[0:0]
    return frame[frame["crop_year"].isin(years[3:])].copy()


def _evaluate_baseline(frame: pd.DataFrame, target: str, pred: pd.Series, label: str) -> dict:
    work = frame[["Date", "crop_year", target]].copy()
    work["pred"] = pred
    work = _eligible_oof(work).dropna(subset=[target, "pred"])
    if len(work) < 40 or work[target].nunique() < 2:
        return {"baseline": label, "status": "SKIPPED", "reason": "insufficient_data", "n": int(len(work))}
    y = work[target].astype(float)
    y_pred = work["pred"].astype(float)
    correct = y.eq(y_pred).astype(float)
    ci = bootstrap_ci(correct.to_numpy(), np.mean, n_draws=500)
    base_rate = float(y.mean())
    majority = float(max(base_rate, 1.0 - base_rate))
    da = float(correct.mean())
    return {
        "baseline": label,
        "status": "OK",
        "n": int(len(work)),
        "base_rate": base_rate,
        "majority_baseline_da": majority,
        "da": da,
        "balanced_accuracy": float(balanced_accuracy_score(y, y_pred)),
        "lift_vs_majority": float(da - majority),
        "ci95_lo": ci["ci_lo"],
        "ci95_hi": ci["ci_hi"],
    }


def _walk_forward_majority(frame: pd.DataFrame, target: str) -> pd.Series:
    pred = pd.Series(np.nan, index=frame.index)
    years = sorted(frame["crop_year"].dropna().unique())
    for idx in range(3, len(years)):
        train = frame[frame["crop_year"].isin(years[:idx])]
        test_idx = frame[frame["crop_year"].eq(years[idx])].index
        train_target = train[target].dropna()
        if len(train_target):
            pred.loc[test_idx] = float(train_target.mean() >= 0.5)
    return pred


def _walk_forward_month_rule(frame: pd.DataFrame, target: str) -> pd.Series:
    pred = pd.Series(np.nan, index=frame.index)
    years = sorted(frame["crop_year"].dropna().unique())
    for idx in range(3, len(years)):
        train = frame[frame["crop_year"].isin(years[:idx])]
        month_rates = train.groupby("month")[target].mean()
        fallback = float(train[target].dropna().mean() >= 0.5) if train[target].notna().any() else np.nan
        test = frame[frame["crop_year"].eq(years[idx])]
        for row_idx, month in test["month"].items():
            rate = month_rates.get(month, np.nan)
            pred.loc[row_idx] = float(rate >= 0.5) if pd.notna(rate) else fallback
    return pred


def _random_baseline(frame: pd.DataFrame, seed: int = 42) -> pd.Series:
    rng = np.random.default_rng(seed)
    return pd.Series(rng.integers(0, 2, size=len(frame)).astype(float), index=frame.index)


def _model_reference(direction_data: dict, label: str) -> dict:
    for row in direction_data["daily_results"]:
        if row.get("target_label") == label and "da" in row:
            return {
                "status": "OK",
                "da": row.get("da"),
                "balanced_accuracy": row.get("balanced_accuracy"),
                "auc": row.get("auc"),
                "n": row.get("n"),
            }
    return {"status": "missing"}


def build_smart_baselines() -> dict:
    frame = _base_frame()
    direction_data = build_direction_benchmarks_v2()
    results = {}
    for label, target in _TARGETS.items():
        baselines = [
            _evaluate_baseline(frame, target, _walk_forward_majority(frame, target), "walk_forward_majority"),
            _evaluate_baseline(frame, target, frame["ema_momentum_20d"], "ema_momentum_20d"),
            _evaluate_baseline(frame, target, frame["cbot_momentum_20d"], "cbot_momentum_20d"),
            _evaluate_baseline(frame, target, frame["basis_z_rule"], "basis_z_rule"),
            _evaluate_baseline(frame, target, _walk_forward_month_rule(frame, target), "seasonal_month_rule"),
            _evaluate_baseline(frame, target, _random_baseline(frame), "random_50_50"),
        ]
        ok = [row for row in baselines if row.get("status") == "OK"]
        best_baseline = max(ok, key=lambda row: row["balanced_accuracy"], default={})
        model = _model_reference(direction_data, label)
        model_beats = (
            model.get("balanced_accuracy") is not None
            and best_baseline.get("balanced_accuracy") is not None
            and float(model["balanced_accuracy"]) > float(best_baseline["balanced_accuracy"])
        )
        results[label] = {
            "target": target,
            "model_reference": model,
            "baselines": baselines,
            "best_baseline": best_baseline,
            "model_beats_best_baseline": bool(model_beats),
        }
    robust = results["relative_ema_outperformance_h40"]
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "results": results,
        "key_findings": {
            "robust_target": "relative_ema_outperformance_h40",
            "robust_model_balanced_accuracy": robust["model_reference"].get("balanced_accuracy"),
            "robust_best_baseline": robust["best_baseline"].get("baseline"),
            "robust_best_baseline_balanced_accuracy": robust["best_baseline"].get("balanced_accuracy"),
            "robust_model_beats_best_baseline": robust["model_beats_best_baseline"],
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


def _fmt(value: object, digits: int = 3) -> str:
    if value is None:
        return "N/A"
    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return str(value)
    return "N/A" if not np.isfinite(value_float) else f"{value_float:.{digits}f}"


def _write_markdown(data: dict, path: Path) -> None:
    k = data["key_findings"]
    lines = [
        "# EMA SMART BASELINES",
        "",
        "> Comparaison du modèle EMA aux règles simples.",
        "",
        "## Verdict",
        "",
        f"- Target robuste : {k['robust_target']}",
        f"- Balanced accuracy modèle : {_fmt(k.get('robust_model_balanced_accuracy'))}",
        f"- Meilleure baseline : {k.get('robust_best_baseline')} ({_fmt(k.get('robust_best_baseline_balanced_accuracy'))})",
        f"- Modèle bat meilleure baseline : {k.get('robust_model_beats_best_baseline')}",
        "",
    ]
    for label, result in data["results"].items():
        lines += [
            f"## {label}",
            "",
            "| Baseline | n | DA | Balanced acc. | Lift majority |",
            "|---|---:|---:|---:|---:|",
        ]
        for row in result["baselines"]:
            lines.append(
                f"| {row['baseline']} | {row.get('n', 0)} | {_fmt(row.get('da'))} | "
                f"{_fmt(row.get('balanced_accuracy'))} | {_fmt(row.get('lift_vs_majority'))} |"
            )
        model = result["model_reference"]
        lines.append(
            f"| model_reference | {model.get('n', 0)} | {_fmt(model.get('da'))} | "
            f"{_fmt(model.get('balanced_accuracy'))} | N/A |"
        )
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_smart_baselines(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_smart_baselines()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_smart_baselines()
    print(f"Smart baselines saved -> {out}")
