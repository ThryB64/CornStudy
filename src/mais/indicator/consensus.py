"""Multi-horizon consensus for the maize direction indicator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.utils import write_parquet

ZONE_MAP: dict[str, list[int]] = {
    "Z1_court": [1, 2, 3, 4, 5, 7],
    "Z2_sous_mens": [10, 12, 15],
    "Z3_mensuel": [18, 20, 22, 25, 28, 30],
    "Z4_bimensuel": [35, 40, 45],
    "Z5_trimestr": [50, 60, 70],
    "Z6_long": [80, 90, 100],
}

DEFAULT_MAX_DATE = pd.Timestamp("2022-12-31")
DEFAULT_OUTPUT_DIR = ARTEFACTS_DIR / "indicator"
DEFAULT_MODEL_ZOO_DIR = ARTEFACTS_DIR / "model_zoo"
DEFAULT_BASELINE_TOP20 = 0.74273


def vote_simple(
    p_up_by_horizon: dict[int, float | None],
    bullish_threshold: float = 0.50,
) -> dict[str, float | int]:
    """Simple vote across available horizons."""
    probs = _clean_probs(p_up_by_horizon)
    if not probs:
        return {"bullish_ratio": 0.0, "bearish_ratio": 0.0, "neutral_ratio": 1.0, "n_horizons": 0}

    bullish = sum(p > bullish_threshold for p in probs.values())
    bearish = sum(p < 1.0 - bullish_threshold for p in probs.values())
    neutral = len(probs) - bullish - bearish
    n = len(probs)
    return {
        "bullish_ratio": float(bullish / n),
        "bearish_ratio": float(bearish / n),
        "neutral_ratio": float(neutral / n),
        "n_horizons": int(n),
    }


def vote_pondere(
    p_up_by_horizon: dict[int, float | None],
    auc_weights: dict[int, float],
) -> float:
    """AUC-weighted global P(up), using only provided train/validation weights."""
    probs = _clean_probs(p_up_by_horizon)
    if not probs:
        return 0.5

    weights = []
    values = []
    for h, p_up in probs.items():
        weight = float(auc_weights.get(h, 0.5))
        if not np.isfinite(weight) or weight <= 0.0:
            weight = 0.5
        weights.append(weight)
        values.append(p_up)
    return float(np.average(values, weights=weights))


def zone_labels(
    p_up_by_horizon: dict[int, float | None],
    zone_map: dict[str, list[int]] = ZONE_MAP,
    bullish_prob_threshold: float = 0.58,
    bullish_agreement_threshold: float = 0.65,
) -> dict[str, str]:
    """Label each horizon zone as BULLISH, BEARISH, NEUTRAL or UNKNOWN."""
    probs = _clean_probs(p_up_by_horizon)
    labels: dict[str, str] = {}
    for zone, horizons in zone_map.items():
        vals = [probs[h] for h in horizons if h in probs]
        if not vals:
            labels[zone] = "UNKNOWN"
            continue
        mean_p = float(np.mean(vals))
        bull_share = float(np.mean([v >= bullish_prob_threshold for v in vals]))
        bear_share = float(np.mean([v <= 1.0 - bullish_prob_threshold for v in vals]))
        if mean_p >= bullish_prob_threshold and bull_share >= bullish_agreement_threshold:
            labels[zone] = "BULLISH"
        elif mean_p <= 1.0 - bullish_prob_threshold and bear_share >= bullish_agreement_threshold:
            labels[zone] = "BEARISH"
        else:
            labels[zone] = "NEUTRAL"
    return labels


def horizon_slope(p_up_by_horizon: dict[int, float | None]) -> float:
    """Linear slope of P(up) as a function of horizon."""
    probs = _clean_probs(p_up_by_horizon)
    if len(probs) < 2:
        return 0.0
    x = np.asarray(sorted(probs), dtype=float)
    y = np.asarray([probs[int(h)] for h in x], dtype=float)
    return float(np.polyfit(x, y, deg=1)[0])


def local_stability(
    p_up_by_horizon: dict[int, float | None],
    main_horizon: int = 20,
    local_window: list[int] | None = None,
    threshold: float = 0.55,
) -> float:
    """Share of local horizons agreeing with the main horizon direction."""
    probs = _clean_probs(p_up_by_horizon)
    if not probs:
        return 0.0
    if main_horizon not in probs:
        main_horizon = min(probs, key=lambda h: abs(h - main_horizon))

    window = local_window if local_window is not None else [
        h for h in probs if abs(h - main_horizon) <= 5
    ]
    window = [h for h in window if h in probs]
    if not window:
        return 1.0

    main_dir = _direction_from_prob(probs[main_horizon], threshold)
    if main_dir == 0:
        return float(np.mean([_direction_from_prob(probs[h], threshold) == 0 for h in window]))
    return float(np.mean([_direction_from_prob(probs[h], threshold) == main_dir for h in window]))


def horizon_disagreement(p_up_by_horizon: dict[int, float | None]) -> float:
    """Standard deviation of multi-horizon probabilities."""
    probs = _clean_probs(p_up_by_horizon)
    if len(probs) < 2:
        return 0.0
    return float(np.std(list(probs.values()), ddof=0))


def compute_consensus_score(
    p_up_by_horizon: dict[int, float | None],
    auc_weights: dict[int, float],
    main_horizon: int = 20,
) -> dict[str, Any]:
    """Unified consensus score and meta-features for downstream stacking."""
    probs = _clean_probs(p_up_by_horizon)
    vs = vote_simple(probs)
    weighted_p = vote_pondere(probs, auc_weights)
    stability = local_stability(probs, main_horizon=main_horizon)
    disagreement = horizon_disagreement(probs)
    slope = horizon_slope(probs)

    bullish_consensus = float(weighted_p)
    bearish_consensus = float(1.0 - weighted_p)
    directional_strength = float(max(bullish_consensus, bearish_consensus))
    directional_score = float(np.clip((directional_strength - 0.5) / 0.5, 0.0, 1.0))
    slope_norm = float(np.clip((slope + 0.02) / 0.04, 0.0, 1.0))

    score = (
        0.40 * directional_score
        + 0.25 * stability
        + 0.20 * max(0.0, 1.0 - disagreement / 0.08)
        + 0.15 * slope_norm
    )
    direction = "NEUTRAL"
    if weighted_p > 0.5:
        direction = "BULLISH"
    elif weighted_p < 0.5:
        direction = "BEARISH"

    labels = zone_labels(probs)
    return {
        "consensus_score": float(np.clip(score, 0.0, 1.0)),
        "consensus_direction": direction,
        "disagreement": float(disagreement),
        "bullish_consensus": bullish_consensus,
        "bearish_consensus": bearish_consensus,
        "directional_strength": directional_strength,
        "local_stability": float(stability),
        "slope": float(slope),
        "slope_normalized": slope_norm,
        "zone_labels": labels,
        "bullish_ratio": float(vs["bullish_ratio"]),
        "bearish_ratio": float(vs["bearish_ratio"]),
        "neutral_ratio": float(vs["neutral_ratio"]),
        "n_horizons": int(vs["n_horizons"]),
        "meta_directional_score": directional_score,
        "meta_bullish_consensus": bullish_consensus,
        "meta_local_stability": float(stability),
        "meta_disagreement": float(disagreement),
        "meta_slope": float(slope),
    }


def decide_signal_with_consensus(
    p_up_by_horizon: dict[int, float | None],
    confidence: float,
    auc_weights: dict[int, float],
    main_horizon: int = 20,
    confidence_threshold: float = 0.45694,
    bullish_prob_threshold: float = 0.60,
    bearish_prob_threshold: float = 0.60,
    min_prob_gap: float = 0.15,
    neutral_max_gap: float = 0.10,
    disagreement_threshold: float = 0.08,
) -> dict[str, Any]:
    """Apply the V3 decision rule with the mandatory disagreement guardrail."""
    consensus = compute_consensus_score(
        p_up_by_horizon,
        auc_weights=auc_weights,
        main_horizon=main_horizon,
    )
    probs = _clean_probs(p_up_by_horizon)
    label = "UNCERTAIN"
    if probs and consensus["disagreement"] <= disagreement_threshold and confidence >= confidence_threshold:
        mean_p = float(np.mean(list(probs.values())))
        gap = abs(2.0 * mean_p - 1.0)
        if mean_p > bullish_prob_threshold and gap > min_prob_gap:
            label = "BULLISH"
        elif mean_p < (1.0 - bearish_prob_threshold) and gap > min_prob_gap:
            label = "BEARISH"
        elif gap < neutral_max_gap:
            label = "NEUTRAL"

    force = "medium"
    if consensus["consensus_score"] < 0.55:
        force = "weak"
    if consensus["consensus_score"] > 0.75 and confidence > 0.70:
        force = "strong"
    return {"label": label, "force": force, "consensus": consensus}


def run_consensus_from_model_zoo(
    model_zoo_dir: Path = DEFAULT_MODEL_ZOO_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    max_date: pd.Timestamp | str = DEFAULT_MAX_DATE,
    main_horizon: int | None = None,
    selected_models: list[str] | None = None,
    baseline_top20: float = DEFAULT_BASELINE_TOP20,
) -> pd.DataFrame:
    """Build V3-04 consensus artefacts from V3-03 OOF predictions."""
    max_ts = pd.Timestamp(max_date)
    output_dir.mkdir(parents=True, exist_ok=True)
    oof_path = model_zoo_dir / "model_zoo_oof_predictions.parquet"
    results_path = model_zoo_dir / "model_zoo_results.parquet"
    if not oof_path.exists():
        raise FileNotFoundError(f"Missing V3-03 OOF predictions: {oof_path}")

    oof = pd.read_parquet(oof_path)
    oof["Date"] = pd.to_datetime(oof["Date"])
    oof = oof[oof["Date"] <= max_ts].copy()
    if selected_models is not None:
        kept = oof[oof["model"].isin(selected_models)].copy()
        if not kept.empty:
            oof = kept

    results = pd.read_parquet(results_path) if results_path.exists() else pd.DataFrame()
    model_source = _select_consensus_model_source(results)
    if selected_models is None and model_source:
        parts = []
        for horizon, model_name in model_source.items():
            part = oof[(oof["horizon"] == horizon) & (oof["model"] == model_name)].copy()
            if not part.empty:
                parts.append(part)
        if parts:
            oof = pd.concat(parts, ignore_index=True)

    auc_weights = _auc_weights_from_results(results)
    available_horizons = sorted(int(h) for h in oof["horizon"].dropna().unique())
    if main_horizon is None:
        main_horizon = 40 if 40 in available_horizons else (available_horizons[0] if available_horizons else 20)

    agg = (
        oof.groupby(["Date", "horizon"], as_index=False)
        .agg(p_up=("p_up", "mean"), y_true_up=("y_true_up", "first"))
        .sort_values(["Date", "horizon"])
    )
    records: list[dict[str, Any]] = []
    for date, sub in agg.groupby("Date"):
        probs = {int(row.horizon): float(row.p_up) for row in sub.itertuples()}
        consensus = compute_consensus_score(probs, auc_weights=auc_weights, main_horizon=main_horizon)
        label = _label_from_consensus(consensus, disagreement_threshold=0.08)
        row: dict[str, Any] = {
            "Date": pd.Timestamp(date),
            "y_true_up": int(sub["y_true_up"].iloc[0]),
            "label": label,
            "pred_up": int(consensus["bullish_consensus"] >= 0.5),
            "main_horizon": int(main_horizon),
        }
        row.update(_flatten_consensus(consensus))
        for h, p_up in probs.items():
            row[f"p_up_h{h}"] = p_up
        records.append(row)

    consensus_df = pd.DataFrame(records).sort_values("Date").reset_index(drop=True)
    thresholds = _calibrate_thresholds(consensus_df, baseline_top20=baseline_top20)
    thresholds["model_source"] = {
        str(k): v for k, v in model_source.items()
    } if selected_models is None else {"explicit_models": ",".join(selected_models)}
    meta_df = _metafeatures(consensus_df)

    write_parquet(consensus_df, output_dir / "consensus_results.parquet")
    write_parquet(meta_df, output_dir / "consensus_metafeatures.parquet")
    _write_threshold_yaml(thresholds, output_dir / "consensus_seuils_calibration.yaml")
    (output_dir / "consensus_report.txt").write_text(
        _report_text(consensus_df, thresholds, available_horizons, baseline_top20),
        encoding="utf-8",
    )
    return consensus_df


def _clean_probs(p_up_by_horizon: dict[int, float | None]) -> dict[int, float]:
    probs: dict[int, float] = {}
    for horizon, value in p_up_by_horizon.items():
        if value is None:
            continue
        p = float(value)
        if np.isfinite(p):
            probs[int(horizon)] = float(np.clip(p, 0.0, 1.0))
    return probs


def _direction_from_prob(p_up: float, threshold: float) -> int:
    if p_up >= threshold:
        return 1
    if p_up <= 1.0 - threshold:
        return -1
    return 0


def _auc_weights_from_results(results: pd.DataFrame) -> dict[int, float]:
    if results.empty or "horizon" not in results.columns or "auc" not in results.columns:
        return {}
    valid = results[pd.to_numeric(results["auc"], errors="coerce").notna()].copy()
    if valid.empty:
        return {}
    return {
        int(h): float(np.clip(sub["auc"].astype(float).mean(), 0.5, 1.0))
        for h, sub in valid.groupby("horizon")
    }


def _select_consensus_model_source(results: pd.DataFrame) -> dict[int, str]:
    if results.empty or "horizon" not in results.columns or "model" not in results.columns:
        return {}
    score_cols = [c for c in ["da_top20pct", "da", "auc"] if c in results.columns]
    if not score_cols:
        return {}
    candidates = results[~results["model"].isin(["vote_majority", "avg_proba"])].copy()
    if candidates.empty:
        candidates = results.copy()
    for col in score_cols:
        candidates[col] = pd.to_numeric(candidates[col], errors="coerce")
    source: dict[int, str] = {}
    for horizon, sub in candidates.groupby("horizon"):
        ordered = sub.sort_values(score_cols, ascending=[False] * len(score_cols))
        source[int(horizon)] = str(ordered.iloc[0]["model"])
    return source


def _flatten_consensus(consensus: dict[str, Any]) -> dict[str, Any]:
    flat = {k: v for k, v in consensus.items() if k != "zone_labels"}
    for zone, label in consensus["zone_labels"].items():
        flat[f"zone_{zone}_label"] = label
    return flat


def _metafeatures(consensus_df: pd.DataFrame) -> pd.DataFrame:
    keep = [
        "Date",
        "consensus_score",
        "disagreement",
        "bullish_ratio",
        "bearish_ratio",
        "local_stability",
        "slope",
        "meta_directional_score",
        "meta_bullish_consensus",
        "meta_local_stability",
        "meta_disagreement",
        "meta_slope",
    ]
    zone_cols = [c for c in consensus_df.columns if c.startswith("zone_") and c.endswith("_label")]
    return consensus_df[[c for c in keep + zone_cols if c in consensus_df.columns]].copy()


def _label_from_consensus(consensus: dict[str, Any], disagreement_threshold: float) -> str:
    if consensus["disagreement"] > disagreement_threshold:
        return "UNCERTAIN"
    if consensus["bullish_consensus"] >= 0.60:
        return "BULLISH"
    if consensus["bearish_consensus"] >= 0.60:
        return "BEARISH"
    return "NEUTRAL"


def _calibrate_thresholds(consensus_df: pd.DataFrame, baseline_top20: float) -> dict[str, Any]:
    if consensus_df.empty:
        return {
            "disagreement_threshold": 0.08,
            "consensus_threshold": 0.55,
            "signals_per_year": 0.0,
            "da_top20pct": None,
            "baseline_top20": baseline_top20,
            "top20_regression_points": None,
        }

    chosen: dict[str, Any] | None = None
    for dis_threshold in [0.06, 0.08, 0.10]:
        for consensus_threshold in [0.50, 0.55, 0.60]:
            selected = (
                (consensus_df["disagreement"] <= dis_threshold)
                & (consensus_df["consensus_score"] >= consensus_threshold)
                & (consensus_df["label"] != "UNCERTAIN")
            )
            metrics = _metrics(consensus_df, selected)
            row = {
                "disagreement_threshold": dis_threshold,
                "consensus_threshold": consensus_threshold,
                **metrics,
                "baseline_top20": baseline_top20,
                "top20_regression_points": (
                    None if metrics["da_top20pct"] is None else baseline_top20 - metrics["da_top20pct"]
                ),
            }
            if chosen is None:
                chosen = row
                continue
            da_ok = row["da_top20pct"] is not None and row["da_top20pct"] >= baseline_top20 - 0.01
            chosen_da_ok = (
                chosen["da_top20pct"] is not None and chosen["da_top20pct"] >= baseline_top20 - 0.01
            )
            if da_ok != chosen_da_ok:
                if da_ok:
                    chosen = row
                continue
            if row["signals_per_year"] > chosen["signals_per_year"]:
                chosen = row
    return chosen or {}


def _metrics(consensus_df: pd.DataFrame, selected: pd.Series) -> dict[str, float | None]:
    dates = pd.to_datetime(consensus_df["Date"])
    years = max((dates.max() - dates.min()).days / 365.25, 1.0)
    selected_df = consensus_df[selected].copy()
    signals_per_year = float(len(selected_df) / years)
    if selected_df.empty:
        da = None
    else:
        da = float((selected_df["pred_up"].astype(int) == selected_df["y_true_up"].astype(int)).mean())

    conf = consensus_df["directional_strength"].sub(0.5).abs()
    top20_cut = float(conf.quantile(0.80))
    top20 = consensus_df[conf >= top20_cut]
    da_top20 = None
    if not top20.empty:
        da_top20 = float((top20["pred_up"].astype(int) == top20["y_true_up"].astype(int)).mean())
    return {"signals_per_year": signals_per_year, "da_selected": da, "da_top20pct": da_top20}


def _write_threshold_yaml(payload: dict[str, Any], path: Path) -> None:
    lines = ["# V3-04 consensus thresholds calibrated on validation OOF data"]
    for key, value in payload.items():
        if value is None:
            lines.append(f"{key}: null")
        elif isinstance(value, dict):
            lines.append(f"{key}:")
            for nested_key, nested_value in value.items():
                lines.append(f"  {nested_key}: {nested_value}")
        elif isinstance(value, float):
            lines.append(f"{key}: {value:.6f}")
        else:
            lines.append(f"{key}: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _report_text(
    consensus_df: pd.DataFrame,
    thresholds: dict[str, Any],
    horizons: list[int],
    baseline_top20: float,
) -> str:
    max_date = pd.to_datetime(consensus_df["Date"]).max().date() if not consensus_df.empty else "N/A"
    lines = [
        "Consensus multi-horizon V3-04",
        "",
        f"Horizons disponibles dans les OOF V3-03 : {horizons}",
        f"Max date utilisee : {max_date}",
        f"Seuils retenus : disagreement={thresholds.get('disagreement_threshold')}, "
        f"consensus={thresholds.get('consensus_threshold')}",
        f"Signaux/an : {thresholds.get('signals_per_year')}",
        f"DA top20 consensus : {thresholds.get('da_top20pct')}",
        f"DA top20 reference V3-03 : {baseline_top20}",
        f"Regression top20 (points) : {thresholds.get('top20_regression_points')}",
        f"Source modele par horizon : {thresholds.get('model_source')}",
    ]
    if len(horizons) < 2:
        lines.extend(
            [
                "",
                "Reserve : les artefacts V3-03 disponibles contiennent un seul horizon.",
                "Le module reste multi-horizon, mais le desaccord mesure sur cet export est donc nul.",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    run_consensus_from_model_zoo()


if __name__ == "__main__":
    main()
