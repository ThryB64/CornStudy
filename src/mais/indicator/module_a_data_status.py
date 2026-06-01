"""Data-status audit for Module A market-context signals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.features.ema_targets import EMA_TARGETS_PARQUET
from mais.indicator.module_a_calibration import MODULE_A_CALIBRATION_JSON
from mais.indicator.module_a_context import SIGNAL_DEFINITIONS, compute_context_timeseries
from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, PROJECT_ROOT

MODULE_A_DATA_STATUS_JSON = ARTEFACTS_DIR / "ema_study" / "module_a_data_status.json"
MODULE_A_DATA_STATUS_MD = PROJECT_ROOT / "docs" / "MODULE_A_DATA_STATUS.md"

DECLARED_SIGNAL_STATUS: dict[str, str] = {
    "bilan_mondial": "real",
    "bilan_stocks_eu": "proxy",
    "crop_condition_eu": "proxy",
    "brazil_supply_pressure": "proxy",
    "ukraine_corridor": "manual",
    "us_crop_condition": "real",
    "china_demand": "proxy",
    "wasde_surprise": "real",
    "export_pace_eu": "proxy",
    "cot_positioning": "real",
    "futures_structure": "proxy",
    "eur_usd_competitive": "proxy",
}

STATUS_NOTES: dict[str, str] = {
    "bilan_mondial": "WASDE stocks/use data.",
    "bilan_stocks_eu": "EMA-CBOT basis used as proxy for European tightness, not true EU stocks.",
    "crop_condition_eu": "US crop condition and drought proxies, not EC MARS or EU crop condition.",
    "brazil_supply_pressure": "Derived from cross-market/WASDE proxies, not a full Brazil local dataset.",
    "ukraine_corridor": "Manual placeholder; must be documented at report time.",
    "us_crop_condition": "USDA crop condition/drought data.",
    "china_demand": "US export/WASDE proxy for China demand when available.",
    "wasde_surprise": "WASDE surprise features.",
    "export_pace_eu": "Fallback export pace proxy; not true EU export pace.",
    "cot_positioning": "CFTC COT positioning data.",
    "futures_structure": "Partial EMA front/basis/liquidity fragments, not a complete futures curve.",
    "eur_usd_competitive": "Derived competitiveness proxy from CBOT EUR/t and EMA relative strength.",
}


def classify_signal_data_status(
    signal_name: str,
    definition: dict[str, Any],
    features: pd.DataFrame,
) -> dict[str, Any]:
    """Classify one Module A signal as real, proxy, missing or manual."""
    columns = list(definition.get("columns", []))
    available_cols = [col for col in columns if col in features.columns]
    coverage_by_col = {
        col: _json_float(pd.to_numeric(features[col], errors="coerce").notna().mean())
        for col in available_cols
    }
    candidate_coverage = 0.0
    if available_cols:
        candidate_coverage = float(
            features[available_cols].apply(pd.to_numeric, errors="coerce").notna().any(axis=1).mean()
        )

    declared = DECLARED_SIGNAL_STATUS.get(signal_name, "proxy")
    if definition.get("structure"):
        active_column = "/".join(available_cols) if available_cols else None
        active_coverage = candidate_coverage
    else:
        active_column = available_cols[0] if available_cols else None
        active_coverage = float(coverage_by_col.get(active_column, 0.0) or 0.0) if active_column else 0.0
    if declared == "manual":
        data_status = "manual"
    elif active_coverage == 0.0:
        data_status = "missing"
    else:
        data_status = declared

    return {
        "signal": signal_name,
        "block": definition["block"],
        "data_status": data_status,
        "declared_status": declared,
        "coverage": _json_float(active_coverage),
        "candidate_coverage": _json_float(candidate_coverage),
        "active_column": active_column,
        "available_columns": available_cols,
        "missing_columns": [col for col in columns if col not in features.columns],
        "coverage_by_column": coverage_by_col,
        "note": STATUS_NOTES.get(signal_name, ""),
    }


def evaluate_signal_da(
    context: pd.DataFrame,
    targets: pd.DataFrame,
    signal_name: str,
    *,
    target_col: str = "y_up_h20_ema",
) -> dict[str, Any]:
    """Evaluate the weekly standalone DA of one Module A signal."""
    signal_col = f"signal_{signal_name}"
    if signal_col not in context.columns or target_col not in targets.columns:
        return {"da_weekly": None, "n_weekly": 0, "positive_signal_rate": None}

    left = context[["Date", signal_col]].copy()
    right = targets[["Date", target_col]].copy()
    left["Date"] = pd.to_datetime(left["Date"]).dt.normalize()
    right["Date"] = pd.to_datetime(right["Date"]).dt.normalize()
    merged = left.merge(right, on="Date", how="inner")
    merged[signal_col] = pd.to_numeric(merged[signal_col], errors="coerce")
    merged[target_col] = pd.to_numeric(merged[target_col], errors="coerce")
    merged = merged.dropna(subset=[signal_col, target_col])
    if merged.empty:
        return {"da_weekly": None, "n_weekly": 0, "positive_signal_rate": None}

    weekly = _one_point_per_week(merged)
    pred = weekly[signal_col].gt(0).astype(int)
    truth = weekly[target_col].astype(int)
    return {
        "da_weekly": _json_float(pred.eq(truth).mean()),
        "n_weekly": int(len(weekly)),
        "positive_signal_rate": _json_float(pred.mean()),
    }


def run_module_a_data_status(
    *,
    features_path: Path = FEATURES_PARQUET,
    targets_path: Path = EMA_TARGETS_PARQUET,
    calibration_path: Path = MODULE_A_CALIBRATION_JSON,
    output_json_path: Path = MODULE_A_DATA_STATUS_JSON,
    output_markdown_path: Path = MODULE_A_DATA_STATUS_MD,
    max_date: str | pd.Timestamp = "2022-12-31",
    target_col: str = "y_up_h20_ema",
) -> dict[str, Any]:
    """Build the Module A signal data-status report and write JSON/Markdown outputs."""
    features = pd.read_parquet(features_path)
    targets = pd.read_parquet(targets_path)
    features = _normalise_dates(features)
    targets = _normalise_dates(targets)
    features = features[features["Date"] <= pd.Timestamp(max_date)].copy()
    coverage_features = _coverage_frame(features, targets, target_col=target_col)

    context = compute_context_timeseries(features)
    weights = _load_final_weights(calibration_path)
    signal_reports: list[dict[str, Any]] = []
    for signal_name, definition in SIGNAL_DEFINITIONS.items():
        status = classify_signal_data_status(signal_name, definition, coverage_features)
        da = evaluate_signal_da(context, targets, signal_name, target_col=target_col)
        status.update(
            {
                "weight": _json_float(weights.get(signal_name)),
                "standalone_da_weekly": da["da_weekly"],
                "n_weekly": da["n_weekly"],
                "positive_signal_rate": da["positive_signal_rate"],
            }
        )
        status["decision"] = _decision(status)
        signal_reports.append(status)

    payload = {
        "target_col": target_col,
        "max_date": str(pd.Timestamp(max_date).date()),
        "n_features": int(len(features)),
        "n_coverage_features": int(len(coverage_features)),
        "n_targets": int(len(targets)),
        "n_signals": int(len(signal_reports)),
        "status_counts": _count_by(signal_reports, "data_status"),
        "decision_counts": _count_by(signal_reports, "decision"),
        "mean_coverage": _json_float(np.mean([row["coverage"] for row in signal_reports])),
        "mean_weighted_coverage": _weighted_coverage(signal_reports),
        "signals": signal_reports,
        "guardrails": [
            "Do not treat proxy or manual Module A signals as validated economic data.",
            "EMA historical prices remain exploratory Barchart-derived data, not official Euronext settlement.",
            "Futures-structure signals are partial EMA front/basis/liquidity fragments, not a complete curve.",
        ],
    }
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    output_markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    """Render a compact French Markdown report for the Module A data status."""
    rows = payload["signals"]
    lines = [
        "# Module A — Data Status",
        "",
        "Ce rapport classe chaque signal du Module A en `real`, `proxy`, `missing` ou `manual`.",
        "Il sert à éviter qu'un proxy ou un placeholder soit lu comme une donnée économique validée.",
        "",
        "## Synthèse",
        "",
        f"- Cible évaluée : `{payload['target_col']}`.",
        f"- Période features : jusqu'au {payload['max_date']} ({payload['n_features']} lignes).",
        f"- Fenêtre de couverture effective : {payload['n_coverage_features']} lignes avec cible non nulle.",
        f"- Signaux audités : {payload['n_signals']}.",
        f"- Couverture moyenne : {_fmt_pct(payload['mean_coverage'])}.",
        f"- Couverture moyenne pondérée par les poids calibrés : {_fmt_pct(payload['mean_weighted_coverage'])}.",
        f"- Statuts : {_fmt_counts(payload['status_counts'])}.",
        f"- Décisions : {_fmt_counts(payload['decision_counts'])}.",
        "",
        "## Table des signaux",
        "",
        "| Signal | Bloc | Statut | Source active | Couverture | DA seul hebdo | Poids | Décision | Note |",
        "|---|---|---:|---|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {signal} | {block} | {status} | {active} | {coverage} | {da} | {weight} | {decision} | {note} |".format(
                signal=row["signal"],
                block=row["block"],
                status=row["data_status"],
                active=row["active_column"] or "NA",
                coverage=_fmt_pct(row["coverage"]),
                da=_fmt_pct(row["standalone_da_weekly"]),
                weight=_fmt_num(row["weight"]),
                decision=row["decision"],
                note=row["note"],
            )
        )
    lines.extend(
        [
            "",
            "## Garde-fous",
            "",
            "- Les signaux `proxy` restent utilisables pour le contexte, mais doivent être libellés comme proxies.",
            "- Les signaux `missing` doivent être remplacés par une vraie source ou exclus des conclusions fortes.",
            "- Les signaux `manual` doivent être documentés explicitement dans chaque rapport produit.",
            "- Les signaux de structure futures EMA restent des fragments front/basis/liquidité, pas une courbe complète.",
        ]
    )
    return "\n".join(lines) + "\n"


def _normalise_dates(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["Date"] = pd.to_datetime(work["Date"]).dt.normalize()
    return work


def _coverage_frame(features: pd.DataFrame, targets: pd.DataFrame, *, target_col: str) -> pd.DataFrame:
    if target_col not in targets.columns:
        return features
    target_dates = targets.loc[targets[target_col].notna(), "Date"]
    if target_dates.empty:
        return features
    subset = features[features["Date"].isin(set(pd.to_datetime(target_dates).dt.normalize()))].copy()
    return subset if not subset.empty else features


def _decision(row: dict[str, Any]) -> str:
    status = row["data_status"]
    coverage = float(row["coverage"] or 0.0)
    weight = row.get("weight")
    if status == "missing":
        return "REMPLACER"
    if status == "manual":
        return "DOCUMENTER_MANUEL"
    if status == "proxy" and coverage < 0.40:
        return "REMPLACER_PRIORITE"
    if status == "proxy":
        return "GARDER_COMME_PROXY"
    if coverage < 0.40:
        return "SURVEILLER_COUVERTURE"
    if weight is not None and float(weight) >= 0.08:
        return "GARDER_PRIORITAIRE"
    return "GARDER"


def _load_final_weights(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    weights = data.get("final_weights", {})
    return {str(key): float(value) for key, value in weights.items() if value is not None}


def _one_point_per_week(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["week_start"] = work["Date"] - pd.to_timedelta(work["Date"].dt.weekday, unit="D")
    work["_dow_distance"] = work["Date"].dt.weekday.abs()
    return (
        work.sort_values(["week_start", "_dow_distance", "Date"])
        .groupby("week_start", as_index=False)
        .first()
        .drop(columns=["week_start", "_dow_distance"])
    )


def _count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row[key])
        counts[value] = counts.get(value, 0) + 1
    return counts


def _weighted_coverage(rows: list[dict[str, Any]]) -> float | None:
    weighted = [(row["coverage"], row["weight"]) for row in rows if row.get("weight") is not None]
    if not weighted:
        return None
    weights = np.array([float(weight) for _, weight in weighted], dtype=float)
    coverages = np.array([float(coverage or 0.0) for coverage, _ in weighted], dtype=float)
    if weights.sum() == 0:
        return None
    return _json_float(np.average(coverages, weights=weights))


def _fmt_pct(value: Any) -> str:
    if value is None:
        return "NA"
    return f"{float(value):.1%}"


def _fmt_num(value: Any) -> str:
    if value is None:
        return "NA"
    return f"{float(value):.3f}"


def _fmt_counts(counts: dict[str, int]) -> str:
    return ", ".join(f"`{key}`={value}" for key, value in sorted(counts.items()))


def _json_float(value: Any) -> float | None:
    if value is None:
        return None
    out = float(value)
    return out if np.isfinite(out) else None


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (np.integer, np.floating)):
        return _json_float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


if __name__ == "__main__":
    result = run_module_a_data_status()
    print(json.dumps(_json_ready(result), indent=2, ensure_ascii=False))
