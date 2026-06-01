"""V71b — Localité géographique de la prime EU : France vs UE totale comme driver du basis.

V71 a montré que la production EU ANNUELLE en NIVEAU est confondue par la tendance. Ici on (1) détrende en
travaillant sur les VARIATIONS annuelles (YoY) production vs variation annuelle du basis, et (2) on teste une
hypothèse de LOCALITÉ : le contrat EMA est livré en France -> une baisse de production FRANÇAISE devrait
peser plus sur le basis qu'une baisse de production UE totale. Si corr(ΔprodFR, Δbasis) est plus négative que
corr(ΔprodEU, Δbasis), la prime est encore plus LOCALE qu'on ne pensait (renforce V16/V36/V60).

LIMITE HONNÊTE : annuel -> ~13 campagnes, très faible puissance. Comparaison RELATIVE (FR vs UE) seulement,
descriptive, aucun fit. Pas d'intégration build_features.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V71B_DIR = ARTEFACTS_DIR / "v71b"
V71B_DIR.mkdir(parents=True, exist_ok=True)


def _annual_production() -> pd.DataFrame:
    """Table annuelle {year, eu_kt, fr_kt, fr_ro_hu_kt} depuis ec_mars + franceagrimer. Vide si indispo."""
    try:
        from mais.collect.ec_mars import build_ec_mars_features
        from mais.collect.franceagrimer import build_franceagrimer_features
        ec = build_ec_mars_features()
        fa = build_franceagrimer_features()
    except Exception:  # noqa: BLE001
        return pd.DataFrame()
    if ec is None or fa is None or len(ec) == 0 or len(fa) == 0:
        return pd.DataFrame()

    def _yearly(frame, col):
        if col not in frame.columns:
            return pd.Series(dtype=float)
        s = frame.set_index(pd.to_datetime(frame["Date"]))[col]
        return s.groupby(s.index.year).last()

    eu = _yearly(ec, "ec_mars_production_eu_kt_lag1")
    fr = _yearly(fa, "fr_mais_production_kt_lag1")
    frh = _yearly(fa, "fr_ro_hu_mais_total_kt_lag1")
    out = pd.DataFrame({"eu_kt": eu, "fr_kt": fr, "fr_ro_hu_kt": frh}).dropna(how="all")
    return out


def run_v71b_locality(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    prod = _annual_production()
    if len(prod) < 6:
        return {"version": "V71B-EU-LOCALITY", "verdict": "NO_DATA_EU_PRODUCTION"}

    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    basis_year = basis.groupby(basis.index.year).mean()  # basis moyen par année civile

    # variations annuelles (détrendées)
    tab = prod.copy()
    for c in ("eu_kt", "fr_kt", "fr_ro_hu_kt"):
        tab[f"{c}_yoy"] = tab[c].pct_change() * 100
    tab["basis_year"] = basis_year.reindex(tab.index)
    tab["basis_chg"] = tab["basis_year"].diff()

    corrs = {}
    for c in ("eu_kt", "fr_kt", "fr_ro_hu_kt"):
        x = tab[f"{c}_yoy"]
        m = x.notna() & tab["basis_chg"].notna()
        if m.sum() >= 6 and x[m].std() > 0 and tab["basis_chg"][m].std() > 0:
            corrs[c] = {"n_years": int(m.sum()),
                        "corr_prod_yoy_vs_basis_change": round(
                            float(np.corrcoef(x[m], tab["basis_chg"][m])[0, 1]), 3)}

    fr_corr = corrs.get("fr_kt", {}).get("corr_prod_yoy_vs_basis_change")
    eu_corr = corrs.get("eu_kt", {}).get("corr_prod_yoy_vs_basis_change")
    # hypothèse locale : baisse prod FR -> basis MONTE -> corr négative, et FR plus négative que EU
    french_more_local = bool(fr_corr is not None and eu_corr is not None and fr_corr < eu_corr)
    french_negative = bool(fr_corr is not None and fr_corr < -0.1)

    if french_negative and french_more_local:
        verdict = "FRENCH_PRODUCTION_MORE_LOCAL_DRIVER_OF_BASIS"
    elif french_negative or (eu_corr is not None and eu_corr < -0.1):
        verdict = "EU_PRODUCTION_CHANGE_WEAK_INVERSE_LINK_WATCHLIST"
    else:
        verdict = "EU_PRODUCTION_CHANGE_NOT_DISCRIMINANT"

    out = {
        "version": "V71B-EU-LOCALITY",
        "n_years": int(tab["basis_chg"].notna().sum()),
        "corr_by_geography": corrs,
        "french_corr": fr_corr,
        "eu_corr": eu_corr,
        "french_more_local_than_eu": french_more_local,
        "verdict": verdict,
        "interpretation": (
            f"corr(ΔprodFR YoY, Δbasis) = {fr_corr} vs corr(ΔprodEU, Δbasis) = {eu_corr} (négatif attendu : "
            "production en baisse -> basis en hausse). Détrendé via variations annuelles. Si la France est plus "
            "négative que l'UE totale, le basis (contrat livré en France) est piloté davantage par l'offre "
            "FRANÇAISE -> prime encore plus LOCALE (renforce V16/V36/V60). Sinon, lien faible/non discriminant."),
        "caveat": "Annuel -> ~13 campagnes, très faible puissance. Comparaison relative descriptive, aucun fit. "
                  "Vraie donnée = MARS yields intra-campagne. Pas d'intégration build_features.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V71B_DIR / "v71b_locality.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
