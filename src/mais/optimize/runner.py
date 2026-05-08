"""Train one or more models with walk-forward (Optuna optional)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from mais.models import ModelRegistry
from mais.paths import (
    ARTEFACTS_DIR,
    FEATURES_PARQUET,
    PREDICTIONS_DIR,
    TARGETS_PARQUET,
    ensure_dirs,
)
from mais.utils import get_logger, read_parquet, write_parquet
from mais.walkforward import walk_forward_run

log = get_logger("mais.optimize.runner")


def run_training(
    model: str | None = None,
    all_models: bool = False,
    target: str = "y_logret_h20",
    n_trials: int = 20,
) -> str:
    ensure_dirs()
    if not FEATURES_PARQUET.exists() or not TARGETS_PARQUET.exists():
        return ("Missing features.parquet or targets.parquet. "
                "Run `mais features && mais targets` first.")

    features = read_parquet(FEATURES_PARQUET)
    targets = read_parquet(TARGETS_PARQUET)

    horizon = _horizon_from_target(target)

    names = ModelRegistry.list() if all_models else [model]
    summary_rows = []
    for name in names:
        try:
            adapter = ModelRegistry.get(name)
        except KeyError:
            log.warning("model_not_in_registry", name=name)
            continue
        try:
            run = walk_forward_run(adapter, features, targets, target, horizon)
        except NotImplementedError as e:
            log.info("model_skipped_legacy", name=name, reason=str(e))
            summary_rows.append({"model": name, "status": "stub", "n_folds": 0,
                                  "rmse_mean": None, "da_mean": None})
            continue
        except Exception as e:
            log.warning("model_failed", name=name, error=str(e))
            summary_rows.append({"model": name, "status": "fail", "n_folds": 0,
                                  "rmse_mean": None, "da_mean": None})
            continue

        # Save predictions and per-fold metrics
        out_dir = PREDICTIONS_DIR / target
        out_dir.mkdir(parents=True, exist_ok=True)
        write_parquet(run.predictions, out_dir / f"{name}.parquet")
        run.metrics_per_fold.to_csv(out_dir / f"{name}_metrics.csv", index=False)

        summary_rows.append({
            "model": name, "status": "ok", "n_folds": len(run.metrics_per_fold),
            "rmse_mean": run.metrics_per_fold["rmse"].mean() if not run.metrics_per_fold.empty else None,
            "da_mean": run.metrics_per_fold["directional_accuracy"].mean() if not run.metrics_per_fold.empty else None,
        })
        log.info("model_trained", name=name, n_folds=len(run.metrics_per_fold))

    summary_df = pd.DataFrame(summary_rows).sort_values("rmse_mean", na_position="last")
    summary_df.to_csv(ARTEFACTS_DIR / "training_summary.csv", index=False)
    return summary_df.to_string(index=False)


def _horizon_from_target(target: str) -> int:
    """Extract H from a target name like ``y_logret_h20``."""
    import re
    m = re.search(r"h(\d+)", target)
    return int(m.group(1)) if m else 1
