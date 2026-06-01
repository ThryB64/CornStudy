"""V108 — Reconstruction de la série basis LIVE 2026 + ADVERSE_RISK live (débloque un diagnostic en retard).

Le contexte live (V107) a rafraîchi CBOT_SUPPORT + COT. Restent en retard ADVERSE_RISK et PHYSICAL_TENSION.
Ici on débloque ADVERSE_RISK en reconstruisant la jambe CBOT du basis en EUR/t à partir de ZC=F + EUR/USD
(conversion officielle `cents/100/eurusd*39.3679`), VALIDÉE contre le journal officiel (qui contient déjà
cbot_eur_t), puis en calculant ADVERSE_RISK live :
  - prime modérée : basis_z (officiel) dans [1,1.5) ?            (V32)
  - substitution haute : ratio blé/maïs z (frais) > 0.5 ?        (V36)
  - résidu bas : basis_z plus haut que ce que la substitution explique ? (régression basis_z~wc_z ajustée
    sur le master, appliquée au point live)                      (V37)

PHYSICAL_TENSION reste en retard (courbe EMA officielle = forward). Réseau requis ; SKIP propre hors ligne.
Statut : RESEARCH_ONLY_NOT_TRADING. Holdout verrouillé. Baseline figée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V108_DIR = ARTEFACTS_DIR / "v108"
V108_DIR.mkdir(parents=True, exist_ok=True)
OFFICIAL_JOURNAL = ROOT / "data" / "forward_journal" / "official_forward_journal.parquet"
BUSHEL_TO_TONNE = 39.3679


def reconstruct_cbot_eur_t(zc_cents: pd.Series, eurusd: pd.Series) -> pd.Series:
    """CBOT maïs cents/boisseau -> EUR/tonne : cents/100/eurusd*39.3679 (conversion projet)."""
    return (zc_cents / 100.0) / eurusd * BUSHEL_TO_TONNE


def _substitution_fit_from_master() -> dict[str, float] | None:
    """Régression basis_z ~ wheat/corn z sur le master (coeffs + écart-type des résidus) pour l'appliquer live."""
    try:
        from mais.research.v38_adverse_risk import _wheat_corn_ratio_z
        from mais.scripts.run_v8_phase_a import filter_out_holdout, load_master_dataset
        df = filter_out_holdout(load_master_dataset())
        bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
        wcz = _wheat_corn_ratio_z(df)
        m = bz.notna() & wcz.notna()
        if m.sum() < 200:
            return None
        x = wcz[m].to_numpy()
        y = bz[m].to_numpy()
        a, b = np.polyfit(x, y, 1)  # bz ≈ a*wcz + b
        resid = y - (a * x + b)
        return {"slope": float(a), "intercept": float(b), "resid_std": float(np.std(resid))}
    except Exception:  # noqa: BLE001
        return None


