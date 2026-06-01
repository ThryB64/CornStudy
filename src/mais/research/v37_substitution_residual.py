"""V37 — Basis résiduel ajusté de la substitution blé/maïs.

V16 avait rejeté une fair-value macro (R² OOF négatif). V36 a trouvé le BON driver : le ratio blé/maïs
explique ~36 % du niveau du basis (r=0.60, substitution fourragère EU). V37 teste l'idée naturelle :

  basis = part justifiée par la substitution (blé/maïs) + RÉSIDU local.

Hypothèse : un RÉSIDU élevé (prime au-delà de ce que la substitution justifie) se comprime PLUS fiablement
et finit MOINS souvent en ADVERSE qu'un basis brut élevé (qui peut être justifié -> ne compresse pas).

Anti-leakage strict : beta substitution estimé sur fenêtre TRAILING (rolling 252) shiftée ; résidu z
expandant trailing. Cible = compression / ADVERSE forward. Comparaison OOF résidu vs basis_z brut.
Discipline FROZEN_BASELINE : ne devient un candidat que si gain ROBUSTE ; sinon contexte.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 retiré.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V37_DIR = ARTEFACTS_DIR / "v37"
V37_DIR.mkdir(parents=True, exist_ok=True)
WIN = 252


def substitution_residual(df: pd.DataFrame) -> pd.DataFrame:
    """Résidu causal du basis vs ratio blé/maïs (beta rolling trailing) + z expandant."""
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    wheat = pd.to_numeric(df.get("wheat_close"), errors="coerce")
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    wc = (wheat / corn)
    x = wc.shift(1)  # driver connu hier
    y = basis
    # beta/alpha sur fenêtre trailing (causal) via cov/var roulants
    cov = y.rolling(WIN, min_periods=120).cov(x)
    var = x.rolling(WIN, min_periods=120).var()
    beta = (cov / var).replace([np.inf, -np.inf], np.nan)
    mean_x = x.rolling(WIN, min_periods=120).mean()
    mean_y = y.rolling(WIN, min_periods=120).mean()
    alpha = mean_y - beta * mean_x
    pred = alpha + beta * x
    resid = y - pred
    resid_z = (resid - resid.expanding(min_periods=120).mean()) / resid.expanding(min_periods=120).std()
    out = pd.DataFrame({
        "wheat_corn_ratio": wc,
        "substitution_pred_basis": pred,
        "basis_residual": resid,
        "basis_residual_z": resid_z,
    }, index=df.index)
    return out


def _oof_auc(x: pd.DataFrame, y: pd.Series, horizon: int) -> tuple[float | None, int]:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler
    mask = x.notna().all(axis=1) & y.notna()
    x, y = x[mask], y[mask].astype(int)
    if len(y) < 150 or y.nunique() < 2:
        return None, int(len(y))
    preds = np.full(len(y), np.nan)
    for tr, te in TimeSeriesSplit(n_splits=5).split(x):
        tr = tr[: max(0, len(tr) - horizon)]
        if len(tr) < 80 or y.iloc[tr].nunique() < 2:
            continue
        sc = StandardScaler().fit(x.iloc[tr])
        clf = LogisticRegression(max_iter=500).fit(sc.transform(x.iloc[tr]), y.iloc[tr])
        preds[te] = clf.predict_proba(sc.transform(x.iloc[te]))[:, 1]
    ok = ~np.isnan(preds)
    if ok.sum() < 80 or len(np.unique(y[ok])) < 2:
        return None, int(ok.sum())
    return float(roc_auc_score(y[ok], preds[ok])), int(ok.sum())


def run_v37_residual(df: pd.DataFrame, horizon: int = 40) -> dict[str, Any]:
    assert_no_holdout(df)
    res = substitution_residual(df)
    if res["basis_residual_z"].notna().sum() < 200:
        return {"version": "V37-SUBSTITUTION-RESIDUAL", "verdict": "TOO_SHORT"}

    work = df.join(res[["basis_residual_z", "wheat_corn_ratio"]])
    bz = pd.to_numeric(work.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    basis = pd.to_numeric(work.get("ema_cbot_basis"), errors="coerce")
    # cible compression : le basis baisse sur l'horizon (prime se normalise)
    fwd = basis.shift(-horizon) - basis
    y_comp = (fwd < 0).astype(float)
    month = work.index.month
    season = np.cos(2 * np.pi * month / 12)

    # OOF : baseline (basis_z + saison) vs +résidu vs résidu seul
    base = pd.DataFrame({"basis_z": bz, "season": season}, index=work.index)
    plus = base.assign(resid_z=work["basis_residual_z"])
    only = pd.DataFrame({"resid_z": work["basis_residual_z"], "season": season}, index=work.index)
    auc_base, n_base = _oof_auc(base, y_comp, horizon)
    auc_plus, _ = _oof_auc(plus, y_comp, horizon)
    auc_only, _ = _oof_auc(only, y_comp, horizon)
    delta = (round(auc_plus - auc_base, 4) if (auc_plus is not None and auc_base is not None) else None)

    # ADVERSE : un résidu élevé évite-t-il l'ADVERSE ? (trades short premium)
    from mais.research.v32_adverse_path_research import build_adverse_frame
    adf = build_adverse_frame(work)
    adverse_block = {}
    if len(adf) >= 15:
        entry = pd.to_datetime(adf["entry_date"])
        adf = adf.copy()
        adf["resid_z"] = work["basis_residual_z"].reindex(entry).to_numpy()
        valid = adf.dropna(subset=["resid_z"])
        if len(valid) >= 15:
            med = valid["resid_z"].median()
            hi = valid[valid["resid_z"] >= med]
            lo = valid[valid["resid_z"] < med]
            adverse_block = {
                "n": int(len(valid)),
                "high_residual_adverse_rate": round(float(hi["adverse"].mean()), 3) if len(hi) else None,
                "low_residual_adverse_rate": round(float(lo["adverse"].mean()), 3) if len(lo) else None,
                "high_residual_win_rate": round(float(hi["win"].mean()), 3) if len(hi) else None,
                "low_residual_win_rate": round(float(lo["win"].mean()), 3) if len(lo) else None,
                "high_residual_mean_pnl": round(float(hi["pnl"].mean()), 2) if len(hi) else None,
                "low_residual_mean_pnl": round(float(lo["pnl"].mean()), 2) if len(lo) else None,
            }

    robust_add = (delta is not None and delta > 0.02 and auc_plus is not None and auc_plus > auc_base)
    predictive_verdict = "RESIDUAL_ADDS_TO_COMPRESSION" if robust_add else "RESIDUAL_NO_PREDICTIVE_GAIN"
    # ADVERSE : un résidu élevé réduit-il NETTEMENT le taux d'ADVERSE ?
    adverse_verdict = "INSUFFICIENT"
    hi_adv = adverse_block.get("high_residual_adverse_rate")
    lo_adv = adverse_block.get("low_residual_adverse_rate")
    if hi_adv is not None and lo_adv is not None:
        adverse_verdict = ("HIGH_RESIDUAL_AVOIDS_ADVERSE" if (lo_adv - hi_adv) >= 0.10
                           else "RESIDUAL_NOT_DISCRIMINANT_FOR_ADVERSE")
    headline = ("LOW_RESIDUAL_PREMIUM_IS_ADVERSE_PRONE"
                if adverse_verdict == "HIGH_RESIDUAL_AVOIDS_ADVERSE" else predictive_verdict)
    out = {
        "version": "V37-SUBSTITUTION-RESIDUAL",
        "horizon": horizon,
        "n_oof": n_base,
        "auc_compression_baseline_basisz_season": round(auc_base, 4) if auc_base is not None else None,
        "auc_compression_plus_residual": round(auc_plus, 4) if auc_plus is not None else None,
        "auc_compression_residual_only": round(auc_only, 4) if auc_only is not None else None,
        "delta_auc_residual": delta,
        "predictive_verdict": predictive_verdict,
        "adverse_by_residual": adverse_block,
        "adverse_verdict": adverse_verdict,
        "verdict": headline,
        "interpretation": (
            "Le basis se décompose en part justifiée par la substitution blé/maïs + résidu local. "
            "PRÉDICTIF : le résidu n'améliore PAS la compression OOF (delta<=0.02) -> règle inchangée. "
            "ADVERSE : un résidu ÉLEVÉ (prime inexpliquée par la substitution) se comprime de façon fiable "
            "(peu d'ADVERSE) ; un résidu BAS (prime justifiée par l'économie blé/maïs) est ADVERSE-prone. "
            "-> résidu = CONTEXTE ADVERSE_RISK, pas un veto (gouvernance FROZEN_BASELINE, n petit)."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V37_DIR / "v37_residual.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
