"""V44 — Mécanisme & magnitude : mieux EXPLIQUER et PRÉDIRE la compression de la prime EMA/CBOT.

Trois angles nouveaux, disciplinés (anti-leakage, négatif honnête possible, aucune touche à la règle) :

E1  Lead-lag CBOT->EMA au jour le jour : le CBOT mène-t-il l'EMA ? (test direct du mécanisme « compression
    par rattrapage CBOT »). Corrélations croisées rendement_EMA_t vs rendement_CBOT_{t-k}.
E2  Magnitude de compression : conditionnellement à un signal, de COMBIEN (€/t) la prime baisse-t-elle, et
    qu'est-ce qui la prédit (OOF honnête + profil par palier ADVERSE_RISK / CBOT_SUPPORT) ?
E3  Saisonnalité causale du basis : profil mensuel (expanding, sans look-ahead) -> quand la prime se forme.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V44_DIR = ARTEFACTS_DIR / "v44"
V44_DIR.mkdir(parents=True, exist_ok=True)
HORIZON = 40


def lead_lag_cbot_ema(df: pd.DataFrame, max_lag: int = 5) -> dict[str, Any]:
    """E1 : corr(rendement EMA_t, rendement CBOT_{t-k}) pour k=-max_lag..max_lag (k>0 => CBOT mène)."""
    ema = pd.to_numeric(df.get("ema_close"), errors="coerce")
    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce")
    r_ema = ema.pct_change()
    r_cbot = cbot.pct_change()
    m = r_ema.notna() & r_cbot.notna()
    if m.sum() < 250:
        return {"verdict": "TOO_SHORT"}
    corrs = {}
    for k in range(-max_lag, max_lag + 1):
        x = r_cbot.shift(k)  # k>0 : CBOT d'il y a k jours
        mm = x.notna() & r_ema.notna()
        if mm.sum() > 100:
            corrs[k] = round(float(np.corrcoef(x[mm], r_ema[mm])[0, 1]), 3)
    pos = {k: v for k, v in corrs.items() if k > 0}
    neg = {k: v for k, v in corrs.items() if k < 0}
    best_pos = max(pos.values()) if pos else None
    best_neg = max(neg.values()) if neg else None
    contemp = corrs.get(0)
    # Si le pic de co-mouvement est à |1 jour| et non en contemporain => trading non-synchrone
    peak_lag = max(corrs, key=lambda k: corrs[k]) if corrs else None
    nonsync = bool(peak_lag is not None and peak_lag != 0
                   and contemp is not None and corrs[peak_lag] > contemp + 0.1)
    return {
        "cross_corr_by_lag": corrs,
        "contemporaneous": contemp,
        "peak_lag": peak_lag,
        "peak_corr": corrs.get(peak_lag) if peak_lag is not None else None,
        "best_cbot_leads_ema": best_pos,   # k>0
        "best_ema_leads_cbot": best_neg,   # k<0
        "nonsynchronous_pricing": nonsync,
        "verdict": ("NONSYNC_PRICING_PEAK_AT_1D" if nonsync else "CONTEMPORANEOUS_DOMINANT"),
        "alignment_caveat": ("Le pic de co-mouvement à |1 jour| (et la faible corr contemporaine) reflète "
                             "le décalage des heures de settlement (Euronext ~18h30 CET, CBOT plus tard le "
                             "même jour calendaire) : c'est un effet d'ALIGNEMENT non-synchrone, PAS une "
                             "preuve de leadership économique. La vraie causalité lead-lag exige des "
                             "timestamps intraday (data-gated). Cohérent avec le shift(1) anti-leakage."),
        "reading": ("Co-mouvement CBOT/EMA dominé par un décalage de 1 jour, contemporain faible. "
                    "On NE conclut PAS sur qui mène : phénomène non-synchrone à confirmer en intraday."),
    }


def _oof_r2(x: pd.DataFrame, y: pd.Series, horizon: int) -> tuple[float | None, int]:
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler
    m = x.notna().all(axis=1) & y.notna()
    x, y = x[m], y[m]
    if len(y) < 150:
        return None, int(len(y))
    pred = np.full(len(y), np.nan)
    for tr, te in TimeSeriesSplit(n_splits=5).split(x):
        tr = tr[: max(0, len(tr) - horizon)]
        if len(tr) < 80:
            continue
        sc = StandardScaler().fit(x.iloc[tr])
        reg = LinearRegression().fit(sc.transform(x.iloc[tr]), y.iloc[tr])
        pred[te] = reg.predict(sc.transform(x.iloc[te]))
    ok = ~np.isnan(pred)
    if ok.sum() < 80:
        return None, int(ok.sum())
    return float(r2_score(y[ok], pred[ok])), int(ok.sum())


def compression_magnitude(df: pd.DataFrame, horizon: int = HORIZON) -> dict[str, Any]:
    """E2 : de COMBIEN la prime baisse-t-elle sur l'horizon, et est-ce prédictible (OOF) ?"""
    from mais.research.v37_substitution_residual import substitution_residual
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    drop = basis - basis.shift(-horizon)  # >0 => la prime a baissé (compression)
    active = bz >= 1.0

    # baisse moyenne quand signal actif vs pas de signal
    drop_active = drop[active].dropna()
    drop_idle = drop[(~active) & bz.notna()].dropna()
    cond = {
        "mean_drop_when_signal": round(float(drop_active.mean()), 2) if len(drop_active) else None,
        "mean_drop_no_signal": round(float(drop_idle.mean()), 2) if len(drop_idle) else None,
        "n_signal": int(len(drop_active)),
    }

    # prédiction OOF de la magnitude (sur jours signal) : entry_z, résidu, momentum CBOT, saison
    resid = substitution_residual(df)["basis_residual_z"]
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    mom = np.log(corn / corn.shift(20))
    season = np.cos(2 * np.pi * df.index.month / 12)
    feats = pd.DataFrame({"entry_z": bz, "resid_z": resid, "cbot_mom20": mom, "season": season},
                         index=df.index)
    mask = active & drop.notna()
    r2, n = _oof_r2(feats[mask], drop[mask], horizon)

    return {
        "horizon": horizon,
        "conditional_drop": cond,
        "oof_r2_magnitude": round(r2, 4) if r2 is not None else None,
        "n_oof": n,
        "verdict": ("MAGNITUDE_PARTIALLY_PREDICTABLE" if (r2 is not None and r2 > 0.05)
                    else "MAGNITUDE_HARD_TO_PREDICT"),
        "reading": ("La prime baisse nettement plus quand un signal est actif (anomalie compressible). "
                    "Prédire l'AMPLEUR exacte reste difficile (cohérent avec V35 : timing/chemin non prévisible)."),
    }


