"""V3-03 tabular model zoo for the maize direction indicator."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    ExtraTreesClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import (
    BayesianRidge,
    ElasticNet,
    Lasso,
    LogisticRegression,
    Ridge,
    RidgeClassifier,
)
from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

from mais.features import build_multi_horizon_targets
from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, INTERIM_DIR
from mais.research.horizon_sweep import (
    _feature_columns,
    _merge_features_targets,
    _walk_forward_splits,
)
from mais.utils import get_logger, read_table, write_parquet

log = get_logger("mais.research.model_zoo")

RANDOM_STATE = 42
DEFAULT_HORIZONS = [28, 35, 40, 45, 60]
MAX_DATE = pd.Timestamp("2022-12-31")
MODEL_ZOO_DIR = ARTEFACTS_DIR / "model_zoo"


def model_specs(random_state: int = RANDOM_STATE) -> dict[str, dict[str, Any]]:
    """Return model specifications for the V3-03 zoo."""
    specs: dict[str, dict[str, Any]] = {
        "ridge": {"kind": "regressor", "builder": lambda: _scaled(Ridge(alpha=1.0))},
        "lasso": {"kind": "regressor", "builder": lambda: _scaled(Lasso(alpha=0.001, max_iter=5000))},
        "elasticnet": {
            "kind": "regressor",
            "builder": lambda: _scaled(ElasticNet(alpha=0.001, l1_ratio=0.5, max_iter=5000)),
        },
        "bayesian_ridge": {"kind": "regressor", "builder": lambda: _scaled(BayesianRidge())},
        "logistic": {
            "kind": "classifier",
            "builder": lambda: _scaled(
                LogisticRegression(C=1.0, max_iter=500, random_state=random_state)
            ),
        },
        "rf": {
            "kind": "classifier",
            "builder": lambda: RandomForestClassifier(
                n_estimators=40,
                max_depth=6,
                min_samples_leaf=30,
                random_state=random_state,
                n_jobs=-1,
            ),
        },
        "extratrees": {
            "kind": "classifier",
            "builder": lambda: ExtraTreesClassifier(
                n_estimators=40,
                max_depth=6,
                min_samples_leaf=30,
                random_state=random_state,
                n_jobs=-1,
            ),
        },
        "histgb": {
            "kind": "classifier",
            "builder": lambda: HistGradientBoostingClassifier(
                max_iter=40,
                learning_rate=0.05,
                max_leaf_nodes=15,
                l2_regularization=1.0,
                random_state=random_state,
            ),
        },
        "linear_svm": {
            "kind": "classifier",
            "builder": lambda: _scaled(LinearSVC(C=1.0, max_iter=4000, random_state=random_state)),
        },
        "ridge_classifier": {
            "kind": "classifier",
            "builder": lambda: _scaled(RidgeClassifier(alpha=1.0)),
        },
        "gaussian_nb": {
            "kind": "classifier",
            "builder": lambda: _scaled(GaussianNB()),
        },
        "mlp": {
            "kind": "classifier",
            "builder": lambda: _scaled(
                MLPClassifier(
                    hidden_layer_sizes=(32,),
                    alpha=1e-3,
                    max_iter=80,
                    early_stopping=True,
                    random_state=random_state,
                )
            ),
        },
    }

    try:
        import lightgbm as lgb

        specs["lgbm"] = {
            "kind": "classifier",
            "builder": lambda: lgb.LGBMClassifier(
                n_estimators=40,
                learning_rate=0.05,
                num_leaves=15,
                min_child_samples=40,
                lambda_l2=1.0,
                verbose=-1,
                random_state=random_state,
            ),
        }
    except ImportError:
        pass

    return specs


def run_model_zoo(
    features: pd.DataFrame,
    targets: pd.DataFrame,
    horizons: list[int],
    specs: dict[str, dict[str, Any]] | None = None,
    n_splits: int = 5,
    output_dir: Path = MODEL_ZOO_DIR,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """Run every model on selected horizons with strict OOF predictions."""
    output_dir.mkdir(parents=True, exist_ok=True)
    active_specs = specs if specs is not None else model_specs(random_state)

    prediction_frames: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []

    for horizon in horizons:
        for name, spec in active_specs.items():
            oof = _run_model_oof(
                features=features,
                targets=targets,
                horizon=int(horizon),
                model_name=name,
                spec=spec,
                n_splits=n_splits,
            )
            if oof.empty:
                continue
            prediction_frames.append(oof)
            metric_rows.append(_summarize_oof(oof, model_name=name, horizon=int(horizon)))

    predictions = pd.concat(prediction_frames, ignore_index=True) if prediction_frames else pd.DataFrame()
    if not predictions.empty:
        ensemble_preds = _ensemble_predictions(predictions)
        if not ensemble_preds.empty:
            predictions = pd.concat([predictions, ensemble_preds], ignore_index=True)
            for (horizon, model_name), sub in ensemble_preds.groupby(["horizon", "model"]):
                metric_rows.append(_summarize_oof(sub, model_name=str(model_name), horizon=int(horizon)))

    results = pd.DataFrame(metric_rows)
    if not results.empty:
        results = results.sort_values(["horizon", "da", "auc"], ascending=[True, False, False])

    corr = compute_error_correlation(_prediction_error_dict(predictions))
    selected = select_diverse_models(results, corr, top_n=5, min_auc=0.55)

    write_parquet(results, output_dir / "model_zoo_results.parquet")
    write_parquet(predictions, output_dir / "model_zoo_oof_predictions.parquet")
    write_parquet(corr, output_dir / "model_zoo_error_correlation.parquet")
    (output_dir / "model_zoo_selected_models.json").write_text(
        json.dumps(selected, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_dir / "model_zoo_report.txt").write_text(
        _report_text(results, selected),
        encoding="utf-8",
    )
    return results


def compute_error_correlation(predictions_dict: dict[str, np.ndarray]) -> pd.DataFrame:
    """Correlation matrix of per-model OOF error vectors."""
    if not predictions_dict:
        return pd.DataFrame()
    aligned = pd.DataFrame({k: pd.Series(v).reset_index(drop=True) for k, v in predictions_dict.items()})
    return aligned.corr().fillna(0.0)


def select_diverse_models(
    results_df: pd.DataFrame,
    corr_matrix: pd.DataFrame,
    top_n: int = 5,
    min_auc: float = 0.55,
) -> list[str]:
    """Select strong and diverse models for downstream stacking."""
    if results_df.empty:
        return []
    agg = (
        results_df[~results_df["model"].isin(["vote_majority", "avg_proba"])]
        .groupby("model", as_index=False)
        .agg(da=("da", "mean"), auc=("auc", "mean"), da_std=("da_std", "mean"))
    )
    agg = agg[agg["auc"].fillna(0.0) >= min_auc].sort_values(
        ["da", "auc", "da_std"],
        ascending=[False, False, True],
    )
    if agg.empty:
        agg = results_df.groupby("model", as_index=False).agg(
            da=("da", "mean"),
            auc=("auc", "mean"),
            da_std=("da_std", "mean"),
        ).sort_values(["da", "auc"], ascending=False)

    selected: list[str] = []
    for model in agg["model"].tolist():
        if len(selected) >= top_n:
            break
        if not selected:
            selected.append(str(model))
            continue
        too_similar = False
        for kept in selected:
            if model in corr_matrix.index and kept in corr_matrix.columns:
                too_similar = abs(float(corr_matrix.loc[model, kept])) >= 0.70
                if too_similar:
                    break
        if not too_similar:
            selected.append(str(model))
    return selected


def run_project_model_zoo() -> pd.DataFrame:
    """Load standard project inputs and run V3-03."""
    features = pd.read_parquet(FEATURES_PARQUET)
    db = read_table(INTERIM_DIR / "database.parquet", date_col="Date")
    targets = build_multi_horizon_targets(db[["Date", "corn_close"]], DEFAULT_HORIZONS)
    horizons = _load_v3_02_horizons() or DEFAULT_HORIZONS
    specs = model_specs()
    # Keep slow variants available for direct experiments, but the project run
    # must finish reliably on every machine while still testing 12+ methods
    # once the two OOF ensembles are added.
    for slow_model in ("linear_svm", "mlp"):
        specs.pop(slow_model, None)
    return run_model_zoo(features, targets, horizons=horizons, specs=specs, output_dir=MODEL_ZOO_DIR)


def _scaled(estimator: Any) -> Pipeline:
    return Pipeline([("scaler", StandardScaler()), ("model", estimator)])


def _run_model_oof(
    features: pd.DataFrame,
    targets: pd.DataFrame,
    horizon: int,
    model_name: str,
    spec: dict[str, Any],
    n_splits: int,
) -> pd.DataFrame:
    target_col = f"y_cont_h{horizon}"
    up_col = f"y_up_h{horizon}"
    work = _merge_features_targets(features, targets, target_col, up_col, max_date=MAX_DATE)
    feature_cols = _feature_columns(work, exclude={target_col, up_col})
    splits = _walk_forward_splits(len(work), n_splits=n_splits, embargo_days=horizon)
    if not splits:
        return pd.DataFrame()

    frames = []
    for fold, (train_idx, test_idx) in enumerate(splits):
        train = work.iloc[train_idx].copy()
        test = work.iloc[test_idx].copy()
        pred_cont, p_up, method = _fit_predict(train, test, feature_cols, target_col, up_col, spec)
        frames.append(
            pd.DataFrame(
                {
                    "Date": test["Date"].values,
                    "horizon": horizon,
                    "fold": fold,
                    "model": model_name,
                    "prob_method": method,
                    "y_true_cont": test[target_col].to_numpy(dtype=float),
                    "y_true_up": test[up_col].to_numpy(dtype=int),
                    "y_pred_cont": pred_cont,
                    "p_up": p_up,
                    "pred_up": (p_up >= 0.5).astype(int),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def _fit_predict(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    up_col: str,
    spec: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray, str]:
    x_train, x_test = _matrices(train, test, feature_cols)
    model = spec["builder"]()
    if spec["kind"] == "regressor":
        y_train = train[target_col].to_numpy(dtype=float)
        model.fit(x_train, y_train)
        pred = np.asarray(model.predict(x_test), dtype=float)
        scale = float(np.nanstd(y_train))
        if not math.isfinite(scale) or scale <= 1e-8:
            scale = 0.03
        p_up = _sigmoid(pred / scale)
        return pred, p_up, "sign"

    y_train = train[up_col].astype(int).to_numpy()
    if len(np.unique(y_train)) < 2:
        p_up = np.full(len(test), float(np.mean(y_train)))
        return p_up - 0.5, p_up, "constant"
    model.fit(x_train, y_train)
    if hasattr(model, "predict_proba"):
        p_up = np.asarray(model.predict_proba(x_test)[:, 1], dtype=float)
        return p_up - 0.5, np.clip(p_up, 0.0, 1.0), "proba"
    if hasattr(model, "decision_function"):
        score = np.asarray(model.decision_function(x_test), dtype=float)
        p_up = _sigmoid(score)
        return p_up - 0.5, p_up, "decision_function"
    pred = np.asarray(model.predict(x_test), dtype=float)
    return pred - 0.5, np.clip(pred, 0.0, 1.0), "predict"


def _matrices(
    train: pd.DataFrame,
    test: pd.DataFrame,
    cols: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    imputer = SimpleImputer(strategy="median", keep_empty_features=True)
    x_train = train[cols].replace([np.inf, -np.inf], np.nan)
    x_test = test[cols].replace([np.inf, -np.inf], np.nan)
    return (
        pd.DataFrame(imputer.fit_transform(x_train), columns=cols),
        pd.DataFrame(imputer.transform(x_test), columns=cols),
    )


def _ensemble_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    base = predictions[~predictions["model"].isin(["vote_majority", "avg_proba"])].copy()
    if base.empty:
        return pd.DataFrame()
    rows = []
    keys = ["Date", "horizon", "fold"]
    for key, sub in base.groupby(keys):
        p_values = sub["p_up"].to_numpy(dtype=float)
        y_true_up = int(sub["y_true_up"].iloc[0])
        y_true_cont = float(sub["y_true_cont"].iloc[0])
        avg_p = float(np.mean(p_values))
        vote_p = float(np.mean(p_values >= 0.5))
        for model_name, p_up in [("avg_proba", avg_p), ("vote_majority", vote_p)]:
            rows.append(
                {
                    "Date": key[0],
                    "horizon": int(key[1]),
                    "fold": int(key[2]),
                    "model": model_name,
                    "prob_method": "ensemble",
                    "y_true_cont": y_true_cont,
                    "y_true_up": y_true_up,
                    "y_pred_cont": p_up - 0.5,
                    "p_up": p_up,
                    "pred_up": int(p_up >= 0.5),
                }
            )
    return pd.DataFrame(rows)


def _summarize_oof(oof: pd.DataFrame, model_name: str, horizon: int) -> dict[str, Any]:
    y = oof["y_true_up"].to_numpy(dtype=int)
    p = np.clip(oof["p_up"].to_numpy(dtype=float), 0.0, 1.0)
    pred = (p >= 0.5).astype(int)
    by_fold = oof.groupby("fold").apply(
        lambda s: accuracy_score(s["y_true_up"].astype(int), (s["p_up"] >= 0.5).astype(int)),
        include_groups=False,
    )
    conf = np.abs(p - 0.5)
    top20 = conf >= np.quantile(conf, 0.80)
    return {
        "horizon": int(horizon),
        "model": model_name,
        "da": float(accuracy_score(y, pred)),
        "auc": _auc(y, p),
        "brier": float(brier_score_loss(y, p)),
        "da_top20pct": float(accuracy_score(y[top20], pred[top20])) if top20.any() else np.nan,
        "da_std": float(by_fold.std(ddof=0)),
        "n_obs_test": int(len(oof)),
        "n_folds": int(oof["fold"].nunique()),
        "prob_method": str(oof["prob_method"].iloc[0]),
        "test_start": str(pd.to_datetime(oof["Date"]).min().date()),
        "test_end": str(pd.to_datetime(oof["Date"]).max().date()),
    }


def _prediction_error_dict(predictions: pd.DataFrame) -> dict[str, np.ndarray]:
    if predictions.empty:
        return {}
    out = {}
    for model, sub in predictions.groupby("model"):
        ordered = sub.sort_values(["horizon", "Date"]).copy()
        out[str(model)] = (ordered["pred_up"].astype(int) != ordered["y_true_up"].astype(int)).to_numpy(dtype=float)
    return out


def _auc(y_true: np.ndarray, p_up: np.ndarray) -> float:
    try:
        if len(np.unique(y_true)) < 2:
            return np.nan
        return float(roc_auc_score(y_true, p_up))
    except ValueError:
        return np.nan


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(np.asarray(x, dtype=float), -50.0, 50.0)))


def _load_v3_02_horizons() -> list[int]:
    path = ARTEFACTS_DIR / "indicator" / "horizon_sweep_zone.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    robust = [int(h) for h in payload.get("robust_zone", [])]
    if robust:
        return robust
    best_horizon = payload.get("best_horizon")
    return [int(best_horizon)] if best_horizon is not None else []


def _report_text(results: pd.DataFrame, selected: list[str]) -> str:
    lines = [
        "Model zoo V3-03 — résultats comparatifs",
        "",
        f"Modèles retenus pour V3-05 : {selected}",
        "",
        "| Horizon | Modèle | DA | AUC | Brier | DA top20 | Std DA | Prob method |",
        "|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for _, row in results.sort_values(["horizon", "da"], ascending=[True, False]).iterrows():
        lines.append(
            f"| J+{int(row['horizon'])} | {row['model']} | {row['da']:.3f} | "
            f"{row['auc']:.3f} | {row['brier']:.3f} | {row['da_top20pct']:.3f} | "
            f"{row['da_std']:.3f} | {row['prob_method']} |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    run_project_model_zoo()
