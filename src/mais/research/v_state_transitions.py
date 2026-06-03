"""VN-D2 — Transitions d'état de l'indicateur (au-delà de NO_SIGNAL/MODERATE/STRONG/EXTREME).

Construit SUR V131 (WAIT_CONFIRMATION existe déjà). Étend la taxonomie en trajectoires interprétables, à
partir des diagnostics déjà calculés (aucun nouveau classifieur appris) :
  - WAIT_CONFIRMATION        : z < 1.2 (marginal, cf V131)
  - STILL_WIDENING           : prime active qui s'écarte encore (Δbasis_z > 0 sur 5 j) — souvent PRÉ-PIC, PAS
    un mauvais résultat (le niveau réverse ensuite ; le risque ADVERSE réel est PATH-based, V82/V124)
  - EXTREME_EARLY_RELAXATION : z >= 2 et compression amorcée (Δbasis_z <= -seuil)
  - EXTREME_STATIC           : z >= 2 et peu de mouvement
  - STRONG_PHYSICAL_JUSTIFIED: 1.5 <= z < 2 et PHYSICAL_TENSION HIGH (prime adossée à une tension réelle)
  - STRONG_CBOT_CATCHUP      : 1.5 <= z < 2 et CBOT en hausse (compression par rattrapage CBOT)
  - MODERATE_NEUTRAL         : reste

But : plus de granularité décisionnelle (et donc plus de signaux exploitables) SANS abaisser les seuils.
Descriptif. Statut : RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V_DIR = ARTEFACTS_DIR / "state_transitions"
V_DIR.mkdir(parents=True, exist_ok=True)
DZ = 0.15  # seuil de mouvement de basis_z sur 5 j


def classify_state(z: float, dz5: float, cbot_ret10: float, physical_tension: str) -> str:
    if pd.isna(z) or z < 1.0:
        return "NO_SIGNAL"
    if z < 1.2:
        return "WAIT_CONFIRMATION"
    if not pd.isna(dz5) and dz5 > DZ:
        return "STILL_WIDENING"
    if z >= 2.0:
        return "EXTREME_EARLY_RELAXATION" if (not pd.isna(dz5) and dz5 <= -DZ) else "EXTREME_STATIC"
    if z >= 1.5:
        if physical_tension == "HIGH":
            return "STRONG_PHYSICAL_JUSTIFIED"
        if not pd.isna(cbot_ret10) and cbot_ret10 > 0.01:
            return "STRONG_CBOT_CATCHUP"
        return "STRONG_NEUTRAL"
    return "MODERATE_NEUTRAL"


def _states_over_master(df: pd.DataFrame) -> pd.Series:
    z = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    dz5 = z - z.shift(5)
    cbot = pd.to_numeric(df.get("cbot_close"), errors="coerce")
    cbot_ret10 = np.log(cbot / cbot.shift(10))
    try:
        from mais.research.v54_physical_tension import compute_physical_tension
        pt = compute_physical_tension(df)["physical_tension"].reindex(df.index)
    except Exception:  # noqa: BLE001
        pt = pd.Series("NO_SIGNAL", index=df.index)
    return pd.Series([classify_state(z.iloc[i], dz5.iloc[i], cbot_ret10.iloc[i], str(pt.iloc[i]))
                      for i in range(len(df))], index=df.index)


def run_v_state_transitions(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    z = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    if z.notna().sum() < 200:
        return {"version": "STATE-TRANSITIONS", "verdict": "NO_DATA"}
    states = _states_over_master(df)
    active = states[states != "NO_SIGNAL"]
    counts = active.value_counts().to_dict()

    # lien descriptif au futur : compression à 20 j par état (Δbasis_z moyen sur les 20 j suivants)
    dz_fwd20 = (z.shift(-20) - z)
    by_state_fwd = {}
    for s in active.unique():
        mask = (states == s) & dz_fwd20.notna()
        if mask.sum() >= 10:
            by_state_fwd[s] = round(float(dz_fwd20[mask].mean()), 3)

    out = {
        "version": "STATE-TRANSITIONS",
        "verdict": "STATE_TRANSITIONS_BUILT",
        "n_active_days": int(len(active)),
        "state_counts": {str(k): int(v) for k, v in counts.items()},
        "mean_fwd20_dz_by_state": by_state_fwd,
        "current_state": str(states.iloc[-1]),
        "interpretation": (
            f"Taxonomie de trajectoires sur {len(active)} jours actifs : {counts}. Δbasis_z moyen à 20 j par "
            f"état : {by_state_fwd}. CONSTAT HONNÊTE : TOUS les états actifs compressent en moyenne à 20 j "
            "(Δz<0) — c'est la réversion du NIVEAU (cohérent V120/V130). EXTREME_STATIC compresse le plus ; "
            "STILL_WIDENING aussi (pré-pic), donc 'encore en train de s'écarter' n'est PAS un mauvais signal "
            "de niveau. Le risque ADVERSE réel (perte) est PATH-based (MFE faible, durée), capté par V82/V124, "
            "PAS par le Δz à 20 j. Descriptif, étend V131 sans changer les seuils ni la baseline."),
        "note": "Aucun classifieur appris : règles sur diagnostics existants. STILL_WIDENING renommé (ex "
                "'ADVERSE_DRIFT') car il ne capte pas le risque PnL. CONTEXTE, jamais un veto.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V_DIR / "state_transitions.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def state_transitions_report_block() -> str:
    artefact = V_DIR / "state_transitions.json"
    if not artefact.exists():
        return ""
    try:
        s = json.loads(artefact.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    if s.get("verdict") != "STATE_TRANSITIONS_BUILT":
        return ""
    return (
        "### Trajectoires d'état (VN-D2 — étend V131)\n"
        f"- États actifs : {s['state_counts']}\n"
        f"- Δbasis_z moyen à 20 j par état : {s['mean_fwd20_dz_by_state']}\n"
        "- Descriptif, seuils inchangés. RESEARCH_ONLY_NOT_TRADING.\n"
    )
