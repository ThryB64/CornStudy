"""NB-EMA-00 — Vue d'ensemble du projet Étude Mais CBOT & Euronext EMA."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import (
    ARTEFACTS_DIR,
    EMA_FRONT_RAW,
    EMA_HARVEST_NOV,
    FEATURES_PARQUET,
)

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_project_overview.json"


def _safe_val(v):
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, np.ndarray):
        return v.tolist()
    if isinstance(v, pd.Timestamp):
        return str(v.date())
    return v


def _index_date_str(idx_val) -> str | None:
    try:
        return str(pd.Timestamp(idx_val).date())
    except Exception:
        return str(idx_val)


def _series_stats(series: pd.Series, name: str) -> dict:
    s = series.dropna()
    return {
        "name": name,
        "n_days": int(len(s)),
        "period_start": _index_date_str(s.index.min()) if len(s) else None,
        "period_end": _index_date_str(s.index.max()) if len(s) else None,
        "mean": float(s.mean()) if len(s) else None,
        "std": float(s.std()) if len(s) else None,
        "min": float(s.min()) if len(s) else None,
        "max": float(s.max()) if len(s) else None,
        "median": float(s.median()) if len(s) else None,
    }


def _load_benchmark_results() -> dict:
    """Charge les résultats clés depuis les artefacts existants."""
    results: dict = {}

    ema_audit_path = _STUDY_DIR / "ema_data_audit.json"
    if ema_audit_path.exists():
        with open(ema_audit_path) as f:
            audit = json.load(f)
        results["data_audit"] = {
            "total_rows": audit.get("total_rows"),
            "n_front_rows": audit.get("n_front_rows"),
            "source": audit.get("source_quality_counts"),
            "pct_dates_multi_contracts": audit.get("pct_dates_with_2plus_contracts"),
        }

    rel_path = _STUDY_DIR / "ema_cbot_relationship.json"
    if rel_path.exists():
        with open(rel_path) as f:
            rel = json.load(f)
        results["cbot_relationship"] = {
            "correlation_levels": rel.get("correlation_levels"),
            "correlation_returns": rel.get("correlation_daily_returns"),
            "basis_mean": rel.get("basis_mean_eur_t"),
            "granger_ema_to_cbot_min_p": rel.get("granger_ema_to_cbot", {}).get("min_p_value"),
            "granger_cbot_to_ema_min_p": rel.get("granger_cbot_to_ema", {}).get("min_p_value"),
        }

    basis_path = _STUDY_DIR / "ema_basis_study.json"
    if basis_path.exists():
        with open(basis_path) as f:
            basis = json.load(f)
        results["basis_study"] = {
            "verdict": basis.get("verdict"),
            "hit_rate_h20_high": basis.get("high_basis", {}).get("reversion_rate_h20"),
            "avg_change_h20_high": basis.get("high_basis", {}).get("avg_basis_change_h20"),
        }

    bench_dir = ARTEFACTS_DIR / "benchmark_pivot"
    bench_csv = bench_dir / "tableau_benchmark_pivot.csv"
    if bench_csv.exists():
        try:
            bdf = pd.read_csv(bench_csv)
            best_row = bdf[bdf.get("feature_set", bdf.columns[0]).notna()].head(5)
            results["direction_benchmark_sample"] = best_row.to_dict(orient="records")
        except Exception:
            results["direction_benchmark_sample"] = "not_loaded"

    return results


def build_project_overview() -> dict:
    overview: dict = {
        "project": "Étude Statistique Maïs CBOT & Euronext EMA",
        "pivot_date": "2026-05-20",
        "guiding_phrase": (
            "CBOT explique la tendance mondiale. EMA révèle la prime européenne via le basis. "
            "La vraie étude Euronext = basis + transmission CBOT→EMA + découplage + résidu EU."
        ),
        "data_source_quality": "exploratory (Barchart proxy — not official Euronext settlement)",
    }

    if EMA_FRONT_RAW.exists():
        front = pd.read_parquet(EMA_FRONT_RAW)
        price_col = "close_or_last" if "close_or_last" in front.columns else front.select_dtypes("number").columns[0]
        if "date" in front.columns:
            front = front.set_index("date")
        front.index = pd.to_datetime(front.index)
        overview["ema_front_stats"] = _series_stats(front[price_col], "EMA_front_raw")
    else:
        overview["ema_front_stats"] = {"error": "EMA_FRONT_RAW not found"}

    if EMA_HARVEST_NOV.exists():
        harv = pd.read_parquet(EMA_HARVEST_NOV)
        price_col = "close_or_last" if "close_or_last" in harv.columns else harv.select_dtypes("number").columns[0]
        if "date" in harv.columns:
            harv = harv.set_index("date")
        harv.index = pd.to_datetime(harv.index)
        overview["ema_harvest_nov_stats"] = _series_stats(harv[price_col], "EMA_harvest_nov")

    if FEATURES_PARQUET.exists():
        feat = pd.read_parquet(FEATURES_PARQUET, columns=["cbot_eur_t", "ema_cbot_basis"])
        if "cbot_eur_t" in feat.columns:
            overview["cbot_eur_t_stats"] = _series_stats(feat["cbot_eur_t"], "CBOT_EUR_t")
        if "ema_cbot_basis" in feat.columns:
            overview["basis_stats"] = _series_stats(feat["ema_cbot_basis"], "EMA_CBOT_basis")
            basis = feat["ema_cbot_basis"].dropna()
            if len(basis):
                overview["basis_stats"]["pct_positive"] = float((basis > 0).mean())
                overview["basis_stats"]["pct_negative"] = float((basis < 0).mean())

    overview["benchmark_results"] = _load_benchmark_results()

    overview["known_results_summary"] = {
        "ema_direction_da_h20": 0.4673,
        "ema_direction_ic95": [0.4432, 0.4902],
        "ema_direction_verdict": "NO_GO",
        "basis_only_on_cbot_da": 0.5840,
        "basis_only_on_cbot_auc": 0.6336,
        "basis_mean_reversion_hit_rate_h20": 0.704,
        "cqr_prix_ema_coverage": 0.792,
        "cqr_coverage_required": 0.88,
        "cqr_verdict": "NO_GO",
        "granger_ema_to_cbot_p": 0.0144,
        "granger_status": "PROMETTEUR — non confirmé OOF",
        "pct_dates_curve_2plus_contracts": 0.149,
    }

    return overview


def save_overview(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_project_overview()

    def _convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return str(obj.date())
        raise TypeError(f"Not serialisable: {type(obj)}")

    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=_convert)
    return path


if __name__ == "__main__":
    out = save_overview()
    print(f"Overview saved → {out}")
