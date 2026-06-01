"""AutoML runner + Markdown report generator.

Entry point: ``run_automl(csv_path, target_col, out_dir)``
CLI: ``mais platform run --csv file.csv --target col``

Flow:
  1. profile_dataset   → ProfileReport
  2. GenericPreprocessor fit/transform
  3. Walk-forward (TS) or KFold (tabular) benchmark
  4. SHAP importance (optional, tree models only)
  5. Write report.md + benchmarks.csv to out_dir
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    HistGradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import KFold, StratifiedKFold

from mais.platform.preprocessing import GenericPreprocessor, PreprocessingConfig
from mais.platform.profiler import (
    BINARY,
    MULTICLASS,
    ORDINAL,
    ProfileReport,
    profile_dataset,
)
from mais.utils import get_logger

log = get_logger("mais.platform.reporting")


# ---------------------------------------------------------------------------
# Model factory
# ---------------------------------------------------------------------------

def _make_models(problem_type: str) -> dict[str, Any]:
    is_clf = problem_type in (BINARY, MULTICLASS, ORDINAL)
    models: dict[str, Any] = {}

    if is_clf:
        models["logistic"] = LogisticRegression(max_iter=500, n_jobs=1)
        models["rf"] = RandomForestClassifier(n_estimators=100, n_jobs=1, random_state=42)
        try:
            import lightgbm as lgb
            models["lgbm"] = lgb.LGBMClassifier(n_estimators=100, verbose=-1, random_state=42)
        except ImportError:
            pass
    else:
        models["ridge"] = Ridge(alpha=1.0)
        models["rf"] = RandomForestRegressor(n_estimators=100, n_jobs=1, random_state=42)
        models["hgb"] = HistGradientBoostingRegressor(max_iter=100, random_state=42)
        try:
            import lightgbm as lgb
            models["lgbm"] = lgb.LGBMRegressor(n_estimators=100, verbose=-1, random_state=42)
        except ImportError:
            pass
        try:
            import xgboost as xgb
            models["xgb"] = xgb.XGBRegressor(n_estimators=100, verbosity=0, random_state=42)
        except ImportError:
            pass

    return models


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

def _regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    # Directional accuracy (useful for price series)
    if len(y_true) > 1:
        da = float(np.mean(np.sign(y_pred[1:]) == np.sign(y_true[1:])))
    else:
        da = float("nan")
    return {"rmse": rmse, "mae": mae, "r2": r2, "directional_accuracy": da}


def _classification_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    acc = float(accuracy_score(y_true, y_pred))
    return {"accuracy": acc, "rmse": float("nan"), "mae": float("nan"), "r2": float("nan"), "directional_accuracy": float("nan")}


def _evaluate_model(
    model: Any,
    X_train: pd.DataFrame,  # noqa: N803
    y_train: pd.Series,
    X_test: pd.DataFrame,  # noqa: N803
    y_test: pd.Series,
    problem_type: str,
) -> dict[str, float]:
    is_clf = problem_type in (BINARY, MULTICLASS, ORDINAL)
    try:
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
    except Exception as e:
        log.warning("model_fit_failed", error=str(e))
        nan = float("nan")
        return {"rmse": nan, "mae": nan, "r2": nan, "directional_accuracy": nan, "accuracy": nan}
    if is_clf:
        return _classification_metrics(np.array(y_test), np.array(y_pred))
    return _regression_metrics(np.array(y_test), np.array(y_pred))


# ---------------------------------------------------------------------------
# Cross-validation strategies
# ---------------------------------------------------------------------------

def _kfold_benchmark(
    X: pd.DataFrame,  # noqa: N803
    y: pd.Series,
    models: dict[str, Any],
    problem_type: str,
    n_splits: int = 5,
) -> pd.DataFrame:
    is_clf = problem_type in (BINARY, MULTICLASS, ORDINAL)
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42) if is_clf else KFold(n_splits=n_splits, shuffle=True, random_state=42)
    rows = []
    for name, model in models.items():
        fold_metrics: list[dict[str, float]] = []
        try:
            for tr_idx, te_idx in cv.split(X, y if is_clf else None):
                m = _evaluate_model(
                    model.__class__(**model.get_params()),
                    X.iloc[tr_idx], y.iloc[tr_idx],
                    X.iloc[te_idx], y.iloc[te_idx],
                    problem_type,
                )
                fold_metrics.append(m)
        except Exception as e:
            log.warning("cv_failed", model=name, error=str(e))
            continue
        agg = {k: float(np.nanmean([fm[k] for fm in fold_metrics])) for k in fold_metrics[0]}
        rows.append({"model": name, "n_folds": len(fold_metrics), **agg})
    return pd.DataFrame(rows)


def _walk_forward_benchmark(
    X: pd.DataFrame,  # noqa: N803
    y: pd.Series,
    models: dict[str, Any],
    problem_type: str,
    min_train: int = 100,
    test_size: int = 50,
) -> pd.DataFrame:
    n = len(X)
    splits = []
    start = min_train
    while start + test_size <= n:
        splits.append((list(range(0, start)), list(range(start, min(start + test_size, n)))))
        start += test_size
    if not splits:
        return _kfold_benchmark(X, y, models, problem_type)

    rows = []
    for name, model in models.items():
        fold_metrics: list[dict[str, float]] = []
        for tr_idx, te_idx in splits:
            m = _evaluate_model(
                model.__class__(**model.get_params()),
                X.iloc[tr_idx], y.iloc[tr_idx],
                X.iloc[te_idx], y.iloc[te_idx],
                problem_type,
            )
            fold_metrics.append(m)
        if not fold_metrics:
            continue
        agg = {k: float(np.nanmean([fm[k] for fm in fold_metrics])) for k in fold_metrics[0]}
        rows.append({"model": name, "n_folds": len(fold_metrics), **agg})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# SHAP importance
# ---------------------------------------------------------------------------

def _shap_importance(model: Any, X: pd.DataFrame) -> pd.DataFrame | None:  # noqa: N803
    try:
        import shap
    except ImportError:
        return None
    try:
        explainer = shap.TreeExplainer(model)
        vals = explainer.shap_values(X)
        if isinstance(vals, list):
            vals = vals[0]
        importance = np.abs(vals).mean(axis=0)
        return (
            pd.DataFrame({"feature": X.columns, "mean_abs_shap": importance})
            .sort_values("mean_abs_shap", ascending=False)
            .reset_index(drop=True)
        )
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def _write_report(
    out_dir: Path,
    profile: ProfileReport,
    benchmarks: pd.DataFrame,
    shap_df: pd.DataFrame | None,
    preprocessing_summary: str,
    dataset_name: str,
    elapsed_sec: float,
) -> Path:
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    is_clf = profile.problem_type in (BINARY, MULTICLASS, ORDINAL)

    # Metric column for ordering
    metric_col = "accuracy" if is_clf else "rmse"
    ascending = is_clf is False  # lower RMSE = better; higher accuracy = better
    bm_sorted = benchmarks.sort_values(metric_col, ascending=ascending) if metric_col in benchmarks.columns else benchmarks

    lines = [
        f"# Rapport AutoML — {dataset_name} — {date_str}",
        "",
        "## Dataset",
        "",
        "| Propriété | Valeur |",
        "|---|---|",
        f"| Lignes | {profile.n_rows:,} |",
        f"| Colonnes | {profile.n_cols} |",
        f"| Type de problème | `{profile.problem_type}` |",
        f"| Cible | `{profile.target_col}` |",
        f"| Colonne date | `{profile.date_col}` |",
        f"| Valeurs uniques cible | {profile.n_unique_target} |",
        f"| Split recommandé | `{profile.split_recommendation}` |",
        f"| Colonnes numériques | {len(profile.numeric_cols)} |",
        f"| Colonnes catégorielles | {len(profile.categorical_cols)} |",
        "",
    ]

    if profile.warnings:
        lines += ["## Avertissements", ""]
        for w in profile.warnings:
            lines.append(f"- ⚠️ {w}")
        lines.append("")

    lines += [
        "## Prétraitement",
        "",
        "```",
        preprocessing_summary,
        "```",
        "",
    ]

    lines += ["## Benchmark modèles", ""]
    if not benchmarks.empty:
        cols_show = ["model", "n_folds"] + [c for c in ["rmse", "mae", "r2", "directional_accuracy", "accuracy"] if c in bm_sorted.columns and bm_sorted[c].notna().any()]
        bm_disp = bm_sorted[cols_show].copy()
        for c in cols_show[2:]:
            bm_disp[c] = bm_disp[c].map(lambda x: f"{x:.4f}" if pd.notna(x) else "—")
        lines.append("| " + " | ".join(cols_show) + " |")
        lines.append("| " + " | ".join(["---"] * len(cols_show)) + " |")
        for _, row in bm_disp.iterrows():
            lines.append("| " + " | ".join(str(row[c]) for c in cols_show) + " |")
        lines.append("")
    else:
        lines += ["*Benchmark non disponible.*", ""]

    if shap_df is not None and not shap_df.empty:
        lines += ["## Importance des variables (SHAP)", ""]
        lines.append("| Rang | Feature | Mean |SHAP| |")
        lines.append("|---|---|---|")
        for i, row in shap_df.head(15).iterrows():
            lines.append(f"| {i+1} | `{row['feature']}` | {row['mean_abs_shap']:.4f} |")
        lines.append("")

    lines += [
        "## Limites",
        "",
        "- Benchmark avec les modèles par défaut (hyperparamètres non optimisés).",
        "- SHAP disponible uniquement pour les modèles à arbres.",
    ]
    if profile.is_time_series:
        lines.append("- Walk-forward avec fenêtres fixes — la taille du test est fixée à 50 lignes par pli.")
    if profile.warnings:
        lines.append(f"- {len(profile.warnings)} avertissement(s) détectés — voir section Avertissements.")

    lines += [
        "",
        "## Recommandations",
        "",
        f"- Modèle recommandé (défaut) : **{bm_sorted.iloc[0]['model'] if not bm_sorted.empty else 'N/A'}**.",
        "- Lancer Optuna pour optimiser les hyperparamètres (`mais platform run --optimize`).",
    ]
    if profile.categorical_cols:
        lines.append(f"- {len(profile.categorical_cols)} colonne(s) catégorielle(s) encodées — vérifier l'encodage.")
    lines += [
        "",
        "---",
        "",
        f"*Généré par mais.platform en {elapsed_sec:.1f}s.*",
    ]

    report_path = out_dir / "automl_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("report_written", path=str(report_path))
    return report_path


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_automl(
    csv_path: str | Path,
    target_col: str | None = None,
    out_dir: str | Path | None = None,
    date_col: str | None = None,
    n_splits: int = 5,
) -> Path:
    """Run full AutoML pipeline and write a Markdown report.

    Parameters
    ----------
    csv_path:   path to CSV or Parquet
    target_col: column to predict (auto-detected if None)
    out_dir:    output directory (defaults to same dir as csv)
    date_col:   date column (auto-detected if None)
    n_splits:   number of CV folds (or walk-forward blocks)

    Returns
    -------
    Path to the generated automl_report.md
    """
    import time
    t0 = time.time()

    csv_path = Path(csv_path)
    if out_dir is None:
        out_dir = csv_path.parent / f"automl_{csv_path.stem}"
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Profile
    profile = profile_dataset(csv_path, target_col=target_col, date_col=date_col)
    log.info("automl_profile_done", problem_type=profile.problem_type, target=profile.target_col)

    # Load dataframe
    if csv_path.suffix == ".parquet":
        df = pd.read_parquet(csv_path)
    else:
        df = pd.read_csv(csv_path, low_memory=False)

    # 2. Preprocess
    config = PreprocessingConfig(horizon=1)
    is_linear = False  # default to tree-friendly preprocessing
    prep = GenericPreprocessor(profile, config, linear_model=is_linear)
    X, y = prep.fit_transform(df)  # noqa: N806
    X = X.fillna(0.0)  # noqa: N806

    log.info("automl_preprocessed", features=X.shape[1], rows=len(X))

    # 3. Benchmark
    models = _make_models(profile.problem_type)
    use_wf = profile.is_time_series and n_splits is not None
    min_train = max(int(len(X) * 0.5), 50)
    test_size = max(int(len(X) * 0.1), 20)

    if use_wf:
        benchmarks = _walk_forward_benchmark(X, y, models, profile.problem_type, min_train=min_train, test_size=test_size)
    else:
        benchmarks = _kfold_benchmark(X, y, models, profile.problem_type, n_splits=n_splits)

    benchmarks_path = out_dir / "benchmarks.csv"
    benchmarks.to_csv(benchmarks_path, index=False)
    log.info("automl_benchmark_done", models=list(benchmarks["model"]) if not benchmarks.empty else [])

    # 4. SHAP (best tree model)
    shap_df: pd.DataFrame | None = None
    tree_models = ["rf", "lgbm", "hgb", "xgb"]
    for mname in tree_models:
        if mname in models:
            try:
                best_model = models[mname]
                best_model.fit(X, y)
                shap_df = _shap_importance(best_model, X)
                if shap_df is not None:
                    shap_df.to_csv(out_dir / "shap_importance.csv", index=False)
                    break
            except Exception:
                continue

    # 5. Save profile
    profile_dict = {
        "n_rows": profile.n_rows, "n_cols": profile.n_cols,
        "problem_type": profile.problem_type, "target_col": profile.target_col,
        "date_col": profile.date_col, "split_recommendation": profile.split_recommendation,
        "compatible_models": profile.compatible_models, "warnings": profile.warnings,
    }
    (out_dir / "profile.json").write_text(json.dumps(profile_dict, indent=2), encoding="utf-8")

    # 6. Write report
    elapsed = time.time() - t0
    report_path = _write_report(
        out_dir=out_dir,
        profile=profile,
        benchmarks=benchmarks,
        shap_df=shap_df,
        preprocessing_summary=prep.summary(),
        dataset_name=csv_path.stem,
        elapsed_sec=elapsed,
    )
    log.info("automl_done", report=str(report_path), elapsed=f"{elapsed:.1f}s")
    return report_path
