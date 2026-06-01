"""EMA-NEXT-04 — Saisonnalite de la prime relative EMA/CBOT."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_relative_study import oof_relative_predictions

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_relative_seasonality.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_RELATIVE_SEASONALITY.md"
_HORIZONS = (40, 90)


def _season(month: int) -> str:
    if month in {1, 2, 3}:
        return "jan_mar_old_crop_import"
    if month in {4, 5, 6}:
        return "apr_jun_sowing_weather"
    if month in {7, 8}:
        return "jul_aug_yield_stress"
    if month in {9, 10, 11}:
        return "sep_nov_eu_harvest"
    return "dec_import_export_arbitrage"


def _metrics(sub: pd.DataFrame, horizon: int, season: str) -> dict:
    if len(sub) < 40 or sub["y_true"].nunique() < 2:
        return {
            "horizon": int(horizon),
            "season": season,
            "status": "SKIPPED",
            "reason": "insufficient_data_or_single_class",
            "n": int(len(sub)),
        }
    top_n = max(1, int(len(sub) * 0.20))
    top = sub.nlargest(top_n, "confidence")
    y = sub["y_true"].astype(float)
    y_pred = sub["y_pred"].astype(float)
    return {
        "horizon": int(horizon),
        "season": season,
        "status": "OK",
        "n": int(len(sub)),
        "base_rate": float(y.mean()),
        "da": float(accuracy_score(y, y_pred)),
        "auc": float(roc_auc_score(y, sub["prob"])),
        "balanced_accuracy": float(balanced_accuracy_score(y, y_pred)),
        "top20_da": float(accuracy_score(top["y_true"], top["y_pred"])),
        "basis_mean": float(sub["ema_cbot_basis"].mean()),
        "basis_z_mean": float(sub["ema_cbot_basis_zscore_52w"].mean()),
    }


def _seasonal_horizon(horizon: int) -> dict:
    pred = oof_relative_predictions(horizon=horizon)
    pred["season"] = pred["month"].apply(_season)
    rows = []
    for season, sub in pred.groupby("season", sort=False):
        rows.append(_metrics(sub, horizon, season))
    ok = [row for row in rows if row.get("status") == "OK"]
    best = max(ok, key=lambda row: (row.get("auc", -1), row.get("balanced_accuracy", -1)), default={})
    weakest = min(ok, key=lambda row: (row.get("auc", 999), row.get("balanced_accuracy", 999)), default={})
    return {
        "horizon": int(horizon),
        "seasonal_results": rows,
        "best_season": best.get("season"),
        "best_season_auc": best.get("auc"),
        "best_season_da": best.get("da"),
        "weakest_season": weakest.get("season"),
        "weakest_season_auc": weakest.get("auc"),
    }


def build_relative_seasonality() -> dict:
    results = [_seasonal_horizon(horizon) for horizon in _HORIZONS]
    h40 = next(row for row in results if row["horizon"] == 40)
    h90 = next(row for row in results if row["horizon"] == 90)
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "target_family": "relative_ema_outperformance",
        "season_definitions": {
            "jan_mar_old_crop_import": "Janvier-mars : old crop, import et arbitrages de fin de campagne.",
            "apr_jun_sowing_weather": "Avril-juin : semis Europe et premiere meteo.",
            "jul_aug_yield_stress": "Juillet-aout : stress rendement.",
            "sep_nov_eu_harvest": "Septembre-novembre : recolte Europe.",
            "dec_import_export_arbitrage": "Decembre : arbitrage import/export.",
        },
        "results": results,
        "key_findings": {
            "h40_best_season": h40.get("best_season"),
            "h40_best_auc": h40.get("best_season_auc"),
            "h90_best_season": h90.get("best_season"),
            "h90_best_auc": h90.get("best_season_auc"),
            "interpretation": _interpretation(results),
        },
    }


def _interpretation(results: list[dict]) -> str:
    best_seasons = {row.get("best_season") for row in results}
    if "sep_nov_eu_harvest" in best_seasons:
        return "La prime relative semble particulierement lisible autour de la recolte europeenne."
    if "jul_aug_yield_stress" in best_seasons:
        return "La prime relative semble sensible a la fenetre de stress rendement ete."
    return "Le signal relatif existe sur plusieurs saisons ; utiliser la saison comme filtre de confiance."


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
        "# EMA RELATIVE SEASONALITY",
        "",
        "> Etude saisonniere de `relative_ema_outperformance`.",
        "",
        "## Verdict",
        "",
        f"- H40 meilleure saison : `{data['key_findings']['h40_best_season']}` AUC {_fmt(data['key_findings']['h40_best_auc'])}",
        f"- H90 meilleure saison : `{data['key_findings']['h90_best_season']}` AUC {_fmt(data['key_findings']['h90_best_auc'])}",
        f"- Lecture : {data['key_findings']['interpretation']}",
        "",
    ]
    for result in data["results"]:
        lines += [
            f"## H{result['horizon']}",
            "",
            "| Saison | n | Base rate | DA | AUC | Balanced acc. | Top20 DA | Basis moyen |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for row in result["seasonal_results"]:
            lines.append(
                f"| {row['season']} | {row.get('n', 0)} | {_fmt(row.get('base_rate'))} | "
                f"{_fmt(row.get('da'))} | {_fmt(row.get('auc'))} | {_fmt(row.get('balanced_accuracy'))} | "
                f"{_fmt(row.get('top20_da'))} | {_fmt(row.get('basis_mean'), 2)} |"
            )
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_relative_seasonality(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_relative_seasonality()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_relative_seasonality()
    print(f"Relative seasonality saved -> {out}")
