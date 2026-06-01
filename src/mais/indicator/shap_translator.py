"""Translate model contributions into farmer-readable market language."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class TranslatedFactors:
    bullish: list[str]
    bearish: list[str]
    risks: list[str]


def translate_shap_rows(shap_rows: pd.DataFrame | list[dict[str, Any]] | None, *, max_items: int = 3) -> TranslatedFactors:
    """Translate signed contribution rows into plain French factor sentences."""
    if shap_rows is None:
        return TranslatedFactors(bullish=[], bearish=[], risks=[])
    rows = pd.DataFrame(shap_rows)
    if rows.empty:
        return TranslatedFactors(bullish=[], bearish=[], risks=[])
    feature_col = "feature" if "feature" in rows.columns else "factor"
    value_col = "shap_value" if "shap_value" in rows.columns else "contribution"
    if feature_col not in rows.columns or value_col not in rows.columns:
        return TranslatedFactors(bullish=[], bearish=[], risks=[])
    rows = rows.copy()
    rows[value_col] = pd.to_numeric(rows[value_col], errors="coerce").fillna(0.0)
    rows["abs_value"] = rows[value_col].abs()
    rows = rows.sort_values("abs_value", ascending=False)

    bullish: list[str] = []
    bearish: list[str] = []
    risks: list[str] = []
    for row in rows.itertuples(index=False):
        feature = str(getattr(row, feature_col))
        contribution = float(getattr(row, value_col))
        sentence = _sentence_for_feature(feature, contribution)
        bucket = _bucket_for_feature(feature, contribution)
        if bucket == "risk":
            risks.append(sentence)
        elif bucket == "bullish":
            bullish.append(sentence)
        else:
            bearish.append(sentence)
    return TranslatedFactors(
        bullish=bullish[:max_items],
        bearish=bearish[:max_items],
        risks=risks[:max_items],
    )


def _bucket_for_feature(feature: str, contribution: float) -> str:
    name = feature.lower()
    if "cot" in name and "extreme_long" in name:
        return "risk"
    if contribution >= 0:
        return "bullish"
    return "bearish"


def _sentence_for_feature(feature: str, contribution: float) -> str:
    name = feature.lower()
    direction = "soutient les prix" if contribution >= 0 else "pese sur les prix"
    if "wasde" in name:
        return f"Le dernier contexte USDA {direction}."
    if "drought" in name or "rain" in name or "crop" in name:
        return f"La situation des cultures et de la meteo {direction}."
    if "export" in name or "fas" in name:
        return f"Le rythme des ventes export {direction}."
    if "dollar" in name or "macro" in name:
        return f"Le contexte macro et le dollar {direction}."
    if "cot" in name and "extreme_long" in name:
        return "Les fonds speculatifs sont tres achetes, ce qui augmente le risque de retournement."
    if "cot" in name:
        return f"Le positionnement des fonds {direction}."
    if "spread" in name or "curve" in name:
        return f"La courbe des futures {direction}."
    return f"{_humanize_feature(feature)} {direction}."


def _humanize_feature(feature: str) -> str:
    return feature.replace("_", " ").strip().capitalize()
