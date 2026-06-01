"""EMA-SEASON-02 — Regimes saisonniers de prime EMA/CBOT."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_relative_seasonality import build_relative_seasonality

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_seasonal_premium_regimes.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_SEASONAL_PREMIUM_REGIMES.md"


def _action(row: dict) -> str:
    auc = row.get("auc") or 0.0
    da = row.get("da") or 0.0
    if auc >= 0.75 and da >= 0.65:
        return "TRADE_ALLOWED_RESEARCH"
    if auc >= 0.60 and da >= 0.55:
        return "CAUTION"
    return "ABSTAIN"


def _regime_table(seasonality: dict) -> list[dict]:
    by_season: dict[str, dict[int, dict]] = {}
    for result in seasonality.get("results", []):
        horizon = int(result["horizon"])
        for row in result.get("seasonal_results", []):
            if row.get("status") != "OK":
                continue
            by_season.setdefault(row["season"], {})[horizon] = row
    regimes = []
    for season, horizons in by_season.items():
        best_horizon, best_row = max(
            horizons.items(),
            key=lambda item: (item[1].get("auc", -1), item[1].get("balanced_accuracy", -1)),
        )
        regimes.append(
            {
                "season": season,
                "recommended_horizon": int(best_horizon),
                "recommended_action": _action(best_row),
                "best_auc": best_row.get("auc"),
                "best_da": best_row.get("da"),
                "best_balanced_accuracy": best_row.get("balanced_accuracy"),
                "best_top20_da": best_row.get("top20_da"),
                "h40_auc": horizons.get(40, {}).get("auc"),
                "h40_da": horizons.get(40, {}).get("da"),
                "h90_auc": horizons.get(90, {}).get("auc"),
                "h90_da": horizons.get(90, {}).get("da"),
                "basis_mean": best_row.get("basis_mean"),
            }
        )
    return sorted(regimes, key=lambda row: row.get("best_auc", 0), reverse=True)


def build_seasonal_premium_regimes() -> dict:
    seasonality = build_relative_seasonality()
    regimes = _regime_table(seasonality)
    allowed = [row for row in regimes if row["recommended_action"] == "TRADE_ALLOWED_RESEARCH"]
    abstain = [row for row in regimes if row["recommended_action"] == "ABSTAIN"]
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "scope": "Seasonal confidence gates for EMA/CBOT premium signal.",
        "regimes": regimes,
        "key_findings": {
            "allowed_seasons": [row["season"] for row in allowed],
            "abstain_seasons": [row["season"] for row in abstain],
            "best_overall_season": regimes[0]["season"] if regimes else None,
            "best_overall_horizon": regimes[0]["recommended_horizon"] if regimes else None,
            "interpretation": _interpretation(allowed, abstain),
        },
    }


def _interpretation(allowed: list[dict], abstain: list[dict]) -> str:
    if allowed and abstain:
        return "Use seasonal gates: trade/research only in strong premium seasons and abstain in weak windows."
    if allowed:
        return "Most seasons remain usable, but keep confidence tiers."
    return "Seasonal signal is too uneven; abstention should dominate."


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
        "# EMA SEASONAL PREMIUM REGIMES",
        "",
        "> Regimes saisonniers pour filtrer l'indicateur de prime EMA/CBOT.",
        "",
        "## Verdict",
        "",
        f"- Saisons autorisées recherche : {', '.join(data['key_findings']['allowed_seasons']) or 'aucune'}",
        f"- Saisons abstention : {', '.join(data['key_findings']['abstain_seasons']) or 'aucune'}",
        f"- Meilleure saison : `{data['key_findings']['best_overall_season']}` H{data['key_findings']['best_overall_horizon']}",
        f"- Lecture : {data['key_findings']['interpretation']}",
        "",
        "| Saison | Action | H recommandé | AUC | DA | BAcc | Top20 | H40 AUC | H90 AUC |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["regimes"]:
        lines.append(
            f"| {row['season']} | {row['recommended_action']} | {row['recommended_horizon']} | "
            f"{_fmt(row.get('best_auc'))} | {_fmt(row.get('best_da'))} | {_fmt(row.get('best_balanced_accuracy'))} | "
            f"{_fmt(row.get('best_top20_da'))} | {_fmt(row.get('h40_auc'))} | {_fmt(row.get('h90_auc'))} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_seasonal_premium_regimes(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_seasonal_premium_regimes()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_seasonal_premium_regimes()
    print(f"Seasonal premium regimes saved -> {out}")
