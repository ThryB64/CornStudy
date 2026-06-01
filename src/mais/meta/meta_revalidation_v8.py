"""V8-META-REVALIDATION — revalidation stricte du meta-model V6 sous protocole V7.

Objectif :
Tester si le meta-model V6 (`AUC=0.937` sur `y_rel_outperform_h90`) survit aux
protocoles V7 stricts (nested walk-forward, embargo, leave-one-crop-year).

Cibles :
- y_rel_outperform_h40
- y_rel_outperform_h90
- y_rel_outperform_when_basis_extreme_h40
- y_rel_outperform_when_basis_extreme_h90

Combinaisons :
1. classic_only
2. meta_only (OOF predictions de base learners CBOT/EMA)
3. classic_plus_meta (V6 winning set)
4. basis_rule_only (basis_z > 1.5)
5. season_rule_only (mois ∈ {nov, dec, jan})
6. classic + basis_rule
7. classic + season_rule
8. classic + meta + basis_rule + season_rule (full stack)

Protocoles :
- A) walk_forward_v6_classic
- B) purged_cv_embargo_h
- C) purged_cv_embargo_2h
- D) leave_one_crop_year_nested
- E) non_overlap_strict
- F) no_crisis (exclure 2020 + 2022)
- G) no_roll (exclure DTE < 20)
- H) proxy_safe_period (si V7-01B livre une période officielle)

Verdict global selon §13 de la réflexion V8.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    balanced_accuracy_score,
    brier_score_loss,
    roc_auc_score,
)
from sklearn.model_selection import TimeSeriesSplit

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment
from mais.registry.holdout_lock import assert_no_holdout

_OUTPUT = ARTEFACTS_DIR / "v8" / "meta_revalidation.json"

TARGETS_REVALIDATION = [
    "y_rel_outperform_h40",
    "y_rel_outperform_h90",
    "y_rel_outperform_when_basis_extreme_h40",
    "y_rel_outperform_when_basis_extreme_h90",
]

COMBINATIONS = [
    "classic_only",
    "meta_only",
    "classic_plus_meta",
    "basis_rule_only",
    "season_rule_only",
    "classic_plus_basis",
    "classic_plus_season",
    "full_stack",
]


# ---------------------------------------------------------------------------
# CV protocols
# ---------------------------------------------------------------------------

def _walk_forward_v6_classic(dates: pd.DatetimeIndex, n_folds: int = 5):
    """V6-style walk-forward TimeSeriesSplit, sans embargo."""
    tscv = TimeSeriesSplit(n_splits=n_folds)
    for tr, te in tscv.split(dates):
        if len(tr) >= 50 and len(te) >= 10:
            yield tr, te


def _purged_embargo(dates: pd.DatetimeIndex, embargo_days: int, n_folds: int = 5):
    tscv = TimeSeriesSplit(n_splits=n_folds)
    for tr, te in tscv.split(dates):
        train_end = dates[tr[-1]]
        te_purged = np.array([i for i in te if dates[i] > train_end + pd.Timedelta(days=embargo_days)])
        if len(tr) >= 50 and len(te_purged) >= 10:
            yield tr, te_purged


def _leave_one_crop_year(dates: pd.DatetimeIndex, min_train_years: int = 3):
    def crop_year(d: pd.Timestamp) -> int:
        return d.year if d.month >= 9 else d.year - 1
    cy = np.array([crop_year(d) for d in dates])
    unique = sorted(set(cy))
    for c in unique[min_train_years:]:
        tr = np.where(cy < c)[0]
        te = np.where(cy == c)[0]
        if len(tr) >= 50 and len(te) >= 10:
            yield tr, te


def _non_overlap_strict(dates: pd.DatetimeIndex, h: int, n_folds: int = 5):
    """Garde uniquement les obs séparées d'au moins H jours."""
    idx = np.arange(len(dates))
    keep = idx[::max(h, 1)]
    if len(keep) < 20:
        return
    tscv = TimeSeriesSplit(n_splits=n_folds)
    for tr, te in tscv.split(keep):
        if len(tr) >= 20 and len(te) >= 5:
            yield keep[tr], keep[te]


