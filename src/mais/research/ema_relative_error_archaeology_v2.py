"""EMA-ERR-02 — Archéologie des erreurs relatives H40/H90."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_relative_study import oof_relative_predictions

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_relative_error_archaeology_v2.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_RELATIVE_ERROR_ARCHAEOLOGY_V2.md"
_HORIZONS = (40, 90)
_ROLL_RISK_MONTHS = {2, 3, 5, 6, 7, 8, 10, 11}
_CRISIS_YEARS = {2020, 2021, 2022}


def _tag_row(row: pd.Series, rel_threshold: float, cbot_threshold: float) -> list[str]:
    tags = []
    if int(row["month"]) in _ROLL_RISK_MONTHS:
        tags.append("ROLL_ARTIFACT")
    if int(pd.Timestamp(row["Date"]).year) in _CRISIS_YEARS:
        tags.append("CRISIS_PERIOD")
    if abs(float(row.get("ema_cbot_basis_zscore_52w", 0.0))) >= 1.5:
        tags.append("BASIS_EXTREME")
    if abs(float(row.get("cbot_eur_return", 0.0))) >= cbot_threshold:
        tags.append("CBOT_SHOCK")
    if abs(float(row.get("relative_return", 0.0))) >= rel_threshold:
        tags.append("EU_PREMIUM_SHOCK")
    return tags or ["UNKNOWN"]


def _compact_records(frame: pd.DataFrame) -> list[dict]:
    cols = [
        "Date",
        "crop_year",
        "month",
        "y_true",
        "y_pred",
        "prob",
        "confidence",
        "relative_return",
        "cbot_eur_return",
        "ema_cbot_basis",
        "ema_cbot_basis_zscore_52w",
        "error_score",
        "tags",
    ]
    out = frame[cols].copy()
    out["Date"] = out["Date"].astype(str)
    return out.to_dict(orient="records")


def _summarise_tags(records: list[dict]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for record in records:
        counter.update(record.get("tags", []))
    return dict(counter.most_common())


def _horizon_catalogue(horizon: int) -> dict:
    pred = oof_relative_predictions(horizon=horizon)
    pred = pred.rename(
        columns={
            f"relative_return_h{horizon}": "relative_return",
            f"cbot_eur_return_h{horizon}": "cbot_eur_return",
        }
    )
    pred["correct"] = pred["y_true"].eq(pred["y_pred"])
    pred["error_score"] = np.where(
        pred["correct"],
        0.0,
        np.abs(pred["prob"] - pred["y_true"].astype(float)),
    )
    rel_threshold = float(pred["relative_return"].abs().quantile(0.90))
    cbot_threshold = float(pred["cbot_eur_return"].abs().quantile(0.90))
    pred["tags"] = [
        _tag_row(row, rel_threshold, cbot_threshold)
        for _, row in pred.iterrows()
    ]
    top_correct = pred[pred["correct"]].nlargest(100, "confidence")
    worst_errors = pred[~pred["correct"]].nlargest(100, "error_score")
    top20 = pred.nlargest(max(1, int(len(pred) * 0.20)), "confidence")
    failed_top20 = top20[~top20["correct"]].nlargest(50, "error_score")
    top_correct_records = _compact_records(top_correct)
    worst_error_records = _compact_records(worst_errors)
    failed_top20_records = _compact_records(failed_top20)
    return {
        "horizon": int(horizon),
        "n_oof": int(len(pred)),
        "n_errors": int((~pred["correct"]).sum()),
        "n_failed_top20": int(len(failed_top20)),
        "top_correct_tag_summary": _summarise_tags(top_correct_records),
        "worst_error_tag_summary": _summarise_tags(worst_error_records),
        "failed_top20_tag_summary": _summarise_tags(failed_top20_records),
        "top_correct": top_correct_records,
        "worst_errors": worst_error_records,
        "failed_top20": failed_top20_records,
    }


def build_relative_error_archaeology_v2() -> dict:
    catalogues = [_horizon_catalogue(horizon) for horizon in _HORIZONS]
    h40 = next(row for row in catalogues if row["horizon"] == 40)
    h90 = next(row for row in catalogues if row["horizon"] == 90)
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "scope": "Error archaeology for relative EMA/CBOT H40/H90.",
        "catalogues": catalogues,
        "key_findings": {
            "h40_main_error_tag": _first_tag(h40["worst_error_tag_summary"]),
            "h90_main_error_tag": _first_tag(h90["worst_error_tag_summary"]),
            "h40_failed_top20_main_tag": _first_tag(h40["failed_top20_tag_summary"]),
            "h90_failed_top20_main_tag": _first_tag(h90["failed_top20_tag_summary"]),
            "interpretation": "Use dominant tags to refine abstention filters and season/roll/crisis gates.",
        },
    }


def _first_tag(summary: dict[str, int]) -> str | None:
    return next(iter(summary), None)


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
        "# EMA RELATIVE ERROR ARCHAEOLOGY V2",
        "",
        "> Analyse des erreurs H40/H90 pour les signaux relatifs EMA/CBOT.",
        "",
        "## Verdict",
        "",
        f"- H40 tag principal pires erreurs : `{data['key_findings']['h40_main_error_tag']}`",
        f"- H90 tag principal pires erreurs : `{data['key_findings']['h90_main_error_tag']}`",
        f"- H40 failed top20 principal : `{data['key_findings']['h40_failed_top20_main_tag']}`",
        f"- H90 failed top20 principal : `{data['key_findings']['h90_failed_top20_main_tag']}`",
        f"- Lecture : {data['key_findings']['interpretation']}",
        "",
    ]
    for cat in data["catalogues"]:
        lines += [
            f"## H{cat['horizon']}",
            "",
            f"- OOF : {cat['n_oof']}",
            f"- Erreurs : {cat['n_errors']}",
            f"- Failed top20 : {cat['n_failed_top20']}",
            "",
            "### Tags pires erreurs",
            "",
        ]
        for tag, count in cat["worst_error_tag_summary"].items():
            lines.append(f"- `{tag}` : {count}")
        lines += ["", "### Tags failed top20", ""]
        for tag, count in cat["failed_top20_tag_summary"].items():
            lines.append(f"- `{tag}` : {count}")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_relative_error_archaeology_v2(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_relative_error_archaeology_v2()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_relative_error_archaeology_v2()
    print(f"Relative error archaeology V2 saved -> {out}")
