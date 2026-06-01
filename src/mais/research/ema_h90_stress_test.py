"""EMA-H90-01 — Stress test strict du signal relatif H90."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_relative_backtest_v2 import build_relative_backtest_v2
from mais.research.ema_relative_study import build_relative_frame, oof_relative_predictions

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_h90_stress_test.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_H90_STRESS_TEST.md"
_HORIZON = 90
_CRISIS_YEARS = {2020, 2021, 2022}
_ROLL_RISK_MONTHS = {2, 3, 5, 6, 7, 8, 10, 11}


def _prediction_frame() -> pd.DataFrame:
    base = build_relative_frame((_HORIZON,)).sort_values("Date").reset_index(drop=True)
    base["entry_pos"] = np.arange(len(base))
    pred = oof_relative_predictions(base, horizon=_HORIZON)
    pred = pred.merge(base[["Date", "entry_pos"]], on="Date", how="left")
    pred["Date"] = pd.to_datetime(pred["Date"])
    pred["year"] = pred["Date"].dt.year
    pred["roll_risk_proxy"] = pred["month"].isin(_ROLL_RISK_MONTHS)
    return pred.dropna(subset=["entry_pos"]).sort_values("Date").reset_index(drop=True)


def _non_overlap(frame: pd.DataFrame, horizon: int = _HORIZON) -> pd.DataFrame:
    selected = []
    last_exit = -horizon - 1
    for _, row in frame.sort_values("Date").iterrows():
        entry = int(row["entry_pos"])
        if entry <= last_exit:
            continue
        selected.append(row)
        last_exit = entry + horizon
    return pd.DataFrame(selected)


def _metrics(frame: pd.DataFrame, label: str) -> dict:
    if len(frame) < 20 or frame["y_true"].nunique() < 2:
        return {"scenario": label, "status": "SKIPPED", "n": int(len(frame))}
    top_n = max(1, int(len(frame) * 0.20))
    top = frame.nlargest(top_n, "confidence")
    y = frame["y_true"].astype(float)
    y_pred = frame["y_pred"].astype(float)
    annual = (
        frame.assign(correct=y.eq(y_pred).astype(float))
        .groupby("year")
        .agg(n=("correct", "size"), da=("correct", "mean"))
        .reset_index()
    )
    return {
        "scenario": label,
        "status": "OK",
        "n": int(len(frame)),
        "base_rate": float(y.mean()),
        "da": float(accuracy_score(y, y_pred)),
        "auc": float(roc_auc_score(y, frame["prob"])),
        "balanced_accuracy": float(balanced_accuracy_score(y, y_pred)),
        "top20_da": float(accuracy_score(top["y_true"], top["y_pred"])),
        "annual_stability_da_ge_53": float((annual["da"] >= 0.53).mean()),
    }


def _scenario_results(pred: pd.DataFrame) -> list[dict]:
    scenarios = {
        "all_oof": pred,
        "strict_non_overlap": _non_overlap(pred),
        "no_roll_proxy": pred[~pred["roll_risk_proxy"]],
        "no_crisis_2020_2022": pred[~pred["year"].isin(_CRISIS_YEARS)],
        "strict_non_overlap_no_roll_proxy": _non_overlap(pred[~pred["roll_risk_proxy"]]),
    }
    for year in sorted(_CRISIS_YEARS):
        scenarios[f"leave_out_{year}"] = pred[pred["year"] != year]
    return [_metrics(frame.copy(), label) for label, frame in scenarios.items()]


def _cost_stress() -> list[dict]:
    bt = build_relative_backtest_v2()
    return [
        row
        for row in bt.get("results", [])
        if row.get("strategy") == "h90_combined_top40_weekly" and row.get("status") == "OK"
    ]


def _verdict(rows: list[dict], costs: list[dict]) -> str:
    strict = next((row for row in rows if row["scenario"] == "strict_non_overlap" and row["status"] == "OK"), {})
    no_crisis = next((row for row in rows if row["scenario"] == "no_crisis_2020_2022" and row["status"] == "OK"), {})
    high_cost = next((row for row in costs if row.get("cost_per_leg_eur_t") == 5.0), {})
    if not strict:
        return "H90_REJECTED_OVERLAP"
    if (
        strict.get("balanced_accuracy", 0) >= 0.60
        and no_crisis.get("balanced_accuracy", 0) >= 0.60
        and high_cost.get("pnl_mean_eur_t", 0) > 0
    ):
        return "H90_MAIN_GO_RESEARCH_ONLY"
    if strict.get("balanced_accuracy", 0) >= 0.55:
        return "H90_RESEARCH_ONLY"
    return "H90_REJECTED_OVERLAP"


def build_h90_stress_test() -> dict:
    pred = _prediction_frame()
    scenarios = _scenario_results(pred)
    costs = _cost_stress()
    verdict = _verdict(scenarios, costs)
    strict = next((row for row in scenarios if row["scenario"] == "strict_non_overlap"), {})
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "target": "relative_ema_outperformance_h90",
        "status": verdict,
        "production_verdict": "NO_PRODUCTION_BACKTEST",
        "scenario_results": scenarios,
        "h90_cost_stress": costs,
        "key_findings": {
            "strict_non_overlap_da": strict.get("da"),
            "strict_non_overlap_auc": strict.get("auc"),
            "strict_non_overlap_balanced_accuracy": strict.get("balanced_accuracy"),
            "strict_non_overlap_n": strict.get("n"),
            "cost_5_positive": next((row.get("pnl_mean_eur_t") > 0 for row in costs if row.get("cost_per_leg_eur_t") == 5.0), None),
            "interpretation": _interpretation(verdict),
        },
    }


def _interpretation(verdict: str) -> str:
    if verdict == "H90_MAIN_GO_RESEARCH_ONLY":
        return "H90 survives strict non-overlap, crisis exclusion and simplified high costs, but remains research-only."
    if verdict == "H90_RESEARCH_ONLY":
        return "H90 remains promising but not strong enough for main status without more execution/data validation."
    return "H90 loses too much robustness under strict stress tests."


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
        "# EMA H90 STRESS TEST",
        "",
        "> Stress test strict de `relative_ema_outperformance_h90`.",
        "",
        "## Verdict",
        "",
        f"- Statut : `{data['status']}`",
        f"- Production : `{data['production_verdict']}`",
        f"- Strict non-overlap n : {k.get('strict_non_overlap_n')}",
        f"- Strict non-overlap DA : {_fmt(k.get('strict_non_overlap_da'))}",
        f"- Strict non-overlap AUC : {_fmt(k.get('strict_non_overlap_auc'))}",
        f"- Strict non-overlap balanced accuracy : {_fmt(k.get('strict_non_overlap_balanced_accuracy'))}",
        f"- Cout 5 EUR/t/leg positif : {k.get('cost_5_positive')}",
        f"- Lecture : {k.get('interpretation')}",
        "",
        "## Scenarios",
        "",
        "| Scenario | n | DA | AUC | Balanced acc. | Top20 DA | Stability |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["scenario_results"]:
        lines.append(
            f"| {row['scenario']} | {row.get('n', 0)} | {_fmt(row.get('da'))} | {_fmt(row.get('auc'))} | "
            f"{_fmt(row.get('balanced_accuracy'))} | {_fmt(row.get('top20_da'))} | "
            f"{_fmt(row.get('annual_stability_da_ge_53'))} |"
        )
    lines += [
        "",
        "## Cout Stress H90 Combined Top40",
        "",
        "| Cout/leg | n | Hit rate | PnL moyen | PnL total | PF | Pos years |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["h90_cost_stress"]:
        lines.append(
            f"| {_fmt(row.get('cost_per_leg_eur_t'), 1)} | {row.get('n_trades')} | {_fmt(row.get('hit_rate'))} | "
            f"{_fmt(row.get('pnl_mean_eur_t'), 2)} | {_fmt(row.get('pnl_total_eur_t'), 2)} | "
            f"{_fmt(row.get('profit_factor'))} | {_fmt(row.get('positive_year_share'))} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_h90_stress_test(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_h90_stress_test()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_h90_stress_test()
    print(f"H90 stress test saved -> {out}")
