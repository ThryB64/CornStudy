"""V80 — Spreads inter-commodités : corn/soy, crude/corn (éthanol), gas, corn/wheat → CBOT, basis, ADVERSE.

Axe J. On teste si les relations inter-commodités portent un signal sur (a) la DIRECTION du CBOT (moteur de
compression, global) ou (b) le BASIS (prime EU, local) ou (c) l'ADVERSE des short-premium. Hypothèses :
- corn/soy : ratio bas (maïs cheap vs soja) -> arbitrage de surface/demande -> potentiel haussier maïs ;
- crude/corn (proxy marge éthanol) : crude haut -> demande éthanol -> haussier maïs ;
- corn/wheat : substitution feed (déjà V36 côté EU) ;
- gas : coût énergie/intrants.

Tout en variations causales (rendements), z-scores expandants, OOF honnête (embargo). On s'attend, par
cohérence avec l'étude, à ce que l'effet (s'il existe) passe par le CBOT mondial, pas par le basis local.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V80_DIR = ARTEFACTS_DIR / "v80"
V80_DIR.mkdir(parents=True, exist_ok=True)


def intercommodity_features(df: pd.DataFrame) -> pd.DataFrame:
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    soy = pd.to_numeric(df.get("soy_close"), errors="coerce")
    crude = pd.to_numeric(df.get("oil_close"), errors="coerce")
    gas = pd.to_numeric(df.get("gas_close"), errors="coerce")
    wheat = pd.to_numeric(df.get("wheat_close"), errors="coerce")

    def _z(s):
        return (s - s.expanding(min_periods=120).mean()) / s.expanding(min_periods=120).std()

    f = pd.DataFrame(index=df.index)
    f["corn_soy_ratio_z"] = _z(corn / soy)
    f["crude_corn_ratio_z"] = _z(crude / corn)   # proxy marge éthanol (crude relatif au maïs)
    f["gas_z"] = _z(gas)
    f["corn_wheat_ratio_z"] = _z(corn / wheat)
    return f.shift(1)  # anti-leakage


def _corr_fwd(x: pd.Series, fwd: pd.Series) -> float | None:
    m = x.notna() & fwd.notna()
    if m.sum() < 300 or x[m].std() == 0 or fwd[m].std() == 0:
        return None
    return round(float(np.corrcoef(x[m], fwd[m])[0, 1]), 3)


def run_v80_intercommodity(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    f = intercommodity_features(df)
    if f.notna().any(axis=1).sum() < 500:
        return {"version": "V80-INTERCOMMODITY", "verdict": "NO_DATA"}
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")

    # rendements forward CBOT 20j et variation de basis 40j
    cbot_fwd = corn.shift(-20) / corn - 1.0
    basis_chg = basis.shift(-40) - basis

    cbot_corr = {c: _corr_fwd(f[c], cbot_fwd) for c in f.columns}
    basis_corr = {c: _corr_fwd(f[c], basis_chg) for c in f.columns}

    # ADVERSE des short-premium par spread à l'entrée (corn/soy bas = maïs cheap -> CBOT plus porteur ?)
    adverse_block = {}
    try:
        from mais.research.v32_adverse_path_research import build_adverse_frame
        adf = build_adverse_frame(df)
        if len(adf) >= 15:
            entry = pd.to_datetime(adf["entry_date"])
            adf = adf.copy()
            adf["corn_soy_z"] = f["corn_soy_ratio_z"].reindex(entry).to_numpy()
            v = adf.dropna(subset=["corn_soy_z"])
            if len(v) >= 15:
                med = v["corn_soy_z"].median()
                lo = v[v["corn_soy_z"] < med]   # maïs relativement cheap
                hi = v[v["corn_soy_z"] >= med]
                adverse_block = {
                    "n": int(len(v)),
                    "adverse_low_corn_soy": round(float(lo["adverse"].mean()), 3) if len(lo) else None,
                    "adverse_high_corn_soy": round(float(hi["adverse"].mean()), 3) if len(hi) else None,
                }
    except Exception:  # noqa: BLE001
        pass

    # quel spread est le plus lié au CBOT ? (magnitude)
    ranked_cbot = dict(sorted(
        ((k, v) for k, v in cbot_corr.items() if v is not None), key=lambda kv: -abs(kv[1])))
    top_cbot = next(iter(ranked_cbot), None)
    best_cbot_abs = abs(ranked_cbot[top_cbot]) if top_cbot else 0.0
    max_basis_abs = max((abs(v) for v in basis_corr.values() if v is not None), default=0.0)

    cbot_channel = bool(best_cbot_abs >= 0.08 and best_cbot_abs >= max_basis_abs)
    if best_cbot_abs >= 0.08:
        verdict = ("INTERCOMMODITY_LINKS_CBOT_NOT_BASIS" if cbot_channel
                   else "INTERCOMMODITY_WEAK_MIXED")
    else:
        verdict = "INTERCOMMODITY_NO_ROBUST_LINK"

    out = {
        "version": "V80-INTERCOMMODITY",
        "corr_vs_cbot_fwd20": cbot_corr,
        "corr_vs_basis_chg40": basis_corr,
        "top_cbot_feature": top_cbot,
        "adverse_by_corn_soy": adverse_block,
        "channel_is_cbot_not_basis": cbot_channel,
        "verdict": verdict,
        "interpretation": (
            f"Spread le plus lié au CBOT forward : {top_cbot} (|corr| {round(best_cbot_abs, 3)}). "
            f"Lien max au basis {round(max_basis_abs, 3)}. Conforme à l'étude si l'effet inter-commodités "
            "passe par le CBOT mondial (offre/demande globale, éthanol, surface) et NON par la prime EU "
            "locale. Signaux faibles attendus (déjà price-in) ; au mieux un CONTEXTE pour CBOT_SUPPORT."),
        "caveat": "Variations causales + z expandants ; corrélations faibles probables (marché efficient). "
                  "Descriptif, aucun fit, jamais un veto.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V80_DIR / "v80_intercommodity.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
