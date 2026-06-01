"""V32 — Recherche du chemin ADVERSE : peut-on prévoir AVANT l'entrée les basis qui ne se compressent pas ?

V29 a montré que 100 % des pertes du short premium sont le chemin ADVERSE (le basis s'écarte au lieu de
se comprimer). Plutôt que chercher un modèle plus puissant, on cherche à DÉTECTER l'ADVERSE à l'entrée,
avec des features connues au moment du signal (anti-leakage). Le but n'est PAS un veto binaire mais un
score `ADVERSE_RISK` low/med/high qui module l'objectif (z→0.5 seulement) / la prudence — sans toucher la
règle figée.

n est petit (~42 trades, ~7 ADVERSE) : on reste descriptif + LOO honnête, on n'optimise aucun seuil.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 retiré.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V32_DIR = ARTEFACTS_DIR / "v32"
V32_DIR.mkdir(parents=True, exist_ok=True)


def _classify_path(ema, cbot, d_entry, d_exit) -> str:
    e0, e1 = ema.get(pd.Timestamp(d_entry)), ema.get(pd.Timestamp(d_exit))
    c0, c1 = cbot.get(pd.Timestamp(d_entry)), cbot.get(pd.Timestamp(d_exit))
    if any(pd.isna(v) for v in (e0, e1, c0, c1)):
        return "unknown"
    d_ema, d_cbot = e1 - e0, c1 - c0
    if (d_ema - d_cbot) >= 0:
        return "ADVERSE"
    cbot_contrib, ema_contrib = max(d_cbot, 0.0), max(-d_ema, 0.0)
    if cbot_contrib > 1.5 * ema_contrib:
        return "CBOT_DRIVEN"
    if ema_contrib > 1.5 * cbot_contrib:
        return "EMA_DRIVEN"
    return "BOTH"


def build_adverse_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Trades historiques + label ADVERSE + features d'entrée (toutes causales)."""
    from mais.research.v17_research_indicator import build_trades_detailed
    from mais.research.v29_premium_risk_path import _drawdown_risk_score
    tdf = build_trades_detailed(df)
    if len(tdf) == 0:
        return tdf
    ema, cbot = df["ema_close"], df["cbot_eur_t"]
    bz = df["ema_cbot_basis_zscore_52w"]
    basis = df.get("ema_cbot_basis", pd.Series(np.nan, index=df.index))
    backw = df.get("curve_backwardation_proxy", pd.Series(np.nan, index=df.index))
    vol = df.get("corn_realized_vol_20", pd.Series(np.nan, index=df.index))
    oi = df.get("ema_oi_total", pd.Series(np.nan, index=df.index))
    corn = df["corn_close"]
    risk = _drawdown_risk_score(df)
    oi_med = oi[oi > 0].median() if (oi > 0).any() else np.nan

    rows = []
    for _, t in tdf.iterrows():
        d = pd.Timestamp(t["entry_date"])
        if d not in df.index:
            continue
        i = df.index.get_loc(d)
        j20 = max(0, i - 20)
        path = _classify_path(ema, cbot, t["entry_date"], t["exit_date"])
        rows.append({
            "entry_date": t["entry_date"],
            "path": path,
            "adverse": int(path == "ADVERSE"),
            "win": int(t["win"]),
            "pnl": float(t["pnl_z0_max90_sl20"]),
            "entry_z": float(t["entry_z"]),
            # vitesse récente du basis_z : >0 => la prime montait encore à l'entrée
            "basis_z_velocity_20": float(bz.iloc[i] - bz.iloc[j20]) if not pd.isna(bz.iloc[i]) else np.nan,
            "basis_level": float(basis.iloc[i]) if not pd.isna(basis.iloc[i]) else np.nan,
            # backwardation proxy (>0) = tension physique
            "backwardation": float(backw.iloc[i]) if not pd.isna(backw.iloc[i]) else np.nan,
            "cbot_drawdown_risk": float(risk.iloc[i]) if (i < len(risk) and not pd.isna(risk.iloc[i])) else np.nan,
            # momentum CBOT 20j : si CBOT déjà faible, le rattrapage (compression) est moins probable
            "cbot_mom_20": float(corn.iloc[i] / corn.iloc[j20] - 1.0) if corn.iloc[j20] else np.nan,
            "realized_vol_20": float(vol.iloc[i]) if not pd.isna(vol.iloc[i]) else np.nan,
            "low_liquidity": int(oi.iloc[i] < oi_med) if (not pd.isna(oi.iloc[i]) and not pd.isna(oi_med)) else 0,
            "roll_month": int(d.month in (2, 5, 7, 10)),
            "crisis": int(d.year in (2020, 2021, 2022)),
            "month": int(d.month),
        })
    return pd.DataFrame(rows)


