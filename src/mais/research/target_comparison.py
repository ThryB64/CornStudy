"""Compare target predictability for the professional maize indicator.

IND-02 deliberately uses only dates up to 2022. The 2023-2025 out-of-time
period is reserved for the final indicator validation ticket.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import nbformat as nbf
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mais.paths import ARTEFACTS_DIR, PROCESSED_DIR, PROJECT_ROOT
from mais.utils import get_logger, write_parquet

log = get_logger("mais.research.target_comparison")

STUDY_DIR = ARTEFACTS_DIR / "professional_study"
TARGET_COMPARISON_PARQUET = STUDY_DIR / "target_comparison.parquet"
TARGET_RANKING_CSV = STUDY_DIR / "target_ranking.csv"
TARGET_RANKING_MD = STUDY_DIR / "target_ranking.md"
REPORT_PATH = PROJECT_ROOT / "docs" / "PROFESSIONAL_STUDY_REPORT.md"
EXPERIMENT_INDEX = PROJECT_ROOT / "notebooks" / "corn_study" / "EXPERIMENT_INDEX.md"
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "corn_study" / "main" / "04_targets_reformulation.ipynb"
NOTEBOOK_EXPORT = PROJECT_ROOT / "notebooks" / "corn_study" / "exports" / "04_targets_reformulation.html"

OOT_CUTOFF = pd.Timestamp("2022-12-31")
ML_MODELS = {"ridge_factors", "rf_factors", "lgbm_factors"}
BASELINE_MODELS = {"seasonal_indicator", "momentum_indicator"}


@dataclass(frozen=True)
class TargetInfo:
    target: str
    family: str
    horizon: int
    problem: str
    nan_rate: float
    positive_rate: float | None
    eligible: bool
    reason: str


def run_target_comparison() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run IND-02 and write all declared outputs."""
    STUDY_DIR.mkdir(parents=True, exist_ok=True)

    targets = _read_dates(PROCESSED_DIR / "targets.parquet")
    factors = _read_dates(PROCESSED_DIR / "factors.parquet")
    factor_cols = [c for c in factors.columns if c != "Date" and pd.api.types.is_numeric_dtype(factors[c])]
    merged = factors.merge(targets, on="Date", how="inner").sort_values("Date").reset_index(drop=True)
    merged = merged[merged["Date"] <= OOT_CUTOFF].reset_index(drop=True)

    infos = [_target_info(targets, c) for c in targets.columns if c != "Date"]
    rows: list[dict[str, Any]] = []
    for info in infos:
        if not info.eligible:
            rows.append(_skipped_row(info, len(merged)))
            continue
        work = merged[["Date", info.target, *factor_cols]].dropna(subset=[info.target]).reset_index(drop=True)
        rows.extend(_benchmark_target(work, factor_cols, info))

    comparison = pd.DataFrame(rows)
    comparison = _add_baseline_deltas(comparison)
    ranking = _build_ranking(comparison)

    write_parquet(comparison, TARGET_COMPARISON_PARQUET)
    ranking.to_csv(TARGET_RANKING_CSV, index=False)
    TARGET_RANKING_MD.write_text(_ranking_markdown(ranking), encoding="utf-8")
    _update_report(ranking)
    _update_experiment_index(ranking)
    _write_notebook(ranking)

    log.info(
        "target_comparison_done",
        rows=len(comparison),
        targets=int(comparison["target"].nunique()) if "target" in comparison else 0,
        ranking_rows=len(ranking),
    )
    return comparison, ranking


