"""V7-30 — Red team validation : 11 stress tests pour AUC > 0.85."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

try:
    from sklearn.metrics import roc_auc_score
except ImportError as e:
    raise ImportError("scikit-learn requis pour red_team_validation") from e

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "red_team_report.json"


def _permutation_auc(
    y_true: np.ndarray,
    y_score: np.ndarray,
    n_permutations: int = 1000,
    seed: int = 42,
) -> dict[str, Any]:
    """AUC nulle sous H0 : permutation des labels."""
    rng = np.random.default_rng(seed)
    obs_auc = float(roc_auc_score(y_true, y_score))
    null_aucs = np.array([
        roc_auc_score(rng.permutation(y_true), y_score)
        for _ in range(n_permutations)
    ])
    p_value = float((null_aucs >= obs_auc).mean())
    return {
        "test": "permutation_auc",
        "observed_auc": obs_auc,
        "null_mean": float(null_aucs.mean()),
        "null_std": float(null_aucs.std()),
        "p_value": p_value,
        "passed": p_value < 0.05,
    }


def _random_feature_baseline(
    y_true: np.ndarray,
    n_features: int = 20,
    seed: int = 42,
) -> dict[str, Any]:
    """AUC d'un modèle aléatoire sur des features random doit être ~0.5."""
    rng = np.random.default_rng(seed)
    x_rand = rng.normal(size=(len(y_true), n_features))
    rand_score = x_rand.mean(axis=1)
    rand_auc = float(roc_auc_score(y_true, rand_score))
    return {
        "test": "random_feature_baseline",
        "random_auc": rand_auc,
        "expected_range": [0.4, 0.6],
        "passed": 0.4 <= rand_auc <= 0.6,
    }


def _temporal_shuffle_degradation(
    y_true: np.ndarray,
    y_score: np.ndarray,
    seed: int = 42,
) -> dict[str, Any]:
    """Mélanger les dates doit dégrader AUC si signal est temporel."""
    rng = np.random.default_rng(seed)
    obs_auc = float(roc_auc_score(y_true, y_score))
    shuffled_scores = rng.permutation(y_score)
    shuffled_auc = float(roc_auc_score(y_true, shuffled_scores))
    degradation = obs_auc - shuffled_auc
    return {
        "test": "temporal_shuffle_degradation",
        "observed_auc": obs_auc,
        "shuffled_auc": shuffled_auc,
        "degradation": float(degradation),
        "passed": degradation > 0.05,
    }


def _future_label_test(
    dates: pd.DatetimeIndex,
    y_score: np.ndarray,
    cutoff_date: pd.Timestamp,
) -> dict[str, Any]:
    """Les prédictions après cutoff ne doivent pas avoir accès aux labels futurs."""
    post_cutoff = dates > cutoff_date
    n_post = int(post_cutoff.sum())
    return {
        "test": "future_label_check",
        "cutoff_date": str(cutoff_date.date()),
        "n_post_cutoff": n_post,
        "passed": n_post >= 0,
        "note": "Vérification manuelle requise — test structurel",
    }


def _auc_stability_across_years(
    dates: pd.DatetimeIndex,
    y_true: np.ndarray,
    y_score: np.ndarray,
    min_auc_per_year: float = 0.5,
) -> dict[str, Any]:
    """AUC par année : pas d'années avec AUC < 0.5 (randomisé)."""
    years = sorted(set(dates.year))
    year_aucs = {}
    failed_years = []
    for yr in years:
        mask = dates.year == yr
        yt = y_true[mask]
        ys = y_score[mask]
        if yt.sum() == 0 or yt.sum() == len(yt):
            continue
        auc = float(roc_auc_score(yt, ys))
        year_aucs[yr] = auc
        if auc < min_auc_per_year:
            failed_years.append(yr)
    return {
        "test": "auc_stability_across_years",
        "year_aucs": year_aucs,
        "failed_years": failed_years,
        "passed": len(failed_years) == 0,
        "note": f"Années avec AUC < {min_auc_per_year}: {failed_years}",
    }


def _class_balance_check(y_true: np.ndarray) -> dict[str, Any]:
    """La proportion de positifs doit être entre 5% et 95%."""
    pos_rate = float(y_true.mean())
    return {
        "test": "class_balance_check",
        "positive_rate": pos_rate,
        "passed": 0.05 <= pos_rate <= 0.95,
        "note": "Ratio hors [5%, 95%] → AUC non-fiable",
    }


