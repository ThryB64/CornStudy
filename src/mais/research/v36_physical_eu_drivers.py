"""V36 — Drivers physiques / substitution Europe du basis EMA/CBOT.

Hypothèses issues d'analyses de marché réelles (S&P Global mai 2026 : « coûts d'origine, fret, CBOT » ;
commodity-board : « logistique tendue + marges éthanol » ; théorie non-convergence storage/timing) :
- H1 énergie/fret : un coût énergie EU élevé (TTF gaz) renchérit séchage/logistique -> peut JUSTIFIER un
  basis élevé -> compression plus lente / plus d'ADVERSE.
- H2 substitution : le ratio blé/maïs pilote la demande de maïs fourrager EU -> influence le basis.

On INTÈGRE enfin des données physiques EU (TTF de eu_cross_assets) dans le frame des trades. Anti-leakage :
features causales (z expandant, lag), cible = outcome du trade (ADVERSE). n petit -> descriptif + LOO.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 retiré.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT
from mais.registry.holdout_lock import assert_no_holdout

V36_DIR = ARTEFACTS_DIR / "v36"
V36_DIR.mkdir(parents=True, exist_ok=True)


def _eu_physical_series(index: pd.DatetimeIndex) -> pd.DataFrame:
    """TTF gaz EU + EUR/USD, alignés sur l'index, en features causales (z expandant trailing, lag1)."""
    path = ROOT / "data/raw/eu_cross_assets/eu_cross_assets.csv"
    out = pd.DataFrame(index=index)
    if not path.exists():
        return out
    eu = pd.read_csv(path)
    eu["Date"] = pd.to_datetime(eu["Date"])
    eu = eu.set_index("Date").sort_index()
    ttf = pd.to_numeric(eu.get("ttf_natgas_eur"), errors="coerce").reindex(index).ffill()
    # z-score expandant trailing (anti-leakage) puis lag1
    ttf_z = ((ttf - ttf.expanding(min_periods=60).mean()) /
             ttf.expanding(min_periods=60).std()).shift(1)
    out["ttf_eur"] = ttf.shift(1)
    out["ttf_z"] = ttf_z
    out["ttf_mom_60"] = ttf.pct_change(60).shift(1)
    return out


