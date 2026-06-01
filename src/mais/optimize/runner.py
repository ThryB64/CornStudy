"""Train one or more models with walk-forward (Optuna optional)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error

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


def optimize_lgbm_for_study(
    factors: pd.DataFrame,
    targets: pd.DataFrame,
    *,
    out_dir: Path,
    horizons: tuple[int, ...] = (5, 10, 20, 30),
    n_trials: int = 12,
    max_eval_splits: int = 3,
    random_state: int = 42,
) -> pd.DataFrame:
    """Optimize LightGBM on study walk-forward splits and log honest deltas.

    This is intentionally off by default in ``build_professional_study`` because
    Optuna can make the study much slower. The result compares optimized params
    against the local default LightGBM configuration on the same factors,
    horizons and walk-forward protocol.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "optuna_lgbm_results.parquet"

    try:
        import lightgbm as lgb
        import optuna
    except ImportError as exc:
        result = pd.DataFrame(
            [{
                "status": "skipped_missing_dependency",
                "error": str(exc),
                "model": "lgbm_optuna_factors",
                "n_trials": 0,
            }]
        )
        write_parquet(result, out_path)
        return result

    fac = _normalize_dates(factors)
    tar = _normalize_dates(targets)
    factor_cols = [c for c in fac.columns if c != "Date" and pd.api.types.is_numeric_dtype(fac[c])]
    merged = fac.merge(tar, on="Date", how="inner").sort_values("Date").reset_index(drop=True)

    rows: list[dict[str, Any]] = []
    default_params = _default_lgbm_params(random_state=random_state)
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    for horizon in horizons:
        target_col = f"y_logret_h{horizon}"
        if target_col not in merged.columns:
            rows.append(_optuna_skip_row(horizon, target_col, "missing_target"))
            continue

        work = merged[["Date", target_col, *factor_cols]].dropna(subset=[target_col]).reset_index(drop=True)
        splits = _study_walk_splits(len(work), horizon=horizon)
        if not splits:
            rows.append(_optuna_skip_row(horizon, target_col, "no_walk_forward_splits"))
            continue

        eval_splits = splits[-max_eval_splits:] if max_eval_splits > 0 else splits
        x = work[factor_cols].replace([np.inf, -np.inf], np.nan)
        y_series = work[target_col].astype(float)

        def objective(
            trial: optuna.Trial,
            x_fold: pd.DataFrame = x,
            y_fold: pd.Series = y_series,
            eval_fold_splits: list[tuple[np.ndarray, np.ndarray]] = eval_splits,
        ) -> float:
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 80, 260),
                "learning_rate": trial.suggest_float("learning_rate", 0.015, 0.10, log=True),
                "num_leaves": trial.suggest_int("num_leaves", 7, 31),
                "min_child_samples": trial.suggest_int("min_child_samples", 20, 90),
                "lambda_l2": trial.suggest_float("lambda_l2", 0.05, 5.0, log=True),
                "feature_fraction": trial.suggest_float("feature_fraction", 0.60, 1.0),
                "bagging_fraction": trial.suggest_float("bagging_fraction", 0.60, 1.0),
                "bagging_freq": trial.suggest_int("bagging_freq", 1, 7),
            }
            return _evaluate_lgbm_rmse(lgb, x_fold, y_fold, eval_fold_splits, params, random_state=random_state)

        study = optuna.create_study(
            direction="minimize",
            study_name=f"mais_lgbm_h{horizon}",
            sampler=optuna.samplers.TPESampler(seed=random_state + horizon),
            pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=0),
        )
        study.optimize(objective, n_trials=max(1, int(n_trials)), show_progress_bar=False)

        default_metrics = _evaluate_lgbm_metrics(lgb, x, y_series, splits, default_params, random_state=random_state)
        optimized_metrics = _evaluate_lgbm_metrics(
            lgb, x, y_series, splits, study.best_params, random_state=random_state
        )

        row = {
            "status": "ok",
            "model": "lgbm_optuna_factors",
            "horizon": horizon,
            "target": target_col,
            "n_trials": int(len(study.trials)),
            "n_folds": int(len(splits)),
            "optimized_rmse": optimized_metrics["rmse"],
            "default_rmse": default_metrics["rmse"],
            "rmse_delta_optimized_minus_default": optimized_metrics["rmse"] - default_metrics["rmse"],
            "optimized_directional_accuracy": optimized_metrics["directional_accuracy"],
            "default_directional_accuracy": default_metrics["directional_accuracy"],
            "directional_accuracy_delta": (
                optimized_metrics["directional_accuracy"] - default_metrics["directional_accuracy"]
            ),
            "best_params_json": _json_dumps(study.best_params),
            "test_start": str(work.iloc[splits[0][1]]["Date"].min().date()),
            "test_end": str(work.iloc[splits[-1][1]]["Date"].max().date()),
        }
        rows.append(row)
        log.info(
            "study_lgbm_optuna_done",
            horizon=horizon,
            rmse_default=round(default_metrics["rmse"], 5),
            rmse_optimized=round(optimized_metrics["rmse"], 5),
            n_trials=len(study.trials),
        )

    result = pd.DataFrame(rows)
    write_parquet(result, out_path)
    return result


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


