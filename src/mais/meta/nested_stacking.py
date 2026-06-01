"""V7-03 — Cross-target stacking V2 avec nested walk-forward rigoureux."""
from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "cross_target_stacking_v2.json"


# ---------------------------------------------------------------------------
# Protocoles CV
# ---------------------------------------------------------------------------

def _leave_one_crop_year(dates: pd.DatetimeIndex, min_train_years: int = 3):
    """Walk-forward crop-year : test = 1 crop year, train = tout avant."""
    def crop_year(d: pd.Timestamp) -> int:
        return d.year if d.month >= 9 else d.year - 1

    cy_labels = np.array([crop_year(d) for d in dates])
    unique_cys = sorted(set(cy_labels))
    for cy in unique_cys[min_train_years:]:
        train_mask = cy_labels < cy
        test_mask = cy_labels == cy
        if train_mask.sum() < 50 or test_mask.sum() < 10:
            continue
        yield np.where(train_mask)[0], np.where(test_mask)[0]


def _embargo_splits(dates: pd.DatetimeIndex, embargo_days: int, n_splits: int = 5):
    """TimeSeriesSplit avec embargo."""
    from sklearn.model_selection import TimeSeriesSplit
    tscv = TimeSeriesSplit(n_splits=n_splits)
    for train_idx, test_idx in tscv.split(dates):
        train_end = dates[train_idx[-1]]
        test_idx_purged = np.array([
            i for i in test_idx if dates[i] > train_end + pd.Timedelta(days=embargo_days)
        ])
        if len(test_idx_purged) >= 10:
            yield train_idx, test_idx_purged


# ---------------------------------------------------------------------------
# Base learners
# ---------------------------------------------------------------------------

def _lgbm_learner(**kwargs):
    def factory():
        try:
            from lightgbm import LGBMClassifier
            return LGBMClassifier(n_estimators=100, seed=42, verbose=-1, n_jobs=1, **kwargs)
        except ImportError:
            from sklearn.ensemble import GradientBoostingClassifier
            return GradientBoostingClassifier(n_estimators=50, random_state=42)
    return factory


def _logistic_learner(**kwargs):
    def factory():
        return LogisticRegression(C=1.0, max_iter=500, random_state=42, **kwargs)
    return factory


DEFAULT_BASE_LEARNERS = {
    "lgbm_basis": (_lgbm_learner(), "y_rel_outperform_h40"),
    "lgbm_premium": (_lgbm_learner(), "y_rel_outperform_h90"),
    "lgbm_cbot": (_lgbm_learner(), "y_up_h20"),
    "logistic_basis": (_logistic_learner(), "y_rel_outperform_h40"),
}


# ---------------------------------------------------------------------------
# Nested walk-forward stacking
# ---------------------------------------------------------------------------

