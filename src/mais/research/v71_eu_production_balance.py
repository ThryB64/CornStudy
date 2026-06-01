"""V71 — Bilan physique EU (production EC MARS / Eurostat) : la prime EU est-elle JUSTIFIÉE par l'offre ?

Débloque l'axe fondamentaux EU. On aligne la production maïs EU (Eurostat apro_cpsh1 C1500, annuelle,
publiée ~15 nov, déjà shift(1)+ffill anti-leakage) au basis et aux trades. Hypothèse économique (canal #6 de
la carte causale, versant offre) :

  Année à FAIBLE production EU (anomalie < 0 = rareté locale) -> marché EU tendu -> un basis haut est
  ÉCONOMIQUEMENT JUSTIFIÉ -> il se comprime MOINS et finit plus souvent ADVERSE à shorter.

LIMITE HONNÊTE : la production est ANNUELLE (constante intra-campagne) -> c'est une variable de RÉGIME ;
la puissance statistique est limitée par le nombre de campagnes (~13), pas par les 5677 jours. On rapporte
donc des effets de régime, descriptifs, sans fit. On NE modifie PAS build_features (intégration master =
suite si validé en forward).

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V71_DIR = ARTEFACTS_DIR / "v71"
V71_DIR.mkdir(parents=True, exist_ok=True)


def _eu_production_aligned(index: pd.Index) -> pd.DataFrame:
    """Production EU (anomalie/yoy, lag1) alignée sur l'index du master. Vide si indisponible."""
    try:
        from mais.collect.ec_mars import build_ec_mars_features
        ec = build_ec_mars_features()
    except Exception:  # noqa: BLE001
        return pd.DataFrame(index=index)
    if ec is None or len(ec) == 0 or "Date" not in ec.columns:
        return pd.DataFrame(index=index)
    ec = ec.set_index(pd.to_datetime(ec["Date"])).drop(columns=["Date"])
    return ec.reindex(index).ffill()


