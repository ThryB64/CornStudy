"""Consensus V2 using true multi-horizon OOF probabilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score

from mais.research.multi_horizon_oof import align_multi_horizon_oof


def build_consensus_v2(
    oof: pd.DataFrame,
    *,
    horizons: list[int] | tuple[int, ...],
    output_path: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build consensus probabilities, calibrate disagreement threshold, save metrics."""
    aligned = align_multi_horizon_oof(oof, horizons)
    if aligned.empty:
        payload = {"verdict": "REJETÉ", "reason": "no aligned OOF", "threshold_calibrated": None}
        return pd.DataFrame(), payload
    wide = aligned.pivot(index="Date", columns="horizon", values="p_up").sort_index()
    truth = aligned.pivot(index="Date", columns="horizon", values="y_true_up").sort_index()
    consensus = pd.DataFrame({"Date": wide.index})
    consensus["consensus_proba"] = wide.mean(axis=1).to_numpy()
    consensus["disagreement"] = wide.std(axis=1).to_numpy()
    consensus["actual_up_majority"] = (truth.mean(axis=1) >= 0.5).astype(int).to_numpy()
    consensus["pred_up"] = (consensus["consensus_proba"] >= 0.5).astype(int)
    threshold, curve = calibrate_disagreement_threshold(consensus)
    consensus["signal"] = np.where(
        consensus["disagreement"] > threshold,
        "UNCERTAIN",
        np.where(consensus["consensus_proba"] >= 0.5, "BULLISH", "BEARISH"),
    )
    metrics = summarize_consensus(consensus, threshold=threshold, threshold_curve=curve)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    return consensus, metrics


def calibrate_disagreement_threshold(consensus: pd.DataFrame) -> tuple[float, list[dict[str, float]]]:
    """Search threshold on OOF instead of hard-coding a constant."""
    thresholds = np.round(np.arange(0.02, 0.151, 0.01), 3)
    rows: list[dict[str, float]] = []
    best_threshold = float(thresholds[0])
    best_score = -np.inf
    for threshold in thresholds:
        actionable = consensus["disagreement"] <= threshold
        if actionable.sum() == 0:
            da = np.nan
            prop_uncertain = 1.0
            score = -np.inf
        else:
            da = float(accuracy_score(consensus.loc[actionable, "actual_up_majority"], consensus.loc[actionable, "pred_up"]))
            prop_uncertain = float((~actionable).mean())
            actionability = 1.0 - prop_uncertain
            score = da * actionability if 0.05 <= prop_uncertain <= 0.60 else da * actionability * 0.5
        rows.append({"threshold": float(threshold), "da_actionable": da, "proportion_uncertain": prop_uncertain, "score": float(score)})
        if score > best_score:
            best_score = score
            best_threshold = float(threshold)
    return best_threshold, rows


def summarize_consensus(
    consensus: pd.DataFrame,
    *,
    threshold: float,
    threshold_curve: list[dict[str, float]],
) -> dict[str, Any]:
    actionable = consensus["signal"] != "UNCERTAIN"
    if actionable.any():
        da_actionable = float(accuracy_score(consensus.loc[actionable, "actual_up_majority"], consensus.loc[actionable, "pred_up"]))
    else:
        da_actionable = None
    disagreement = consensus["disagreement"]
    unique_values = int(disagreement.round(8).nunique())
    flip_rate = _flip_rate(consensus["signal"])
    prop_uncertain = float((~actionable).mean())
    verdict = "ALPHA" if da_actionable is not None and da_actionable >= 0.56 else (
        "FILTRE" if flip_rate < 0.15 and prop_uncertain <= 0.60 else (
            "PRUDENCE" if 0.05 <= prop_uncertain <= 0.60 else "REJETÉ"
        )
    )
    return {
        "verdict": verdict,
        "threshold_calibrated": float(threshold),
        "threshold_curve": threshold_curve,
        "n_obs": int(len(consensus)),
        "disagreement_std": float(disagreement.std()),
        "disagreement_unique_values": unique_values,
        "proportion_uncertain": prop_uncertain,
        "da_actionable": da_actionable,
        "flip_rate": flip_rate,
    }


def _flip_rate(signal: pd.Series) -> float:
    actionable = signal[signal != "UNCERTAIN"].reset_index(drop=True)
    if len(actionable) < 2:
        return 0.0
    return float((actionable != actionable.shift(1)).iloc[1:].mean())
