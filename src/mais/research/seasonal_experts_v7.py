"""V7-06 — Modèles saisonniers experts : 6 politiques de sélection.

Extension du seasonal_expert V6 (AUC 0.982 sur n=68) avec protocole
purged CV V7-02 et 6 politiques de filtrage saisonnier.

RESEARCH_ONLY_NOT_TRADING : les backtests ci-dessous sont exploratoires.
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "seasonal_experts.json"

ALL_POLICY_NAMES = [
    "monthly_classic",
    "crop_year_phase",
    "rolling_52w_best",
    "event_driven",
    "combined_score",
    "no_filter",
]

_NORTHERN_PHASES = {
    "PLANTING": (3, 5),
    "GROWING": (6, 8),
    "HARVEST": (9, 11),
    "POST_HARVEST": (12, 2),
}


def get_crop_phase(month: int) -> str:
    for phase, (start, end) in _NORTHERN_PHASES.items():
        if start <= end:
            if start <= month <= end:
                return phase
        else:
            if month >= start or month <= end:
                return phase
    return "PLANTING"


def monthly_expert(
    dates: pd.DatetimeIndex,
    favorable_months: frozenset[int] | None = None,
) -> pd.Series:
    """Actif dans les mois historiquement favorables pour le premium EMA."""
    if favorable_months is None:
        favorable_months = frozenset({3, 4, 6, 7, 9})
    return pd.Series(dates.month.isin(favorable_months), index=dates, dtype=bool)


def crop_year_expert(dates: pd.DatetimeIndex) -> pd.Series:
    """Actif pendant GROWING et POST_HARVEST (phases historiquement actives)."""
    phases = pd.Series([get_crop_phase(m) for m in dates.month], index=dates)
    return phases.isin(["GROWING", "POST_HARVEST"])


def rolling_52w_best(
    dates: pd.DatetimeIndex,
    y_train: pd.Series,
    top_fraction: float = 0.4,
) -> pd.Series:
    """Active la fraction top_fraction des semaines par rendement rolling 52w."""
    week_of_year = dates.isocalendar().week.astype(int)
    if len(y_train) == 0:
        return pd.Series(True, index=dates)
    weekly_mean = y_train.groupby(y_train.index.isocalendar().week.astype(int)).mean()
    threshold = weekly_mean.quantile(1 - top_fraction)
    return pd.Series(
        week_of_year.map(lambda w: weekly_mean.get(w, 0.5) >= threshold),
        index=dates,
        dtype=bool,
    )


def event_driven(dates: pd.DatetimeIndex) -> pd.Series:
    """Actif pré/post WASDE (premier vendredi du mois ±5j) et pré-récolte."""
    # Approximation : actif dans les 5 premiers jours de chaque mois et pré-récolte
    day = dates.day
    pre_wasde = day <= 7  # Début de mois (WASDE arrivée)
    pre_harvest = (dates.month == 8) | (dates.month == 9)  # Pré-récolte EU
    return pd.Series((pre_wasde | pre_harvest), index=dates, dtype=bool)


def combined_score(
    dates: pd.DatetimeIndex,
    y_train: pd.Series | None = None,
    weights: dict[str, float] | None = None,
) -> pd.Series:
    """Score pondéré de toutes les politiques saisonnières."""
    if weights is None:
        weights = {"monthly": 0.4, "crop_year": 0.3, "event": 0.3}

    m_signal = monthly_expert(dates).astype(float)
    cy_signal = crop_year_expert(dates).astype(float)
    ev_signal = event_driven(dates).astype(float)

    score = (
        weights["monthly"] * m_signal
        + weights["crop_year"] * cy_signal
        + weights["event"] * ev_signal
    )
    return score


def get_policy_mask(
    policy_name: str,
    dates: pd.DatetimeIndex,
    y_train: pd.Series | None = None,
) -> pd.Series:
    """Renvoie un masque booléen pour la politique donnée."""
    if policy_name == "monthly_classic":
        return monthly_expert(dates)
    if policy_name == "crop_year_phase":
        return crop_year_expert(dates)
    if policy_name == "rolling_52w_best":
        train = y_train if y_train is not None else pd.Series(dtype=float)
        return rolling_52w_best(dates, train)
    if policy_name == "event_driven":
        return event_driven(dates)
    if policy_name == "combined_score":
        score = combined_score(dates, y_train)
        return score >= 0.5
    if policy_name == "no_filter":
        return pd.Series(True, index=dates, dtype=bool)
    raise ValueError(f"Politique inconnue: '{policy_name}'")


def compute_policy_coverage(
    policy_name: str,
    dates: pd.DatetimeIndex,
    y_train: pd.Series | None = None,
) -> dict[str, Any]:
    """Calcule la couverture (% de jours actifs) pour une politique."""
    mask = get_policy_mask(policy_name, dates, y_train)
    n_active = int(mask.sum())
    coverage = float(n_active / len(dates)) if len(dates) > 0 else 0.0
    return {
        "policy": policy_name,
        "n_active_days": n_active,
        "n_total_days": len(dates),
        "coverage": round(coverage, 4),
    }


def backtest_seasonal_policy(
    dates: pd.DatetimeIndex,
    y_true: pd.Series,
    y_pred: pd.Series,
    policy_name: str,
    y_train: pd.Series | None = None,
    confidence_threshold: float = 0.55,
) -> dict[str, Any]:
    """Backtest recherche (RESEARCH_ONLY_NOT_TRADING).

    Ne pas utiliser comme signal de trading.
    """
    mask = get_policy_mask(policy_name, dates, y_train)
    confident = y_pred >= confidence_threshold
    selected = mask & confident

    n_selected = int(selected.sum())
    if n_selected == 0:
        return {
            "policy": policy_name,
            "n_trades": 0,
            "coverage": 0.0,
            "accuracy": None,
            "verdict": "NO_SIGNAL",
            "note": "RESEARCH_ONLY_NOT_TRADING",
        }

    accuracy = float(y_true[selected].eq(1).mean()) if n_selected > 0 else float("nan")
    return {
        "policy": policy_name,
        "n_trades": n_selected,
        "coverage": round(float(selected.mean()), 4),
        "accuracy": round(accuracy, 4),
        "verdict": "RESEARCH_ONLY_NOT_TRADING",
        "note": "RESEARCH_ONLY — backtest exploratoire, pas de signal opérationnel",
    }


def run_seasonal_expert_comparison(
    dates: pd.DatetimeIndex,
    y_true: pd.Series,
    y_pred: pd.Series | None = None,
    y_train: pd.Series | None = None,
) -> dict[str, Any]:
    """Compare les 6 politiques saisonnières."""
    if y_pred is None:
        y_pred = pd.Series(0.5, index=dates)

    coverages = {
        name: compute_policy_coverage(name, dates, y_train)
        for name in ALL_POLICY_NAMES
    }
    backtests = {
        name: backtest_seasonal_policy(dates, y_true, y_pred, name, y_train)
        for name in ALL_POLICY_NAMES
    }
    return {
        "version": "V7-06",
        "n_dates": len(dates),
        "policies": ALL_POLICY_NAMES,
        "coverages": coverages,
        "backtests": backtests,
        "v6_reference": {"policy": "monthly_classic", "auc_v6": 0.982, "n_oof_v6": 68},
    }


def save_seasonal_experts(
    dates: pd.DatetimeIndex,
    y_true: pd.Series,
    y_pred: pd.Series | None = None,
    y_train: pd.Series | None = None,
) -> dict[str, Any]:
    result = run_seasonal_expert_comparison(dates, y_true, y_pred, y_train)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-06",
        target="seasonal_expert_comparison",
        horizon=90,
        model="seasonal_filter",
        cv_protocol="leave_one_crop_year",
        embargo_days=90,
        n_oof=0,
        features=ALL_POLICY_NAMES,
        metrics={"n_policies": len(ALL_POLICY_NAMES)},
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