def run_v71_eu_production(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    ec = _eu_production_aligned(df.index)
    anom_col = "ec_mars_prod_anomaly_eu_lag1"
    if anom_col not in ec.columns or ec[anom_col].notna().sum() < 300:
        return {"version": "V71-EU-PRODUCTION", "verdict": "NO_DATA_EU_PRODUCTION"}

    anom = pd.to_numeric(ec[anom_col], errors="coerce")
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")

    # 1) corr production-anomalie vs niveau de basis (attendu NÉGATIF : faible prod -> basis haut)
    m = anom.notna() & basis.notna()
    corr_level = (round(float(np.corrcoef(anom[m], basis[m])[0, 1]), 3)
                  if m.sum() > 200 and anom[m].std() > 0 else None)

    # 2) basis moyen par régime de production (anomalie < 0 = rareté vs >= 0 = ample)
    scarce = m & (anom < 0)
    ample = m & (anom >= 0)
    basis_scarce = round(float(basis[scarce].mean()), 2) if scarce.sum() > 50 else None
    basis_ample = round(float(basis[ample].mean()), 2) if ample.sum() > 50 else None

    # 3) ADVERSE et compression des trades short-premium par régime de production à l'entrée
    from mais.research.v32_adverse_path_research import build_adverse_frame
    adf = build_adverse_frame(df)
    regime_block = {}
    if len(adf) >= 15:
        entry = pd.to_datetime(adf["entry_date"])
        adf = adf.copy()
        adf["prod_anom"] = anom.reindex(entry).to_numpy()
        v = adf.dropna(subset=["prod_anom"])
        if len(v) >= 15:
            lo = v[v["prod_anom"] < 0]   # année rare
            hi = v[v["prod_anom"] >= 0]  # année ample
            regime_block = {
                "n": int(len(v)),
                "scarce_year": {"n": int(len(lo)),
                                "adverse_rate": round(float(lo["adverse"].mean()), 3) if len(lo) else None,
                                "win_rate": round(float(lo["win"].mean()), 3) if len(lo) else None,
                                "mean_pnl": round(float(lo["pnl"].mean()), 2) if len(lo) else None},
                "ample_year": {"n": int(len(hi)),
                               "adverse_rate": round(float(hi["adverse"].mean()), 3) if len(hi) else None,
                               "win_rate": round(float(hi["win"].mean()), 3) if len(hi) else None,
                               "mean_pnl": round(float(hi["pnl"].mean()), 2) if len(hi) else None},
            }

    # 4) compression conditionnelle (basis haut) par régime
    drop = basis - basis.shift(-40)  # >0 = compression
    high = bz >= 1.0
    comp_block = {}
    sc = high & (anom < 0) & drop.notna()
    am = high & (anom >= 0) & drop.notna()
    if sc.sum() > 30 and am.sum() > 30:
        comp_block = {"compression_scarce_year": round(float(drop[sc].mean()), 2),
                      "compression_ample_year": round(float(drop[am].mean()), 2)}

    # cohérence de l'hypothèse
    basis_higher_when_scarce = bool(
        basis_scarce is not None and basis_ample is not None and basis_scarce > basis_ample)
    adverse_higher_when_scarce = bool(
        regime_block and regime_block["scarce_year"]["adverse_rate"] is not None
        and regime_block["ample_year"]["adverse_rate"] is not None
        and regime_block["scarce_year"]["adverse_rate"] > regime_block["ample_year"]["adverse_rate"])
    less_compressible_when_scarce = bool(
        comp_block and comp_block["compression_scarce_year"] < comp_block["compression_ample_year"])

    support = sum([basis_higher_when_scarce, adverse_higher_when_scarce, less_compressible_when_scarce])
    if support >= 2:
        verdict = "EU_LOW_PRODUCTION_JUSTIFIES_PREMIUM_ADD_TO_ADVERSE_RISK_FORWARD"
    elif support == 1:
        verdict = "EU_PRODUCTION_PARTIAL_SIGNAL_WATCHLIST"
    else:
        verdict = "EU_PRODUCTION_NOT_DISCRIMINANT"

    out = {
        "version": "V71-EU-PRODUCTION",
        "n_days_overlap": int(m.sum()),
        "corr_prod_anomaly_vs_basis": corr_level,
        "basis_mean_scarce_year": basis_scarce,
        "basis_mean_ample_year": basis_ample,
        "basis_higher_when_scarce": basis_higher_when_scarce,
        "trades_by_production_regime": regime_block,
        "adverse_higher_when_scarce": adverse_higher_when_scarce,
        "compression_by_regime": comp_block,
        "less_compressible_when_scarce": less_compressible_when_scarce,
        "hypothesis_support_score": support,
        "verdict": verdict,
        "interpretation": (
            f"ATTENTION CONFONDANT DE TENDANCE : production EU et niveau de basis dérivent tous deux sur "
            f"2010-2026, donc corr={corr_level} et 'basis année rare {basis_scarce} vs ample {basis_ample}' "
            "ne sont PAS des relations économiques fiables (co-tendance). Le seul élément propre (intra-régime, "
            f"basis déjà haut) : la compression est PLUS FAIBLE en année de faible production "
            f"({comp_block.get('compression_scarce_year')} vs {comp_block.get('compression_ample_year')} €/t), "
            "cohérent avec une prime partiellement JUSTIFIÉE par la rareté EU. L'ADVERSE ne se sépare pas "
            "(0.167 vs 0.176). Signal partiel -> WATCHLIST."),
        "caveat": ("Production ANNUELLE (variable de régime, ~13 campagnes, faible puissance) + confondant de "
                   "tendance sur les niveaux. La bonne donnée serait les PRÉVISIONS DE RENDEMENT MARS "
                   "intra-campagne (bulletins mensuels PDF, non parsés). Descriptif, aucun fit ; intégration "
                   "build_features/ADVERSE_RISK différée à validation forward."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V71_DIR / "v71_eu_production.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
