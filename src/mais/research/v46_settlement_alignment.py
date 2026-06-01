"""V46 — Alignement de settlement CBOT/EMA : le basis quotidien est-il bruité par la non-synchronisation ?

V44 a montré que le co-mouvement CBOT/EMA pique à 1 jour de décalage (corr ~0.42) et non en contemporain
(~0.10) : Euronext settle ~18h30 CET, le CBOT plus tard le même jour calendaire. Le basis = EMA_settl −
CBOT_settl(converti) mélange donc des informations de moments différents -> bruit potentiel.

On teste plusieurs ALIGNEMENTS du CBOT (décalage k jours) et on mesure, pour chaque basis obtenu :
- corrélation de rendement CONTEMPORAINE EMA vs CBOT décalé (k qui maximise = alignement informationnel),
- bruit jour à jour (std de Δbasis) et autocorrélation lag-1 de Δbasis (signature micro-structure / rebond),
- vitesse de réversion (AR(1) -> demi-vie),
- accord du signal basis_z>1 et pouvoir de compression OOF.

Discipline : exploratoire. La règle figée utilise le basis contemporain (k=0). Un ré-alignement ne devient
candidat que s'il AMÉLIORE nettement ET reste sans fuite pour le live (k>=0 ; k<0 = diagnostic only).
Le vrai correctif (CBOT à l'heure exacte du settlement Euronext) exige de l'intraday (data-gated).

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V46_DIR = ARTEFACTS_DIR / "v46"
V46_DIR.mkdir(parents=True, exist_ok=True)


def aligned_basis(df: pd.DataFrame, k: int) -> pd.Series:
    """Basis = EMA_t − CBOT_{t-k} (k>0 = CBOT décalé vers le passé ; k=0 = contemporain baseline)."""
    ema = pd.to_numeric(df.get("ema_close"), errors="coerce")
    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce")
    return ema - cbot.shift(k)


def _ar1_halflife(level: pd.Series) -> float | None:
    s = level.dropna()
    if len(s) < 200:
        return None
    x, y = s.shift(1).dropna(), s.iloc[1:]
    idx = x.index.intersection(y.index)
    x, y = x.loc[idx], y.loc[idx]
    if len(x) < 200 or x.std() == 0:
        return None
    rho = float(np.cov(x, y)[0, 1] / np.var(x))
    if not (0 < rho < 1):
        return None
    return round(float(np.log(0.5) / np.log(rho)), 1)


def _trailing_z(s: pd.Series, window: int = 260, minp: int = 20) -> pd.Series:
    mu = s.rolling(window, min_periods=minp).mean()
    sd = s.rolling(window, min_periods=minp).std()
    return (s - mu) / sd


def _compression_auc(basis: pd.Series, df: pd.DataFrame, horizon: int = 40) -> float | None:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler
    bz = _trailing_z(basis)
    y = ((basis.shift(-horizon) - basis) < 0).astype(float)
    season = np.cos(2 * np.pi * df.index.month / 12)
    x = pd.DataFrame({"bz": bz, "season": season}, index=df.index)
    m = x.notna().all(axis=1) & y.notna()
    x, y = x[m], y[m]
    if len(y) < 200 or y.nunique() < 2:
        return None
    pred = np.full(len(y), np.nan)
    for tr, te in TimeSeriesSplit(n_splits=5).split(x):
        tr = tr[: max(0, len(tr) - horizon)]
        if len(tr) < 100 or y.iloc[tr].nunique() < 2:
            continue
        sc = StandardScaler().fit(x.iloc[tr])
        clf = LogisticRegression(max_iter=400).fit(sc.transform(x.iloc[tr]), y.iloc[tr])
        pred[te] = clf.predict_proba(sc.transform(x.iloc[te]))[:, 1]
    ok = ~np.isnan(pred)
    if ok.sum() < 100 or len(np.unique(y[ok])) < 2:
        return None
    return round(float(roc_auc_score(y[ok], pred[ok])), 4)


def _return_corr(df: pd.DataFrame, k: int) -> float | None:
    ema = pd.to_numeric(df.get("ema_close"), errors="coerce").pct_change()
    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce").pct_change().shift(k)
    m = ema.notna() & cbot.notna()
    if m.sum() < 200:
        return None
    return round(float(np.corrcoef(ema[m], cbot[m])[0, 1]), 3)


def alignment_metrics(df: pd.DataFrame, k: int) -> dict[str, Any]:
    basis = aligned_basis(df, k)
    delta = basis.diff()
    d = delta.dropna()
    lag1 = round(float(d.autocorr(lag=1)), 3) if len(d) > 200 else None
    return {
        "k": k,
        "return_corr_ema_vs_cbot_shift": _return_corr(df, k),
        "delta_std": round(float(d.std()), 3) if len(d) else None,
        "delta_lag1_autocorr": lag1,
        "ar1_halflife_days": _ar1_halflife(basis),
        "compression_oof_auc": _compression_auc(basis, df),
    }


def run_v46_alignment(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    if "ema_close" not in df.columns or "cbot_eur_t" not in df.columns:
        return {"version": "V46-SETTLEMENT-ALIGNMENT", "verdict": "MISSING_DATA"}

    # k=0 baseline (live, contemporain) ; k=1 CBOT veille (live, sans fuite) ; k=-1 diagnostic (FUITE, non live)
    res = {k: alignment_metrics(df, k) for k in (-1, 0, 1)}

    corrs = {k: res[k]["return_corr_ema_vs_cbot_shift"] for k in res
             if res[k]["return_corr_ema_vs_cbot_shift"] is not None}
    best_info_k = max(corrs, key=corrs.get) if corrs else None

    # comparaison LIVE (k in {0,1}) : ré-aligner réduit-il le bruit / améliore-t-il la compression ?
    base_auc = res[0]["compression_oof_auc"]
    lag_auc = res[1]["compression_oof_auc"]
    base_noise = res[0]["delta_std"]
    lag_noise = res[1]["delta_std"]
    realign_helps_live = bool(
        lag_auc is not None and base_auc is not None and lag_auc > base_auc + 0.02
        and lag_noise is not None and base_noise is not None and lag_noise <= base_noise)

    out = {
        "version": "V46-SETTLEMENT-ALIGNMENT",
        "by_alignment": res,
        "best_information_alignment_k": best_info_k,
        "nonsync_confirmed": bool(best_info_k is not None and best_info_k != 0),
        "live_realignment_helps": realign_helps_live,
        "verdict": (
            "REALIGN_HELPS_LIVE" if realign_helps_live
            else "NONSYNC_REAL_BUT_REALIGN_MARGINAL_LIVE" if (best_info_k not in (None, 0))
            else "ALIGNMENT_NEGLIGIBLE"),
        "interpretation": (
            "Si le meilleur alignement informationnel est k<0 (CBOT du lendemain), c'est un décalage de "
            "settlement réel mais NON exploitable live (fuite) : à l'instant du close Euronext, le CBOT le "
            "plus frais connu est celui du jour (k=0). Le correctif propre = CBOT à l'heure du settlement "
            "Euronext (intraday, data-gated). En attendant, k=0 reste le bon choix LIVE sauf gain net démontré."),
        "recommendation": (
            "Conserver le basis contemporain (k=0) pour le live ; viser l'intraday pour le vrai alignement. "
            "Aucune modification de la règle figée."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V46_DIR / "v46_alignment.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
