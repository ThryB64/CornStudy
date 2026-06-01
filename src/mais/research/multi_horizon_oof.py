"""Generate real multi-horizon OOF predictions for consensus V2."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from mais.research.canonical_benchmark import DEFAULT_HORIZONS, run_model_oof

DEFAULT_CONSENSUS_MODELS = ["extratrees", "histgb", "lgbm"]


def generate_multi_horizon_oof(
    features: pd.DataFrame,
    targets: pd.DataFrame,
    *,
    horizons: list[int] | tuple[int, ...] = DEFAULT_HORIZONS,
    models: list[str] | tuple[str, ...] = DEFAULT_CONSENSUS_MODELS,
    split_name: str = "crop_year_walk_forward",
    output_path: Path | None = None,
) -> pd.DataFrame:
    """Generate OOF probabilities for each model and horizon."""
    frames: list[pd.DataFrame] = []
    for horizon in horizons:
        for model_name in models:
            oof, n_features = run_model_oof(
                features,
                targets,
                horizon=int(horizon),
                model_name=str(model_name),
                split_name=split_name,
            )
            if oof.empty:
                continue
            keep = oof[
                [
                    "Date",
                    "horizon",
                    "model",
                    "split",
                    "fold",
                    "fold_label",
                    "y_true_up",
                    "p_up",
                    "pred_up",
                ]
            ].copy()
            keep["n_features"] = int(n_features)
            frames.append(keep)
    result = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.to_parquet(output_path, index=False)
    return result


def align_multi_horizon_oof(oof: pd.DataFrame, horizons: list[int] | tuple[int, ...]) -> pd.DataFrame:
    """Average models per horizon and retain dates common to all horizons."""
    if oof.empty:
        return pd.DataFrame()
    avg = (
        oof.groupby(["Date", "horizon"], as_index=False)
        .agg(p_up=("p_up", "mean"), y_true_up=("y_true_up", "first"))
        .sort_values(["Date", "horizon"])
    )
    expected = {int(h) for h in horizons}
    counts = avg.groupby("Date")["horizon"].apply(lambda s: set(s.astype(int)))
    common_dates = counts[counts.map(lambda got: expected.issubset(got))].index
    return avg[avg["Date"].isin(common_dates)].reset_index(drop=True)
