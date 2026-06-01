"""Canonical R&D benchmark for V3 maize direction models.

This module deliberately centralizes the moving parts that differed between
the V3 horizon sweep and the model zoo: target construction, feature columns,
splitters, models, metrics, confidence intervals, and multiple-test correction.
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import (
    ExtraTreesClassifier,
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Lasso, LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import KFold
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mais.features import build_multi_horizon_targets
from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, INTERIM_DIR, PROJECT_ROOT
from mais.research.horizon_sweep import _feature_columns, _merge_features_targets
from mais.utils import read_table

MAX_DATE = pd.Timestamp("2022-12-31")
DEFAULT_HORIZONS = [28, 35, 40, 45, 60]
DEFAULT_MODELS = ["lasso", "histgb", "gaussian_nb", "logistic", "extratrees", "lgbm", "ridge"]
VALID_VERDICTS = {"CONFIRMÉ", "PROMETTEUR", "NEUTRE", "REJETÉ", "INCONCLU"}


@dataclass(frozen=True)
class CropYearWalkForward:
    """Expanding walk-forward with one US corn crop year per validation fold."""

    min_train_years: int = 5
    start_month: int = 9

    def crop_year(self, dates: pd.Series) -> pd.Series:
        dt = pd.to_datetime(dates)
        return np.where(dt.dt.month >= self.start_month, dt.dt.year + 1, dt.dt.year)

    def split(self, dates: pd.Series) -> list[tuple[np.ndarray, np.ndarray, int]]:
        crop_years = pd.Series(self.crop_year(dates), index=np.arange(len(dates)), dtype=int)
        unique_years = sorted(crop_years.dropna().unique().tolist())
        if len(unique_years) <= self.min_train_years:
            return []

        splits: list[tuple[np.ndarray, np.ndarray, int]] = []
        for val_year in unique_years[self.min_train_years :]:
            train_years = [year for year in unique_years if year < val_year]
            if len(train_years) < self.min_train_years:
                continue
            train_idx = crop_years[crop_years < val_year].index.to_numpy(dtype=int)
            val_idx = crop_years[crop_years == val_year].index.to_numpy(dtype=int)
            if len(train_idx) and len(val_idx):
                splits.append((train_idx, val_idx, int(val_year)))
        return splits


def run_project_canonical_benchmark(output_dir: Path | None = None) -> dict[str, Any]:
    """Run the canonical benchmark on the standard project artefacts."""
    features = pd.read_parquet(FEATURES_PARQUET)
    db = read_table(INTERIM_DIR / "database.parquet", date_col="Date")
    targets = build_multi_horizon_targets(db[["Date", "corn_close"]], DEFAULT_HORIZONS)
    out = output_dir if output_dir is not None else ARTEFACTS_DIR / "canonical"
    return run_canonical_benchmark(features, targets, output_dir=out)


def run_canonical_benchmark(
    features: pd.DataFrame,
    targets: pd.DataFrame,
    output_dir: Path,
    *,
    horizons: Iterable[int] = DEFAULT_HORIZONS,
    models: Iterable[str] = DEFAULT_MODELS,
    max_date: str | pd.Timestamp = MAX_DATE,
    n_bootstrap: int = 1000,
    random_state: int = 42,
    report_path: Path | None = None,
    protocol_path: Path | None = None,
) -> dict[str, Any]:
    """Run all canonical cells and write JSON/Markdown artefacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    oof_frames: list[pd.DataFrame] = []
    feature_counts: dict[str, int] = {}

    for horizon in [int(h) for h in horizons]:
        for model_name in models:
            for split_name in ("kfold_no_shuffle", "crop_year_walk_forward"):
                oof, n_features = run_model_oof(
                    features,
                    targets,
                    horizon=horizon,
                    model_name=str(model_name),
                    split_name=split_name,
                    max_date=max_date,
                    random_state=random_state,
                )
                feature_counts[f"{split_name}:{horizon}:{model_name}"] = n_features
                if oof.empty:
                    rows.append(_empty_metric_row(horizon, str(model_name), split_name, n_features))
                    continue
                rows.append(
                    summarize_oof(
                        oof,
                        horizon=horizon,
                        model_name=str(model_name),
                        split_name=split_name,
                        n_features=n_features,
                        n_bootstrap=n_bootstrap,
                        random_state=random_state,
                    )
                )
                oof_frames.append(oof)

    results = pd.DataFrame(rows)
    results = add_benjamini_hochberg(results, p_col="da_p_value", out_col="da_q_value")
    payload = {
        "metadata": {
            "horizons": [int(h) for h in horizons],
            "models": list(models),
            "max_date": str(pd.Timestamp(max_date).date()),
            "n_bootstrap": int(n_bootstrap),
            "splitters": ["kfold_no_shuffle", "crop_year_walk_forward"],
        },
        "feature_counts": feature_counts,
        "results": _json_records(results),
    }
    (output_dir / "benchmark_results.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    contradiction = analyze_sweep_zoo_contradiction(features, targets, output_dir=output_dir)
    write_benchmark_report(
        results,
        contradiction,
        report_path if report_path is not None else PROJECT_ROOT / "docs" / "BENCHMARK_CANONICAL.md",
    )
    write_protocol_freeze(
        protocol_path if protocol_path is not None else PROJECT_ROOT / "docs" / "PROTOCOL_FREEZE.md"
    )

    if oof_frames:
        oof_all = pd.concat(oof_frames, ignore_index=True)
        oof_all["fold_label"] = oof_all["fold_label"].astype(str)
        oof_all.to_parquet(output_dir / "canonical_oof_predictions.parquet", index=False)

    return {"results": payload, "contradiction": contradiction}


def run_model_oof(
    features: pd.DataFrame,
    targets: pd.DataFrame,
    *,
    horizon: int,
    model_name: str,
    split_name: str,
    max_date: str | pd.Timestamp = MAX_DATE,
    random_state: int = 42,
) -> tuple[pd.DataFrame, int]:
    """Return OOF predictions for one canonical cell."""
    target_col = f"y_cont_h{int(horizon)}"
    up_col = f"y_up_h{int(horizon)}"
    work = _merge_features_targets(features, targets, target_col, up_col, max_date=max_date)
    feature_cols = _feature_columns(work, exclude={target_col, up_col})
    if not feature_cols or len(work) < 80:
        return pd.DataFrame(), len(feature_cols)

    splits = _splits(work, split_name=split_name, random_state=random_state)
    if not splits:
        return pd.DataFrame(), len(feature_cols)

    frames: list[pd.DataFrame] = []
    spec = _model_spec(model_name, random_state=random_state)
    for fold, (train_idx, test_idx, fold_label) in enumerate(splits):
        train = work.iloc[train_idx].copy()
        test = work.iloc[test_idx].copy()
        if len(train) < 40 or len(test) < 10:
            continue
        pred_cont, p_up, method = _fit_predict(train, test, feature_cols, target_col, up_col, spec)
        frames.append(
            pd.DataFrame(
                {
                    "Date": test["Date"].values,
                    "horizon": int(horizon),
                    "model": model_name,
                    "split": split_name,
                    "fold": int(fold),
                    "fold_label": fold_label,
                    "y_true_cont": test[target_col].to_numpy(dtype=float),
                    "y_true_up": test[up_col].astype(int).to_numpy(),
                    "y_pred_cont": pred_cont,
                    "p_up": p_up,
                    "pred_up": (p_up >= 0.5).astype(int),
                    "prob_method": method,
                }
            )
        )
    return (pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()), len(feature_cols)


def summarize_oof(
    oof: pd.DataFrame,
    *,
    horizon: int,
    model_name: str,
    split_name: str,
    n_features: int,
    n_bootstrap: int = 1000,
    random_state: int = 42,
) -> dict[str, Any]:
    """Summarize one OOF frame with daily, weekly, annual, and CI metrics."""
    y = oof["y_true_up"].astype(int).to_numpy()
    p = np.clip(oof["p_up"].to_numpy(dtype=float), 0.0, 1.0)
    pred = (p >= 0.5).astype(int)
    confidence = np.abs(p - 0.5)
    top20 = confidence >= np.quantile(confidence, 0.80)
    annual_da = annual_directional_accuracy(oof)
    weekly = weekly_oof(oof)
    weekly_y = weekly["y_true_up"].astype(int).to_numpy() if not weekly.empty else np.array([], dtype=int)
    weekly_pred = weekly["pred_up"].astype(int).to_numpy() if not weekly.empty else np.array([], dtype=int)
    da = float(accuracy_score(y, pred))
    auc = safe_auc(y, p)
    da_ci = bootstrap_ci(y, pred, metric="da", n_bootstrap=n_bootstrap, random_state=random_state)
    auc_ci = bootstrap_ci(y, p, metric="auc", n_bootstrap=n_bootstrap, random_state=random_state)
    da_top20 = float(accuracy_score(y[top20], pred[top20])) if top20.any() else np.nan
    return {
        "horizon": int(horizon),
        "model": model_name,
        "split": split_name,
        "n_features": int(n_features),
        "n_obs_test": int(len(oof)),
        "n_folds": int(oof["fold"].nunique()),
        "test_start": str(pd.to_datetime(oof["Date"]).min().date()),
        "test_end": str(pd.to_datetime(oof["Date"]).max().date()),
        "da": da,
        "da_ci95_low": da_ci[0],
        "da_ci95_high": da_ci[1],
        "auc": auc,
        "auc_ci95_low": auc_ci[0],
        "auc_ci95_high": auc_ci[1],
        "brier": float(brier_score_loss(y, p)),
        "da_top20": da_top20,
        "da_weekly": float(accuracy_score(weekly_y, weekly_pred)) if len(weekly) else np.nan,
        "annual_da": annual_da,
        "weak_years": [int(year) for year, val in annual_da.items() if val < 0.48],
        "da_p_value": two_sided_accuracy_p_value(y, pred),
        "verdict": verdict_from_metrics(da, da_ci),
    }


def analyze_sweep_zoo_contradiction(
    features: pd.DataFrame,
    targets: pd.DataFrame,
    *,
    output_dir: Path,
    horizon: int = 40,
) -> dict[str, Any]:
    """Run small iso-experiments that decompose the sweep/zoo gap."""
    output_dir.mkdir(parents=True, exist_ok=True)
    target_col = f"y_cont_h{horizon}"
    up_col = f"y_up_h{horizon}"
    work = _merge_features_targets(features, targets, target_col, up_col, max_date=MAX_DATE)
    all_features = _feature_columns(work, exclude={target_col, up_col})
    factor_features = [col for col in all_features if col.startswith("factor_")]
    if not factor_features:
        factor_features = all_features

    experiments = {
        "lgbm_sweep_exact": ("lgbm_sweep_regressor", factor_features),
        "lgbm_zoo_exact": ("lgbm", all_features),
        "lgbm_swap_features": ("lgbm_sweep_regressor", all_features),
        "lgbm_swap_hyperparams": ("lgbm", factor_features),
    }
    scores: dict[str, float | None] = {}
    for name, (model_name, cols) in experiments.items():
        oof = _run_iso_oof(work, cols, target_col, up_col, model_name)
        scores[f"da_{name}"] = float((oof["pred_up"] == oof["y_true_up"]).mean()) if not oof.empty else None

    sweep = scores.get("da_lgbm_sweep_exact")
    zoo = scores.get("da_lgbm_zoo_exact")
    swap_features = scores.get("da_lgbm_swap_features")
    swap_params = scores.get("da_lgbm_swap_hyperparams")
    delta_features = _safe_delta(swap_features, sweep)
    delta_params = _safe_delta(swap_params, sweep)
    residual = _safe_delta(zoo, sweep)
    primary = "INCONCLU"
    explained = 0.0
    candidates = {
        "features": abs(delta_features or 0.0),
        "hyperparams_or_model_family": abs(delta_params or 0.0),
        "residual_protocol": abs(residual or 0.0),
    }
    if any(v > 0.03 for v in candidates.values()):
        primary = max(candidates, key=candidates.get)
        explained = candidates[primary]

    payload: dict[str, Any] = {
        "sweep_features_count": int(len(factor_features)),
        "zoo_features_count": int(len(all_features)),
        "sweep_target_construction": f"{target_col} / {up_col} from build_multi_horizon_targets",
        "zoo_target_construction": f"{target_col} / {up_col} from build_multi_horizon_targets",
        "sweep_lgbm_params": _params_for("lgbm_sweep_regressor"),
        "zoo_lgbm_params": _params_for("lgbm"),
        **scores,
        "identified_primary_cause": primary,
        "delta_da_explained_by_features": delta_features,
        "delta_da_explained_by_hyperparams": delta_params,
        "residual_unexplained": residual,
        "delta_explained_abs": explained,
    }
    (output_dir / "contradiction_analysis.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return payload


def annual_directional_accuracy(oof: pd.DataFrame) -> dict[int, float]:
    dates = pd.to_datetime(oof["Date"])
    crop_year = np.where(dates.dt.month >= 9, dates.dt.year + 1, dates.dt.year)
    tmp = oof.assign(crop_year=crop_year)
    out: dict[int, float] = {}
    for year, sub in tmp.groupby("crop_year"):
        out[int(year)] = float((sub["pred_up"].astype(int) == sub["y_true_up"].astype(int)).mean())
    return out


def weekly_oof(oof: pd.DataFrame) -> pd.DataFrame:
    tmp = oof.copy()
    tmp["Date"] = pd.to_datetime(tmp["Date"])
    mondays = tmp[tmp["Date"].dt.weekday == 0].copy()
    if not mondays.empty:
        return mondays
    tmp["week"] = tmp["Date"].dt.to_period("W-MON")
    return tmp.sort_values("Date").groupby("week", as_index=False).head(1).drop(columns=["week"])


def bootstrap_ci(
    y_true: np.ndarray,
    y_pred_or_score: np.ndarray,
    *,
    metric: str,
    n_bootstrap: int = 1000,
    random_state: int = 42,
) -> tuple[float, float]:
    rng = np.random.default_rng(random_state)
    y = np.asarray(y_true)
    x = np.asarray(y_pred_or_score)
    if len(y) == 0:
        return (np.nan, np.nan)
    stats: list[float] = []
    for _ in range(int(n_bootstrap)):
        idx = rng.integers(0, len(y), len(y))
        if metric == "auc":
            val = safe_auc(y[idx], x[idx])
        elif metric == "da":
            val = float(accuracy_score(y[idx], x[idx]))
        else:
            raise ValueError(metric)
        if math.isfinite(val):
            stats.append(float(val))
    if not stats:
        return (np.nan, np.nan)
    return (float(np.quantile(stats, 0.025)), float(np.quantile(stats, 0.975)))


def add_benjamini_hochberg(df: pd.DataFrame, *, p_col: str, out_col: str) -> pd.DataFrame:
    out = df.copy()
    out[out_col] = np.nan
    valid = out[p_col].notna()
    pvals = out.loc[valid, p_col].astype(float).to_numpy()
    if len(pvals) == 0:
        return out
    order = np.argsort(pvals)
    ranked = pvals[order]
    m = float(len(ranked))
    q = ranked * m / (np.arange(len(ranked)) + 1.0)
    q = np.minimum.accumulate(q[::-1])[::-1]
    restored = np.empty_like(q)
    restored[order] = np.clip(q, 0.0, 1.0)
    out.loc[valid, out_col] = restored
    return out


def verdict_from_metrics(da: float, da_ci: tuple[float, float]) -> str:
    if not math.isfinite(da) or not math.isfinite(da_ci[0]):
        return "INCONCLU"
    if da_ci[0] > 0.5:
        return "CONFIRMÉ"
    if da > 0.55:
        return "PROMETTEUR"
    if da < 0.48:
        return "REJETÉ"
    return "NEUTRE"


def write_benchmark_report(results: pd.DataFrame, contradiction: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Benchmark canonique V3",
        "",
        "Statut : généré par `mais.research.canonical_benchmark`.",
        "",
        "## Contradiction sweep / zoo",
        "",
        f"Cause primaire identifiée : `{contradiction.get('identified_primary_cause')}`.",
        f"Features sweep : {contradiction.get('sweep_features_count')} ; features zoo : {contradiction.get('zoo_features_count')}.",
        "",
        "## Résultats canoniques",
        "",
        "| Split | Horizon | Modèle | DA | IC95 DA | AUC | IC95 AUC | DA hebdo | Verdict |",
        "|---|---:|---|---:|---|---:|---|---:|---|",
    ]
    for _, row in results.sort_values(["split", "horizon", "model"]).iterrows():
        lines.append(
            f"| {row['split']} | J+{int(row['horizon'])} | {row['model']} | "
            f"{_fmt(row['da'])} | [{_fmt(row['da_ci95_low'])}; {_fmt(row['da_ci95_high'])}] | "
            f"{_fmt(row['auc'])} | [{_fmt(row['auc_ci95_low'])}; {_fmt(row['auc_ci95_high'])}] | "
            f"{_fmt(row['da_weekly'])} | {row['verdict']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_protocol_freeze(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = """# Protocol Freeze — R&D maïs

Ce protocole est figé par R&D-01 avant les tickets de modélisation suivants.

- Période d'optimisation : 2010–2022 uniquement.
- Backtest final non réoptimisé : 2023–2025.
- Validation crop years : 2015–2022 si les données 2022 sont complètes.
- Horizons autorisés : J+28, J+35, J+40, J+45, J+60.
- Target directionnelle : `y_up_hH` construite par `build_multi_horizon_targets`.
- Features autorisées : colonnes numériques de `build_features()`, hors `Date` et colonnes `y_*`.
- Heure du signal : fin de journée ; les fondamentaux restent shiftés selon leur calendrier de publication.
- Fréquences d'évaluation : quotidienne et hebdomadaire lundi.
- Métriques principales : DA, AUC, Brier, DA_top20, DA par crop year, IC95 bootstrap.
- Correction tests multiples : Benjamini-Hochberg sur les comparaisons inter-modèles.
- Règle 2026+ production : aucun seuil métier ne doit être recalibré hors validation OOF documentée.
"""
    path.write_text(text, encoding="utf-8")


def safe_auc(y_true: np.ndarray, p_up: np.ndarray) -> float:
    try:
        if len(np.unique(y_true)) < 2:
            return np.nan
        return float(roc_auc_score(y_true, p_up))
    except ValueError:
        return np.nan


def two_sided_accuracy_p_value(y_true: np.ndarray, pred: np.ndarray) -> float:
    n = int(len(y_true))
    if n == 0:
        return np.nan
    correct = int(np.sum(np.asarray(y_true) == np.asarray(pred)))
    mean = n * 0.5
    sd = math.sqrt(n * 0.25)
    if sd == 0:
        return np.nan
    z = abs((correct - mean) / sd)
    return float(math.erfc(z / math.sqrt(2.0)))


def _splits(
    work: pd.DataFrame,
    *,
    split_name: str,
    random_state: int,
) -> list[tuple[np.ndarray, np.ndarray, int | str]]:
    if split_name == "crop_year_walk_forward":
        return CropYearWalkForward().split(work["Date"])
    if split_name == "kfold_no_shuffle":
        kfold = KFold(n_splits=5, shuffle=False)
        return [(train, test, f"fold_{i}") for i, (train, test) in enumerate(kfold.split(work))]
    raise ValueError(split_name)


def _model_spec(model_name: str, random_state: int) -> dict[str, Any]:
    specs: dict[str, dict[str, Any]] = {
        "lasso": {"kind": "regressor", "estimator": Pipeline([("scaler", StandardScaler()), ("model", Lasso(alpha=0.001, max_iter=5000))])},
        "ridge": {"kind": "regressor", "estimator": Pipeline([("scaler", StandardScaler()), ("model", Ridge(alpha=1.0))])},
        "logistic": {"kind": "classifier", "estimator": Pipeline([("scaler", StandardScaler()), ("model", LogisticRegression(C=1.0, max_iter=500, random_state=random_state))])},
        "gaussian_nb": {"kind": "classifier", "estimator": Pipeline([("scaler", StandardScaler()), ("model", GaussianNB())])},
        "extratrees": {"kind": "classifier", "estimator": ExtraTreesClassifier(n_estimators=40, max_depth=6, min_samples_leaf=20, random_state=random_state, n_jobs=-1)},
        "histgb": {"kind": "classifier", "estimator": HistGradientBoostingClassifier(max_iter=40, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0, random_state=random_state)},
        "lgbm_sweep_regressor": {"kind": "regressor", "estimator": _lgbm_sweep_estimator(random_state)},
        "lgbm": {"kind": "classifier", "estimator": _lgbm_classifier(random_state)},
    }
    if model_name not in specs:
        raise ValueError(model_name)
    return specs[model_name]


def _lgbm_classifier(random_state: int) -> Any:
    try:
        import lightgbm as lgb

        return lgb.LGBMClassifier(
            n_estimators=40,
            learning_rate=0.05,
            num_leaves=15,
            min_child_samples=40,
            lambda_l2=1.0,
            verbose=-1,
            random_state=random_state,
        )
    except ImportError:
        return HistGradientBoostingClassifier(
            max_iter=40,
            learning_rate=0.05,
            max_leaf_nodes=15,
            l2_regularization=1.0,
            random_state=random_state,
        )


def _lgbm_sweep_estimator(random_state: int) -> Any:
    try:
        import lightgbm as lgb

        return lgb.LGBMRegressor(
            n_estimators=80,
            learning_rate=0.05,
            num_leaves=15,
            min_child_samples=40,
            lambda_l2=1.0,
            feature_fraction=0.8,
            bagging_fraction=0.8,
            bagging_freq=5,
            verbose=-1,
            random_state=random_state,
        )
    except ImportError:
        return HistGradientBoostingRegressor(
            max_iter=80,
            learning_rate=0.05,
            max_leaf_nodes=15,
            l2_regularization=1.0,
            random_state=random_state,
        )


def _fit_predict(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    up_col: str,
    spec: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray, str]:
    imputer = SimpleImputer(strategy="median", keep_empty_features=True)
    x_train = train[feature_cols].replace([np.inf, -np.inf], np.nan)
    x_test = test[feature_cols].replace([np.inf, -np.inf], np.nan)
    x_train_i = pd.DataFrame(imputer.fit_transform(x_train), columns=feature_cols)
    x_test_i = pd.DataFrame(imputer.transform(x_test), columns=feature_cols)
    estimator = clone(spec["estimator"])
    if spec["kind"] == "regressor":
        y_train = train[target_col].to_numpy(dtype=float)
        estimator.fit(x_train_i, y_train)
        pred = np.asarray(estimator.predict(x_test_i), dtype=float)
        scale = float(np.nanstd(y_train))
        if not math.isfinite(scale) or scale <= 1e-8:
            scale = 0.03
        return pred, _sigmoid(pred / scale), "regression_sign"

    y_train = train[up_col].astype(int).to_numpy()
    if len(np.unique(y_train)) < 2:
        p = np.full(len(test), float(y_train.mean()))
        return p - 0.5, p, "constant"
    estimator.fit(x_train_i, y_train)
    if hasattr(estimator, "predict_proba"):
        p = np.asarray(estimator.predict_proba(x_test_i)[:, 1], dtype=float)
        return p - 0.5, np.clip(p, 0.0, 1.0), "predict_proba"
    pred = np.asarray(estimator.predict(x_test_i), dtype=float)
    return pred - 0.5, np.clip(pred, 0.0, 1.0), "predict"


def _run_iso_oof(
    work: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    up_col: str,
    model_name: str,
) -> pd.DataFrame:
    splits = _splits(work, split_name="kfold_no_shuffle", random_state=42)
    frames: list[pd.DataFrame] = []
    spec = _model_spec(model_name, random_state=42)
    for fold, (train_idx, test_idx, _) in enumerate(splits):
        train = work.iloc[train_idx].copy()
        test = work.iloc[test_idx].copy()
        pred, p, method = _fit_predict(train, test, feature_cols, target_col, up_col, spec)
        frames.append(
            pd.DataFrame(
                {
                    "fold": fold,
                    "y_true_up": test[up_col].astype(int).to_numpy(),
                    "pred_up": (p >= 0.5).astype(int),
                    "p_up": p,
                    "prob_method": method,
                    "y_pred_cont": pred,
                }
            )
        )
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _params_for(model_name: str) -> dict[str, Any]:
    estimator = _model_spec(model_name, random_state=42)["estimator"]
    if hasattr(estimator, "get_params"):
        params = estimator.get_params()
        return {k: v for k, v in params.items() if isinstance(v, (str, int, float, bool, type(None)))}
    return {"repr": repr(estimator)}


def _safe_delta(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return float(a - b)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(np.asarray(x, dtype=float), -50.0, 50.0)))


def _fmt(value: Any) -> str:
    try:
        val = float(value)
    except (TypeError, ValueError):
        return "NA"
    return "NA" if not math.isfinite(val) else f"{val:.3f}"


def _json_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    records = []
    for record in df.to_dict(orient="records"):
        clean: dict[str, Any] = {}
        for key, value in record.items():
            if isinstance(value, float) and not math.isfinite(value):
                clean[key] = None
            elif isinstance(value, np.generic):
                clean[key] = value.item()
            else:
                clean[key] = value
        records.append(clean)
    return records


def _empty_metric_row(horizon: int, model_name: str, split_name: str, n_features: int) -> dict[str, Any]:
    return {
        "horizon": int(horizon),
        "model": model_name,
        "split": split_name,
        "n_features": int(n_features),
        "n_obs_test": 0,
        "n_folds": 0,
        "test_start": None,
        "test_end": None,
        "da": np.nan,
        "da_ci95_low": np.nan,
        "da_ci95_high": np.nan,
        "auc": np.nan,
        "auc_ci95_low": np.nan,
        "auc_ci95_high": np.nan,
        "brier": np.nan,
        "da_top20": np.nan,
        "da_weekly": np.nan,
        "annual_da": {},
        "weak_years": [],
        "da_p_value": np.nan,
        "verdict": "INCONCLU",
    }


if __name__ == "__main__":
    run_project_canonical_benchmark()
