"""FIX-EMA-07 — Indicateur de prime européenne EMA/CBOT."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_direction_benchmarks_v2 import _load_dataset

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_premium_indicator.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_PREMIUM_INDICATOR.md"
_HORIZONS = (20, 40, 60)


def _zone(zscore: float) -> str:
    if zscore >= 2.0:
        return "very_high_premium"
    if zscore >= 1.5:
        return "high_premium"
    if zscore <= -2.0:
        return "very_low_premium"
    if zscore <= -1.5:
        return "low_premium"
    return "normal"


def _relative_signal(zone: str) -> str:
    if zone in {"very_high_premium", "high_premium"}:
        return "ema_expected_to_underperform_cbot"
    if zone in {"very_low_premium", "low_premium"}:
        return "ema_expected_to_outperform_cbot"
    return "neutral_relative_signal"


def _confidence(n_events: int, source_quality: str) -> str:
    if source_quality != "exploratoire_barchart_proxy":
        return "high" if n_events >= 80 else "medium"
    if n_events >= 80:
        return "medium"
    if n_events >= 30:
        return "low_to_medium"
    return "low"


def _reversion_stats(df: pd.DataFrame) -> list[dict]:
    rows = []
    basis = df["ema_cbot_basis"]
    z = df["ema_cbot_basis_zscore_52w"]
    for zone_name, mask in {
        "high_premium": z >= 1.5,
        "very_high_premium": z >= 2.0,
        "low_premium": z <= -1.5,
        "very_low_premium": z <= -2.0,
    }.items():
        for horizon in _HORIZONS:
            future = basis.shift(-horizon)
            reverts = future < basis if "high" in zone_name else future > basis
            valid = mask & future.notna() & basis.notna()
            n_events = int(valid.sum())
            hit_rate = float(reverts[valid].mean()) if n_events else None
            rows.append({
                "zone": zone_name,
                "horizon_days": int(horizon),
                "n_events": n_events,
                "reversion_hit_rate": hit_rate,
                "confidence": _confidence(n_events, "exploratoire_barchart_proxy"),
            })
    return rows


def _latest_snapshot(df: pd.DataFrame, reversion_stats: list[dict]) -> dict:
    latest = df.dropna(subset=["ema_front_price", "cbot_eur_t", "ema_cbot_basis"]).iloc[-1]
    zscore = float(latest["ema_cbot_basis_zscore_52w"])
    zone_name = _zone(zscore)
    zone_stats = [row for row in reversion_stats if row["zone"] == zone_name]
    best_stat = max(
        zone_stats,
        key=lambda row: -1.0 if row["reversion_hit_rate"] is None else row["reversion_hit_rate"],
        default=None,
    )
    n_events = int(best_stat["n_events"]) if best_stat else 0
    return {
        "date": str(pd.Timestamp(latest["Date"]).date()),
        "ema_price_eur_t": float(latest["ema_front_price"]),
        "cbot_eur_t": float(latest["cbot_eur_t"]),
        "basis_eur_t": float(latest["ema_cbot_basis"]),
        "basis_zscore_52w": zscore,
        "premium_zone": zone_name,
        "relative_signal": _relative_signal(zone_name),
        "best_historical_reversion": best_stat,
        "confidence": _confidence(n_events, "exploratoire_barchart_proxy"),
        "interpretation": _interpretation(zone_name),
    }


def _interpretation(zone_name: str) -> str:
    if zone_name in {"very_high_premium", "high_premium"}:
        return "EMA est cher relativement au CBOT; le signal porte sur une sous-performance relative ou une reversion du basis."
    if zone_name in {"very_low_premium", "low_premium"}:
        return "EMA est bas relativement au CBOT; le signal porte sur une surperformance relative ou une reversion du basis."
    return "Le basis est en zone normale; aucun signal relatif fort."


def build_premium_indicator() -> dict:
    df = _load_dataset()
    stats = _reversion_stats(df)
    snapshot = _latest_snapshot(df, stats)
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "scope": "relative EMA/CBOT and basis, not absolute EMA up/down.",
        "latest_snapshot": snapshot,
        "historical_reversion_stats": stats,
        "key_findings": {
            "latest_zone": snapshot["premium_zone"],
            "latest_relative_signal": snapshot["relative_signal"],
            "latest_confidence": snapshot["confidence"],
            "basis_eur_t": snapshot["basis_eur_t"],
            "basis_zscore_52w": snapshot["basis_zscore_52w"],
        },
    }


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
    value_float = float(value)
    return "N/A" if not np.isfinite(value_float) else f"{value_float:.{digits}f}"


def _write_markdown(data: dict, path: Path) -> None:
    snap = data["latest_snapshot"]
    lines = [
        "# EMA PREMIUM INDICATOR",
        "",
        "> Indicateur de prime européenne EMA/CBOT. Il ne prédit pas EMA up/down.",
        "",
        "## Snapshot",
        "",
        f"- Date : {snap['date']}",
        f"- EMA : {_fmt(snap['ema_price_eur_t'], 2)} EUR/t",
        f"- CBOT converti : {_fmt(snap['cbot_eur_t'], 2)} EUR/t",
        f"- Basis : {_fmt(snap['basis_eur_t'], 2)} EUR/t",
        f"- Z-score basis 52w : {_fmt(snap['basis_zscore_52w'])}",
        f"- Zone : {snap['premium_zone']}",
        f"- Signal relatif : {snap['relative_signal']}",
        f"- Confiance : {snap['confidence']}",
        "",
        snap["interpretation"],
        "",
        "## Reversion historique",
        "",
        "| Zone | Horizon | n | Hit rate | Confiance |",
        "|---|---:|---:|---:|---|",
    ]
    for row in data["historical_reversion_stats"]:
        hit = row["reversion_hit_rate"]
        hit_text = "N/A" if hit is None else f"{hit:.1%}"
        lines.append(
            f"| {row['zone']} | {row['horizon_days']} | {row['n_events']} | "
            f"{hit_text} | {row['confidence']} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_premium_indicator(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_premium_indicator()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_premium_indicator()
    print(f"Premium indicator saved -> {out}")
