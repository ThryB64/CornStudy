"""VN-D3 — Discriminant « bon short premium vs ADVERSE » à partir de l'info connue TÔT.

Question : qu'est-ce qui distingue, à l'ENTRÉE (info disponible tôt, pas l'issue), un épisode ADVERSE d'un
bon ? On lit la librairie d'épisodes V82 et on mesure le pouvoir de séparation de chaque feature ENTRÉE
(entry_z, cbot_support, adverse_risk, wheat_corn_z, roll_month, crisis) vis-à-vis du label `adverse`. On
EXCLUT les outcomes (mfe/mae/duration = connus seulement à la sortie → leakage circulaire).

Leçon V64 : empiler dilue. On regarde donc les séparateurs UN PAR UN (AUC univarié), n=42 → descriptif,
WATCHLIST. Aucun fit multivarié sur 42 trades. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V_DIR = ARTEFACTS_DIR / "adverse_discriminator"
V_DIR.mkdir(parents=True, exist_ok=True)
EPISODES = ROOT / "data" / "research" / "high_basis_episodes.parquet"
SUPPORT_MAP = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
RISK_MAP = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


def _encode(ep: pd.DataFrame) -> pd.DataFrame:
    f = pd.DataFrame(index=ep.index)
    f["entry_z"] = pd.to_numeric(ep.get("entry_z"), errors="coerce")
    f["wheat_corn_z"] = pd.to_numeric(ep.get("wheat_corn_z"), errors="coerce")
    f["roll_month"] = pd.to_numeric(ep.get("roll_month"), errors="coerce")
    f["crisis"] = pd.to_numeric(ep.get("crisis"), errors="coerce")
    if "cbot_support" in ep.columns:
        f["cbot_support_ord"] = ep["cbot_support"].map(SUPPORT_MAP)
    if "adverse_risk" in ep.columns:
        f["adverse_risk_ord"] = ep["adverse_risk"].map(RISK_MAP)
    return f


def _univariate_auc(x: pd.Series, y: np.ndarray) -> float | None:
    m = x.notna().to_numpy() & ~np.isnan(y)
    if m.sum() < 15 or len(np.unique(y[m])) < 2:
        return None
    try:
        from sklearn.metrics import roc_auc_score
    except ImportError:
        return None
    xv = x.to_numpy()[m]
    auc = roc_auc_score(y[m], xv)
    return round(float(max(auc, 1 - auc)), 3)  # |AUC-0.5| : pouvoir de séparation, direction ignorée


def run_v_adverse_discriminator() -> dict[str, Any]:
    if not EPISODES.exists():
        return {"version": "ADVERSE-DISCRIMINATOR", "verdict": "NO_EPISODES"}
    ep = pd.read_parquet(EPISODES)
    if "adverse" not in ep.columns or len(ep) < 20:
        return {"version": "ADVERSE-DISCRIMINATOR", "verdict": "INSUFFICIENT", "n": int(len(ep))}
    y = pd.to_numeric(ep["adverse"], errors="coerce").to_numpy()
    feats = _encode(ep)
    seps = {c: _univariate_auc(feats[c], y) for c in feats.columns}
    seps = {k: v for k, v in seps.items() if v is not None}
    ranked = dict(sorted(seps.items(), key=lambda kv: kv[1], reverse=True))
    best = next(iter(ranked.items())) if ranked else (None, None)
    n_adverse = int(np.nansum(y))

    out = {
        "version": "ADVERSE-DISCRIMINATOR",
        "verdict": "WATCHLIST_SMALL_N",
        "n_episodes": int(len(ep)),
        "n_adverse": n_adverse,
        "univariate_separation_auc": ranked,
        "best_early_separator": {"feature": best[0], "auc": best[1]},
        "interpretation": (
            f"{len(ep)} épisodes ({n_adverse} ADVERSE). Pouvoir de séparation univarié (|AUC-0.5|+0.5) des "
            f"features connues À L'ENTRÉE : {ranked}. Meilleur séparateur précoce : {best[0]} ({best[1]}). "
            "Outcomes (mfe/mae/durée) EXCLUS (leakage). n=42 -> DESCRIPTIF/WATCHLIST, pas un filtre dur ; "
            "cohérent V38 (ADVERSE_RISK règle-basé) et V64 (empiler dilue). Le vrai filtre opérationnel se "
            "construira en FORWARD (V124 santé post-entrée)."),
        "note": "Aucun fit multivarié sur 42 trades. Séparateurs un par un. Contexte, jamais un veto.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V_DIR / "adverse_discriminator.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
