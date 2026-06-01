"""FIX-EMA-05 — Split qualité données EMA pour les signaux directionnels."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, EMA_CONTRACT_DAILY, PROJECT_ROOT
from mais.research.ema_direction_benchmarks_v2 import _evaluate, _load_dataset

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_data_quality_split.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_DATA_QUALITY_SPLIT.md"

_TARGETS = {
    "relative_ema_outperformance_h40": "y_ema_outperforms_cbot_h40",
    "ema_direction_absolute_h40": "y_up_h40_ema_raw",
    "basis_reversion_h20": "basis_reversion_h20",
}


def _source_by_date() -> pd.DataFrame:
    contracts = pd.read_parquet(EMA_CONTRACT_DAILY)
    contracts["Date"] = pd.to_datetime(contracts["date"]).dt.normalize()
    source = contracts.get("source", pd.Series("", index=contracts.index)).astype(str).str.lower()
    source_quality = contracts.get("source_quality", pd.Series("", index=contracts.index)).astype(str).str.lower()
    is_proxy = contracts.get("is_proxy", pd.Series(False, index=contracts.index)).fillna(False).astype(bool)
    contracts["_is_official"] = source.str.contains("euronext") & ~is_proxy
    contracts["_is_proxy"] = source.str.contains("barchart") | source_quality.str.contains("exploratory") | is_proxy
    grouped = contracts.groupby("Date").agg(
        n_contract_rows=("Date", "size"),
        official_rows=("_is_official", "sum"),
        proxy_rows=("_is_proxy", "sum"),
    )
    grouped["official_share"] = grouped["official_rows"] / grouped["n_contract_rows"].replace(0, np.nan)
    grouped["proxy_share"] = grouped["proxy_rows"] / grouped["n_contract_rows"].replace(0, np.nan)
    return grouped.reset_index()


def _split_frames(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    availability = pd.to_numeric(df.get("ema_data_availability_score", pd.Series(np.nan, index=df.index)), errors="coerce")
    median_availability = float(availability.dropna().median()) if availability.notna().any() else 0.0
    return {
        "all_data": df,
        "proxy_dominant": df[df["proxy_share"].fillna(0.0) >= 0.50],
        "official_recent": df[df["official_share"].fillna(0.0) >= 0.50],
        "high_availability": df[availability >= max(0.60, median_availability)],
        "low_quality_excluded": df[(availability >= 0.50) & (df["proxy_share"].fillna(0.0) < 1.0)],
    }


def _split_summary(name: str, frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {
            "split": name,
            "n_rows": 0,
            "period_start": None,
            "period_end": None,
            "official_share_mean": None,
            "proxy_share_mean": None,
        }
    return {
        "split": name,
        "n_rows": int(len(frame)),
        "period_start": str(frame["Date"].min().date()),
        "period_end": str(frame["Date"].max().date()),
        "official_share_mean": float(frame["official_share"].fillna(0.0).mean()),
        "proxy_share_mean": float(frame["proxy_share"].fillna(0.0).mean()),
        "availability_mean": float(
            pd.to_numeric(frame.get("ema_data_availability_score", pd.Series(np.nan, index=frame.index)), errors="coerce").mean()
        ),
    }


def build_data_quality_split() -> dict:
    df = _load_dataset()
    source = _source_by_date()
    df = df.merge(source, on="Date", how="left")
    df[["official_share", "proxy_share"]] = df[["official_share", "proxy_share"]].fillna(0.0)
    splits = _split_frames(df)
    split_results = {}
    for name, frame in splits.items():
        targets = {}
        for label, target in _TARGETS.items():
            targets[label] = _evaluate(frame, target, weekly=False) if target in frame else {"error": "missing_target"}
        split_results[name] = {
            "summary": _split_summary(name, frame),
            "targets": targets,
        }
    robust = split_results["all_data"]["targets"]["relative_ema_outperformance_h40"]
    proxy = split_results["proxy_dominant"]["targets"]["relative_ema_outperformance_h40"]
    official = split_results["official_recent"]["targets"]["relative_ema_outperformance_h40"]
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "targets": _TARGETS,
        "splits": split_results,
        "key_findings": {
            "robust_signal": "relative_ema_outperformance_h40",
            "all_data_auc": robust.get("auc"),
            "proxy_dominant_auc": proxy.get("auc"),
            "official_recent_status": official.get("error", official.get("status", "OK")),
            "official_recent_n_rows": split_results["official_recent"]["summary"]["n_rows"],
            "conclusion": _conclusion(robust, proxy, official),
        },
    }


def _conclusion(robust: dict, proxy: dict, official: dict) -> str:
    official_error = official.get("error")
    robust_auc = robust.get("auc")
    proxy_auc = proxy.get("auc")
    if official_error:
        return "Signal robuste observable surtout sur historique proxy; période officielle récente trop courte pour validation OOF."
    if robust_auc is not None and proxy_auc is not None and abs(float(robust_auc) - float(proxy_auc)) <= 0.05:
        return "Signal stable entre all data et proxy dominant, mais validation officielle reste nécessaire."
    return "Signal sensible au split qualité; conclusions EMA doivent rester exploratoires."


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
        "# EMA DATA QUALITY SPLIT",
        "",
        "> Comparaison des signaux EMA par qualité/source de données.",
        "",
        "## Verdict",
        "",
        f"- Signal suivi : {k['robust_signal']}",
        f"- AUC all data : {_fmt(k.get('all_data_auc'))}",
        f"- AUC proxy dominant : {_fmt(k.get('proxy_dominant_auc'))}",
        f"- Official recent : {k.get('official_recent_status')} ({k.get('official_recent_n_rows')} lignes)",
        f"- Conclusion : {k['conclusion']}",
        "",
        "## Splits",
        "",
        "| Split | n | Période | Official share | Proxy share | Relative H40 AUC | Relative H40 balanced acc. |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for name, split in data["splits"].items():
        summary = split["summary"]
        rel = split["targets"]["relative_ema_outperformance_h40"]
        period = f"{summary['period_start']} -> {summary['period_end']}" if summary["period_start"] else "N/A"
        lines.append(
            f"| {name} | {summary['n_rows']} | {period} | "
            f"{_fmt(summary.get('official_share_mean'))} | {_fmt(summary.get('proxy_share_mean'))} | "
            f"{_fmt(rel.get('auc'))} | {_fmt(rel.get('balanced_accuracy'))} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_data_quality_split(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_data_quality_split()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_data_quality_split()
    print(f"Data quality split saved -> {out}")
