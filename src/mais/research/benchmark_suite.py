"""V7-31 — Benchmark naïf et professionnel.

5 benchmarks naïfs + 3 benchmarks professionnels.
Toute AUC V7 est évaluée en delta vs ces baselines.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

try:
    from sklearn.metrics import roc_auc_score
except ImportError as e:
    raise ImportError("scikit-learn requis pour benchmark_suite") from e

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "benchmark_suite.json"

NAIVE_BENCHMARKS = ["random", "persistence", "naive_seasonal", "always_up", "always_down"]
PROFESSIONAL_BENCHMARKS = ["momentum_20d", "trend_following_52w", "carry_signal"]
ALL_BENCHMARK_NAMES = NAIVE_BENCHMARKS + PROFESSIONAL_BENCHMARKS


class NaiveBenchmarks:

    @staticmethod
    def random(y_true: pd.Series, seed: int = 42) -> pd.Series:
        rng = np.random.default_rng(seed)
        return pd.Series(rng.random(len(y_true)), index=y_true.index)

    @staticmethod
    def persistence(y_true: pd.Series) -> pd.Series:
        return (y_true.shift(1) > 0).astype(float).fillna(0.5)

    @staticmethod
    def naive_seasonal(y_true: pd.Series, dates: pd.DatetimeIndex | None = None) -> pd.Series:
        if dates is None:
            dates = y_true.index
        monthly_mean = y_true.groupby(dates.month).transform("mean")
        median_val = monthly_mean.median()
        return (monthly_mean > median_val).astype(float)

    @staticmethod
    def always_up(y_true: pd.Series) -> pd.Series:
        return pd.Series(1.0, index=y_true.index)

    @staticmethod
    def always_down(y_true: pd.Series) -> pd.Series:
        return pd.Series(0.0, index=y_true.index)


class ProfessionalBenchmarks:

    @staticmethod
    def momentum_20d(prices: pd.Series) -> pd.Series:
        return (prices.pct_change(20).rolling(5).mean() > 0).astype(float).fillna(0.5)

    @staticmethod
    def trend_following_52w(prices: pd.Series) -> pd.Series:
        return (prices > prices.rolling(252, min_periods=20).mean()).astype(float).fillna(0.5)

    @staticmethod
    def carry_signal(basis: pd.Series) -> pd.Series:
        return (basis > basis.rolling(60, min_periods=10).mean()).astype(float).fillna(0.5)


def _safe_auc(y_true: pd.Series, y_score: pd.Series) -> float | None:
    mask = y_true.notna() & y_score.notna()
    yt = y_true[mask].values
    ys = y_score[mask].values
    if len(yt) < 10 or yt.sum() == 0 or yt.sum() == len(yt):
        return None
    return float(roc_auc_score(yt, ys))


def evaluate_all_benchmarks(
    y_true: pd.Series,
    prices: pd.Series | None = None,
    basis: pd.Series | None = None,
) -> dict[str, float | None]:
    """Évalue les 8 benchmarks pour une cible donnée."""
    dates = y_true.index if isinstance(y_true.index, pd.DatetimeIndex) else None
    ref_prices = prices if prices is not None else y_true
    ref_basis = basis if basis is not None else y_true

    benchmarks = {
        "random": NaiveBenchmarks.random(y_true),
        "persistence": NaiveBenchmarks.persistence(y_true),
        "naive_seasonal": NaiveBenchmarks.naive_seasonal(y_true, dates),
        "always_up": NaiveBenchmarks.always_up(y_true),
        "always_down": NaiveBenchmarks.always_down(y_true),
        "momentum_20d": ProfessionalBenchmarks.momentum_20d(ref_prices),
        "trend_following_52w": ProfessionalBenchmarks.trend_following_52w(ref_prices),
        "carry_signal": ProfessionalBenchmarks.carry_signal(ref_basis),
    }
    return {name: _safe_auc(y_true, scores) for name, scores in benchmarks.items()}


def compute_delta_auc(auc_model: float, benchmark_aucs: dict[str, float | None]) -> dict[str, Any]:
    """Calcule le delta AUC entre un modèle et chaque benchmark."""
    valid = {k: v for k, v in benchmark_aucs.items() if v is not None}
    best_baseline = max(valid, key=lambda k: valid[k]) if valid else None
    best_baseline_auc = valid[best_baseline] if best_baseline else None
    return {
        "model_auc": auc_model,
        "best_baseline": best_baseline,
        "best_baseline_auc": best_baseline_auc,
        "delta_vs_best": round(auc_model - best_baseline_auc, 4) if best_baseline_auc else None,
        "deltas": {
            k: round(auc_model - v, 4) if v is not None else None
            for k, v in benchmark_aucs.items()
        },
    }


def run_benchmark_suite(
    targets: dict[str, pd.Series],
    prices: pd.Series | None = None,
    basis: pd.Series | None = None,
) -> dict[str, Any]:
    """Évalue les 8 benchmarks pour chaque cible."""
    results: dict[str, Any] = {}
    for target_name, y_true in targets.items():
        aucs = evaluate_all_benchmarks(y_true, prices, basis)
        valid_aucs = {k: v for k, v in aucs.items() if v is not None}
        best = max(valid_aucs, key=lambda k: valid_aucs[k]) if valid_aucs else None
        results[target_name] = {
            "benchmark_aucs": aucs,
            "best_benchmark": best,
            "best_benchmark_auc": valid_aucs.get(best) if best else None,
            "n_valid_benchmarks": len(valid_aucs),
        }
    return {
        "n_targets": len(targets),
        "benchmarks": ALL_BENCHMARK_NAMES,
        "results": results,
    }


def save_benchmark_suite(
    targets: dict[str, pd.Series],
    prices: pd.Series | None = None,
    basis: pd.Series | None = None,
) -> dict[str, Any]:
    import json
    suite = run_benchmark_suite(targets, prices, basis)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(suite, indent=2, ensure_ascii=False), encoding="utf-8")

    best_aucs = [
        r["best_benchmark_auc"]
        for r in suite["results"].values()
        if r["best_benchmark_auc"] is not None
    ]
    mean_best = float(np.mean(best_aucs)) if best_aucs else 0.0

    register_experiment(
        experiment_id="V7-31",
        target="benchmark_suite",
        horizon=0,
        model="naive_and_professional_baselines",
        cv_protocol="none",
        embargo_days=0,
        n_oof=0,
        features=ALL_BENCHMARK_NAMES,
        metrics={
            "n_targets": suite["n_targets"],
            "n_benchmarks": len(ALL_BENCHMARK_NAMES),
            "mean_best_baseline_auc": round(mean_best, 4),
        },
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return suite
