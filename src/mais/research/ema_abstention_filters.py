"""REL-EMA-04 — Filtres d'abstention sur relative EMA/CBOT H40."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_relative_study import oof_relative_predictions
from mais.research.ema_utils import bootstrap_ci

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_abstention_filters.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_ABSTENTION_FILTERS.md"
_ROLL_RISK_MONTHS = {2, 3, 5, 6, 7, 8, 10, 11}
_CRISIS_YEARS = {2012, 2020, 2021, 2022}


def _base_predictions() -> pd.DataFrame:
    pred = oof_relative_predictions(horizon=40)
    pred["year"] = pd.to_datetime(pred["Date"]).dt.year
    pred["month"] = pd.to_datetime(pred["Date"]).dt.month
    pred["roll_risk_proxy"] = pred["month"].isin(_ROLL_RISK_MONTHS)
    pred["crisis_period"] = pred["year"].isin(_CRISIS_YEARS)
    pred["basis_extreme"] = pred["ema_cbot_basis_zscore_52w"].abs() >= 1.5
    pred["correct"] = pred["y_true"].eq(pred["y_pred"])
    return pred


def _filter_masks(pred: pd.DataFrame) -> dict[str, pd.Series]:
    top20_cutoff = pred["confidence"].quantile(0.80)
    top40_cutoff = pred["confidence"].quantile(0.60)
    return {
        "all_signals": pd.Series(True, index=pred.index),
        "top20_confidence": pred["confidence"] >= top20_cutoff,
        "top40_confidence": pred["confidence"] >= top40_cutoff,
        "no_roll_risk_proxy": ~pred["roll_risk_proxy"],
        "no_crisis_years": ~pred["crisis_period"],
        "no_roll_no_crisis": (~pred["roll_risk_proxy"]) & (~pred["crisis_period"]),
        "basis_extreme_only": pred["basis_extreme"],
        "top40_no_roll_no_crisis": (pred["confidence"] >= top40_cutoff)
        & (~pred["roll_risk_proxy"])
        & (~pred["crisis_period"]),
    }


def _evaluate_filtered(pred: pd.DataFrame, mask: pd.Series, label: str, total_n: int) -> dict:
    sub = pred[mask].copy()
    if len(sub) < 40 or sub["y_true"].nunique() < 2:
        return {
            "filter": label,
            "status": "SKIPPED",
            "reason": "insufficient_data_or_single_class",
            "n": int(len(sub)),
            "coverage": float(len(sub) / total_n) if total_n else 0.0,
        }
    y = sub["y_true"].astype(float)
    y_pred = sub["y_pred"].astype(float)
    correct = y.eq(y_pred).astype(float)
    ci = bootstrap_ci(correct.to_numpy(), np.mean, n_draws=500)
    top_n = max(1, int(len(sub) * 0.20))
    top = sub.nlargest(top_n, "confidence")
    return {
        "filter": label,
        "status": "OK",
        "n": int(len(sub)),
        "coverage": float(len(sub) / total_n),
        "base_rate": float(y.mean()),
        "da": float(accuracy_score(y, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y, y_pred)),
        "auc": float(roc_auc_score(y, sub["prob"])),
        "top20_da": float(accuracy_score(top["y_true"], top["y_pred"])),
        "ci95_da_lo": ci["ci_lo"],
        "ci95_da_hi": ci["ci_hi"],
    }


def build_abstention_filters() -> dict:
    pred = _base_predictions()
    masks = _filter_masks(pred)
    rows = [_evaluate_filtered(pred, mask, label, len(pred)) for label, mask in masks.items()]
    baseline = next(row for row in rows if row["filter"] == "all_signals")
    for row in rows:
        if row.get("status") == "OK":
            row["delta_da_vs_all"] = float(row["da"] - baseline["da"])
            row["delta_balanced_accuracy_vs_all"] = float(row["balanced_accuracy"] - baseline["balanced_accuracy"])
    candidates = [
        row
        for row in rows
        if row.get("status") == "OK" and row["filter"] != "all_signals" and row.get("coverage", 0) >= 0.15
    ]
    best = max(candidates, key=lambda row: (row["balanced_accuracy"], row["coverage"]), default={})
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "target": "relative_ema_outperformance_h40",
        "n_oof": int(len(pred)),
        "filters": rows,
        "key_findings": {
            "baseline_da": baseline.get("da"),
            "baseline_balanced_accuracy": baseline.get("balanced_accuracy"),
            "best_filter": best.get("filter"),
            "best_filter_da": best.get("da"),
            "best_filter_balanced_accuracy": best.get("balanced_accuracy"),
            "best_filter_coverage": best.get("coverage"),
            "interpretation": _interpretation(best, baseline),
        },
    }


def _interpretation(best: dict, baseline: dict) -> str:
    if not best:
        return "No abstention filter keeps enough observations while improving the signal."
    delta = float(best.get("balanced_accuracy", 0.0) - baseline.get("balanced_accuracy", 0.0))
    if delta >= 0.03:
        return "Abstention materially improves balanced accuracy, but must be checked in backtest."
    if delta > 0:
        return "Abstention improves balanced accuracy modestly; use as risk filter, not as proof of alpha."
    return "Abstention does not improve balanced accuracy over all signals."


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
        "# EMA ABSTENTION FILTERS",
        "",
        "> Filtres d'abstention sur `relative_ema_outperformance_h40`.",
        "",
        "## Verdict",
        "",
        f"- Baseline DA : {_fmt(k.get('baseline_da'))}",
        f"- Baseline balanced accuracy : {_fmt(k.get('baseline_balanced_accuracy'))}",
        f"- Meilleur filtre : {k.get('best_filter')}",
        f"- Balanced accuracy meilleur filtre : {_fmt(k.get('best_filter_balanced_accuracy'))}",
        f"- Coverage meilleur filtre : {_fmt(k.get('best_filter_coverage'))}",
        f"- Lecture : {k.get('interpretation')}",
        "",
        "## Filtres",
        "",
        "| Filtre | n | Coverage | DA | AUC | Balanced acc. | Top20 DA | Δ BAcc |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["filters"]:
        lines.append(
            f"| {row['filter']} | {row.get('n', 0)} | {_fmt(row.get('coverage'))} | "
            f"{_fmt(row.get('da'))} | {_fmt(row.get('auc'))} | {_fmt(row.get('balanced_accuracy'))} | "
            f"{_fmt(row.get('top20_da'))} | {_fmt(row.get('delta_balanced_accuracy_vs_all'))} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_abstention_filters(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_abstention_filters()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_abstention_filters()
    print(f"Abstention filters saved -> {out}")
