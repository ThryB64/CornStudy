"""EMA-PREM-02 — European Premium Indicator V2."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_relative_seasonality import _season
from mais.research.ema_relative_study import oof_relative_predictions

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_premium_indicator_v2.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_PREMIUM_INDICATOR_V2.md"


def _basis_score(zscore: pd.Series) -> pd.Series:
    return 1.0 / (1.0 + np.exp(zscore.clip(-8, 8)))


def _confidence_tier(confidence: float) -> str:
    if confidence >= 0.25:
        return "high"
    if confidence >= 0.15:
        return "medium"
    if confidence >= 0.08:
        return "low"
    return "uncertain"


def _premium_signal(score: float, basis_z: float, confidence: float) -> str:
    if confidence < 0.08:
        return "UNCERTAIN"
    if basis_z >= 1.5 and score < 0.50:
        return "EU_PREMIUM_BEARISH"
    if basis_z <= -1.5 and score > 0.50:
        return "EU_PREMIUM_BULLISH"
    if score >= 0.60:
        return "EU_PREMIUM_BULLISH"
    if score <= 0.40:
        return "EU_PREMIUM_BEARISH"
    return "NEUTRAL"


def _history_frame() -> pd.DataFrame:
    h40 = oof_relative_predictions(horizon=40)
    h90 = oof_relative_predictions(horizon=90)[["Date", "prob", "confidence"]].rename(
        columns={"prob": "prob_h90", "confidence": "confidence_h90"}
    )
    out = h40.rename(columns={"prob": "prob_h40", "confidence": "confidence_h40"}).merge(h90, on="Date", how="inner")
    out["basis_score"] = _basis_score(out["ema_cbot_basis_zscore_52w"])
    out["premium_score"] = 0.40 * out["prob_h40"] + 0.30 * out["prob_h90"] + 0.30 * out["basis_score"]
    out["premium_confidence"] = (out["premium_score"] - 0.5).abs()
    out["confidence_tier"] = out["premium_confidence"].apply(_confidence_tier)
    out["premium_signal"] = [
        _premium_signal(score, basis_z, conf)
        for score, basis_z, conf in zip(
            out["premium_score"],
            out["ema_cbot_basis_zscore_52w"],
            out["premium_confidence"],
            strict=False,
        )
    ]
    out["season"] = out["month"].apply(_season)
    out["correct"] = (out["premium_score"] >= 0.5).astype(float).eq(out["y_true"].astype(float))
    return out.sort_values("Date").reset_index(drop=True)


def build_premium_indicator_v2() -> dict:
    hist = _history_frame()
    latest = hist.iloc[-1]
    signal_counts = hist["premium_signal"].value_counts().to_dict()
    tier_counts = hist["confidence_tier"].value_counts().to_dict()
    top = hist[hist["confidence_tier"].isin(["medium", "high"])]
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "scope": "Relative EMA/CBOT premium indicator. It is not an absolute EMA up/down signal.",
        "snapshot": {
            "date": str(pd.Timestamp(latest["Date"]).date()),
            "basis_eur_t": float(latest["ema_cbot_basis"]),
            "basis_zscore": float(latest["ema_cbot_basis_zscore_52w"]),
            "prob_h40_ema_outperforms": float(latest["prob_h40"]),
            "prob_h90_ema_outperforms": float(latest["prob_h90"]),
            "basis_score": float(latest["basis_score"]),
            "premium_score": float(latest["premium_score"]),
            "premium_signal": str(latest["premium_signal"]),
            "confidence": float(latest["premium_confidence"]),
            "confidence_tier": str(latest["confidence_tier"]),
            "season": str(latest["season"]),
            "reading": _reading(latest),
        },
        "history_summary": {
            "n": int(len(hist)),
            "signal_counts": {str(key): int(value) for key, value in signal_counts.items()},
            "confidence_tier_counts": {str(key): int(value) for key, value in tier_counts.items()},
            "all_signal_accuracy": float(hist["correct"].mean()),
            "medium_high_accuracy": float(top["correct"].mean()) if len(top) else None,
            "medium_high_coverage": float(len(top) / len(hist)) if len(hist) else 0.0,
        },
        "recent_history": hist.tail(20)[
            [
                "Date",
                "premium_signal",
                "premium_score",
                "confidence_tier",
                "ema_cbot_basis_zscore_52w",
                "season",
                "correct",
            ]
        ].to_dict(orient="records"),
    }


def _reading(row: pd.Series) -> str:
    signal = row["premium_signal"]
    if signal == "EU_PREMIUM_BULLISH":
        return "EMA expected to outperform CBOT on a relative basis."
    if signal == "EU_PREMIUM_BEARISH":
        return "EMA expected to underperform CBOT on a relative basis."
    if signal == "NEUTRAL":
        return "No strong relative premium signal."
    return "Signal too close to neutral; abstain."


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
    s = data["snapshot"]
    h = data["history_summary"]
    lines = [
        "# EMA PREMIUM INDICATOR V2",
        "",
        "> Indicateur relatif EMA/CBOT. Ce n'est pas un signal directionnel absolu du prix EMA.",
        "",
        "## Snapshot",
        "",
        f"- Date : {s['date']}",
        f"- Signal : `{s['premium_signal']}`",
        f"- Confidence tier : `{s['confidence_tier']}`",
        f"- Premium score : {_fmt(s['premium_score'])}",
        f"- Basis : {_fmt(s['basis_eur_t'], 2)} EUR/t",
        f"- Basis z-score : {_fmt(s['basis_zscore'])}",
        f"- Prob H40 EMA outperforms : {_fmt(s['prob_h40_ema_outperforms'])}",
        f"- Prob H90 EMA outperforms : {_fmt(s['prob_h90_ema_outperforms'])}",
        f"- Saison : `{s['season']}`",
        f"- Lecture : {s['reading']}",
        "",
        "## Historique",
        "",
        f"- n : {h['n']}",
        f"- Accuracy tous signaux : {_fmt(h['all_signal_accuracy'])}",
        f"- Accuracy medium/high : {_fmt(h['medium_high_accuracy'])}",
        f"- Coverage medium/high : {_fmt(h['medium_high_coverage'])}",
        "",
        "## Limites",
        "",
        "- Source EMA exploratoire/proxy.",
        "- Lecture relative EMA vs CBOT uniquement.",
        "- Pas de claim trading production.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_premium_indicator_v2(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_premium_indicator_v2()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_premium_indicator_v2()
    print(f"Premium indicator V2 saved -> {out}")