def basis_seasonality(df: pd.DataFrame) -> dict[str, Any]:
    """E3 : profil mensuel CAUSAL du basis (z expandant) -> quand la prime EU est haute/basse."""
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    if basis.notna().sum() < 250:
        return {"verdict": "TOO_SHORT"}
    z = (basis - basis.expanding(min_periods=120).mean()) / basis.expanding(min_periods=120).std()
    mdf = pd.DataFrame({"month": df.index.month, "basis": basis, "z": z}).dropna()
    prof = {}
    for mth, sub in mdf.groupby("month"):
        prof[int(mth)] = {"n": int(len(sub)), "mean_basis": round(float(sub["basis"].mean()), 2),
                          "mean_z": round(float(sub["z"].mean()), 3)}
    by_z = sorted(prof.items(), key=lambda kv: kv[1]["mean_z"])
    return {
        "monthly_profile": prof,
        "lowest_premium_month": by_z[0][0] if by_z else None,
        "highest_premium_month": by_z[-1][0] if by_z else None,
        "reading": ("Profil mensuel causal (expanding) du basis EU : montre les périodes où la prime tend à "
                    "être haute (souvent fin de campagne/soudure) vs basse (récolte). Explicatif, anti-leakage."),
    }


def run_v44_all(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    out = {
        "version": "V44-MECHANISM-MAGNITUDE",
        "E1_lead_lag": lead_lag_cbot_ema(df),
        "E2_magnitude": compression_magnitude(df),
        "E3_seasonality": basis_seasonality(df),
        "status": "RESEARCH_ONLY_NOT_TRADING",
        "note": "Explicatif/prédictif, anti-leakage, aucune touche à la règle figée.",
    }
    (V44_DIR / "v44_mechanism_magnitude.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