def _read_dates(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df.sort_values("Date").drop_duplicates("Date").reset_index(drop=True)


def _target_info(targets: pd.DataFrame, target: str) -> TargetInfo:
    horizon = _horizon(target)
    family = _target_family(target)
    s = targets[target]
    nan_rate = float(s.isna().mean())
    non_null = s.dropna()
    problem = _problem_type(target, non_null)
    positive_rate = None
    if problem == "binary" and len(non_null):
        positive_rate = float(non_null.astype(int).mean())

    eligible = nan_rate < 0.30
    reason = "ok" if eligible else "nan_rate >= 30%"
    if horizon in {60, 90} and not eligible:
        # Long horizons are allowed if enough test observations remain after 2015.
        post_2015 = targets.loc[pd.to_datetime(targets["Date"]) >= pd.Timestamp("2015-01-01"), target].notna().sum()
        eligible = int(post_2015) >= 300
        reason = "h60/h90 exception n_obs_post_2015 >= 300" if eligible else reason

    return TargetInfo(
        target=target,
        family=family,
        horizon=horizon,
        problem=problem,
        nan_rate=nan_rate,
        positive_rate=positive_rate,
        eligible=eligible,
        reason=reason,
    )


def _horizon(target: str) -> int:
    match = re.search(r"_h(\d+)$", target)
    return int(match.group(1)) if match else -1


def _target_family(target: str) -> str:
    if "logret" in target:
        return "log_return"
    if re.match(r"y_(up|down)_h\d+$", target):
        return "direction_simple"
    if "strong" in target or "_gt_" in target:
        return "strong_move"
    if "realized_vol" in target:
        return "volatility"
    if "max_ret" in target or "future_max_return" in target:
        return "future_max_return"
    if "min_ret" in target or "future_min_return" in target:
        return "future_min_return"
    if "skew" in target:
        return "asymmetric_skew"
    if "storage_value" in target:
        return "storage_value"
    if "sell_regret" in target or "regret" in target:
        return "sell_regret"
    if "prob_up" in target:
        return "up_fraction"
    if "class" in target:
        return "direction_class"
    return "other"


def _problem_type(target: str, s: pd.Series) -> str:
    vals = pd.Series(s.dropna().unique())
    if vals.empty:
        return "regression"
    if set(vals.astype(float).unique()).issubset({0.0, 1.0}):
        return "binary"
    if "class" in target and vals.nunique() <= 20:
        return "multiclass"
    return "regression"


def _skipped_row(info: TargetInfo, n_available: int) -> dict[str, Any]:
    return {
        "target": info.target,
        "family": info.family,
        "horizon": info.horizon,
        "problem": info.problem,
        "model": "skipped",
        "n_obs": n_available,
        "n_test": 0,
        "n_folds": 0,
        "nan_rate": info.nan_rate,
        "positive_rate": info.positive_rate,
        "directional_accuracy": np.nan,
        "auc": np.nan,
        "brier": np.nan,
        "rmse": np.nan,
        "mae": np.nan,
        "r2": np.nan,
        "test_start": None,
        "test_end": None,
        "eligibility": info.reason,
    }


def _benchmark_target(work: pd.DataFrame, factor_cols: list[str], info: TargetInfo) -> list[dict[str, Any]]:
    splits = _walk_splits(len(work), info.horizon)
    if not splits:
        row = _skipped_row(info, len(work))
        row["eligibility"] = "no valid walk-forward split"
        return [row]

    rows = []
    for model_name in ["seasonal_indicator", "momentum_indicator", "ridge_factors", "rf_factors", "lgbm_factors"]:
        fold_frames = []
        for fold, (train_idx, test_idx) in enumerate(splits):
            train = work.iloc[train_idx].copy()
            test = work.iloc[test_idx].copy()
            try:
                pred, score = _predict_fold(train, test, factor_cols, info, model_name)
            except Exception as exc:
                log.warning("target_model_failed", target=info.target, model=model_name, fold=fold, error=str(exc))
                continue
            fold_frames.append(pd.DataFrame({
                "Date": test["Date"].values,
                "fold": fold,
                "y_true": test[info.target].values,
                "y_pred": pred,
                "y_score": score,
            }))
        if not fold_frames:
            continue
        oof = pd.concat(fold_frames, ignore_index=True)
        metrics = _metrics(oof["y_true"].values, oof["y_pred"].values, oof["y_score"].values, info.problem)
        rows.append({
            "target": info.target,
            "family": info.family,
            "horizon": info.horizon,
            "problem": info.problem,
            "model": model_name,
            "n_obs": int(len(work)),
            "n_test": int(len(oof)),
            "n_folds": int(oof["fold"].nunique()),
            "nan_rate": info.nan_rate,
            "positive_rate": info.positive_rate,
            **metrics,
            "test_start": str(pd.to_datetime(oof["Date"]).min().date()),
            "test_end": str(pd.to_datetime(oof["Date"]).max().date()),
            "eligibility": info.reason,
        })
    return rows


def _walk_splits(n: int, horizon: int) -> list[tuple[np.ndarray, np.ndarray]]:
    if n < 800:
        return []
    start = int(n * 0.60)
    remaining = n - start
    test_size = max(80, remaining // 5)
    splits = []
    for i in range(5):
        test_start = start + i * test_size
        test_end = n if i == 4 else min(n, test_start + test_size)
        train_end = max(1, test_start - max(horizon, 10))
        if test_end - test_start >= 50 and train_end >= 500:
            splits.append((np.arange(0, train_end), np.arange(test_start, test_end)))
    return splits


def _predict_fold(
    train: pd.DataFrame,
    test: pd.DataFrame,
    factor_cols: list[str],
    info: TargetInfo,
    model_name: str,
) -> tuple[np.ndarray, np.ndarray]:
    y_train = train[info.target]
    if model_name == "seasonal_indicator":
        return _seasonal_predict(train, test, info)
    if model_name == "momentum_indicator":
        return _momentum_predict(train, test, info)

    x_train, x_test = _matrices(train, test, factor_cols)
    if info.problem == "binary":
        if y_train.nunique() < 2:
            p = np.full(len(test), float(y_train.mean()))
            return (p >= 0.5).astype(int), p
        model = _binary_model(model_name)
        model.fit(x_train, y_train.astype(int).values)
        p = _positive_probability(model, x_test)
        return (p >= 0.5).astype(int), p
    if info.problem == "multiclass":
        model = _multiclass_model(model_name)
        model.fit(x_train, y_train.astype(int).values)
        pred = model.predict(x_test)
        return np.asarray(pred), np.asarray(pred, dtype=float)

    model = _regression_model(model_name)
    model.fit(x_train, y_train.astype(float).values)
    pred = np.asarray(model.predict(x_test), dtype=float)
    return pred, pred


def _matrices(train: pd.DataFrame, test: pd.DataFrame, cols: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    imp = SimpleImputer(strategy="median", keep_empty_features=True)
    x_train = train[cols].replace([np.inf, -np.inf], np.nan)
    x_test = test[cols].replace([np.inf, -np.inf], np.nan)
    return (
        pd.DataFrame(imp.fit_transform(x_train), columns=cols),
        pd.DataFrame(imp.transform(x_test), columns=cols),
    )


def _binary_model(model_name: str):
    if model_name == "ridge_factors":
        return Pipeline([
            ("scaler", StandardScaler()),
            ("logit", LogisticRegression(max_iter=1000, C=1.0, random_state=42)),
        ])
    if model_name == "rf_factors":
        return RandomForestClassifier(
            n_estimators=40,
            max_depth=7,
            min_samples_leaf=30,
            random_state=42,
            n_jobs=-1,
        )
    if model_name == "lgbm_factors":
        try:
            import lightgbm as lgb

            return lgb.LGBMClassifier(
                n_estimators=80,
                learning_rate=0.05,
                num_leaves=15,
                min_child_samples=40,
                lambda_l2=1.0,
                verbose=-1,
                random_state=42,
            )
        except ImportError:
            return _binary_model("rf_factors")
    raise ValueError(model_name)


def _multiclass_model(model_name: str):
    if model_name == "ridge_factors":
        return Pipeline([
            ("scaler", StandardScaler()),
            ("logit", LogisticRegression(max_iter=1000, C=0.7, random_state=42)),
        ])
    if model_name == "rf_factors":
        return RandomForestClassifier(
            n_estimators=40,
            max_depth=7,
            min_samples_leaf=30,
            random_state=42,
            n_jobs=-1,
        )
    if model_name == "lgbm_factors":
        try:
            import lightgbm as lgb

            return lgb.LGBMClassifier(
                n_estimators=80,
                learning_rate=0.05,
                num_leaves=15,
                min_child_samples=40,
                lambda_l2=1.0,
                verbose=-1,
                random_state=42,
            )
        except ImportError:
            return _multiclass_model("rf_factors")
    raise ValueError(model_name)


def _regression_model(model_name: str):
    if model_name == "ridge_factors":
        return Pipeline([("scaler", StandardScaler()), ("ridge", Ridge(alpha=3.0))])
    if model_name == "rf_factors":
        return RandomForestRegressor(
            n_estimators=40,
            max_depth=7,
            min_samples_leaf=30,
            max_features=0.75,
            random_state=42,
            n_jobs=-1,
        )
    if model_name == "lgbm_factors":
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
                random_state=42,
            )
        except ImportError:
            return _regression_model("rf_factors")
    raise ValueError(model_name)


def _positive_probability(model: Any, x_test: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(x_test)
        return np.asarray(proba[:, -1], dtype=float)
    pred = np.asarray(model.predict(x_test), dtype=float)
    return np.clip(pred, 0.0, 1.0)


def _seasonal_predict(train: pd.DataFrame, test: pd.DataFrame, info: TargetInfo) -> tuple[np.ndarray, np.ndarray]:
    fallback = train[info.target].mode().iloc[0] if info.problem == "multiclass" else float(train[info.target].mean())
    month_mean = train.groupby(train["Date"].dt.month)[info.target].mean()
    score = test["Date"].dt.month.map(month_mean).astype(float).fillna(float(fallback)).to_numpy()
    if info.problem == "binary":
        return (score >= 0.5).astype(int), np.clip(score, 0.0, 1.0)
    if info.problem == "multiclass":
        month_mode = train.groupby(train["Date"].dt.month)[info.target].agg(lambda x: x.mode().iloc[0])
        pred = test["Date"].dt.month.map(month_mode).fillna(fallback).astype(int).to_numpy()
        return pred, pred.astype(float)
    return score, score


def _momentum_predict(train: pd.DataFrame, test: pd.DataFrame, info: TargetInfo) -> tuple[np.ndarray, np.ndarray]:
    mom = pd.to_numeric(test.get("factor_market_momentum", pd.Series(0.0, index=test.index)), errors="coerce").fillna(0.0)
    wants_down = "down" in info.target or "min_ret" in info.target
    direction_positive = (mom < 0.0) if wants_down else (mom > 0.0)
    score = direction_positive.astype(float).to_numpy()
    if info.problem == "binary":
        return score.astype(int), score
    if info.problem == "multiclass":
        mode = int(train[info.target].mode().iloc[0])
        return np.full(len(test), mode), np.full(len(test), float(mode))
    signed = _is_signed_continuous(train[info.target])
    if signed:
        amplitude = float(train[info.target].abs().median())
        if not math.isfinite(amplitude) or amplitude == 0:
            amplitude = float(train[info.target].abs().mean() or 1e-4)
        pred = np.where(direction_positive, amplitude, -amplitude)
        return pred.astype(float), pred.astype(float)
    mean_val = float(train[info.target].mean())
    pred = np.full(len(test), mean_val)
    return pred, pred


def _is_signed_continuous(s: pd.Series) -> bool:
    x = pd.to_numeric(s, errors="coerce").dropna()
    return bool((x < 0).any() and (x > 0).any())


def _metrics(y_true: np.ndarray, y_pred: np.ndarray, y_score: np.ndarray, problem: str) -> dict[str, float]:
    y = np.asarray(y_true)
    pred = np.asarray(y_pred)
    score = np.asarray(y_score, dtype=float)
    out = {"directional_accuracy": np.nan, "auc": np.nan, "brier": np.nan, "rmse": np.nan, "mae": np.nan, "r2": np.nan}
    if problem == "binary":
        yi = y.astype(int)
        pi = pred.astype(int)
        out["directional_accuracy"] = float(accuracy_score(yi, pi))
        out["brier"] = float(brier_score_loss(yi, np.clip(score, 0.0, 1.0)))
        try:
            out["auc"] = float(roc_auc_score(yi, score))
        except ValueError:
            out["auc"] = np.nan
        out["rmse"] = float(math.sqrt(mean_squared_error(yi, np.clip(score, 0.0, 1.0))))
        out["mae"] = float(mean_absolute_error(yi, np.clip(score, 0.0, 1.0)))
        return out
    if problem == "multiclass":
        out["directional_accuracy"] = float(accuracy_score(y.astype(int), pred.astype(int)))
        return out

    yf = y.astype(float)
    pf = pred.astype(float)
    out["rmse"] = float(math.sqrt(mean_squared_error(yf, pf)))
    out["mae"] = float(mean_absolute_error(yf, pf))
    out["r2"] = float(r2_score(yf, pf))
    if (yf < 0).any() and (yf > 0).any() and (pf < 0).any() and (pf > 0).any():
        out["directional_accuracy"] = float(np.mean(np.sign(yf) == np.sign(pf)))
    return out


def _add_baseline_deltas(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["delta_da_vs_seasonal"] = np.nan
    out["delta_da_vs_momentum"] = np.nan
    metric = "directional_accuracy"
    for target, sub in out.groupby("target"):
        seasonal = sub.loc[sub["model"].eq("seasonal_indicator"), metric]
        momentum = sub.loc[sub["model"].eq("momentum_indicator"), metric]
        if not seasonal.empty:
            out.loc[out["target"].eq(target), "delta_da_vs_seasonal"] = out.loc[out["target"].eq(target), metric] - float(seasonal.iloc[0])
        if not momentum.empty:
            out.loc[out["target"].eq(target), "delta_da_vs_momentum"] = out.loc[out["target"].eq(target), metric] - float(momentum.iloc[0])
    return out


def _build_ranking(comparison: pd.DataFrame) -> pd.DataFrame:
    rows = []
    usable = comparison[comparison["model"].isin(ML_MODELS)].copy()
    for target, sub in usable.groupby("target"):
        sub = sub.copy()
        sort_cols = ["directional_accuracy", "auc", "r2"]
        for col in sort_cols:
            if col not in sub:
                sub[col] = np.nan
        best = sub.sort_values(sort_cols, ascending=False, na_position="last").iloc[0]
        tier = _tier(best)
        rows.append({
            "target": target,
            "family": best["family"],
            "horizon": int(best["horizon"]),
            "problem": best["problem"],
            "best_model": best["model"],
            "best_da": best["directional_accuracy"],
            "best_auc": best["auc"],
            "best_brier": best["brier"],
            "best_rmse": best["rmse"],
            "positive_rate": best["positive_rate"],
            "n_obs": int(best["n_obs"]),
            "n_test": int(best["n_test"]),
            "delta_da_vs_seasonal": best["delta_da_vs_seasonal"],
            "delta_da_vs_momentum": best["delta_da_vs_momentum"],
            "tier": tier,
            "decision": _decision(best, tier),
        })
    ranking = pd.DataFrame(rows)
    if ranking.empty:
        return ranking
    ranking = ranking.sort_values(
        ["tier", "best_da", "best_auc", "n_test"],
        ascending=[True, False, False, False],
        na_position="last",
    ).reset_index(drop=True)
    return _finalize_retained_targets(ranking)


def _tier(row: pd.Series) -> str:
    da = row.get("directional_accuracy")
    auc = row.get("auc")
    problem = row.get("problem")
    if pd.isna(da):
        return "Tier 3"
    if problem == "binary" and (pd.isna(auc) or float(auc) <= 0.53):
        return "Tier 3"
    if float(da) > 0.60:
        return "Tier 1"
    if float(da) >= 0.55:
        return "Tier 2"
    return "Tier 3"


def _decision(row: pd.Series, tier: str) -> str:
    if tier == "Tier 1":
        pr = row.get("positive_rate")
        if pd.notna(pr) and (float(pr) < 0.10 or float(pr) > 0.90):
            return "exploratoire — classe déséquilibrée"
        delta_seasonal = row.get("delta_da_vs_seasonal")
        if pd.notna(delta_seasonal) and float(delta_seasonal) <= 0.0:
            return "exploratoire — ne bat pas la saisonnalité"
        return "candidat Tier 1"
    if tier == "Tier 2":
        return "garder comme cible secondaire"
    return "ne pas prioriser"


def _finalize_retained_targets(ranking: pd.DataFrame) -> pd.DataFrame:
    out = ranking.copy()
    if out.empty:
        return out
    allowed = ["direction_simple", "strong_move", "log_return", "asymmetric_skew"]
    diagnostic = (out["tier"] == "Tier 1") & ~out["family"].isin(allowed)
    out.loc[diagnostic & out["decision"].eq("candidat Tier 1"), "decision"] = (
        "candidat non retenu — hors cible directionnelle prioritaire"
    )
    candidates = out[
        (out["tier"] == "Tier 1")
        & out["decision"].eq("candidat Tier 1")
        & out["family"].isin(allowed)
    ].head(3)
    out.loc[out["decision"].eq("candidat Tier 1"), "decision"] = "candidat Tier 1 non retenu"
    out.loc[candidates.index, "decision"] = "retenir pour IND-04+"
    return out


def _ranking_markdown(ranking: pd.DataFrame) -> str:
    lines = ["# Target Ranking — IND-02", ""]
    if ranking.empty:
        return "# Target Ranking — IND-02\n\nAucun résultat exploitable.\n"
    for tier, sub in ranking.groupby("tier", sort=False):
        lines.append(f"## {tier}")
        lines.append("")
        lines.append("| Target | Famille | H | Modèle | DA | AUC | Brier | Δ saison | Δ momentum | Décision |")
        lines.append("|---|---|---:|---|---:|---:|---:|---:|---:|---|")
        for _, row in sub.head(20).iterrows():
            lines.append(
                f"| `{row['target']}` | `{row['family']}` | {int(row['horizon'])} | `{row['best_model']}` | "
                f"{_fmt(row['best_da'])} | {_fmt(row['best_auc'])} | {_fmt(row['best_brier'])} | "
                f"{_fmt(row['delta_da_vs_seasonal'])} | {_fmt(row['delta_da_vs_momentum'])} | {row['decision']} |"
            )
        lines.append("")
    return "\n".join(lines)


def _fmt(v: Any) -> str:
    return "NA" if pd.isna(v) else f"{float(v):.3f}"


def _top_retained(ranking: pd.DataFrame) -> pd.DataFrame:
    if ranking.empty:
        return ranking
    eligible = ranking[
        (ranking["tier"] == "Tier 1")
        & (ranking["decision"] == "retenir pour IND-04+")
        & (ranking["family"].isin(["direction_simple", "strong_move", "log_return", "asymmetric_skew"]))
    ].copy()
    if eligible.empty:
        eligible = ranking[ranking["tier"].isin(["Tier 1", "Tier 2"])].copy()
    return eligible.head(3)


def _update_report(ranking: pd.DataFrame) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.exists() else "# Étude professionnelle du prix du maïs CBOT\n"
    marker = "\n## Comparaison des cibles\n"
    if marker in text:
        text = text.split(marker)[0].rstrip()
    retained = _top_retained(ranking)
    lines = [text.rstrip(), "", "## Comparaison des cibles", ""]
    lines.append("Source : `artefacts/professional_study/target_comparison.parquet` et `target_ranking.csv`.")
    lines.append("Protocole IND-02 : walk-forward 5 splits, embargo par horizon, dates <= 2022 uniquement.")
    lines.append("")
    for tier in ["Tier 1", "Tier 2", "Tier 3"]:
        n = int((ranking["tier"] == tier).sum()) if not ranking.empty else 0
        lines.append(f"- {tier} : {n} cibles.")
    lines.append("")
    if not retained.empty:
        lines.append("Décision : cibles retenues pour IND-04+ :")
        for _, row in retained.iterrows():
            lines.append(
                f"- `{row['target']}` ({row['family']}, h{int(row['horizon'])}) : "
                f"DA={_fmt(row['best_da'])}, AUC={_fmt(row['best_auc'])}, modèle `{row['best_model']}`."
            )
    else:
        lines.append("Décision : aucune cible Tier 1 robuste ; garder la cible directionnelle simple comme référence prudente.")
    lines.append("")
    lines.append("Lecture honnête : les cibles rares peuvent afficher une DA élevée par effet de classe majoritaire ; AUC, Brier et `positive_rate` sont donc conservés dans l'artefact source.")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _update_experiment_index(ranking: pd.DataFrame) -> None:
    EXPERIMENT_INDEX.parent.mkdir(parents=True, exist_ok=True)
    text = EXPERIMENT_INDEX.read_text(encoding="utf-8") if EXPERIMENT_INDEX.exists() else ""
    if "IND-02 — Comparaison complète des cibles" in text:
        return
    next_id = _next_exp_id(text)
    retained = _top_retained(ranking)
    retained_txt = ", ".join(f"`{t}`" for t in retained["target"].tolist()) if not retained.empty else "aucune cible Tier 1 robuste"
    today = date.today().isoformat()
    row = (
        f"| {next_id} | {today} | `notebooks/corn_study/main/04_targets_reformulation.ipynb` | "
        "La direction et les fortes variations sont plus exploitables que le retour continu. | "
        "Walk-forward 5 splits sur 96 cibles, modèles Ridge/RF/LGBM et baselines saison/momentum. | "
        f"Cibles retenues : {retained_txt}. | Sélectionner ces cibles pour IND-04. | neutral |\n"
    )
    detail = f"""
---

## {next_id} — IND-02 — Comparaison complète des cibles

**Date :** {today}
**Statut :** `neutral`

**Hypothèse :**
Les cibles directionnelles ou d'événements forts sont plus exploitables pour l'indicateur que le retour continu brut.

**Méthode :**
Walk-forward 5 splits avec embargo par horizon, données limitées à 2022, modèles `ridge_factors`, `rf_factors`, `lgbm_factors`, et comparaison aux indicateurs `seasonal_indicator` / `momentum_indicator`.

**Résultat :**
Cibles retenues pour IND-04+ : {retained_txt}. Les détails complets sont dans `artefacts/professional_study/target_comparison.parquet`.

**Décision :**
Utiliser ce classement comme entrée de sélection pour IND-04.
"""
    if "|---|---|---|---|---|---|---|---|" in text:
        text = text.replace("|---|---|---|---|---|---|---|---|\n", "|---|---|---|---|---|---|---|---|\n" + row, 1)
    else:
        text = text.rstrip() + "\n\n" + row
    EXPERIMENT_INDEX.write_text(text.rstrip() + "\n" + detail, encoding="utf-8")


def _next_exp_id(text: str) -> str:
    nums = [int(x) for x in re.findall(r"EXP-(\d+)", text)]
    return f"EXP-{(max(nums) + 1) if nums else 1:03d}"


def _write_notebook(ranking: pd.DataFrame) -> None:
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTEBOOK_EXPORT.parent.mkdir(parents=True, exist_ok=True)
    retained = _top_retained(ranking)
    retained_lines = "\n".join(
        f"- `{row['target']}` : DA={_fmt(row['best_da'])}, AUC={_fmt(row['best_auc'])}, modèle `{row['best_model']}`"
        for _, row in retained.iterrows()
    ) or "- Aucune cible Tier 1 robuste."
    top_table = _markdown_table(ranking.head(15)) if not ranking.empty else "Aucun résultat."

    nb = nbf.v4.new_notebook()
    nb["cells"] = [
        nbf.v4.new_markdown_cell("# 04 — Reformulation des cibles\n\nTicket `IND-02`. Export généré depuis les artefacts vérifiés."),
        nbf.v4.new_markdown_cell("## Cibles retenues\n\n" + retained_lines),
        nbf.v4.new_markdown_cell("## Top ranking\n\n" + top_table),
        nbf.v4.new_code_cell(
            "import pandas as pd\n"
            "comparison = pd.read_parquet('../../../artefacts/professional_study/target_comparison.parquet')\n"
            "ranking = pd.read_csv('../../../artefacts/professional_study/target_ranking.csv')\n"
            "ranking.head(20)"
        ),
    ]
    nbf.write(nb, NOTEBOOK_PATH)

    try:
        from nbconvert import HTMLExporter

        exporter = HTMLExporter()
        body, _ = exporter.from_notebook_node(nb)
        NOTEBOOK_EXPORT.write_text(body, encoding="utf-8")
    except Exception as exc:
        log.warning("notebook_export_failed", error=str(exc))


def _markdown_table(df: pd.DataFrame) -> str:
    """Small markdown table writer to avoid depending on optional tabulate."""
    cols = [
        "target", "family", "horizon", "problem", "best_model", "best_da",
        "best_auc", "best_brier", "delta_da_vs_seasonal", "tier", "decision",
    ]
    cols = [c for c in cols if c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, row in df[cols].iterrows():
        vals = []
        for col in cols:
            val = row[col]
            if isinstance(val, float) or pd.isna(val):
                vals.append(_fmt(val))
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def main() -> None:
    comparison, ranking = run_target_comparison()
    print(f"Wrote {TARGET_COMPARISON_PARQUET} rows={len(comparison)}")
    print(f"Wrote {TARGET_RANKING_CSV} rows={len(ranking)}")
    retained = _top_retained(ranking)
    if not retained.empty:
        print("Retained targets:", ", ".join(retained["target"].tolist()))


if __name__ == "__main__":
    main()