def _normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Date"] = pd.to_datetime(out["Date"])
    return out.sort_values("Date").drop_duplicates("Date", keep="last").reset_index(drop=True)


def _study_walk_splits(
    n: int,
    horizon: int,
    initial_ratio: float = 0.60,
    test_size: int = 252,
) -> list[tuple[np.ndarray, np.ndarray]]:
    if n < 600:
        cut = int(0.75 * n)
        train_end = max(1, cut - horizon)
        return [(np.arange(0, train_end), np.arange(cut, n))] if train_end >= 120 else []
    start = int(n * initial_ratio)
    out = []
    while start < n:
        train_end = max(1, start - max(horizon, 10))
        test_end = min(n, start + test_size)
        if test_end - start >= 40 and train_end >= 500:
            out.append((np.arange(0, train_end), np.arange(start, test_end)))
        start += test_size
    return out


def _default_lgbm_params(random_state: int = 42) -> dict[str, Any]:
    return {
        "n_estimators": 200,
        "learning_rate": 0.04,
        "num_leaves": 15,
        "min_child_samples": 40,
        "lambda_l2": 1.0,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "random_state": random_state,
    }


def _evaluate_lgbm_rmse(
    lgb: Any,
    x: pd.DataFrame,
    y: pd.Series,
    splits: list[tuple[np.ndarray, np.ndarray]],
    params: dict[str, Any],
    *,
    random_state: int,
) -> float:
    metrics = _evaluate_lgbm_metrics(lgb, x, y, splits, params, random_state=random_state)
    return metrics["rmse"]


def _evaluate_lgbm_metrics(
    lgb: Any,
    x: pd.DataFrame,
    y: pd.Series,
    splits: list[tuple[np.ndarray, np.ndarray]],
    params: dict[str, Any],
    *,
    random_state: int,
) -> dict[str, float]:
    preds = []
    trues = []
    clean_params = dict(params)
    clean_params.setdefault("random_state", random_state)
    clean_params.setdefault("verbose", -1)

    for train_idx, test_idx in splits:
        imp = SimpleImputer(strategy="median", keep_empty_features=True)
        x_train = imp.fit_transform(x.iloc[train_idx])
        x_test = imp.transform(x.iloc[test_idx])
        y_train = y.iloc[train_idx].to_numpy(dtype=float)
        model = lgb.LGBMRegressor(**clean_params)
        model.fit(x_train, y_train)
        preds.append(np.asarray(model.predict(x_test), dtype=float))
        trues.append(y.iloc[test_idx].to_numpy(dtype=float))

    y_true = np.concatenate(trues)
    y_pred = np.concatenate(preds)
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "directional_accuracy": float(np.mean(np.sign(y_true) == np.sign(y_pred))),
    }


def _optuna_skip_row(horizon: int, target_col: str, reason: str) -> dict[str, Any]:
    return {
        "status": reason,
        "model": "lgbm_optuna_factors",
        "horizon": horizon,
        "target": target_col,
        "n_trials": 0,
        "n_folds": 0,
    }


def _json_dumps(obj: Any) -> str:
    import json

    return json.dumps(obj, sort_keys=True, ensure_ascii=True)