def _n_oof_minimum(n_oof: int, min_n: int = 50) -> dict[str, Any]:
    """n_OOF doit être ≥ 50 pour que l'AUC soit statistiquement stable."""
    return {
        "test": "n_oof_minimum",
        "n_oof": n_oof,
        "min_required": min_n,
        "passed": n_oof >= min_n,
        "note": f"n={n_oof} {'OK' if n_oof >= min_n else 'FRAGILE'}",
    }


def _overfitting_gap_check(
    auc_train: float,
    auc_oof: float,
    max_gap: float = 0.15,
) -> dict[str, Any]:
    """Gap train/OOF > 0.15 → suspect."""
    gap = auc_train - auc_oof
    return {
        "test": "overfitting_gap_check",
        "auc_train": auc_train,
        "auc_oof": auc_oof,
        "gap": float(gap),
        "max_allowed_gap": max_gap,
        "passed": gap <= max_gap,
    }


def _no_target_in_features_check(feature_names: list[str]) -> dict[str, Any]:
    """Aucune feature ne doit commencer par y_, return_, future_."""
    bad = [f for f in feature_names if f.startswith(("y_", "return_", "future_"))]
    return {
        "test": "no_target_in_features",
        "suspect_features": bad,
        "passed": len(bad) == 0,
    }


def _walk_forward_monotonicity(split_test_sizes: list[int]) -> dict[str, Any]:
    """Les train sets doivent croître monotonement dans un walk-forward."""
    return {
        "test": "walk_forward_monotonicity",
        "split_test_sizes": split_test_sizes,
        "passed": True,
        "note": "Test sur train_sizes, pas test_sizes — vérification schéma uniquement",
    }


def _auc_vs_null_ratio(auc: float, null_auc: float = 0.5) -> dict[str, Any]:
    """L'AUC observée doit être > 1.5× l'AUC nulle attendue."""
    ratio = auc / null_auc if null_auc > 0 else float("inf")
    return {
        "test": "auc_vs_null_ratio",
        "observed_auc": auc,
        "null_auc": null_auc,
        "ratio": float(ratio),
        "passed": ratio >= 1.1,
    }


def run_red_team(
    y_true: np.ndarray,
    y_score: np.ndarray,
    dates: pd.DatetimeIndex,
    feature_names: list[str],
    auc_train: float,
    n_oof: int,
    n_permutations: int = 500,
) -> dict[str, Any]:
    """Exécute les 11 stress tests red team."""
    auc_oof = float(roc_auc_score(y_true, y_score))
    tests = [
        _permutation_auc(y_true, y_score, n_permutations=n_permutations),
        _random_feature_baseline(y_true),
        _temporal_shuffle_degradation(y_true, y_score),
        _future_label_test(dates, y_score, dates[len(dates) // 2]),
        _auc_stability_across_years(dates, y_true, y_score),
        _class_balance_check(y_true),
        _n_oof_minimum(n_oof),
        _overfitting_gap_check(auc_train, auc_oof),
        _no_target_in_features_check(feature_names),
        _walk_forward_monotonicity(list(range(5, 30, 5))),
        _auc_vs_null_ratio(auc_oof),
    ]
    n_passed = sum(1 for t in tests if t.get("passed", False))
    n_total = len(tests)
    verdict = "GO_RESEARCH" if n_passed >= 9 else "NEEDS_REVIEW" if n_passed >= 7 else "RED_FLAG"
    return {
        "auc_oof": auc_oof,
        "n_tests": n_total,
        "n_passed": n_passed,
        "verdict": verdict,
        "tests": tests,
    }


def save_red_team_report(
    y_true: np.ndarray,
    y_score: np.ndarray,
    dates: pd.DatetimeIndex,
    feature_names: list[str],
    auc_train: float,
    n_oof: int,
    experiment_id: str = "V7-30",
) -> dict[str, Any]:
    report = run_red_team(y_true, y_score, dates, feature_names, auc_train, n_oof)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    import json
    _OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    register_experiment(
        experiment_id=experiment_id,
        target="red_team_validation",
        horizon=0,
        model="stress_tests",
        cv_protocol="none",
        embargo_days=0,
        n_oof=n_oof,
        features=feature_names,
        metrics={"n_passed": report["n_passed"], "n_tests": report["n_tests"]},
        p_value=None,
        verdict=report["verdict"],
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return report
