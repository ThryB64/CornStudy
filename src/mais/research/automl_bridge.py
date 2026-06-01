"""Clean AutoML bridge for research notebooks.

The legacy ``Models/`` directory remains read-only. This module exposes a
small, stable API for notebooks and reuses the clean project stack instead of
importing legacy model code directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import (
    HistGradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import ElasticNet, LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)
from sklearn.model_selection import KFold, StratifiedKFold

from mais.paths import FEATURES_PARQUET, PROCESSED_DIR, TARGETS_PARQUET
from mais.utils import get_logger

log = get_logger("mais.research.automl_bridge")

ValidationMode = Literal["walk_forward", "kfold"]
ProblemType = Literal["regression", "classification"]


@dataclass
class AutoMLExperimentResult:
    """Structured result returned to notebooks."""

    summary_df: pd.DataFrame
    best_model: str | None
    shap_df: pd.DataFrame
    experiment_log: dict[str, Any]
    folds_df: pd.DataFrame


def list_available_models(problem: ProblemType = "regression") -> list[str]:
    """Return model aliases supported by the clean bridge."""
    aliases = ["ridge", "elasticnet", "rf", "hgb"]
    if problem == "classification":
        aliases = ["logistic", "rf"]
    try:
        import lightgbm  # noqa: F401

        aliases.append("lightgbm")
    except ImportError:
        pass
    try:
        import xgboost  # noqa: F401

        aliases.append("xgboost")
    except ImportError:
        pass
    return aliases


def get_models_metadata() -> pd.DataFrame:
    """Describe supported clean model aliases for notebook UIs."""
    rows = [
        {
            "model": "ridge",
            "problem": "regression",
            "description": "Linear ridge regression baseline.",
        },
        {
            "model": "elasticnet",
            "problem": "regression",
            "description": "Sparse linear regression with L1/L2 penalty.",
        },
        {
            "model": "rf",
            "problem": "regression/classification",
            "description": "Random forest with default conservative settings.",
        },
        {
            "model": "hgb",
            "problem": "regression",
            "description": "Scikit-learn histogram gradient boosting regressor.",
        },
        {
            "model": "lightgbm",
            "problem": "regression/classification",
            "description": "Optional LightGBM model, used only when installed.",
        },
        {
            "model": "xgboost",
            "problem": "regression",
            "description": "Optional XGBoost regressor, used only when installed.",
        },
        {
            "model": "logistic",
            "problem": "classification",
            "description": "Logistic regression for binary targets.",
        },
    ]
    return pd.DataFrame(rows)


def _read_frame(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path, low_memory=False)
    raise ValueError(f"Unsupported dataset format: {path}")


def _load_named_dataset(dataset: str | Path) -> pd.DataFrame:
    if isinstance(dataset, Path):
        return _read_frame(dataset)

    aliases = {
        "features": FEATURES_PARQUET,
        "factors": PROCESSED_DIR / "factors.parquet",
        "targets": TARGETS_PARQUET,
    }
    if dataset in aliases:
        return _read_frame(aliases[dataset])

    path = Path(dataset)
    if path.exists():
        return _read_frame(path)
    raise ValueError(
        "dataset must be 'features', 'factors', 'targets', or a CSV/Parquet path"
    )


def _load_xy(
    dataset: str | Path | pd.DataFrame,
    target: str | pd.Series | None,
) -> tuple[pd.DataFrame, pd.Series]:
    if isinstance(dataset, pd.DataFrame):
        if not isinstance(target, pd.Series):
            raise TypeError("When dataset is a DataFrame, target must be a Series.")
        features = dataset.copy()
        y = target.copy()
    else:
        if not isinstance(target, str):
            raise TypeError("target must be a column name when dataset is a name/path.")
        df = _load_named_dataset(dataset)
        if target in df.columns:
            y = df[target].copy()
            features = df.drop(columns=[target]).copy()
        else:
            targets_df = _read_frame(TARGETS_PARQUET)
            if target not in targets_df.columns:
                raise ValueError(f"Target column not found: {target}")
            y = targets_df[target].copy()
            features = df.copy()

    common_idx = features.index.intersection(y.dropna().index)
    features = features.loc[common_idx].copy()
    y = y.loc[common_idx].copy()

    if features.empty or y.empty:
        raise ValueError("No aligned rows available for AutoML experiment.")
    return features, y


def _prepare_features(features: pd.DataFrame) -> pd.DataFrame:
    features = features.copy()
    target_like = [
        c
        for c in features.columns
        if str(c).startswith(("y_", "future_", "realized_vol_", "storage_value_", "sell_regret_"))
    ]
    if target_like:
        features = features.drop(columns=target_like)

    date_cols = features.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns
    if len(date_cols) > 0:
        features = features.drop(columns=list(date_cols))

    features = pd.get_dummies(features, dummy_na=True)
    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.apply(pd.to_numeric, errors="coerce")
    return features.fillna(0.0)


def _infer_problem(y: pd.Series) -> ProblemType:
    values = y.dropna()
    unique = set(values.unique().tolist())
    if values.dtype == bool or unique.issubset({0, 1}):
        return "classification"
    return "regression"


def _make_models(
    model_names: list[str] | None,
    problem: ProblemType,
) -> dict[str, Any]:
    aliases = {m.lower(): m.lower() for m in model_names or []}
    aliases.update({"lgbm": "lightgbm", "xgb": "xgboost", "random_forest": "rf"})
    requested = [aliases.get(m.lower(), m.lower()) for m in model_names] if model_names else []

    if problem == "classification":
        models: dict[str, Any] = {
            "baseline_majority": DummyClassifier(strategy="most_frequent"),
            "logistic": LogisticRegression(max_iter=500, random_state=42),
            "rf": RandomForestClassifier(n_estimators=100, n_jobs=1, random_state=42),
        }
        try:
            import lightgbm as lgb

            models["lightgbm"] = lgb.LGBMClassifier(
                n_estimators=100, random_state=42, verbose=-1
            )
        except ImportError:
            pass
    else:
        models = {
            "baseline_mean": DummyRegressor(strategy="mean"),
            "ridge": Ridge(alpha=1.0),
            "elasticnet": ElasticNet(alpha=0.01, l1_ratio=0.5, random_state=42),
            "rf": RandomForestRegressor(n_estimators=100, n_jobs=1, random_state=42),
            "hgb": HistGradientBoostingRegressor(max_iter=100, random_state=42),
        }
        try:
            import lightgbm as lgb

            models["lightgbm"] = lgb.LGBMRegressor(
                n_estimators=100, random_state=42, verbose=-1
            )
        except ImportError:
            pass
        try:
            import xgboost as xgb

            models["xgboost"] = xgb.XGBRegressor(
                n_estimators=100, random_state=42, verbosity=0
            )
        except ImportError:
            pass

    if requested:
        selected = {name: models[name] for name in requested if name in models}
        missing = sorted(set(requested) - set(selected))
        if missing:
            log.warning("automl_models_unavailable", models=missing)
        return selected
    return models


def _split_indices(
    n_rows: int,
    y: pd.Series,
    validation: ValidationMode,
    problem: ProblemType,
    *,
    min_train: int,
    test_size: int,
    n_splits: int = 5,
) -> list[tuple[np.ndarray, np.ndarray]]:
    if validation == "kfold":
        n_splits = max(2, min(n_splits, n_rows))
        splitter = (
            StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
            if problem == "classification"
            else KFold(n_splits=n_splits, shuffle=True, random_state=42)
        )
        split_y = y if problem == "classification" else None
        return [(tr, te) for tr, te in splitter.split(np.arange(n_rows), split_y)]

    splits = []
    start = min(min_train, max(int(n_rows * 0.5), 20))
    while start + test_size <= n_rows:
        train_idx = np.arange(0, start)
        test_idx = np.arange(start, min(start + test_size, n_rows))
        if len(test_idx) >= 5:
            splits.append((train_idx, test_idx))
        start += test_size
    if not splits:
        return _split_indices(
            n_rows, y, "kfold", problem, min_train=min_train, test_size=test_size, n_splits=n_splits
        )
    return splits


def _metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_score: np.ndarray | None,
    problem: ProblemType,
) -> dict[str, float]:
    nan = float("nan")
    if problem == "classification":
        auc = nan
        if y_score is not None and len(np.unique(y_true)) == 2:
            try:
                auc = float(roc_auc_score(y_true, y_score))
            except ValueError:
                auc = nan
        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "auc": auc,
            "rmse": nan,
            "mae": nan,
            "r2": nan,
            "da": nan,
        }

    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
        "da": float(np.mean(np.sign(y_true) == np.sign(y_pred))),
        "accuracy": nan,
        "auc": nan,
    }


def _score_model(
    model: Any,
    features: pd.DataFrame,
    y: pd.Series,
    split: tuple[np.ndarray, np.ndarray],
) -> tuple[np.ndarray, np.ndarray | None]:
    tr_idx, te_idx = split
    fitted = clone(model)
    fitted.fit(features.iloc[tr_idx], y.iloc[tr_idx])
    pred = np.asarray(fitted.predict(features.iloc[te_idx]))
    score = None
    if hasattr(fitted, "predict_proba"):
        proba = fitted.predict_proba(features.iloc[te_idx])
        if np.asarray(proba).ndim == 2 and proba.shape[1] > 1:
            score = np.asarray(proba)[:, 1]
    return pred, score


def _run_benchmark(
    features: pd.DataFrame,
    y: pd.Series,
    models: dict[str, Any],
    validation: ValidationMode,
    problem: ProblemType,
    *,
    min_train: int,
    test_size: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    splits = _split_indices(
        len(features), y, validation, problem, min_train=min_train, test_size=test_size
    )
    rows = []
    for model_name, model in models.items():
        for fold, split in enumerate(splits):
            try:
                pred, score = _score_model(model, features, y, split)
                _, te_idx = split
                rows.append(
                    {
                        "model": model_name,
                        "fold": fold,
                        "train_size": len(split[0]),
                        "test_size": len(split[1]),
                        **_metrics(
                            np.asarray(y.iloc[te_idx]),
                            pred,
                            score,
                            problem,
                        ),
                    }
                )
            except Exception as exc:
                log.warning("automl_fold_failed", model=model_name, fold=fold, error=str(exc))
    folds_df = pd.DataFrame(rows)
    if folds_df.empty:
        return folds_df, pd.DataFrame()

    def _mean_or_nan(values: pd.Series) -> float:
        clean = values.dropna()
        if clean.empty:
            return float("nan")
        return float(clean.mean())

    metric_cols = ["rmse", "mae", "r2", "da", "accuracy", "auc"]
    summary = (
        folds_df.groupby("model")[metric_cols]
        .agg(_mean_or_nan)
        .reset_index()
    )
    summary["n_folds"] = folds_df.groupby("model")["fold"].count().reindex(summary["model"]).values
    return folds_df, summary


def _select_best(summary_df: pd.DataFrame, problem: ProblemType) -> str | None:
    if summary_df.empty:
        return None
    if problem == "classification" and "accuracy" in summary_df:
        return str(summary_df.sort_values("accuracy", ascending=False).iloc[0]["model"])
    if "rmse" in summary_df:
        valid = summary_df.dropna(subset=["rmse"])
        if not valid.empty:
            return str(valid.sort_values("rmse", ascending=True).iloc[0]["model"])
    return str(summary_df.iloc[0]["model"])


def _importance_df(model: Any, features: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    fitted = clone(model)
    try:
        fitted.fit(features, y)
    except Exception as exc:
        log.warning("automl_importance_fit_failed", error=str(exc))
        return pd.DataFrame(columns=["feature", "mean_abs_shap", "source"])

    try:
        import shap

        explainer = shap.TreeExplainer(fitted)
        vals = explainer.shap_values(features)
        if isinstance(vals, list):
            vals = vals[0]
        importance = np.abs(vals).mean(axis=0)
        source = "shap"
    except Exception:
        if hasattr(fitted, "feature_importances_"):
            importance = np.asarray(fitted.feature_importances_, dtype=float)
            source = "feature_importance"
        elif hasattr(fitted, "coef_"):
            importance = np.abs(np.ravel(fitted.coef_).astype(float))
            source = "coefficient"
        else:
            return pd.DataFrame(columns=["feature", "mean_abs_shap", "source"])

    return (
        pd.DataFrame(
            {"feature": features.columns, "mean_abs_shap": importance, "source": source}
        )
        .sort_values("mean_abs_shap", ascending=False)
        .reset_index(drop=True)
    )


def run_automl_experiment(
    dataset: str | Path | pd.DataFrame,
    target: str | pd.Series | None = None,
    models: list[str] | None = None,
    validation: ValidationMode = "walk_forward",
    optimize: bool = False,
    optuna_trials: int = 20,
    horizon: int = 20,
    experiment_id: str | None = None,
    *,
    min_train: int = 300,
    test_size: int = 50,
    model_names: list[str] | None = None,
    target_col: str | None = None,
    n_optuna_trials: int | None = None,
) -> AutoMLExperimentResult:
    """Run a clean AutoML experiment and return notebook-friendly outputs.

    ``dataset`` can be ``"features"``, ``"factors"``, a CSV/Parquet path, or a
    pre-built feature DataFrame. For backward compatibility, DataFrame input
    accepts ``target`` as a Series plus the legacy ``model_names`` and
    ``target_col`` keyword names.
    """
    if validation not in {"walk_forward", "kfold"}:
        raise ValueError("validation must be 'walk_forward' or 'kfold'")

    selected_models = models or model_names
    selected_target = target if target is not None else target_col
    target_label = (
        selected_target.name
        if isinstance(selected_target, pd.Series) and selected_target.name is not None
        else str(selected_target)
    )
    trials = n_optuna_trials if n_optuna_trials is not None else optuna_trials
    if optimize:
        log.warning("automl_optimize_not_enabled", trials=trials)

    raw_features, y = _load_xy(dataset, selected_target)
    features = _prepare_features(raw_features)
    y = y.loc[features.index]
    problem = _infer_problem(y)
    model_map = _make_models(selected_models, problem)
    if not model_map:
        raise ValueError("No compatible models available for this experiment.")

    folds_df, summary_df = _run_benchmark(
        features,
        y,
        model_map,
        validation,
        problem,
        min_train=min_train,
        test_size=test_size,
    )
    summary_df["horizon"] = horizon
    summary_df["target"] = target_label
    summary_df["validation"] = validation

    best_model = _select_best(summary_df, problem)
    shap_df = (
        _importance_df(model_map[best_model], features, y)
        if best_model in model_map
        else pd.DataFrame(columns=["feature", "mean_abs_shap", "source"])
    )

    experiment_log = {
        "experiment_id": experiment_id,
        "dataset": dataset if isinstance(dataset, str) else str(dataset),
        "target": target_label,
        "horizon": horizon,
        "validation": validation,
        "problem": problem,
        "models": list(model_map),
        "best_model": best_model,
        "n_rows": int(len(features)),
        "n_features": int(features.shape[1]),
        "optimize": bool(optimize),
        "optuna_trials": int(trials),
    }
    return AutoMLExperimentResult(
        summary_df=summary_df,
        best_model=best_model,
        shap_df=shap_df,
        experiment_log=experiment_log,
        folds_df=folds_df,
    )