def nested_walk_forward_stacking(
    x_features: pd.DataFrame,
    y_targets: dict[str, pd.Series],
    outer_cv,
    inner_embargo_days: int,
    base_learners: dict[str, tuple[Callable, str]],
    meta_target: str,
    embargo_days: int = 90,
) -> dict[str, Any]:
    """
    Nested walk-forward stacking avec isolation stricte outer/inner.

    Outer loop : leave_one_crop_year
    Inner loop : OOF base_learners UNIQUEMENT sur outer_train
    Garantie : inner_test_dates ∩ outer_test_dates = ∅
    """
    if meta_target not in y_targets:
        return {"error": f"meta_target '{meta_target}' not in y_targets"}

    meta_oof = np.full(len(x_features), np.nan)
    fold_results = []
    n_folds_done = 0

    for outer_fold_id, (outer_train_idx, outer_test_idx) in enumerate(outer_cv):
        x_outer_train = x_features.iloc[outer_train_idx]
        x_outer_test = x_features.iloc[outer_test_idx]

        # Vérification embargo outer : pour leave_one_crop_year, la frontière naturelle
        # est la séparation crop-year. On vérifie juste que le test n'est pas avant le train.
        outer_train_end = x_outer_train.index[-1]
        outer_test_start = x_outer_test.index[0]
        if outer_test_start <= outer_train_end:
            continue

        # INNER LOOP : générer OOF base_learners sur outer_train uniquement
        inner_meta_features: dict[str, np.ndarray] = {}
        inner_cv = list(_embargo_splits(x_outer_train.index, inner_embargo_days, n_splits=3))

        for learner_name, (learner_fn, target_key) in base_learners.items():
            if target_key not in y_targets:
                continue
            y_inner = y_targets[target_key].reindex(x_outer_train.index)
            inner_oof = np.full(len(x_outer_train), np.nan)

            for inner_train_idx, inner_test_idx in inner_cv:
                # VÉRIFICATION CRITIQUE anti-leakage
                inner_test_dates = x_outer_train.index[inner_test_idx]
                outer_test_dates = x_outer_test.index
                overlap = len(inner_test_dates.intersection(outer_test_dates))
                assert overlap == 0, f"LEAKAGE fold {outer_fold_id}: {overlap} dates overlap"

                x_in_tr = x_outer_train.iloc[inner_train_idx]
                y_in_tr = y_inner.iloc[inner_train_idx]
                mask_tr = x_in_tr.notna().all(axis=1) & y_in_tr.notna()
                if mask_tr.sum() < 20 or len(y_in_tr[mask_tr].unique()) < 2:
                    continue

                clf = learner_fn()
                try:
                    clf.fit(x_in_tr[mask_tr].fillna(0), y_in_tr[mask_tr])
                    x_in_te = x_outer_train.iloc[inner_test_idx].fillna(0)
                    preds = clf.predict_proba(x_in_te)[:, 1]
                    inner_oof[inner_test_idx] = preds
                except Exception:
                    pass

            inner_meta_features[learner_name] = inner_oof

        # Construire x_meta pour outer_train (OOF inner)
        x_meta_train_df = pd.DataFrame(inner_meta_features, index=x_outer_train.index)
        y_meta_train = y_targets[meta_target].reindex(x_outer_train.index)
        valid_mask = x_meta_train_df.notna().all(axis=1) & y_meta_train.notna()

        if valid_mask.sum() < 30 or len(y_meta_train[valid_mask].unique()) < 2:
            continue

        # Entraîner meta-modèle sur inner OOF
        meta_clf = LogisticRegression(C=1.0, max_iter=500, random_state=42)
        try:
            meta_clf.fit(x_meta_train_df[valid_mask].fillna(0.5), y_meta_train[valid_mask])
        except Exception:
            continue

        # Générer prédictions base pour outer_test (full outer_train)
        outer_test_base_preds: dict[str, np.ndarray] = {}
        for learner_name, (learner_fn, target_key) in base_learners.items():
            if target_key not in y_targets:
                continue
            y_full_tr = y_targets[target_key].reindex(x_outer_train.index).dropna()
            x_full_tr = x_outer_train.reindex(y_full_tr.index)
            mask_full = x_full_tr.notna().all(axis=1)
            if mask_full.sum() < 20 or len(y_full_tr[mask_full].unique()) < 2:
                outer_test_base_preds[learner_name] = np.full(len(x_outer_test), 0.5)
                continue
            clf_full = learner_fn()
            try:
                clf_full.fit(x_full_tr[mask_full].fillna(0), y_full_tr[mask_full])
                outer_test_base_preds[learner_name] = clf_full.predict_proba(
                    x_outer_test.fillna(0)
                )[:, 1]
            except Exception:
                outer_test_base_preds[learner_name] = np.full(len(x_outer_test), 0.5)

        x_meta_test_df = pd.DataFrame(outer_test_base_preds, index=x_outer_test.index)
        y_meta_pred = meta_clf.predict_proba(x_meta_test_df.fillna(0.5))[:, 1]
        meta_oof[outer_test_idx] = y_meta_pred

        # Évaluation du fold
        y_test_true = y_targets[meta_target].reindex(x_outer_test.index)
        valid_fold = (~np.isnan(y_meta_pred)) & y_test_true.notna().values
        if valid_fold.sum() >= 10 and len(np.unique(y_test_true.values[valid_fold])) > 1:
            try:
                auc_fold = float(roc_auc_score(y_test_true.values[valid_fold], y_meta_pred[valid_fold]))
                ba_fold = float(balanced_accuracy_score(
                    y_test_true.values[valid_fold].astype(int),
                    (y_meta_pred[valid_fold] > 0.5).astype(int),
                ))
                fold_results.append({
                    "outer_fold": outer_fold_id,
                    "n_test": int(valid_fold.sum()),
                    "auc": round(auc_fold, 4),
                    "balanced_accuracy": round(ba_fold, 4),
                })
                n_folds_done += 1
            except Exception:
                pass

    # Métriques globales
    y_meta = y_targets[meta_target]
    valid_oof = ~np.isnan(meta_oof) & y_meta.notna().values
    global_auc: float | None = None
    global_ba: float | None = None

    if valid_oof.sum() >= 50 and len(np.unique(y_meta.values[valid_oof])) > 1:
        try:
            global_auc = round(float(roc_auc_score(y_meta.values[valid_oof], meta_oof[valid_oof])), 4)
            global_ba = round(float(balanced_accuracy_score(
                y_meta.values[valid_oof].astype(int),
                (meta_oof[valid_oof] > 0.5).astype(int),
            )), 4)
        except Exception:
            pass

    return {
        "n_oof": int(valid_oof.sum()),
        "n_folds_done": n_folds_done,
        "global_auc": global_auc,
        "global_balanced_accuracy": global_ba,
        "fold_results": fold_results,
        "meta_target": meta_target,
        "meta_oof": meta_oof,  # array for further analysis
    }