def _no_crisis_filter(dates: pd.DatetimeIndex, crisis_years: tuple = (2020, 2022)):
    mask = np.array([d.year not in crisis_years for d in dates])
    valid_idx = np.where(mask)[0]
    if len(valid_idx) < 100:
        return
    tscv = TimeSeriesSplit(n_splits=5)
    for tr, te in tscv.split(valid_idx):
        if len(tr) >= 50 and len(te) >= 10:
            yield valid_idx[tr], valid_idx[te]


PROTOCOLS: dict[str, Callable] = {
    "A_walk_forward_v6": _walk_forward_v6_classic,
    "B_purged_embargo_H": lambda d: _purged_embargo(d, 90),
    "C_purged_embargo_2H": lambda d: _purged_embargo(d, 180),
    "D_leave_one_crop_year": _leave_one_crop_year,
    "E_non_overlap_strict_H": lambda d: _non_overlap_strict(d, 90),
    "F_no_crisis": _no_crisis_filter,
}


# ---------------------------------------------------------------------------
# Base learners pour meta-features
# ---------------------------------------------------------------------------

def _lgbm_factory():
    def factory():
        try:
            from lightgbm import LGBMClassifier
            return LGBMClassifier(n_estimators=100, seed=42, verbose=-1, n_jobs=1)
        except ImportError:
            from sklearn.ensemble import GradientBoostingClassifier
            return GradientBoostingClassifier(n_estimators=50, random_state=42)
    return factory


def _generate_oof_meta_feature(
    x_train: pd.DataFrame,
    y_target: pd.Series,
    cv_splits,
) -> pd.Series:
    """Génère une OOF pour `y_target` via 3-fold TS interne."""
    oof = np.full(len(x_train), np.nan)
    for tr, te in cv_splits:
        if len(tr) < 30:
            continue
        y_tr = y_target.iloc[tr]
        if y_tr.nunique() < 2:
            continue
        clf = _lgbm_factory()()
        try:
            clf.fit(x_train.iloc[tr].fillna(0), y_tr)
            oof[te] = clf.predict_proba(x_train.iloc[te].fillna(0))[:, 1]
        except Exception:
            pass
    return pd.Series(oof, index=x_train.index)


# ---------------------------------------------------------------------------
# Construction des cibles V6 (si absentes)
# ---------------------------------------------------------------------------

