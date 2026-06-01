"""Basis mean-reversion study for EMA versus CBOT EUR/t."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import (
    ARTEFACTS_DIR,
    EMA_FRONT_ADJUSTED,
    EMA_FRONT_RAW,
    PROJECT_ROOT,
)
from mais.research.ema_cbot_relationship import (
    DEFAULT_CBOT_PATH,
    DEFAULT_EURUSD_PATH,
    build_relationship_frame,
    rolling_zscore,
)
from mais.research.ema_data_audit import SOURCE_QUALITY_NOTE

EMA_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
EMA_BASIS_STUDY_JSON = EMA_STUDY_DIR / "ema_basis_study.json"
EMA_BASIS_STUDY_MD = PROJECT_ROOT / "docs" / "EMA_BASIS_STUDY.md"
DEFAULT_HORIZONS = (20, 40, 60)


def run_ema_basis_study(
    *,
    ema_front_raw_path: Path = EMA_FRONT_RAW,
    ema_front_adjusted_path: Path = EMA_FRONT_ADJUSTED,
    cbot_path: Path = DEFAULT_CBOT_PATH,
    eurusd_path: Path = DEFAULT_EURUSD_PATH,
    output_json_path: Path = EMA_BASIS_STUDY_JSON,
    output_markdown_path: Path = EMA_BASIS_STUDY_MD,
    horizons: tuple[int, ...] = DEFAULT_HORIZONS,
    z_window: int = 260,
    high_threshold: float = 2.0,
    low_threshold: float = -2.0,
) -> dict[str, Any]:
    """Run basis regime and mean-reversion diagnostics."""
    frame = build_relationship_frame(
        ema_front_raw_path=ema_front_raw_path,
        ema_front_adjusted_path=ema_front_adjusted_path,
        cbot_path=cbot_path,
        eurusd_path=eurusd_path,
    )
    frame["basis_z"] = rolling_zscore(frame["ema_cbot_basis"], window=z_window)
    regime_table = analyze_basis_regimes(
        frame,
        horizons=horizons,
        high_threshold=high_threshold,
        low_threshold=low_threshold,
    )
    payload = {
        "source_quality_note": SOURCE_QUALITY_NOTE,
        "n_rows": int(len(frame)),
        "date_start": _date_min(frame),
        "date_end": _date_max(frame),
        "z_window": int(z_window),
        "thresholds": {"high": float(high_threshold), "low": float(low_threshold)},
        "basis_distribution": basis_distribution(frame),
        "regime_results": regime_table.to_dict(orient="records"),
        "decision": decide_basis_signal(regime_table),
    }
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    output_markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def analyze_basis_regimes(
    frame: pd.DataFrame,
    *,
    horizons: tuple[int, ...] = DEFAULT_HORIZONS,
    high_threshold: float = 2.0,
    low_threshold: float = -2.0,
) -> pd.DataFrame:
    """Measure future returns and basis change by basis-z regime."""
    work = frame.copy().sort_values("Date").reset_index(drop=True)
    if "basis_z" not in work.columns:
        work["basis_z"] = rolling_zscore(work["ema_cbot_basis"], window=260)
    work["regime"] = classify_basis_regime(work["basis_z"], high_threshold=high_threshold, low_threshold=low_threshold)
    rows: list[dict[str, Any]] = []
    for horizon in horizons:
        h = int(horizon)
        future_basis = work["ema_cbot_basis"].shift(-h)
        future_ema = work["ema_price_adjusted"].shift(-h)
        future_cbot = work["cbot_eur_t"].shift(-h)
        current_ema = work["ema_price_adjusted"]
        current_cbot = work["cbot_eur_t"]
        work[f"basis_change_h{h}"] = future_basis - work["ema_cbot_basis"]
        work[f"ema_return_h{h}"] = np.log(future_ema / current_ema)
        work[f"cbot_return_h{h}"] = np.log(future_cbot / current_cbot)
        work[f"relative_ema_minus_cbot_h{h}"] = work[f"ema_return_h{h}"] - work[f"cbot_return_h{h}"]
        for regime in ("high", "low", "neutral"):
            subset = work[work["regime"].eq(regime)].copy()
            subset = subset.dropna(
                subset=[
                    "ema_cbot_basis",
                    "basis_z",
                    f"basis_change_h{h}",
                    f"ema_return_h{h}",
                    f"cbot_return_h{h}",
                ]
            )
            rows.append(_summarize_regime(subset, regime=regime, horizon=h))
    return pd.DataFrame(rows)


def classify_basis_regime(
    basis_z: pd.Series,
    *,
    high_threshold: float,
    low_threshold: float,
) -> pd.Series:
    """Classify basis z-score into high/low/neutral/other regimes."""
    z = pd.to_numeric(basis_z, errors="coerce")
    regime = pd.Series("other", index=z.index, dtype=object)
    regime.loc[z >= high_threshold] = "high"
    regime.loc[z <= low_threshold] = "low"
    regime.loc[z.abs() <= 1.0] = "neutral"
    regime.loc[z.isna()] = "missing"
    return regime


def basis_distribution(frame: pd.DataFrame) -> dict[str, Any]:
    """Summarize basis level and z-score distribution."""
    basis = pd.to_numeric(frame.get("ema_cbot_basis", pd.Series(dtype=float)), errors="coerce").dropna()
    z = pd.to_numeric(frame.get("basis_z", pd.Series(dtype=float)), errors="coerce").dropna()
    return {
        "basis_n": int(len(basis)),
        "basis_mean": _json_float(basis.mean()) if len(basis) else None,
        "basis_std": _json_float(basis.std()) if len(basis) else None,
        "basis_p05": _json_float(basis.quantile(0.05)) if len(basis) else None,
        "basis_p50": _json_float(basis.quantile(0.50)) if len(basis) else None,
        "basis_p95": _json_float(basis.quantile(0.95)) if len(basis) else None,
        "basis_z_n": int(len(z)),
        "basis_z_high_share": _json_float((z >= 2.0).mean()) if len(z) else None,
        "basis_z_low_share": _json_float((z <= -2.0).mean()) if len(z) else None,
        "basis_z_neutral_share": _json_float((z.abs() <= 1.0).mean()) if len(z) else None,
    }


def decide_basis_signal(regime_table: pd.DataFrame) -> dict[str, Any]:
    """Decide whether basis extremes show mean reversion."""
    high = _row(regime_table, "high", 20)
    low = _row(regime_table, "low", 20)
    high_rate = _safe_float(high.get("basis_reversion_rate")) if high is not None else math.nan
    low_rate = _safe_float(low.get("basis_reversion_rate")) if low is not None else math.nan
    high_change = _safe_float(high.get("basis_change_mean")) if high is not None else math.nan
    low_change = _safe_float(low.get("basis_change_mean")) if low is not None else math.nan
    high_n = int(high.get("n", 0)) if high is not None else 0
    low_n = int(low.get("n", 0)) if low is not None else 0
    verdict = "BASIS_INCONCLUSIVE"
    if high_n >= 20 and low_n >= 20 and high_rate > 0.55 and low_rate > 0.55 and high_change < 0 and low_change > 0:
        verdict = "BASIS_MEAN_REVERSION_CONFIRMED"
    elif (high_n >= 20 and high_rate > 0.55 and high_change < 0) or (low_n >= 20 and low_rate > 0.55 and low_change > 0):
        verdict = "BASIS_MEAN_REVERSION_PARTIAL"
    return {
        "verdict": verdict,
        "horizon_reference": 20,
        "high_basis": _row_summary(high),
        "low_basis": _row_summary(low),
        "interpretation": _decision_text(verdict),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    """Render a Markdown basis study report."""
    dist = payload["basis_distribution"]
    decision = payload["decision"]
    lines = [
        "# EMA Basis Study",
        "",
        f"> {payload['source_quality_note']}",
        "",
        "## Dataset",
        "",
        f"- Rows: {payload['n_rows']}",
        f"- Period: {payload['date_start']} -> {payload['date_end']}",
        f"- Basis z-score window: {payload['z_window']} days",
        "",
        "## Basis Distribution",
        "",
        f"- Mean: {_fmt(dist.get('basis_mean'))} EUR/t",
        f"- Std: {_fmt(dist.get('basis_std'))} EUR/t",
        f"- P05/P50/P95: {_fmt(dist.get('basis_p05'))} / {_fmt(dist.get('basis_p50'))} / {_fmt(dist.get('basis_p95'))} EUR/t",
        f"- High z>=2 share: {_pct(dist.get('basis_z_high_share'))}",
        f"- Low z<=-2 share: {_pct(dist.get('basis_z_low_share'))}",
        "",
        "## Mean Reversion By Regime",
        "",
        *_regime_lines(payload["regime_results"]),
        "",
        "## Decision",
        "",
        f"- Verdict: `{decision.get('verdict')}`",
        f"- {decision.get('interpretation')}",
        "",
    ]
    return "\n".join(lines)


def _summarize_regime(subset: pd.DataFrame, *, regime: str, horizon: int) -> dict[str, Any]:
    basis_change = pd.to_numeric(subset[f"basis_change_h{horizon}"], errors="coerce")
    ema_return = pd.to_numeric(subset[f"ema_return_h{horizon}"], errors="coerce")
    cbot_return = pd.to_numeric(subset[f"cbot_return_h{horizon}"], errors="coerce")
    relative = pd.to_numeric(subset[f"relative_ema_minus_cbot_h{horizon}"], errors="coerce")
    if regime == "high":
        reversion = basis_change < 0
    elif regime == "low":
        reversion = basis_change > 0
    else:
        reversion = basis_change.abs() < pd.to_numeric(subset["ema_cbot_basis"], errors="coerce").abs()
    return {
        "regime": regime,
        "horizon": int(horizon),
        "n": int(len(subset)),
        "basis_z_mean": _json_float(subset["basis_z"].mean()) if len(subset) else None,
        "basis_change_mean": _json_float(basis_change.mean()) if len(subset) else None,
        "basis_change_median": _json_float(basis_change.median()) if len(subset) else None,
        "basis_reversion_rate": _json_float(reversion.mean()) if len(subset) else None,
        "ema_return_mean": _json_float(ema_return.mean()) if len(subset) else None,
        "cbot_return_mean": _json_float(cbot_return.mean()) if len(subset) else None,
        "relative_ema_minus_cbot_mean": _json_float(relative.mean()) if len(subset) else None,
    }


def _row(table: pd.DataFrame, regime: str, horizon: int) -> pd.Series | None:
    row = table[table["regime"].eq(regime) & table["horizon"].eq(int(horizon))]
    if row.empty:
        return None
    return row.iloc[0]


def _row_summary(row: pd.Series | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {str(key): _json_ready(value) for key, value in row.to_dict().items()}


def _decision_text(verdict: str) -> str:
    if verdict == "BASIS_MEAN_REVERSION_CONFIRMED":
        return "High and low basis extremes both tend to revert at the reference horizon."
    if verdict == "BASIS_MEAN_REVERSION_PARTIAL":
        return "Only one side of the basis distribution shows usable mean reversion."
    return "Basis extremes are too sparse or do not revert reliably enough yet."


def _regime_lines(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return ["- No regime rows available."]
    out: list[str] = []
    for row in rows:
        out.append(
            f"- {row['regime']} H{row['horizon']}: n={row['n']}, "
            f"basis change mean={_fmt(row.get('basis_change_mean'))}, "
            f"reversion={_pct(row.get('basis_reversion_rate'))}, "
            f"EMA-CBOT return mean={_fmt(row.get('relative_ema_minus_cbot_mean'))}"
        )
    return out


def _date_min(frame: pd.DataFrame) -> str | None:
    if frame.empty or "Date" not in frame:
        return None
    return frame["Date"].min().date().isoformat()


def _date_max(frame: pd.DataFrame) -> str | None:
    if frame.empty or "Date" not in frame:
        return None
    return frame["Date"].max().date().isoformat()


def _fmt(value: Any) -> str:
    number = _safe_float(value)
    return "N/A" if not math.isfinite(number) else f"{number:.4f}"


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
    report = run_ema_basis_study()
    print(json.dumps(_json_ready(report["decision"]), indent=2, ensure_ascii=False))
