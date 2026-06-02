"""V138 — Estimateur d'horizon : convertir la demi-vie par tier (V130) en jours attendus jusqu'à la cible.

V130 a mesuré que la demi-vie de réversion dépend du tier (MODERATE 8.3 / STRONG 4.9 / EXTREME 3.3 j). Sous
un AR(1) de moyenne ~0, partir de z0 et atteindre z_cible prend t = demi-vie × log2(z0 / z_cible). On en tire
un horizon ANALYTIQUE jusqu'à z→0.5 (z→0 est asymptotique sous AR(1) pur -> on garde l'empirique pour le
complet). On VALIDE le modèle contre les durées réalisées (V47 days_z05) : MAE, corrélation. On NE remplace
pas l'horizon saisonnier V27 ; on ajoute une estimation explicable, conditionnée au tier et au z courant.

assert_no_holdout sur la validation. Statut : RESEARCH_ONLY_NOT_TRADING. Contexte, jamais un veto.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT
from mais.registry.holdout_lock import assert_no_holdout

V138_DIR = ARTEFACTS_DIR / "v138"
V138_DIR.mkdir(parents=True, exist_ok=True)
V130_ARTEFACT = ARTEFACTS_DIR / "v130" / "v130_regime_econometrics.json"
OFFICIAL_JOURNAL = ROOT / "data" / "forward_journal" / "official_forward_journal.parquet"
DEFAULT_HALF_LIFE = 17.0
TIER_OF = {"SHORT_PREMIUM_MODERATE": "MODERATE", "SHORT_PREMIUM_STRONG": "STRONG",
           "SHORT_PREMIUM_EXTREME": "EXTREME"}


def _half_life_by_tier() -> dict[str, float]:
    try:
        hl = json.loads(V130_ARTEFACT.read_text(encoding="utf-8")).get("half_life_by_tier", {})
        return {k: float(v) for k, v in hl.items() if v is not None}
    except (OSError, ValueError):
        return {}


def days_to_target(z0: float, z_target: float, half_life: float) -> float | None:
    """Jours attendus pour passer de z0 à z_target sous AR(1) moyenne 0 : HL*log2(z0/z_target)."""
    if z0 is None or z0 <= z_target or z_target <= 0 or half_life is None or half_life <= 0:
        return None
    return round(float(half_life * np.log2(z0 / z_target)), 1)


def _tier_from_z(z: float) -> str:
    if pd.isna(z) or z < 1.0:
        return "NO_SIGNAL"
    if z < 1.5:
        return "MODERATE"
    return "STRONG" if z < 2.0 else "EXTREME"


def validate_against_trades(df: pd.DataFrame, hl: dict[str, float]) -> dict[str, Any]:
    """Compare jours prédits (modèle demi-vie) vs réalisés (days_z05 de V47) sur les trades."""
    from mais.research.v47_objective_choice import _paired_objectives
    t = _paired_objectives(df)
    if len(t) < 15:
        return {"verdict": "TOO_FEW", "n": int(len(t))}
    t = t.copy()
    t["tier"] = t["entry_z"].map(_tier_from_z)
    preds, reals = [], []
    for _, r in t.iterrows():
        h = hl.get(r["tier"], DEFAULT_HALF_LIFE)
        pred = days_to_target(float(r["entry_z"]), 0.5, h)
        if pred is not None and pd.notna(r.get("days_z05")):
            preds.append(pred)
            reals.append(float(r["days_z05"]))
    if len(preds) < 15:
        return {"verdict": "TOO_FEW_VALID", "n": int(len(preds))}
    preds_a, reals_a = np.array(preds), np.array(reals)
    mae = round(float(np.mean(np.abs(preds_a - reals_a))), 1)
    corr = round(float(np.corrcoef(preds_a, reals_a)[0, 1]), 3) if np.std(preds_a) > 0 else None
    bias = round(float(np.mean(preds_a - reals_a)), 1)
    return {"verdict": "VALIDATED", "n": int(len(preds)), "mae_days": mae,
            "corr_pred_real": corr, "bias_days": bias,
            "mean_pred": round(float(preds_a.mean()), 1), "mean_real": round(float(reals_a.mean()), 1)}


def run_v138_horizon(df: pd.DataFrame | None = None) -> dict[str, Any]:
    hl = _half_life_by_tier()
    hl_used = hl or {"MODERATE": DEFAULT_HALF_LIFE, "STRONG": DEFAULT_HALF_LIFE, "EXTREME": DEFAULT_HALF_LIFE}

    validation = None
    if df is not None:
        assert_no_holdout(df)
        validation = validate_against_trades(df, hl_used)

    # estimation live à partir du dernier signal officiel
    # facteur de calage : le modèle AR(1) sous-prédit (réversion non clean depuis l'entrée).
    # On le mesure sur la validation et on l'applique au live comme borne RÉALISTE (pas un fit de seuil).
    scale = None
    if validation and validation.get("verdict") == "VALIDATED" and validation.get("mean_pred"):
        scale = round(validation["mean_real"] / validation["mean_pred"], 2) if validation["mean_pred"] else None

    live = None
    if OFFICIAL_JOURNAL.exists():
        j = pd.read_parquet(OFFICIAL_JOURNAL).sort_values("price_date")
        if len(j) and pd.notna(j.iloc[-1].get("basis_z_used")):
            z0 = float(j.iloc[-1]["basis_z_used"])
            tier = TIER_OF.get(j.iloc[-1].get("signal_tier"), _tier_from_z(z0))
            h = hl_used.get(tier, DEFAULT_HALF_LIFE)
            analytic = days_to_target(z0, 0.5, h)
            live = {"as_of": str(pd.Timestamp(j.iloc[-1]["price_date"]).date()), "basis_z": z0, "tier": tier,
                    "half_life_days": h, "analytic_days_to_z05": analytic,
                    "calibrated_days_to_z05": round(analytic * scale, 1) if (analytic and scale) else None,
                    "expected_days_to_z1": days_to_target(z0, 1.0, h)}

    # le modèle analytique pur sous-prédit largement (corr≈0, biais négatif) -> NE PAS en faire l'horizon
    # primaire ; ADD_TO_HORIZON seulement si la corrélation pred/réel est franche.
    good = bool(validation and validation.get("verdict") == "VALIDATED"
                and validation.get("corr_pred_real") is not None and validation["corr_pred_real"] > 0.2)
    out = {
        "version": "V138-HORIZON-ESTIMATOR",
        "verdict": "ADD_TO_HORIZON" if good else ("WATCHLIST" if validation else "LIVE_ONLY"),
        "half_life_by_tier_used": hl_used,
        "half_life_source": "V130" if hl else "default_17j",
        "validation": validation,
        "live_estimate": live,
        "calibration_factor_real_over_analytic": scale,
        "interpretation": (
            "Horizon analytique jusqu'à z→0.5 = demi-vie_tier × log2(z0/0.5). "
            + (f"Validation : MAE {validation['mae_days']} j, corr pred/réel {validation['corr_pred_real']}, "
               f"biais {validation['bias_days']} j (analytique {validation['mean_pred']} vs réel "
               f"{validation['mean_real']}). **Le modèle AR(1) pur SOUS-PRÉDIT** (réversion non clean depuis "
               f"l'entrée : overshoot + chemin) -> facteur de calage ×{scale}. NE PAS en faire l'horizon "
               "primaire ; l'horizon saisonnier V27 / empirique V72 reste autoritaire. "
               if validation and validation.get("verdict") == "VALIDATED" else "")
            + (f"Live : z {live['basis_z']} ({live['tier']}) → analytique ~{live['analytic_days_to_z05']} j, "
               f"calé ~{live['calibrated_days_to_z05']} j jusqu'à z→0.5. " if live else "")
            + "z→0 reste asymptotique sous AR(1) -> empirique V72/saisonnier V27 pour le complet."),
        "note": "Modèle interprétable (aucun fit de seuil). HONNÊTE : l'analytique pur sous-prédit (corr≈0) "
                "-> WATCHLIST, gardé comme borne calée, pas comme horizon primaire. Baseline inchangée.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V138_DIR / "v138_horizon.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def horizon_estimator_report_block() -> str:
    artefact = V138_DIR / "v138_horizon.json"
    if not artefact.exists():
        return ""
    try:
        s = json.loads(artefact.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    live = s.get("live_estimate")
    if not live:
        return ""
    val = s.get("validation") or {}
    val_txt = (f" · validé MAE {val.get('mae_days')}j corr {val.get('corr_pred_real')}"
               if val.get("verdict") == "VALIDATED" else "")
    cal = live.get("calibrated_days_to_z05")
    headline = cal if cal is not None else live.get("analytic_days_to_z05")
    return (
        "### Horizon estimé jusqu'à la cible (V138)\n"
        f"- z {live['basis_z']} ({live['tier']}, demi-vie {live['half_life_days']} j) → **~{headline} j "
        f"jusqu'à z→0.5** (analytique {live.get('analytic_days_to_z05')}j ×calage){val_txt}\n"
        "- L'analytique AR(1) sous-prédit ; horizon primaire = saisonnier V27 / empirique V72. "
        "Contexte, jamais un veto. RESEARCH_ONLY_NOT_TRADING.\n"
    )