def _profile(sub: pd.DataFrame, cols: list[str]) -> dict[str, Any]:
    if len(sub) == 0:
        return {"n": 0}
    out = {"n": int(len(sub))}
    for c in cols:
        v = pd.to_numeric(sub[c], errors="coerce").dropna()
        out[c] = round(float(v.mean()), 4) if len(v) else None
    return out


def _loo_auc(x: pd.DataFrame, y: pd.Series) -> float | None:
    """Leave-one-out AUC (honnête pour petit n)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.preprocessing import StandardScaler
    mask = x.notna().all(axis=1) & y.notna()
    x, y = x[mask], y[mask].astype(int)
    if len(y) < 15 or y.nunique() < 2 or y.sum() < 3:
        return None
    preds = np.full(len(y), np.nan)
    for k in range(len(y)):
        tr = [m for m in range(len(y)) if m != k]
        if y.iloc[tr].nunique() < 2:
            continue
        sc = StandardScaler().fit(x.iloc[tr])
        clf = LogisticRegression(max_iter=500).fit(sc.transform(x.iloc[tr]), y.iloc[tr])
        preds[k] = clf.predict_proba(sc.transform(x.iloc[[k]]))[:, 1][0]
    ok = ~np.isnan(preds)
    if ok.sum() < 15 or len(np.unique(y[ok])) < 2:
        return None
    return float(roc_auc_score(y[ok], preds[ok]))


def run_v32_adverse(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    adf = build_adverse_frame(df)
    if len(adf) < 15:
        return {"version": "V32-ADVERSE", "verdict": "TOO_FEW", "n": int(len(adf))}
    feat_cols = ["entry_z", "basis_z_velocity_20", "basis_level", "backwardation",
                 "cbot_drawdown_risk", "cbot_mom_20", "realized_vol_20"]
    adverse = adf[adf["adverse"] == 1]
    good = adf[adf["adverse"] == 0]
    prof_adv, prof_good = _profile(adverse, feat_cols), _profile(good, feat_cols)

    # séparateurs : features dont la moyenne diffère le plus (signe + ampleur)
    separators = {}
    for c in feat_cols:
        a, g = prof_adv.get(c), prof_good.get(c)
        if a is not None and g is not None:
            separators[c] = round(a - g, 4)

    # score LOO multivarié (honnête) + meilleurs univariés
    x = adf[feat_cols].apply(pd.to_numeric, errors="coerce")
    y = adf["adverse"]
    auc_multi = _loo_auc(x, y)
    auc_uni = {c: _loo_auc(x[[c]], y) for c in feat_cols}
    auc_uni = {c: v for c, v in auc_uni.items() if v is not None}

    # ADVERSE_RISK descriptif : terciles de la proba LOO multivariée si dispo
    risk_tiers = None
    if auc_multi is not None and auc_multi >= 0.60:
        risk_tiers = "score LOO multivarié exploitable (AUC>=0.60) -> ADVERSE_RISK low/med/high par terciles"
    verdict = ("ADVERSE_PARTIALLY_PREDICTABLE" if (auc_multi is not None and auc_multi >= 0.60)
               else "ADVERSE_WEAKLY_PREDICTABLE")
    out = {
        "version": "V32-ADVERSE",
        "n_trades": int(len(adf)),
        "n_adverse": int(adf["adverse"].sum()),
        "adverse_rate": round(float(adf["adverse"].mean()), 3),
        "profile_adverse": prof_adv,
        "profile_compressed": prof_good,
        "separators_adverse_minus_compressed": separators,
        "loo_auc_multivariate": round(auc_multi, 3) if auc_multi is not None else None,
        "loo_auc_univariate": {k: round(v, 3) for k, v in sorted(auc_uni.items(), key=lambda kv: -kv[1])},
        "adverse_risk_tiers": risk_tiers,
        "verdict": verdict,
        "usage": ("Score ADVERSE_RISK = CONTEXTE/warning, PAS un veto dur (anti sur-filtrage V15/V23/V29). "
                  "Si ADVERSE_RISK élevé : viser z->0.5 seulement, prudence sur z->0 complet."),
        "note": "n petit (LOO), descriptif. À re-tester en forward officiel (V31) avec plus de trades.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    adf.to_parquet(V32_DIR / "adverse_trades.parquet", index=False)
    (V32_DIR / "v32_adverse.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
