"""Statistical audit for the Euronext EMA research dataset."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.features.ema_targets import EMA_TARGETS_PARQUET
from mais.paths import (
    ARTEFACTS_DIR,
    EMA_CONTRACT_DAILY,
    EMA_CURVE_DAILY,
    EMA_CURVE_FEATURES,
    EMA_FRONT_ADJUSTED,
    EMA_FRONT_RAW,
    EMA_HARVEST_NOV,
    EMA_LIQUID_RAW,
    PROJECT_ROOT,
)

EMA_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
EMA_DATA_AUDIT_JSON = EMA_STUDY_DIR / "ema_data_audit.json"
EMA_DATA_AUDIT_MD = PROJECT_ROOT / "docs" / "EMA_DATA_AUDIT.md"
SOURCE_QUALITY_NOTE = "EMA historical prices are exploratory Barchart-derived data, not official Euronext settlement."
RECOMMENDED_CURVE_LABEL = "EMA front/basis/liquidity features, with partial curve fragments"
SPARSE_CURVE_FEATURES = (
    "ema_spread_f0_f1",
    "ema_spread_f1_f2",
    "ema_spread_f0_f2",
    "ema_spread_nov_mar",
    "ema_curve_slope_3",
    "ema_curve_slope_6",
    "ema_carry_front_second",
    "ema_roll_yield_ann",
)


def run_ema_data_audit(
    *,
    contract_daily_path: Path = EMA_CONTRACT_DAILY,
    curve_daily_path: Path = EMA_CURVE_DAILY,
    front_raw_path: Path = EMA_FRONT_RAW,
    front_adjusted_path: Path = EMA_FRONT_ADJUSTED,
    liquid_raw_path: Path = EMA_LIQUID_RAW,
    harvest_nov_path: Path = EMA_HARVEST_NOV,
    curve_features_path: Path = EMA_CURVE_FEATURES,
    ema_targets_path: Path = EMA_TARGETS_PARQUET,
    output_json_path: Path = EMA_DATA_AUDIT_JSON,
    output_markdown_path: Path = EMA_DATA_AUDIT_MD,
) -> dict[str, Any]:
    """Run the EMA data audit and write JSON + Markdown outputs."""
    contracts = _read_parquet(contract_daily_path)
    curve_daily = _read_parquet(curve_daily_path)
    front_raw = _read_parquet(front_raw_path)
    front_adjusted = _read_parquet(front_adjusted_path)
    liquid_raw = _read_parquet(liquid_raw_path)
    harvest_nov = _read_parquet(harvest_nov_path)
    curve_features = _read_parquet(curve_features_path)
    targets = _read_parquet(ema_targets_path)

    payload = {
        "source_quality_note": SOURCE_QUALITY_NOTE,
        "recommended_curve_label": RECOMMENDED_CURVE_LABEL,
        "contract_daily": summarize_contract_daily(contracts),
        "continuous_series": {
            "front_raw": summarize_continuous_series(front_raw),
            "front_adjusted": summarize_continuous_series(front_adjusted),
            "liquid_raw": summarize_continuous_series(liquid_raw),
            "harvest_nov": summarize_continuous_series(harvest_nov),
        },
        "curve_daily": summarize_curve_daily(curve_daily),
        "curve_features": summarize_curve_features(curve_features),
        "targets": summarize_targets(targets),
        "methodological_conclusion": {
            "ema_direct_pivot": "not_validated",
            "curve_maturity": "sparse_partial_curve",
            "best_current_use": "local_price_basis_storage_harvest_nov",
            "wording_guardrail": (
                "Use 'EMA front/basis/liquidity features, with partial curve fragments' "
                "instead of implying a complete Euronext futures curve."
            ),
        },
    }
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    output_markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def summarize_contract_daily(contracts: pd.DataFrame) -> dict[str, Any]:
    """Summarize the discrete EMA contract history."""
    if contracts.empty:
        return _empty_summary()
    work = _normalise_date_column(contracts)
    source_counts = _value_counts(work, "source")
    source_quality_counts = _value_counts(work, "source_quality")
    month_counts = _value_counts(work, "month_code")
    usable = work[work.get("import_verdict", pd.Series(index=work.index, dtype=object)).eq("usable")]
    legacy_f = work[work.get("month_code", pd.Series(index=work.index, dtype=object)).eq("F")]
    return {
        "rows": int(len(work)),
        "date_start": _date_min(work),
        "date_end": _date_max(work),
        "unique_dates": int(work["Date"].nunique()),
        "unique_contracts": int(work[_first_existing(work, ("contract_code", "canonical_contract_code", "source_symbol"))].nunique())
        if _first_existing(work, ("contract_code", "canonical_contract_code", "source_symbol"))
        else 0,
        "source_counts": source_counts,
        "source_quality_counts": source_quality_counts,
        "month_counts": month_counts,
        "usable_rows": int(len(usable)),
        "usable_month_counts": _value_counts(usable, "month_code"),
        "legacy_f_rows": int(len(legacy_f)),
        "legacy_f_usable_rows": int(legacy_f.get("import_verdict", pd.Series(dtype=object)).eq("usable").sum())
        if not legacy_f.empty
        else 0,
        "official_recent_rows": int(work["source"].astype(str).str.startswith("euronext").sum()) if "source" in work else 0,
    }


def summarize_continuous_series(series: pd.DataFrame) -> dict[str, Any]:
    """Summarize one continuous EMA series and its roll gaps."""
    if series.empty:
        return _empty_summary()
    work = _normalise_date_column(series)
    price_col = _first_existing(work, ("price", "adjusted_price", "close_or_last", "settlement"))
    summary = {
        "rows": int(len(work)),
        "date_start": _date_min(work),
        "date_end": _date_max(work),
        "unique_contracts": int(work["contract_code"].nunique()) if "contract_code" in work else 0,
        "price_col": price_col,
        "price_non_null": int(work[price_col].notna().sum()) if price_col else 0,
    }
    if "roll_event" in work.columns:
        rolls = work[work["roll_event"].fillna(False).astype(bool)].copy()
        gaps = pd.to_numeric(rolls.get("roll_adjustment", pd.Series(dtype=float)), errors="coerce")
        abs_gaps = gaps.abs().dropna()
        summary["rolls"] = {
            "n_rolls": int(len(rolls)),
            "abs_gap_mean_eur_t": _json_float(abs_gaps.mean()),
            "abs_gap_median_eur_t": _json_float(abs_gaps.median()),
            "abs_gap_max_eur_t": _json_float(abs_gaps.max()),
            "max_gap_date": _max_gap_date(rolls, gaps),
        }
    return summary


def summarize_curve_daily(curve_daily: pd.DataFrame) -> dict[str, Any]:
    """Summarize how complete the daily curve is."""
    if curve_daily.empty:
        return _empty_summary()
    work = _normalise_date_column(curve_daily)
    counts = work.groupby("Date").size()
    distribution = {str(int(k)): int(v) for k, v in counts.value_counts().sort_index().items()}
    n_dates = int(len(counts))
    return {
        "rows": int(len(work)),
        "date_start": _date_min(work),
        "date_end": _date_max(work),
        "unique_dates": n_dates,
        "avg_contracts_per_date": _json_float(counts.mean()),
        "contract_count_distribution": distribution,
        "dates_ge_2_contracts_pct": _json_float((counts >= 2).mean()),
        "dates_ge_3_contracts_pct": _json_float((counts >= 3).mean()),
        "dates_ge_4_contracts_pct": _json_float((counts >= 4).mean()),
    }


def summarize_curve_features(curve_features: pd.DataFrame) -> dict[str, Any]:
    """Summarize non-null rates for sparse curve feature fragments."""
    if curve_features.empty:
        return _empty_summary()
    work = _normalise_date_column(curve_features)
    rates = {
        col: _json_float(pd.to_numeric(work[col], errors="coerce").notna().mean())
        for col in SPARSE_CURVE_FEATURES
        if col in work.columns
    }
    sparse = {col: rate for col, rate in rates.items() if rate is not None and rate < 0.20}
    return {
        "rows": int(len(work)),
        "date_start": _date_min(work),
        "date_end": _date_max(work),
        "sparse_curve_feature_non_null_rates": rates,
        "sparse_below_20pct": sparse,
        "curve_label_recommendation": RECOMMENDED_CURVE_LABEL,
    }


def summarize_targets(targets: pd.DataFrame) -> dict[str, Any]:
    """Summarize EMA target availability and roll-crossing rates."""
    if targets.empty:
        return _empty_summary()
    work = _normalise_date_column(targets)
    horizons = (20, 40, 60)
    by_horizon: dict[str, Any] = {}
    for horizon in horizons:
        cross_col = f"target_crosses_roll_h{horizon}"
        raw_col = f"y_up_h{horizon}_ema_raw"
        adjusted_col = f"y_up_h{horizon}_ema_adjusted"
        no_roll_col = f"y_up_h{horizon}_ema_no_roll"
        cross = pd.to_numeric(work[cross_col], errors="coerce") if cross_col in work else pd.Series(dtype=float)
        by_horizon[str(horizon)] = {
            "raw_non_null": int(work[raw_col].notna().sum()) if raw_col in work else 0,
            "adjusted_non_null": int(work[adjusted_col].notna().sum()) if adjusted_col in work else 0,
            "no_roll_non_null": int(work[no_roll_col].notna().sum()) if no_roll_col in work else 0,
            "cross_roll_non_null": int(cross.notna().sum()),
            "cross_roll_rate": _json_float(cross.dropna().mean()) if len(cross.dropna()) else None,
        }
    return {
        "rows": int(len(work)),
        "date_start": _date_min(work),
        "date_end": _date_max(work),
        "by_horizon": by_horizon,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    """Render a compact human-readable audit report."""
    contracts = payload["contract_daily"]
    curve = payload["curve_daily"]
    curve_features = payload["curve_features"]
    targets = payload["targets"]
    front_rolls = payload["continuous_series"]["front_raw"].get("rolls", {})
    lines = [
        "# EMA Data Audit",
        "",
        f"> {payload['source_quality_note']}",
        "",
        "## Verdict",
        "",
        "- Pivot directionnel EMA direct : non validé actuellement.",
        f"- Libellé recommandé : **{payload['recommended_curve_label']}**.",
        "- EMA est surtout exploitable pour prix européen réel, basis CBOT-EMA, stockage et harvest_nov.",
        "",
        "## Contrats",
        "",
        f"- Lignes : {contracts.get('rows')}",
        f"- Période : {contracts.get('date_start')} -> {contracts.get('date_end')}",
        f"- Dates uniques : {contracts.get('unique_dates')}",
        f"- Contrats uniques : {contracts.get('unique_contracts')}",
        f"- Sources : `{contracts.get('source_counts')}`",
        f"- Mois utilisables : `{contracts.get('usable_month_counts')}`",
        f"- Lignes F/Janvier utilisables : {contracts.get('legacy_f_usable_rows')}",
        "",
        "## Séries Continues",
        "",
        _series_line("front_raw", payload["continuous_series"]["front_raw"]),
        _series_line("front_adjusted", payload["continuous_series"]["front_adjusted"]),
        _series_line("liquid_raw", payload["continuous_series"]["liquid_raw"]),
        _series_line("harvest_nov", payload["continuous_series"]["harvest_nov"]),
        "",
        "## Rolls Front",
        "",
        f"- Rolls : {front_rolls.get('n_rolls')}",
        f"- Gap moyen absolu : {_fmt(front_rolls.get('abs_gap_mean_eur_t'))} EUR/t",
        f"- Gap médian absolu : {_fmt(front_rolls.get('abs_gap_median_eur_t'))} EUR/t",
        f"- Gap maximum absolu : {_fmt(front_rolls.get('abs_gap_max_eur_t'))} EUR/t ({front_rolls.get('max_gap_date')})",
        "",
        "## Densité De Courbe",
        "",
        f"- Lignes : {curve.get('rows')}",
        f"- Dates uniques : {curve.get('unique_dates')}",
        f"- Contrats moyens par date : {_fmt(curve.get('avg_contracts_per_date'))}",
        f"- Distribution contrats/date : `{curve.get('contract_count_distribution')}`",
        f"- Dates avec >=2 contrats : {_pct(curve.get('dates_ge_2_contracts_pct'))}",
        f"- Dates avec >=3 contrats : {_pct(curve.get('dates_ge_3_contracts_pct'))}",
        "",
        "## Features De Courbe Sparse",
        "",
        *_feature_rate_lines(curve_features.get("sparse_curve_feature_non_null_rates", {})),
        "",
        "## Targets Et Rolls",
        "",
        *_target_lines(targets.get("by_horizon", {})),
        "",
        "## Conclusion Méthodologique",
        "",
        "- Ne pas présenter les features EMA comme une courbe futures complète tant que les contrats simultanés restent rares.",
        "- Pour la direction EMA, H20 reste la seule cible raisonnablement testable en no-roll ; H60 no-roll est structurellement indisponible.",
        "- Le moteur directionnel principal reste CBOT ; EMA doit être traité comme couche prix local, basis et décision stockage.",
        "",
    ]
    return "\n".join(lines)


def _read_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def _normalise_date_column(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    if "Date" not in work.columns and "date" in work.columns:
        work["Date"] = work["date"]
    if "Date" in work.columns:
        work["Date"] = pd.to_datetime(work["Date"]).dt.normalize()
    return work


def _date_min(work: pd.DataFrame) -> str | None:
    if "Date" not in work or work["Date"].dropna().empty:
        return None
    return work["Date"].min().date().isoformat()


def _date_max(work: pd.DataFrame) -> str | None:
    if "Date" not in work or work["Date"].dropna().empty:
        return None
    return work["Date"].max().date().isoformat()


def _value_counts(work: pd.DataFrame, col: str) -> dict[str, int]:
    if col not in work:
        return {}
    return {str(k): int(v) for k, v in work[col].fillna("<missing>").value_counts().sort_index().items()}


def _first_existing(work: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    return next((col for col in candidates if col in work.columns), None)


def _max_gap_date(rolls: pd.DataFrame, gaps: pd.Series) -> str | None:
    abs_gaps = gaps.abs()
    if rolls.empty or abs_gaps.dropna().empty:
        return None
    idx = abs_gaps.idxmax()
    if idx not in rolls.index or "Date" not in rolls:
        return None
    value = pd.Timestamp(rolls.loc[idx, "Date"])
    return value.date().isoformat()


def _empty_summary() -> dict[str, Any]:
    return {"rows": 0, "status": "missing_or_empty"}


def _series_line(name: str, summary: dict[str, Any]) -> str:
    return (
        f"- `{name}` : {summary.get('rows')} lignes, "
        f"{summary.get('date_start')} -> {summary.get('date_end')}"
    )


def _feature_rate_lines(rates: dict[str, Any]) -> list[str]:
    if not rates:
        return ["- Aucune feature de courbe disponible."]
    return [f"- `{col}` : {_pct(rate)} non-null" for col, rate in sorted(rates.items())]


def _target_lines(by_horizon: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for horizon, row in sorted(by_horizon.items(), key=lambda item: int(item[0])):
        lines.append(
            f"- H{horizon} : cross-roll {_pct(row.get('cross_roll_rate'))}, "
            f"raw={row.get('raw_non_null')}, adjusted={row.get('adjusted_non_null')}, "
            f"no-roll={row.get('no_roll_non_null')}"
        )
    return lines


def _fmt(value: Any) -> str:
    number = _safe_float(value)
    return "N/A" if not math.isfinite(number) else f"{number:.3f}"


def _pct(value: Any) -> str:
    number = _safe_float(value)
    return "N/A" if not math.isfinite(number) else f"{number * 100:.1f}%"


def _safe_float(value: Any) -> float:
    if value is None:
        return math.nan
    try:
        out = float(value)
    except (TypeError, ValueError):
        return math.nan
    return out if math.isfinite(out) else math.nan


def _json_float(value: Any) -> float | None:
    out = _safe_float(value)
    return out if math.isfinite(out) else None


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_ready(v) for v in value]
    if isinstance(value, tuple):
        return [_json_ready(v) for v in value]
    if isinstance(value, (np.integer, np.floating)):
        return _json_float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, float):
        return _json_float(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


if __name__ == "__main__":
    audit = run_ema_data_audit()
    print(json.dumps(_json_ready(audit["methodological_conclusion"]), indent=2, ensure_ascii=False))