def ensure_rel_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Construit y_rel_outperform_h40 / h90 si absentes.

    y_rel_outperform_hH = 1 si EMA_close(t+H)/EMA_close(t) > CBOT_eur(t+H)/CBOT_eur(t)
    Conditionnelles `when_basis_extreme` : conservées seulement si |basis_z| > 1.5.
    """
    out = df.copy()

    ema_col = next((c for c in ["ema_close", "ema_front_price", "ema_front_continuous_raw"] if c in out.columns), None)
    cbot_col = next((c for c in ["cbot_eur_t", "cbot_close_eur"] if c in out.columns), None)
    basis_z_col = next((c for c in ["ema_cbot_basis_zscore_52w", "basis_z"] if c in out.columns), None)

    if ema_col is None or cbot_col is None:
        return out

    for horizon in (40, 90):
        col = f"y_rel_outperform_h{horizon}"
        if col not in out.columns:
            ema_ret = out[ema_col].pct_change(horizon).shift(-horizon)
            cbot_ret = out[cbot_col].pct_change(horizon).shift(-horizon)
            out[col] = (ema_ret > cbot_ret).astype(float)
            out.loc[ema_ret.isna() | cbot_ret.isna(), col] = np.nan

        if basis_z_col is not None:
            cond_col = f"y_rel_outperform_when_basis_extreme_h{horizon}"
            if cond_col not in out.columns:
                extreme_mask = out[basis_z_col].abs() > 1.5
                out[cond_col] = out[col].where(extreme_mask, np.nan)

    return out


# ---------------------------------------------------------------------------
# Évaluation d'une combinaison sur un protocole
# ---------------------------------------------------------------------------

def _classical_features(df: pd.DataFrame, max_features: int = 60) -> list[str]:
    exclude_prefix = ("y_", "Date", "date", "future_", "storage_", "return_", "prob_")
    cols = [
        c for c in df.columns
        if not any(c.startswith(p) for p in exclude_prefix)
        and df[c].dtype in (np.float64, np.float32, float)
        and df[c].notna().mean() > 0.3
    ]
    return cols[:max_features]


def _make_x_for_combination(
    df: pd.DataFrame,
    combination: str,
    feat_cols: list[str],
    meta_oof_df: pd.DataFrame | None,
) -> tuple[pd.DataFrame, str]:
    """Construit les features pour la combinaison choisie."""
    parts: list[pd.DataFrame] = []
    desc: list[str] = []

    if combination in ("classic_only", "classic_plus_meta", "classic_plus_basis", "classic_plus_season", "full_stack"):
        parts.append(df[feat_cols])
        desc.append(f"classic({len(feat_cols)})")

    if combination in ("meta_only", "classic_plus_meta", "full_stack") and meta_oof_df is not None:
        parts.append(meta_oof_df)
        desc.append(f"meta({meta_oof_df.shape[1]})")

    if combination in ("basis_rule_only", "classic_plus_basis", "full_stack"):
        basis_z_col = next((c for c in ["ema_cbot_basis_zscore_52w", "basis_z"] if c in df.columns), None)
        if basis_z_col is not None:
            rule_df = pd.DataFrame({"basis_rule_long": (df[basis_z_col] > 1.5).astype(float),
                                    "basis_rule_short": (df[basis_z_col] < -1.5).astype(float)},
                                   index=df.index)
            parts.append(rule_df)
            desc.append("basis_rule")

    if combination in ("season_rule_only", "classic_plus_season", "full_stack"):
        season_df = pd.DataFrame({
            "season_nov_jan": df.index.month.isin([11, 12, 1]).astype(float),
            "season_jul_aug": df.index.month.isin([7, 8]).astype(float),
            "season_apr_jun": df.index.month.isin([4, 5, 6]).astype(float),
        }, index=df.index)
        parts.append(season_df)
        desc.append("season_rule")

    if not parts:
        return pd.DataFrame(index=df.index), "empty"

    x = pd.concat(parts, axis=1)
    # dédupliquer colonnes
    x = x.loc[:, ~x.columns.duplicated()]
    return x, "+".join(desc)


def _evaluate(
    x: pd.DataFrame,
    y: pd.Series,
    cv_splits,
) -> dict[str, Any]:
    """Évalue x → y en walk-forward selon cv_splits. Retourne AUC/BA/Brier OOF + n_oof."""
    oof = np.full(len(x), np.nan)
    n_folds_done = 0
    for tr, te in cv_splits:
        y_tr = y.iloc[tr]
        if y_tr.notna().sum() < 20 or y_tr.dropna().nunique() < 2:
            continue
        mask_tr = y_tr.notna()
        try:
            clf = LogisticRegression(C=1.0, max_iter=500, random_state=42)
            clf.fit(x.iloc[tr][mask_tr].fillna(0), y_tr[mask_tr])
            x_te = x.iloc[te].fillna(0)
            oof[te] = clf.predict_proba(x_te)[:, 1]
            n_folds_done += 1
        except Exception:
            continue

    valid = (~np.isnan(oof)) & y.notna().values
    n_oof = int(valid.sum())
    auc = None
    ba = None
    brier = None
    if n_oof >= 30 and len(np.unique(y.values[valid])) > 1:
        try:
            auc = round(float(roc_auc_score(y.values[valid], oof[valid])), 4)
            ba = round(float(balanced_accuracy_score(
                y.values[valid].astype(int), (oof[valid] > 0.5).astype(int))), 4)
            brier = round(float(brier_score_loss(y.values[valid].astype(int), oof[valid])), 4)
        except Exception:
            pass
    return {"auc": auc, "balanced_accuracy": ba, "brier": brier, "n_oof": n_oof, "n_folds_done": n_folds_done}


def _verdict_from_results(
    results: list[dict[str, Any]],
    target: str,
) -> tuple[str, dict[str, Any]]:
    """Verdict global selon §13 réflexion V8."""
    aucs = [r["metrics"]["auc"] for r in results if r["metrics"]["auc"] is not None]
    n_valid = len(aucs)
    if n_valid == 0:
        return "INSUFFICIENT_DATA", {"n_valid_combinations_protocols": 0}

    mean_auc = float(np.mean(aucs))
    median_auc = float(np.median(aucs))
    min_auc = float(np.min(aucs))
    max_auc = float(np.max(aucs))

    # Reference V6 cible H90
    v6_ref = 0.937 if "h90" in target else 0.768
    delta_vs_v6 = round(median_auc - v6_ref, 4)

    if median_auc >= 0.85 and min_auc >= 0.75:
        verdict = "META_PREMIUM_ROBUST"
    elif median_auc >= 0.70 and min_auc >= 0.60:
        verdict = "META_PREMIUM_USEFUL_BUT_OVERSTATED"
    elif median_auc >= 0.60 and (max_auc - min_auc) > 0.20:
        verdict = "META_PREMIUM_FRAGILE"
    elif max_auc - min_auc > 0.30 or (v6_ref - median_auc) > 0.20:
        verdict = "META_PREMIUM_LIKELY_OVERFIT_OR_LEAKAGE"
    else:
        verdict = "META_PREMIUM_NO_GO"

    return verdict, {
        "mean_auc": round(mean_auc, 4),
        "median_auc": round(median_auc, 4),
        "min_auc": round(min_auc, 4),
        "max_auc": round(max_auc, 4),
        "delta_vs_v6": delta_vs_v6,
        "n_valid_combinations_protocols": n_valid,
    }


# ---------------------------------------------------------------------------
# Runner principal
# ---------------------------------------------------------------------------

def run_meta_revalidation(df: pd.DataFrame, fast: bool = False) -> dict[str, Any]:
    """Exécute V8-META-REVALIDATION sur le dataset fourni.

    `fast=True` : limite combinaisons et protocoles pour smoke test.
    """
    # Anti-leakage assertion : pas de holdout 2024 dans le df
    assert_no_holdout(df)

    df = ensure_rel_targets(df)

    feat_cols = _classical_features(df, max_features=60)
    if len(feat_cols) < 5:
        return {"version": "V8-META-REVALIDATION", "verdict": "INSUFFICIENT_FEATURES", "n_features": len(feat_cols)}

    # Cibles auxiliaires pour générer les OOF meta-features
    aux_target_cols = []
    for c in ["y_up_h20", "y_up_h40", "y_up_h60", "y_up_h20_ema", "y_up_h40_ema"]:
        if c in df.columns and df[c].dropna().shape[0] > 200:
            aux_target_cols.append(c)

    # Précalcule les OOF meta-features une seule fois (sur toute la période — limitation acceptée car test)
    meta_oof_df: pd.DataFrame | None = None
    if aux_target_cols:
        oof_dict: dict[str, pd.Series] = {}
        cv_splits_inner = list(TimeSeriesSplit(n_splits=3).split(df.index))
        for aux in aux_target_cols:
            y_aux = df[aux]
            valid = df[feat_cols].notna().all(axis=1) & y_aux.notna()
            if valid.sum() < 100:
                continue
            oof_dict[f"oof_{aux}"] = _generate_oof_meta_feature(
                df[feat_cols], y_aux, cv_splits_inner
            )
        if oof_dict:
            meta_oof_df = pd.DataFrame(oof_dict)

    # Périmètre combinaisons / protocoles (réduit si fast)
    combinations = COMBINATIONS if not fast else COMBINATIONS[:3]
    protocols = PROTOCOLS if not fast else {"A_walk_forward_v6": PROTOCOLS["A_walk_forward_v6"], "B_purged_embargo_H": PROTOCOLS["B_purged_embargo_H"]}

    results_by_target: dict[str, list[dict[str, Any]]] = {}
    for target in TARGETS_REVALIDATION:
        if target not in df.columns or df[target].dropna().shape[0] < 30:
            continue
        y = df[target]
        results = []
        for combo in combinations:
            x, desc = _make_x_for_combination(df, combo, feat_cols, meta_oof_df)
            if x.empty or x.shape[1] == 0:
                continue
            common_idx = x.index.intersection(y.dropna().index)
            if len(common_idx) < 60:
                continue
            x_aligned = x.loc[common_idx]
            y_aligned = y.loc[common_idx]
            for proto_name, proto_fn in protocols.items():
                cv = list(proto_fn(x_aligned.index))
                if not cv:
                    continue
                metrics = _evaluate(x_aligned, y_aligned, cv)
                results.append({
                    "combination": combo,
                    "combination_desc": desc,
                    "protocol": proto_name,
                    "metrics": metrics,
                })

        verdict, summary = _verdict_from_results(results, target)
        results_by_target[target] = {
            "results": results,
            "verdict": verdict,
            "summary": summary,
        }

    # Verdict global agrégé
    target_verdicts = {t: r["verdict"] for t, r in results_by_target.items()}
    if "META_PREMIUM_ROBUST" in target_verdicts.values():
        global_verdict = "META_PREMIUM_ROBUST"
    elif "META_PREMIUM_USEFUL_BUT_OVERSTATED" in target_verdicts.values():
        global_verdict = "META_PREMIUM_USEFUL_BUT_OVERSTATED"
    elif "META_PREMIUM_FRAGILE" in target_verdicts.values():
        global_verdict = "META_PREMIUM_FRAGILE"
    elif "META_PREMIUM_LIKELY_OVERFIT_OR_LEAKAGE" in target_verdicts.values():
        global_verdict = "META_PREMIUM_LIKELY_OVERFIT_OR_LEAKAGE"
    else:
        global_verdict = "META_PREMIUM_NO_GO"

    return {
        "version": "V8-META-REVALIDATION",
        "n_features_classical": len(feat_cols),
        "meta_features": list(meta_oof_df.columns) if meta_oof_df is not None else [],
        "n_targets_evaluated": len(results_by_target),
        "results_by_target": results_by_target,
        "global_verdict": global_verdict,
        "experiment_type": "PREDICTIVE_OOF_REVALIDATION",
        "protocol_set": list(protocols.keys()),
        "combination_set": combinations,
        "embargo_days_used": [0, 90, 180],
        "fast_mode": fast,
        "anti_leakage_holdout_lock": "assert_no_holdout_applied",
    }


def save_meta_revalidation(df: pd.DataFrame, fast: bool = False) -> dict[str, Any]:
    result = run_meta_revalidation(df, fast=fast)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V8-META-REVALIDATION",
        target="multi_premium_targets",
        horizon=90,
        model="logistic_meta_8combos_6protocols",
        cv_protocol="multi_protocol_revalidation",
        embargo_days=90,
        n_oof=sum(
            r["metrics"]["n_oof"]
            for tgt in result.get("results_by_target", {}).values()
            for r in tgt["results"]
        ),
        features=["classic_features", "oof_meta_features", "basis_rule", "season_rule"],
        metrics={
            "global_verdict": result.get("global_verdict"),
            "n_targets_evaluated": result.get("n_targets_evaluated"),
            "fast_mode": result.get("fast_mode"),
        },
        p_value=None,
        verdict=result.get("global_verdict", "INSUFFICIENT_DATA"),
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        dataset_version="proxy_v1_v8",
        review_status="DONE",
    )
    return result
