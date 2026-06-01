"""REL-EMA-03 — Analyse des erreurs relative EMA/CBOT H40."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_relative_study import build_relative_frame, oof_relative_predictions

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_relative_error_analysis.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_RELATIVE_ERROR_ANALYSIS.md"
_HORIZON = 40
_ROLL_RISK_MONTHS = {2, 3, 5, 6, 7, 8, 10, 11}
_CRISIS_YEARS = {2012, 2020, 2021, 2022}


def _classify(row: pd.Series, large_move_threshold: float) -> list[str]:
    tags = []
    if abs(float(row.get("ema_cbot_basis_zscore_52w", 0.0))) >= 1.5:
        tags.append("basis_extreme")
    if int(pd.Timestamp(row["Date"]).year) in _CRISIS_YEARS:
        tags.append("crisis_period")
    if int(pd.Timestamp(row["Date"]).month) in _ROLL_RISK_MONTHS:
        tags.append("roll_risk_proxy")
    if abs(float(row.get(f"relative_return_h{_HORIZON}", 0.0))) >= large_move_threshold:
        tags.append("large_relative_move")
    return tags or ["unknown"]


def _record_rows(frame: pd.DataFrame, *, limit: int, large_move_threshold: float) -> list[dict]:
    out = frame.head(limit).copy()
    records = []
    for _, row in out.iterrows():
        records.append({
            "date": str(pd.Timestamp(row["Date"]).date()),
            "y_true": float(row["y_true"]),
            "y_pred": float(row["y_pred"]),
            "prob": float(row["prob"]),
            "confidence": float(row["confidence"]),
            "relative_return_h40": float(row[f"relative_return_h{_HORIZON}"]),
            "ema_return_h40": float(row[f"ema_return_h{_HORIZON}"]),
            "cbot_eur_return_h40": float(row[f"cbot_eur_return_h{_HORIZON}"]),
            "basis": float(row["ema_cbot_basis"]),
            "basis_zscore": float(row["ema_cbot_basis_zscore_52w"]),
            "tags": _classify(row, large_move_threshold),
        })
    return records


def _tag_counts(records: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        for tag in record["tags"]:
            counts[tag] = counts.get(tag, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))


def build_relative_error_analysis() -> dict:
    frame = build_relative_frame()
    pred = oof_relative_predictions(frame, horizon=_HORIZON)
    pred["correct"] = pred["y_true"].eq(pred["y_pred"])
    threshold = float(pred[f"relative_return_h{_HORIZON}"].abs().quantile(0.90))
    correct = pred[pred["correct"]].sort_values("confidence", ascending=False)
    errors = pred[~pred["correct"]].sort_values("confidence", ascending=False)
    top20_cutoff = pred["confidence"].quantile(0.80)
    failed_top20 = errors[errors["confidence"] >= top20_cutoff].sort_values("confidence", ascending=False)
    top_correct_records = _record_rows(correct, limit=100, large_move_threshold=threshold)
    worst_error_records = _record_rows(errors, limit=100, large_move_threshold=threshold)
    failed_top20_records = _record_rows(failed_top20, limit=50, large_move_threshold=threshold)
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "target": "relative_ema_outperformance_h40",
        "horizon": _HORIZON,
        "n_oof": int(len(pred)),
        "n_correct": int(pred["correct"].sum()),
        "n_errors": int((~pred["correct"]).sum()),
        "large_relative_move_threshold_abs": threshold,
        "top_correct": top_correct_records,
        "worst_errors": worst_error_records,
        "failed_top20": failed_top20_records,
        "summaries": {
            "top_correct_tags": _tag_counts(top_correct_records),
            "worst_error_tags": _tag_counts(worst_error_records),
            "failed_top20_tags": _tag_counts(failed_top20_records),
            "failed_top20_count": int(len(failed_top20_records)),
        },
        "key_findings": {
            "main_error_tag": next(iter(_tag_counts(worst_error_records)), None),
            "failed_top20_main_tag": next(iter(_tag_counts(failed_top20_records)), None),
            "interpretation": "Use dominant error tags to design abstention filters before any relative backtest.",
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
    lines = [
        "# EMA RELATIVE ERROR ANALYSIS",
        "",
        "> Analyse des erreurs du signal `relative_ema_outperformance_h40`.",
        "",
        "## Verdict",
        "",
        f"- OOF : {data['n_oof']}",
        f"- Corrects : {data['n_correct']}",
        f"- Erreurs : {data['n_errors']}",
        f"- Tag principal erreurs : {data['key_findings']['main_error_tag']}",
        f"- Tag principal failed top20 : {data['key_findings']['failed_top20_main_tag']}",
        "",
        "## Tags erreurs",
        "",
        "| Tag | Worst errors | Failed top20 | Top correct |",
        "|---|---:|---:|---:|",
    ]
    tags = sorted(
        set(data["summaries"]["worst_error_tags"])
        | set(data["summaries"]["failed_top20_tags"])
        | set(data["summaries"]["top_correct_tags"])
    )
    for tag in tags:
        lines.append(
            f"| {tag} | {data['summaries']['worst_error_tags'].get(tag, 0)} | "
            f"{data['summaries']['failed_top20_tags'].get(tag, 0)} | "
            f"{data['summaries']['top_correct_tags'].get(tag, 0)} |"
        )
    lines += [
        "",
        "## Lecture",
        "",
        "Ces tags sont heuristiques. Ils servent à construire les filtres d'abstention, pas à attribuer causalement chaque erreur.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_relative_error_analysis(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_relative_error_analysis()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_relative_error_analysis()
    print(f"Relative error analysis saved -> {out}")
