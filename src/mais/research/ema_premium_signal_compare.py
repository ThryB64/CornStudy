"""EMA-PREM-01 — Comparaison ML, basis z-score et signal combine."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_relative_study import oof_relative_predictions

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_premium_signal_compare.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_PREMIUM_SIGNAL_COMPARE.md"
_HORIZONS = (40, 90)


def _basis_score(zscore: pd.Series) -> pd.Series:
    # Negative basis implies EMA is cheap vs CBOT and more likely to outperform.
    return 1.0 / (1.0 + np.exp(zscore.clip(-8, 8)))


def _strategy_frame(pred: pd.DataFrame, strategy: str) -> pd.DataFrame:
    out = pred.copy()
    basis_prob = _basis_score(out["ema_cbot_basis_zscore_52w"])
    if strategy == "ml_model":
        out["score"] = out["prob"]
        out["signal"] = (out["score"] >= 0.5).astype(float)
        out["coverage_mask"] = True
    elif strategy == "basis_zscore_rule":
        out["score"] = basis_prob
        out["signal"] = (out["ema_cbot_basis_zscore_52w"] < 0).astype(float)
        out["coverage_mask"] = True
    elif strategy == "combined_equal_weight":
        out["score"] = 0.5 * out["prob"] + 0.5 * basis_prob
        out["signal"] = (out["score"] >= 0.5).astype(float)
        out["coverage_mask"] = True
    elif strategy == "ml_with_basis_extreme_filter":
        out["score"] = out["prob"]
        out["signal"] = (out["score"] >= 0.5).astype(float)
        out["coverage_mask"] = out["ema_cbot_basis_zscore_52w"].abs() >= 1.5
    elif strategy == "combined_top40_confidence":
        out["score"] = 0.5 * out["prob"] + 0.5 * basis_prob
        out["signal"] = (out["score"] >= 0.5).astype(float)
        out["confidence_combined"] = (out["score"] - 0.5).abs()
        out["coverage_mask"] = out["confidence_combined"] >= out["confidence_combined"].quantile(0.60)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    out["confidence_used"] = (out["score"] - 0.5).abs()
    return out[out["coverage_mask"]].copy()


def _metrics(frame: pd.DataFrame, strategy: str, horizon: int, total_n: int) -> dict:
    if len(frame) < 40 or frame["y_true"].nunique() < 2:
        return {
            "strategy": strategy,
            "horizon": int(horizon),
            "status": "SKIPPED",
            "n": int(len(frame)),
            "coverage": float(len(frame) / total_n) if total_n else 0.0,
        }
    top_n = max(1, int(len(frame) * 0.20))
    top = frame.nlargest(top_n, "confidence_used")
    y = frame["y_true"].astype(float)
    y_pred = frame["signal"].astype(float)
    return {
        "strategy": strategy,
        "horizon": int(horizon),
        "status": "OK",
        "n": int(len(frame)),
        "coverage": float(len(frame) / total_n),
        "base_rate": float(y.mean()),
        "da": float(accuracy_score(y, y_pred)),
        "auc": float(roc_auc_score(y, frame["score"])),
        "balanced_accuracy": float(balanced_accuracy_score(y, y_pred)),
        "top20_da": float(accuracy_score(top["y_true"], top["signal"])),
    }


def _compare_horizon(horizon: int) -> dict:
    pred = oof_relative_predictions(horizon=horizon)
    strategies = [
        "ml_model",
        "basis_zscore_rule",
        "combined_equal_weight",
        "ml_with_basis_extreme_filter",
        "combined_top40_confidence",
    ]
    rows = [_metrics(_strategy_frame(pred, strategy), strategy, horizon, len(pred)) for strategy in strategies]
    ok = [row for row in rows if row.get("status") == "OK"]
    best = max(ok, key=lambda row: (row.get("balanced_accuracy", -1), row.get("auc", -1)), default={})
    return {
        "horizon": int(horizon),
        "results": rows,
        "best_strategy": best.get("strategy"),
        "best_balanced_accuracy": best.get("balanced_accuracy"),
        "best_auc": best.get("auc"),
    }


def build_premium_signal_compare() -> dict:
    results = [_compare_horizon(horizon) for horizon in _HORIZONS]
    h40 = next(row for row in results if row["horizon"] == 40)
    h90 = next(row for row in results if row["horizon"] == 90)
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "scope": "Compare ML, basis z-score and combined rules for EMA relative outperformance.",
        "results": results,
        "key_findings": {
            "h40_best_strategy": h40.get("best_strategy"),
            "h40_best_balanced_accuracy": h40.get("best_balanced_accuracy"),
            "h40_best_auc": h40.get("best_auc"),
            "h90_best_strategy": h90.get("best_strategy"),
            "h90_best_balanced_accuracy": h90.get("best_balanced_accuracy"),
            "h90_best_auc": h90.get("best_auc"),
            "interpretation": _interpretation(h40, h90),
        },
    }


def _interpretation(h40: dict, h90: dict) -> str:
    best = {h40.get("best_strategy"), h90.get("best_strategy")}
    if any("combined" in str(item) for item in best):
        return "Le signal combine apporte le meilleur compromis ; utiliser ML + basis plutot que ML seul."
    if "basis_zscore_rule" in best:
        return "La regle basis simple reste competitive ; l'indicateur doit rester economique et explicable."
    return "Le ML seul domine dans ce protocole, mais le basis reste le driver economique central."


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
    lines = [
        "# EMA PREMIUM SIGNAL COMPARE",
        "",
        "> Comparaison du modele ML, de la regle basis z-score et de signaux combines.",
        "",
        "## Verdict",
        "",
        f"- H40 meilleure strategie : `{data['key_findings']['h40_best_strategy']}`",
        f"- H40 balanced accuracy : {_fmt(data['key_findings']['h40_best_balanced_accuracy'])}",
        f"- H90 meilleure strategie : `{data['key_findings']['h90_best_strategy']}`",
        f"- H90 balanced accuracy : {_fmt(data['key_findings']['h90_best_balanced_accuracy'])}",
        f"- Lecture : {data['key_findings']['interpretation']}",
        "",
    ]
    for result in data["results"]:
        lines += [
            f"## H{result['horizon']}",
            "",
            "| Strategie | Coverage | n | DA | AUC | Balanced acc. | Top20 DA |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for row in result["results"]:
            lines.append(
                f"| {row['strategy']} | {_fmt(row.get('coverage'))} | {row.get('n', 0)} | "
                f"{_fmt(row.get('da'))} | {_fmt(row.get('auc'))} | {_fmt(row.get('balanced_accuracy'))} | "
                f"{_fmt(row.get('top20_da'))} |"
            )
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_premium_signal_compare(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_premium_signal_compare()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_premium_signal_compare()
    print(f"Premium signal compare saved -> {out}")
