"""V40 — Substitution blé/maïs approfondie : le basis haut est-il justifié par la substitution fourragère ?

V36/V37/V38 ont établi que le ratio blé/maïs explique le NIVEAU du basis (r≈0.60) et qu'une prime
justifiée par la substitution est ADVERSE-prone. V40 approfondit avec des angles nouveaux :

- spécificité EU : le ratio touche-t-il PLUS le basis (prime EU) que le CBOT lui-même ?
- durée de reversion selon le ratio ;
- interaction avec l'énergie (TTF gaz EU, coût de séchage/logistique) ;
- consolidation ADVERSE + saison.

Limite data honnête : le blé disponible est le blé CBOT (ZW=F), PAS le blé MATIF/Euronext. La vraie
substitution EU se mesurerait avec MATIF blé / MATIF maïs — non collecté (data-gated, à brancher comme EMA).
De même, la météo EU forecast reste data-gated. On le signale, on ne le simule pas.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V40_DIR = ARTEFACTS_DIR / "v40"
V40_DIR.mkdir(parents=True, exist_ok=True)
HORIZON = 40


def _wc_z(df: pd.DataFrame) -> pd.Series:
    wheat = pd.to_numeric(df.get("wheat_close"), errors="coerce")
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    ratio = wheat / corn
    return (ratio - ratio.expanding(min_periods=120).mean()) / ratio.expanding(min_periods=120).std()


def _corr(a: pd.Series, b: pd.Series) -> float | None:
    m = a.notna() & b.notna()
    if m.sum() < 100:
        return None
    return round(float(np.corrcoef(a[m], b[m])[0, 1]), 3)


def eu_specificity(df: pd.DataFrame) -> dict[str, Any]:
    """Le ratio blé/maïs touche-t-il PLUS la prime EU (basis) que le niveau CBOT ?"""
    wc = _wc_z(df)
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce")
    c_basis, c_cbot = _corr(wc, basis), _corr(wc, cbot)
    eu_specific = bool(c_basis is not None and c_cbot is not None and abs(c_basis) > abs(c_cbot) + 0.10)
    return {
        "corr_ratio_basis_EU": c_basis,
        "corr_ratio_cbot": c_cbot,
        "substitution_is_EU_specific": eu_specific,
        "reading": ("Le ratio blé/maïs explique le basis EU plus que le CBOT -> substitution = phénomène "
                    "de prime LOCALE européenne (cohérent V16/V39 stocks US faibles sur le basis)."),
    }


def reversion_by_ratio(df: pd.DataFrame) -> dict[str, Any]:
    """Durée de reversion + ADVERSE selon que le ratio blé/maïs est haut (prime justifiée) ou bas."""
    from mais.research.v17_research_indicator import build_trades_detailed
    from mais.research.v32_adverse_path_research import build_adverse_frame
    det = build_trades_detailed(df)
    adv = build_adverse_frame(df)
    if len(det) < 15 or len(adv) == 0:
        return {"verdict": "TOO_FEW"}
    det = det.merge(adv[["entry_date", "adverse"]], on="entry_date", how="inner")
    wc = _wc_z(df)
    entry = pd.to_datetime(det["entry_date"])
    det = det.copy()
    det["wc_z"] = wc.reindex(entry).to_numpy()
    v = det.dropna(subset=["wc_z"])
    if len(v) < 15:
        return {"verdict": "TOO_FEW"}
    med = v["wc_z"].median()
    hi, lo = v[v["wc_z"] >= med], v[v["wc_z"] < med]
    def blk(s):
        return {"n": int(len(s)), "median_days": round(float(s["duration_days"].median()), 1),
                "reverted_rate": round(float(s["reverted"].mean()), 3),
                "adverse_rate": round(float(s["adverse"].mean()), 3),
                "mean_pnl": round(float(s["pnl_z0_max90_sl20"].mean()), 2)}
    b_hi, b_lo = blk(hi), blk(lo)
    return {
        "high_ratio": b_hi, "low_ratio": b_lo,
        "high_ratio_slower_or_adverse": bool(b_hi["adverse_rate"] > b_lo["adverse_rate"]),
        "reading": ("Ratio haut (prime justifiée par substitution) : reversion plus lente / plus d'ADVERSE. "
                    "Ratio bas (prime inexpliquée) : compression plus propre. Cohérent V37."),
    }


def energy_interaction(df: pd.DataFrame) -> dict[str, Any]:
    """L'énergie (TTF gaz EU si dispo, sinon gaz US) amplifie-t-elle le lien ratio↔basis ?"""
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    wc = _wc_z(df)
    # TTF EU prioritaire (V36), sinon gaz US (proxy)
    gas = None
    src = None
    try:
        from mais.research.v36_physical_eu_drivers import _eu_physical_series
        eu = _eu_physical_series(df.index)
        if eu is not None and "ttf_natgas_eur" in getattr(eu, "columns", []):
            gas, src = pd.to_numeric(eu["ttf_natgas_eur"], errors="coerce"), "TTF_EU"
    except Exception:
        pass
    if gas is None:
        g = df.get("gas_close")
        if g is not None:
            gas, src = pd.to_numeric(g, errors="coerce"), "US_natgas_proxy"
    if gas is None:
        return {"verdict": "NO_ENERGY_DATA"}
    gas_z = (gas - gas.expanding(min_periods=120).mean()) / gas.expanding(min_periods=120).std()
    m = wc.notna() & basis.notna() & gas_z.notna()
    if m.sum() < 200:
        return {"verdict": "TOO_SHORT", "source": src}
    med = gas_z[m].median()
    hi_e = m & (gas_z >= med)
    lo_e = m & (gas_z < med)
    corr_hi = _corr(wc[hi_e], basis[hi_e])
    corr_lo = _corr(wc[lo_e], basis[lo_e])
    amplifies = bool(corr_hi is not None and corr_lo is not None and corr_hi > corr_lo + 0.10)
    return {
        "energy_source": src,
        "corr_ratio_basis_high_energy": corr_hi,
        "corr_ratio_basis_low_energy": corr_lo,
        "energy_amplifies_substitution": amplifies,
        "reading": ("En énergie chère, le lien ratio blé/maïs ↔ basis se renforce-t-il ? (coût de séchage / "
                    "logistique). Descriptif."),
    }


def run_v40_substitution_deep(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    if _wc_z(df).notna().sum() < 200:
        return {"version": "V40-SUBSTITUTION-DEEP", "verdict": "TOO_SHORT"}
    out = {
        "version": "V40-SUBSTITUTION-DEEP",
        "eu_specificity": eu_specificity(df),
        "reversion_by_ratio": reversion_by_ratio(df),
        "energy_interaction": energy_interaction(df),
        "data_gated": {
            "matif_wheat_corn_ratio": "NON disponible : blé = CBOT (ZW=F), pas MATIF/Euronext. "
                                      "À brancher comme la collecte EMA officielle (Euronext milling wheat).",
            "eu_weather_forecast": "Météo EU prévue réelle data-gated (host historical-forecast time out).",
        },
        "status": "RESEARCH_ONLY_NOT_TRADING",
        "note": "Approfondissement substitution avec données dispo (blé CBOT). n petit sur le trade-level.",
    }
    (V40_DIR / "v40_substitution_deep.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