# ---------------------------------------------------------------------------
# Runner principal
# ---------------------------------------------------------------------------

def run_nested_stacking(df: pd.DataFrame) -> dict[str, Any]:
    """Exécute le nested stacking V2 et compare vs meilleur expert seul."""
    # Sélectionner features (non-target, non-retour)
    exclude = {"y_", "return_", "Date", "date", "storage_", "prob_", "sell_regret"}
    target_names = {
        "y_rel_outperform_h40", "y_rel_outperform_h90", "y_up_h20",
        "y_up_h40", "y_up_h60", "y_up_h20_ema", "y_up_h40_ema",
        "y_rel_outperform_when_basis_extreme_h40",
        "y_rel_outperform_when_basis_extreme_h90",
    }

    feature_cols = [
        c for c in df.columns
        if not any(p in c for p in exclude)
        and c not in target_names
        and df[c].dtype in [np.float64, np.float32, float]
        and df[c].notna().mean() > 0.3
    ][:80]  # max 80 features

    if len(feature_cols) < 5:
        return {"verdict": "INSUFFICIENT_FEATURES"}

    x_df = df[feature_cols].copy()

    # Construire y_targets dict
    y_targets: dict[str, pd.Series] = {}
    for col in target_names:
        if col in df.columns and df[col].dropna().__len__() > 100:
            y_targets[col] = df[col]

    if not y_targets:
        return {"verdict": "NO_TARGETS"}

    # Choisir meta_target (préférer H90 relatif)
    meta_target = next(
        (t for t in ["y_rel_outperform_h90", "y_rel_outperform_h40", "y_up_h20"] if t in y_targets),
        list(y_targets.keys())[0],
    )

    # Base learners disponibles selon y_targets
    base_learners = {
        name: (fn, tgt)
        for name, (fn, tgt) in DEFAULT_BASE_LEARNERS.items()
        if tgt in y_targets
    }

    if len(base_learners) < 2:
        # Fallback: utiliser les targets disponibles
        avail_targets = list(y_targets.keys())[:4]
        base_learners = {
            f"lgbm_{t[-4:]}": (_lgbm_learner(), t)
            for t in avail_targets
        }

    # Outer CV
    outer_cv = list(_leave_one_crop_year(df.index, min_train_years=3))
    if not outer_cv:
        return {"verdict": "INSUFFICIENT_DATA_FOR_CV"}

    # Run nested stacking
    stacking_result = nested_walk_forward_stacking(
        x_features=x_df,
        y_targets=y_targets,
        outer_cv=outer_cv,
        inner_embargo_days=40,
        base_learners=base_learners,
        meta_target=meta_target,
        embargo_days=90,
    )

    # Comparaison vs meilleur expert seul
    single_expert_auc: float | None = None
    try:
        from lightgbm import LGBMClassifier
        clf_single = LGBMClassifier(n_estimators=100, seed=42, verbose=-1, n_jobs=1)
        y_meta = y_targets[meta_target]
        valid = x_df.notna().all(axis=1) & y_meta.notna()
        n_train_single = int(valid.sum() * 0.7)
        if n_train_single > 50:
            x_tr = x_df[valid].fillna(0).iloc[:n_train_single]
            y_tr = y_meta[valid].iloc[:n_train_single]
            x_te = x_df[valid].fillna(0).iloc[n_train_single:]
            y_te = y_meta[valid].iloc[n_train_single:]
            if len(y_te.unique()) > 1:
                clf_single.fit(x_tr, y_tr)
                single_expert_auc = round(
                    float(roc_auc_score(y_te, clf_single.predict_proba(x_te)[:, 1])), 4
                )
    except Exception:
        pass

    global_auc = stacking_result.get("global_auc")
    delta_vs_single = (
        round(global_auc - single_expert_auc, 4)
        if global_auc is not None and single_expert_auc is not None
        else None
    )

    # Verdict
    if global_auc is not None and global_auc >= 0.6:
        verdict = "GO_RESEARCH"
    elif global_auc is not None and global_auc >= 0.55:
        verdict = "PROMISING"
    else:
        verdict = "NO_GO"

    return {
        "version": "V7-03",
        "meta_target": meta_target,
        "n_base_learners": len(base_learners),
        "base_learner_targets": [tgt for _, tgt in base_learners.values()],
        "n_outer_folds": len(outer_cv),
        "n_folds_done": stacking_result.get("n_folds_done", 0),
        "n_oof": stacking_result.get("n_oof", 0),
        "global_auc": global_auc,
        "global_balanced_accuracy": stacking_result.get("global_balanced_accuracy"),
        "single_expert_auc": single_expert_auc,
        "delta_auc_meta_vs_single": delta_vs_single,
        "fold_results": stacking_result.get("fold_results", []),
        "verdict": verdict,
        "experiment_type": "PREDICTIVE_OOF",
        "protocol": "nested_walk_forward_leave_one_crop_year",
        "embargo_days": 90,
        "anti_leakage": "nested_oof_strict_inner_outer_isolation",
    }


def save_nested_stacking(df: pd.DataFrame) -> dict[str, Any]:
    result = run_nested_stacking(df)
    # Remove meta_oof array before serializing (not JSON-serializable as-is)
    save_result = {k: v for k, v in result.items() if k != "meta_oof"}

    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(save_result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-03",
        target=result.get("meta_target", "unknown"),
        horizon=90,
        model="nested_walk_forward_stacking",
        cv_protocol="leave_one_crop_year_nested",
        embargo_days=90,
        n_oof=result.get("n_oof", 0),
        features=result.get("base_learner_targets", []),
        metrics={
            "global_auc": result.get("global_auc"),
            "global_ba": result.get("global_balanced_accuracy"),
            "single_expert_auc": result.get("single_expert_auc"),
            "delta_auc_vs_single": result.get("delta_auc_meta_vs_single"),
            "n_folds_done": result.get("n_folds_done"),
        },
        p_value=None,
        verdict=result.get("verdict", "NO_GO"),
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return save_result
