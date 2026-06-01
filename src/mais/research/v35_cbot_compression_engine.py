"""V35 — CBOT comme moteur de compression : prédire le CHEMIN probable à l'entrée.

V21/V29 : la compression profitable vient surtout d'un rattrapage CBOT (CBOT_DRIVEN). V35 demande : parmi
les compressions, peut-on prévoir à l'entrée si elle sera CBOT_DRIVEN (rattrapage mondial) ou EMA_DRIVEN
(baisse Euronext) ? Utile pour enrichir le message de l'indicateur :
  « short premium — compression probable par rattrapage CBOT » vs « par baisse EMA ».

Features d'entrée CBOT/technique (causales, réutilise V32). n petit -> LOO + descriptif, aucun seuil optimisé.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 retiré.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V35_DIR = ARTEFACTS_DIR / "v35"
V35_DIR.mkdir(parents=True, exist_ok=True)


def run_v35_compression_engine(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    from mais.research.v32_adverse_path_research import _loo_auc, _profile, build_adverse_frame
    adf = build_adverse_frame(df)
    if len(adf) < 15:
        return {"version": "V35-CBOT-ENGINE", "verdict": "TOO_FEW", "n": int(len(adf))}

    comp = adf[adf["path"].isin(["CBOT_DRIVEN", "EMA_DRIVEN"])].copy()
    if len(comp) < 12 or comp["path"].nunique() < 2:
        return {"version": "V35-CBOT-ENGINE", "verdict": "TOO_FEW_COMPRESSIONS", "n": int(len(comp))}
    comp["is_cbot_driven"] = (comp["path"] == "CBOT_DRIVEN").astype(int)

    feat_cols = ["entry_z", "basis_level", "backwardation", "cbot_drawdown_risk",
                 "cbot_mom_20", "realized_vol_20"]
    prof_cbot = _profile(comp[comp["is_cbot_driven"] == 1], feat_cols)
    prof_ema = _profile(comp[comp["is_cbot_driven"] == 0], feat_cols)
    separators = {c: round(prof_cbot[c] - prof_ema[c], 4)
                  for c in feat_cols if prof_cbot.get(c) is not None and prof_ema.get(c) is not None}

    x = comp[feat_cols].apply(pd.to_numeric, errors="coerce")
    auc = _loo_auc(x, comp["is_cbot_driven"])
    auc_uni = {c: _loo_auc(x[[c]], comp["is_cbot_driven"]) for c in feat_cols}
    auc_uni = {c: round(v, 3) for c, v in auc_uni.items() if v is not None}

    base_rate = float(comp["is_cbot_driven"].mean())
    verdict = ("CBOT_PATH_PARTIALLY_PREDICTABLE" if (auc is not None and auc >= 0.60)
               else "CBOT_PATH_DOMINATES_BUT_HARD_TO_TIME")
    out = {
        "version": "V35-CBOT-ENGINE",
        "n_compressions": int(len(comp)),
        "cbot_driven_share": round(base_rate, 3),
        "profile_cbot_driven": prof_cbot,
        "profile_ema_driven": prof_ema,
        "separators_cbot_minus_ema": separators,
        "loo_auc_cbot_vs_ema": round(auc, 3) if auc is not None else None,
        "loo_auc_univariate": dict(sorted(auc_uni.items(), key=lambda kv: -kv[1])),
        "verdict": verdict,
        "interpretation": (
            "La compression est majoritairement CBOT_DRIVEN (cf. base_rate). Si le chemin est prévisible "
            "(AUC>=0.60), l'indicateur peut annoncer le mécanisme probable ; sinon on affiche seulement "
            "'compression souvent par rattrapage CBOT' comme contexte. CONTEXTE, pas veto."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V35_DIR / "v35_cbot_engine.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