def run_v108_live_basis(try_network: bool = True) -> dict[str, Any]:
    if not OFFICIAL_JOURNAL.exists():
        return {"version": "V108-LIVE-BASIS", "verdict": "NO_OFFICIAL_JOURNAL"}
    j = pd.read_parquet(OFFICIAL_JOURNAL).sort_values("price_date")
    last = j.iloc[-1]
    signal_date = pd.Timestamp(last["price_date"])
    basis_z = float(last["basis_z_used"]) if pd.notna(last.get("basis_z_used")) else None
    basis_official = float(last["basis_official_eur_t"]) if pd.notna(last.get("basis_official_eur_t")) else None

    from mais.research.v107_live_context_refresh import _yahoo_daily, fetch_live_market
    market = fetch_live_market(try_network=try_network)
    if len(market) == 0 or not try_network:
        return {"version": "V108-LIVE-BASIS", "verdict": "NO_MARKET_DATA_OFFLINE"}
    try:
        eurusd = _yahoo_daily("EURUSD=X", rng="5y")
    except Exception:  # noqa: BLE001
        return {"version": "V108-LIVE-BASIS", "verdict": "NO_EURUSD"}

    zc = pd.to_numeric(market.get("corn_close"), errors="coerce")  # ZC=F cents/boisseau
    zw = pd.to_numeric(market.get("wheat_close"), errors="coerce")
    cbot_eur_t = reconstruct_cbot_eur_t(zc, eurusd.reindex(zc.index).ffill())

    # validation vs journal officiel (cbot_eur_t connu)
    val = []
    for _, r in j.iterrows():
        d = pd.Timestamp(r["price_date"])
        if d in cbot_eur_t.index and pd.notna(r.get("cbot_eur_t")):
            recon = float(cbot_eur_t.loc[d])
            official = float(r["cbot_eur_t"])
            val.append({"date": str(d.date()), "reconstructed": round(recon, 2),
                        "official_journal": round(official, 2), "abs_err": round(abs(recon - official), 2)})
    mean_abs_err = round(float(np.mean([v["abs_err"] for v in val])), 2) if val else None
    recon_ok = bool(mean_abs_err is not None and mean_abs_err < 3.0)

    # wheat/corn z live (ratio blé/maïs = ZW/ZC, z expandant) sur la série fraîche
    wc = (zw / zc)
    wc_z_series = (wc - wc.expanding(min_periods=120).mean()) / wc.expanding(min_periods=120).std()
    wc_z = float(wc_z_series.iloc[-1]) if wc_z_series.notna().any() else None

    # ADVERSE_RISK live
    fit = _substitution_fit_from_master()
    resid_z = None
    if fit and wc_z is not None and basis_z is not None and fit["resid_std"] > 0:
        pred = fit["slope"] * wc_z + fit["intercept"]
        resid_z = float((basis_z - pred) / fit["resid_std"])

    components = {}
    score = 0
    if basis_z is not None:
        c_mod = int(1.0 <= basis_z < 1.5)
        components["moderate_premium_z_in_1_1p5"] = c_mod
        score += c_mod
    if resid_z is not None:
        c_lowres = int(resid_z < 0)
        components["low_residual_subst_justified"] = c_lowres
        score += c_lowres
    if wc_z is not None:
        c_hisub = int(wc_z > 0.5)
        components["high_substitution_wc_z_gt_0p5"] = c_hisub
        score += c_hisub
    n_comp = len(components)
    tier = "NO_SIGNAL"
    if basis_z is not None and basis_z >= 1.0 and n_comp >= 1:
        tier = "LOW" if score == 0 else ("MEDIUM" if score == 1 else "HIGH")

    out = {
        "version": "V108-LIVE-BASIS",
        "signal_date": str(signal_date.date()),
        "basis_z_official": basis_z,
        "basis_official_eur_t": basis_official,
        "cbot_eur_t_reconstructed_last": round(float(cbot_eur_t.dropna().iloc[-1]), 2),
        "cbot_eur_t_validation": val,
        "reconstruction_mean_abs_err_eur_t": mean_abs_err,
        "reconstruction_ok": recon_ok,
        "wheat_corn_z_live": round(wc_z, 3) if wc_z is not None else None,
        "substitution_residual_z_live": round(resid_z, 3) if resid_z is not None else None,
        "adverse_risk_live": tier,
        "adverse_risk_components": components,
        "verdict": "ADVERSE_RISK_LIVE_UNBLOCKED" if (recon_ok and tier != "NO_SIGNAL")
                   else "PARTIAL_OR_RECON_WEAK",
        "interpretation": (
            f"CBOT_eur_t reconstruit (ZC=F+EUR/USD, conversion *{BUSHEL_TO_TONNE}) validé contre le journal "
            f"officiel : erreur moyenne {mean_abs_err} €/t (ok={recon_ok}). ADVERSE_RISK live = **{tier}** "
            f"(prime modérée={components.get('moderate_premium_z_in_1_1p5')}, "
            f"résidu bas={components.get('low_residual_subst_justified')}, "
            f"substitution haute={components.get('high_substitution_wc_z_gt_0p5')}). Le basis_z officiel "
            f"({basis_z}) étant EXTRÊME (>1.5), la prime n'est pas 'modérée' -> composant V32 inactif. "
            "Débloque ADVERSE_RISK live ; PHYSICAL_TENSION reste en attente de la courbe EMA officielle."),
        "note": "Résidu substitution = régression basis_z~wc_z ajustée sur le master, appliquée au point live "
                "(z-scores, scale-consistant). CONTEXTE, jamais un veto.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V108_DIR / "v108_live_basis.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def live_basis_report_block() -> str:
    artefact = V108_DIR / "v108_live_basis.json"
    if not artefact.exists():
        return ""
    try:
        s = json.loads(artefact.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    if s.get("version") != "V108-LIVE-BASIS" or s.get("adverse_risk_live") in (None, "NO_SIGNAL"):
        return ""
    return (
        "### Basis reconstruit + ADVERSE_RISK live (V108)\n"
        f"- CBOT_eur_t reconstruit {s.get('cbot_eur_t_reconstructed_last')} €/t "
        f"(validation vs officiel : erreur moy {s.get('reconstruction_mean_abs_err_eur_t')} €/t, "
        f"ok={s.get('reconstruction_ok')})\n"
        f"- basis officiel {s.get('basis_official_eur_t')} €/t (z={s.get('basis_z_official')}) · "
        f"wheat/corn z live {s.get('wheat_corn_z_live')} · résidu subst. z {s.get('substitution_residual_z_live')}\n"
        f"- **ADVERSE_RISK live = {s.get('adverse_risk_live')}** {s.get('adverse_risk_components')}\n"
        "- PHYSICAL_TENSION live fourni par V109 (courbe officielle). RESEARCH_ONLY_NOT_TRADING.\n"
    )