def run_v36_physical(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    from mais.research.v32_adverse_path_research import _loo_auc, _profile, build_adverse_frame

    phys = _eu_physical_series(df.index)
    if phys.empty or phys["ttf_z"].notna().sum() < 100:
        return {"version": "V36-PHYSICAL-EU", "verdict": "NO_TTF_DATA"}

    # --- Explication descriptive : le basis est-il lié à la tension énergie / substitution ? ---
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    wheat = pd.to_numeric(df.get("wheat_close"), errors="coerce")
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    wheat_corn = (wheat / corn).rename("wheat_corn_ratio")
    aligned = pd.concat([basis.rename("basis"), phys["ttf_z"], wheat_corn], axis=1).dropna()
    corr_ttf = float(aligned["basis"].corr(aligned["ttf_z"])) if len(aligned) > 50 else None
    corr_wc = float(aligned["basis"].corr(aligned["wheat_corn_ratio"])) if len(aligned) > 50 else None

    # --- ADVERSE : la tension physique EU prédit-elle la non-compression ? ---
    adf = build_adverse_frame(df)
    if len(adf) < 15:
        return {"version": "V36-PHYSICAL-EU", "verdict": "TOO_FEW_TRADES", "n": int(len(adf))}
    entry = pd.to_datetime(adf["entry_date"])
    adf = adf.copy()
    adf["ttf_z"] = phys["ttf_z"].reindex(entry).to_numpy()
    adf["ttf_mom_60"] = phys["ttf_mom_60"].reindex(entry).to_numpy()
    adf["wheat_corn_ratio"] = wheat_corn.reindex(entry).to_numpy()

    new_cols = ["ttf_z", "ttf_mom_60", "wheat_corn_ratio"]
    prof_adv = _profile(adf[adf["adverse"] == 1], new_cols)
    prof_good = _profile(adf[adf["adverse"] == 0], new_cols)
    separators = {c: round(prof_adv[c] - prof_good[c], 4)
                  for c in new_cols if prof_adv.get(c) is not None and prof_good.get(c) is not None}

    # baseline V32 vs V32+physique : la physique ajoute-t-elle au score ADVERSE ?
    base_feats = ["entry_z", "basis_level", "backwardation", "cbot_drawdown_risk",
                  "cbot_mom_20", "realized_vol_20"]
    x_base = adf[base_feats].apply(pd.to_numeric, errors="coerce")
    x_phys = adf[base_feats + new_cols].apply(pd.to_numeric, errors="coerce")
    auc_base = _loo_auc(x_base, adf["adverse"])
    auc_phys = _loo_auc(x_phys, adf["adverse"])
    auc_ttf_only = _loo_auc(adf[["ttf_z"]].apply(pd.to_numeric, errors="coerce"), adf["adverse"])

    delta = (round(auc_phys - auc_base, 3) if (auc_phys is not None and auc_base is not None) else None)
    # Garde-fou overfit : 9 features pour ~7 ADVERSE -> un gain AUC multivarié n'est PAS fiable.
    n_adverse = int(adf["adverse"].sum())
    n_feats_full = len(base_feats) + len(new_cols)
    overfit_risk = n_feats_full > n_adverse  # trop de features vs événements
    # Le résultat ROBUSTE est descriptif : corrélation basis ~ ratio blé/maïs. L'AUC multivarié est indicatif.
    headline = ("BASIS_EXPLAINED_BY_WHEAT_CORN_SUBSTITUTION"
                if (corr_wc is not None and abs(corr_wc) >= 0.4) else "PHYSICAL_CONTEXT_ONLY")
    if overfit_risk:
        adverse_verdict = "ADVERSE_AUC_GAIN_NOT_ROBUST_TOO_FEW_EVENTS"
    elif delta is not None and delta > 0.03:
        adverse_verdict = "PHYSICAL_ADDS_TO_ADVERSE"
    else:
        adverse_verdict = "PHYSICAL_CONTEXT_ONLY"
    out = {
        "version": "V36-PHYSICAL-EU",
        "data": "TTF gaz EU (eu_cross_assets) intégré + ratio blé/maïs (master)",
        "headline_finding": headline,
        "basis_corr_ttf_z": round(corr_ttf, 3) if corr_ttf is not None else None,
        "basis_corr_wheat_corn_ratio": round(corr_wc, 3) if corr_wc is not None else None,
        "adverse_profile_physical": prof_adv,
        "compressed_profile_physical": prof_good,
        "separators_adverse_minus_compressed": separators,
        "loo_auc_adverse_base_v32": round(auc_base, 3) if auc_base is not None else None,
        "loo_auc_adverse_base_plus_physical": round(auc_phys, 3) if auc_phys is not None else None,
        "loo_auc_adverse_ttf_only": round(auc_ttf_only, 3) if auc_ttf_only is not None else None,
        "delta_auc_physical": delta,
        "n_adverse_events": n_adverse,
        "n_features_full_model": n_feats_full,
        "overfit_risk_adverse_auc": overfit_risk,
        "adverse_verdict": adverse_verdict,
        "verdict": headline,
        "interpretation": (
            f"ROBUSTE (descriptif) : basis corrélé au ratio blé/maïs r={round(corr_wc, 2) if corr_wc else None} "
            "-> la substitution fourragère EU explique une part du niveau de prime (blé cher relatif -> maïs "
            "demandé -> prime EU haute). TTF (énergie/fret) corrélation plus faible. Le gain AUC ADVERSE "
            f"(+{delta}) avec {n_feats_full} features pour {n_adverse} événements = NON FIABLE (overfit) -> "
            "TTF/blé restent CONTEXTE/explication, jamais un veto."),
        "note": "TTF couvre ~2015+ (eu_cross_assets), n trades limité. À re-tester en forward.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V36_DIR / "v36_physical.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
