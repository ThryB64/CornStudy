"""V3-05 stacking multi-modèles pour l'indicateur directionnel du maïs.

Niveau 0 : prédictions OOF de V3-03 (model_zoo_oof_predictions.parquet).
Niveau 1 : méta-features consensus de V3-04 + contexte.
Niveau 2 : méta-modèles (logistic, ridge, lgbm, weighted_avg, vote).

Règle absolue : OOF strict — aucune prédiction de niveau 1 entraînée sur les
données de son propre fold de test. Période 2023-2025 jamais utilisée.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mais.paths import ARTEFACTS_DIR
from mais.utils import get_logger, write_parquet

log = get_logger("mais.research.stacking")

RANDOM_STATE = 42
MAX_DATE = pd.Timestamp("2022-12-31")
MODEL_ZOO_DIR = ARTEFACTS_DIR / "model_zoo"
CONSENSUS_DIR = ARTEFACTS_DIR / "indicator"
STACKING_DIR = ARTEFACTS_DIR / "stacking"

# Modèles sélectionnés par V3-03
SELECTED_MODELS = ["lasso", "histgb", "gaussian_nb", "logistic", "extratrees"]


def run_stacking(
    oof_predictions: pd.DataFrame,
    meta_features: pd.DataFrame,
    selected_models: list[str] | None = None,
    n_splits: int = 5,
    output_dir: Path = STACKING_DIR,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """Entraîne les méta-modèles sur OOF + méta-features.

    Retourne un DataFrame comparatif méta-modèles vs modèles individuels.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    models_to_use = selected_models if selected_models is not None else SELECTED_MODELS

    oof = oof_predictions[oof_predictions["model"].isin(models_to_use)].copy()
    oof["Date"] = pd.to_datetime(oof["Date"])
    oof = oof[oof["Date"] <= MAX_DATE].sort_values(["Date", "model"])

    meta = meta_features.copy()
    meta["Date"] = pd.to_datetime(meta["Date"])
    meta = meta[meta["Date"] <= MAX_DATE]

    base_matrix, dates, y_true = _build_base_matrix(oof, models_to_use, meta)
    if base_matrix.empty:
        log.warning("stacking_empty_base_matrix")
        return pd.DataFrame()

    individual_results = _eval_individual_models(oof, models_to_use)
    meta_results = _run_meta_models(base_matrix, y_true, n_splits, random_state)

    all_results = pd.DataFrame(individual_results + meta_results)
    all_results = all_results.sort_values("da", ascending=False).reset_index(drop=True)

    best = _select_best(all_results)
    oof_meta_preds = _generate_final_oof(base_matrix, y_true, best, n_splits, random_state)

    write_parquet(oof_meta_preds, output_dir / "stacking_oof_predictions.parquet")
    write_parquet(all_results, output_dir / "stacking_results.parquet")
    (output_dir / "stacking_best_model.json").write_text(
        json.dumps(best, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_dir / "stacking_report.txt").write_text(
        _report_text(all_results, best, individual_results),
        encoding="utf-8",
    )
    return all_results


def _build_base_matrix(
    oof: pd.DataFrame,
    model_names: list[str],
    meta: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Pivot OOF predictions to wide format and join consensus meta-features."""
    if oof.empty:
        return pd.DataFrame(), pd.Series(dtype=float), pd.Series(dtype=int)

    pivot = (
        oof.groupby(["Date", "model"], as_index=False)
        .agg(p_up=("p_up", "mean"), y_true_up=("y_true_up", "first"))
        .pivot(index="Date", columns="model", values="p_up")
        .reset_index()
    )
    pivot.columns.name = None
    for m in model_names:
        if m not in pivot.columns:
            pivot[m] = np.nan

    y_true_df = (
        oof.groupby("Date", as_index=False)
        .agg(y_true_up=("y_true_up", "first"))
    )
    pivot = pivot.merge(y_true_df, on="Date", how="left")

    meta_cols = [
        "consensus_score", "disagreement", "bullish_ratio", "local_stability", "slope",
        "meta_directional_score", "meta_bullish_consensus",
    ]
    available_meta = [c for c in meta_cols if c in meta.columns]
    if available_meta:
        meta_sub = meta[["Date"] + available_meta].copy()
        pivot = pivot.merge(meta_sub, on="Date", how="left")

    feature_cols = [c for c in pivot.columns if c not in ("Date", "y_true_up")]
    pivot[feature_cols] = pivot[feature_cols].fillna(pivot[feature_cols].median())

    dates = pivot["Date"]
    y = pivot["y_true_up"].astype(int)
    features = pivot[feature_cols].copy()
    return features, dates, y


def _eval_individual_models(oof: pd.DataFrame, model_names: list[str]) -> list[dict[str, Any]]:
    """Compute metrics for each individual model from OOF predictions."""
    rows = []
    for name in model_names:
        sub = oof[oof["model"] == name].copy()
        if sub.empty:
            continue
        y = sub["y_true_up"].astype(int).to_numpy()
        p = np.clip(sub["p_up"].to_numpy(dtype=float), 0.0, 1.0)
        rows.append(_metrics_row(name, y, p, level="individual"))
    # Baselines ensembles
    for ensemble in ["avg_proba", "vote_majority"]:
        sub = oof[oof["model"] == ensemble].copy() if ensemble in oof["model"].values else pd.DataFrame()
        if sub.empty:
            # build on-the-fly
            all_base = oof[oof["model"].isin(model_names)]
            agg = all_base.groupby("Date", as_index=False).agg(
                p_up=("p_up", "mean"), y_true_up=("y_true_up", "first")
            )
            if ensemble == "avg_proba":
                p = np.clip(agg["p_up"].to_numpy(dtype=float), 0.0, 1.0)
            else:
                p = (agg["p_up"] >= 0.5).astype(float).to_numpy()
            y = agg["y_true_up"].astype(int).to_numpy()
        else:
            y = sub["y_true_up"].astype(int).to_numpy()
            p = np.clip(sub["p_up"].to_numpy(dtype=float), 0.0, 1.0)
        rows.append(_metrics_row(ensemble, y, p, level="ensemble_baseline"))
    return rows


def _run_meta_models(
    features: pd.DataFrame,
    y: pd.Series,
    n_splits: int,
    random_state: int,
) -> list[dict[str, Any]]:
    """Train meta-models with strict OOF (no leakage)."""
    specs = _meta_model_specs(random_state)
    rows = []
    for name, model in specs.items():
        oof_preds, _ = _meta_oof(features, y, model, n_splits, random_state)
        if oof_preds is None:
            continue
        p = np.clip(oof_preds, 0.0, 1.0)
        rows.append(_metrics_row(f"meta_{name}", y.to_numpy(dtype=int), p, level="meta_model"))
    # Weighted average baseline: mean of all base feature columns (proxy)
    base_cols = [c for c in features.columns if not c.startswith("meta_") and not c.startswith("consensus")]
    if base_cols:
        p_avg = np.clip(features[base_cols].mean(axis=1).to_numpy(dtype=float), 0.0, 1.0)
        rows.append(_metrics_row("meta_weighted_avg", y.to_numpy(dtype=int), p_avg, level="meta_model"))
    return rows


def _meta_oof(
    features: pd.DataFrame,
    y: pd.Series,
    model,
    n_splits: int,
    random_state: int,
) -> tuple[np.ndarray | None, np.ndarray | None]:
    """Generate OOF predictions for a meta-model."""
    n = len(features)
    if n < 100:
        return None, None
    oof_preds = np.full(n, np.nan)
    kf = KFold(n_splits=n_splits, shuffle=False)
    for train_idx, test_idx in kf.split(features):
        feat_tr = features.iloc[train_idx]
        y_tr = y.iloc[train_idx]
        feat_te = features.iloc[test_idx]
        try:
            m = _clone_model(model)
            m.fit(feat_tr, y_tr.astype(int))
            if hasattr(m, "predict_proba"):
                oof_preds[test_idx] = m.predict_proba(feat_te)[:, 1]
            else:
                score = m.predict(feat_te)
                scale = float(np.nanstd(score))
                if scale <= 1e-8:
                    scale = 1.0
                oof_preds[test_idx] = _sigmoid(score / scale)
        except Exception as exc:
            log.warning("meta_model_fold_failed", error=str(exc))
            oof_preds[test_idx] = 0.5
    return oof_preds, y.to_numpy(dtype=int)


def _meta_model_specs(random_state: int) -> dict[str, Any]:
    specs: dict[str, Any] = {
        "logistic": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(C=1.0, max_iter=500, random_state=random_state)),
        ]),
        "ridge": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", Ridge(alpha=1.0)),
        ]),
    }
    try:
        import lightgbm as lgb
        specs["lgbm"] = lgb.LGBMClassifier(
            n_estimators=40,
            learning_rate=0.05,
            num_leaves=7,
            lambda_l2=2.0,
            verbose=-1,
            random_state=random_state,
        )
    except ImportError:
        from sklearn.ensemble import HistGradientBoostingClassifier
        specs["lgbm"] = HistGradientBoostingClassifier(
            max_iter=40, learning_rate=0.05, max_leaf_nodes=7, random_state=random_state
        )
    return specs


def _clone_model(model) -> Any:
    """Deep-copy a sklearn Pipeline or estimator."""
    from sklearn.base import clone
    return clone(model)


def _select_best(results: pd.DataFrame) -> dict[str, Any]:
    """Choose the best method (meta or individual) by DA, with AUC as tiebreaker."""
    if results.empty:
        return {"method": "unknown", "da": None}
    row = results.sort_values(["da", "auc"], ascending=False).iloc[0]
    return {
        "method": str(row["method"]),
        "level": str(row["level"]),
        "da": float(row["da"]),
        "auc": float(row["auc"]) if pd.notna(row["auc"]) else None,
        "da_top20pct": float(row["da_top20pct"]) if pd.notna(row["da_top20pct"]) else None,
        "brier": float(row["brier"]) if pd.notna(row["brier"]) else None,
    }


def _generate_final_oof(
    features: pd.DataFrame,
    y: pd.Series,
    best: dict[str, Any],
    n_splits: int,
    random_state: int,
) -> pd.DataFrame:
    """Generate final OOF predictions for the best method."""
    specs = _meta_model_specs(random_state)
    method = best.get("method", "")
    for suffix in ["logistic", "ridge", "lgbm"]:
        if method.endswith(suffix) and suffix in specs and specs[suffix] is not None:
            preds, _ = _meta_oof(features, y, specs[suffix], n_splits, random_state)
            if preds is not None:
                return pd.DataFrame({"p_up_meta": preds, "y_true_up": y.to_numpy()})
    return pd.DataFrame()


def _metrics_row(
    name: str, y: np.ndarray, p: np.ndarray, level: str
) -> dict[str, Any]:
    pred = (p >= 0.5).astype(int)
    conf = np.abs(p - 0.5)
    top20_cut = float(np.quantile(conf, 0.80))
    top20 = conf >= top20_cut
    return {
        "method": name,
        "level": level,
        "da": float(accuracy_score(y, pred)),
        "auc": _auc(y, p),
        "brier": float(brier_score_loss(y, p)),
        "da_top20pct": float(accuracy_score(y[top20], pred[top20])) if top20.any() else np.nan,
        "n_obs": int(len(y)),
    }


def _auc(y: np.ndarray, p: np.ndarray) -> float:
    try:
        if len(np.unique(y)) < 2:
            return np.nan
        return float(roc_auc_score(y, p))
    except ValueError:
        return np.nan


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(np.asarray(x, dtype=float), -50.0, 50.0)))


def _report_text(
    results: pd.DataFrame,
    best: dict[str, Any],
    individual_results: list[dict[str, Any]],
) -> str:
    ind_da = {r["method"]: r["da"] for r in individual_results if r["level"] == "individual"}
    best_ind = max(ind_da.values(), default=0.0) if ind_da else 0.0
    best_meta = float(
        results[results["level"] == "meta_model"]["da"].max()
        if "meta_model" in results["level"].values else 0.0
    )
    verdict = (
        f"Stacking AMÉLIORE le meilleur modèle individuel (+{best_meta - best_ind:+.3f} DA)"
        if best_meta > best_ind
        else f"Stacking NE BAT PAS le meilleur modèle individuel ({best_meta:.3f} vs {best_ind:.3f})"
    )
    lines = [
        "Stacking V3-05 — résultats comparatifs",
        "",
        f"Verdict : {verdict}",
        f"Méthode retenue : {best.get('method')} (DA={best.get('da'):.3f})",
        "",
        "| Méthode | Niveau | DA | AUC | Brier | DA top20 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for _, row in results.sort_values("da", ascending=False).iterrows():
        auc_str = f"{row['auc']:.3f}" if pd.notna(row["auc"]) else "N/A"
        brier_str = f"{row['brier']:.3f}" if pd.notna(row["brier"]) else "N/A"
        top20_str = f"{row['da_top20pct']:.3f}" if pd.notna(row["da_top20pct"]) else "N/A"
        lines.append(
            f"| {row['method']} | {row['level']} | {row['da']:.3f} | "
            f"{auc_str} | {brier_str} | {top20_str} |"
        )
    return "\n".join(lines) + "\n"


def run_project_stacking() -> pd.DataFrame:
    """Load standard project artefacts and run V3-05."""
    oof = pd.read_parquet(MODEL_ZOO_DIR / "model_zoo_oof_predictions.parquet")
    meta = pd.read_parquet(CONSENSUS_DIR / "consensus_metafeatures.parquet")
    selected_path = MODEL_ZOO_DIR / "model_zoo_selected_models.json"
    selected = json.loads(selected_path.read_text(encoding="utf-8")) if selected_path.exists() else None
    return run_stacking(oof, meta, selected_models=selected, output_dir=STACKING_DIR)


if __name__ == "__main__":
    run_project_stacking()
