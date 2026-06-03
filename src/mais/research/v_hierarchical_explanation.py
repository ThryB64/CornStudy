"""VN-D4 — Explication hiérarchique : contribution marginale par FAMILLE de drivers.

Au lieu d'un modèle opaque, on regroupe les covariables en familles économiques et on mesure la contribution
marginale de chaque famille (ablation : AUC walk-forward avec toutes les familles vs sans la famille) sur la
cible « compression ≥0.5 en h jours » (réutilise la machinerie hazard VN-D1).

Familles : MARKET (basis_z, vitesse de spread, CBOT), SUBSTITUTION (blé/maïs z), POSITIONING (COT).
Honnête : si D1 montre un edge faible, les ΔAUC seront petits — on l'écrit. Pas de p-hacking (ablation
simple, walk-forward). EXPLANATORY_ONLY. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V_DIR = ARTEFACTS_DIR / "hierarchical_explanation"
V_DIR.mkdir(parents=True, exist_ok=True)
FAMILIES = {
    "MARKET": ["basis_z", "dz5", "cbot_ret10"],
    "SUBSTITUTION": ["wc_z"],
    "POSITIONING": ["cot_mm_net"],
}
HORIZON = 10


def run_v_hierarchical(df: pd.DataFrame) -> dict[str, Any]:
    from mais.research.v_hazard_compression import _features, _target, _walk_forward_auc
    assert_no_holdout(df)
    feat = _features(df)
    y = _target(df, HORIZON)
    panel = feat["basis_z"] > 1.0
    sub = panel & feat.notna().all(axis=1) & y.notna()
    if sub.sum() < 250:
        return {"version": "HIERARCHICAL-EXPLANATION", "verdict": "NO_DATA", "n": int(sub.sum())}
    cols = list(feat.columns)
    fsub = feat[sub]
    ysub = y[sub].to_numpy()
    dates = df.index[sub]

    full = _walk_forward_auc(fsub[cols].to_numpy(), ysub, dates)
    full_auc = full.get("auc")
    contributions = {}
    for fam, fam_cols in FAMILIES.items():
        present = [c for c in fam_cols if c in cols]
        if not present:
            contributions[fam] = None
            continue
        reduced_cols = [c for c in cols if c not in present]
        if not reduced_cols:
            contributions[fam] = None
            continue
        red = _walk_forward_auc(fsub[reduced_cols].to_numpy(), ysub, dates)
        if full_auc is not None and red.get("auc") is not None:
            contributions[fam] = round(full_auc - red["auc"], 3)  # ΔAUC = apport marginal de la famille
        else:
            contributions[fam] = None

    ranked = dict(sorted(
        ((k, v) for k, v in contributions.items() if v is not None), key=lambda kv: kv[1], reverse=True))
    top = next(iter(ranked.items())) if ranked else (None, None)
    weak = full_auc is None or full_auc < 0.62

    out = {
        "version": "HIERARCHICAL-EXPLANATION",
        "verdict": "EXPLANATORY_FAMILIES_RANKED",
        "target": f"compression>=0.5 en {HORIZON} j",
        "full_model_auc": full_auc,
        "base_rate": full.get("base_rate"),
        "family_marginal_auc": contributions,
        "top_family": {"family": top[0], "delta_auc": top[1]},
        "interpretation": (
            f"AUC modèle complet {full_auc} (base rate {full.get('base_rate')}). Apport marginal par famille "
            f"(ΔAUC ablation) : {contributions}. Famille la plus contributive : {top[0]} ({top[1]}). "
            + ("ATTENTION : l'AUC complet reste faible (~base rate) -> les contributions sont petites et peu "
               "fiables ; EXPLICATIF seulement, cohérent V106/VN-D1 (timing dur). " if weak else
               "Le modèle complet a un AUC notable -> hiérarchie de familles informative. ")
            + "Aucune famille n'entre dans la décision live sans confirmation forward."),
        "note": "Ablation walk-forward (réutilise VN-D1). Pas de p-hacking. EXPLANATORY_ONLY.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V_DIR / "hierarchical_explanation.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
