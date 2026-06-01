"""V7-28 — Architecture finale de l'indicateur maïs V7."""
from __future__ import annotations

import json
from typing import Any

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "final_indicator_v7.json"
_HOLDOUT_LOCK = ARTEFACTS_DIR / "v7" / "holdout_lock.json"


def _check_holdout_lock() -> dict:
    if _HOLDOUT_LOCK.exists():
        return json.loads(_HOLDOUT_LOCK.read_text())
    return {"used": False, "start": "2024-01-01", "end": "2024-12-31"}


def design_final_indicator() -> dict[str, Any]:
    holdout = _check_holdout_lock()

    indicator_architecture = {
        "name": "MaizeStudyIndicator_V7",
        "version": "7.0",
        "primary_signal": "EMA_CBOT_relative_premium_h40_h90",
        "secondary_signals": [
            "basis_mean_reversion_H40",
            "seasonal_expert_eu_harvest",
            "cbot_direction_H20_H60",
        ],
        "components": {
            "basis_module": {
                "features": ["ema_cbot_basis", "ema_cbot_basis_zscore_52w"],
                "horizon": [40, 90],
                "verdict": "PRIMARY_DRIVER",
            },
            "seasonal_filter": {
                "active_months": [6, 7, 8, 9, 10],
                "basis": "eu_harvest_season",
                "verdict": "CONFIDENCE_FILTER",
            },
            "roll_risk_veto": {
                "threshold": 0.7,
                "action": "ABSTAIN",
                "verdict": "RISK_GATE",
            },
            "nested_stacking_meta": {
                "protocol": "nested_walk_forward_leave_one_crop_year",
                "embargo_days": 90,
                "base_learners": ["y_up_h20", "y_up_h40", "y_rel_outperform_h40"],
                "global_auc_v7": None,
                "verdict": "META_LAYER",
            },
            "p_correct_filter": {
                "brier_threshold": 0.25,
                "min_distance_to_boundary": 0.15,
                "verdict": "CALIBRATION_GATE",
            },
        },
        "output_signals": {
            "relative_premium_direction": {
                "type": "binary",
                "description": "EMA va sur/sous-performer CBOT H40",
                "confidence_tiers": ["HIGH", "MEDIUM", "LOW", "UNCERTAIN"],
            },
            "cbot_direction": {
                "type": "binary",
                "description": "CBOT va monter H20/H60",
                "confidence_tiers": ["HIGH", "MEDIUM", "LOW", "UNCERTAIN"],
            },
        },
        "holdout_status": {
            "holdout_period": f"{holdout.get('start')} to {holdout.get('end')}",
            "holdout_used": holdout.get("used", False),
            "authorized_ticket": holdout.get("authorized_ticket", "V7-28"),
            "instruction": (
                "Holdout disponible pour validation externe"
                if not holdout.get("used")
                else "Holdout déjà utilisé"
            ),
        },
        "operational_guidelines": {
            "retraining_frequency": "Trimestrielle (d'après V7-38 model decay)",
            "data_sources_required": [
                "CBOT futures daily (ZC)",
                "EMA Euronext front month",
                "WASDE monthly",
                "COT weekly",
                "EIA weekly",
            ],
            "production_readiness": "RESEARCH_ONLY_NOT_PRODUCTION",
            "next_steps": [
                "Obtenir données EMA officielles Euronext (non-proxy)",
                "Déverrouiller holdout 2024 pour validation externe",
                "Backtester sur période officielle si données disponibles",
            ],
        },
        "caveats": [
            "Source EMA = barchart_proxy_exploratory",
            "Tous les backtests = RESEARCH_ONLY_NOT_TRADING",
            "Holdout 2024 non utilisé dans cette version",
        ],
    }

    # Load nested stacking result if available
    ns_path = ARTEFACTS_DIR / "v7" / "cross_target_stacking_v2.json"
    if ns_path.exists():
        ns = json.loads(ns_path.read_text())
        indicator_architecture["components"]["nested_stacking_meta"]["global_auc_v7"] = ns.get("global_auc")

    return {
        "version": "V7-28",
        "indicator_architecture": indicator_architecture,
        "verdict": "INDICATOR_DESIGNED",
        "experiment_type": "INDICATOR_CANDIDATE",
    }


def save_final_indicator() -> dict[str, Any]:
    result = design_final_indicator()
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-28",
        target="final_indicator",
        horizon=40,
        model="MaizeStudyIndicator_V7",
        cv_protocol="none",
        embargo_days=0,
        n_oof=0,
        features=["basis", "seasonal", "roll_risk", "nested_stacking"],
        metrics={"holdout_used": False},
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
