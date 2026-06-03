"""VN-D1 — Hazard : P(une compression démarre dans 5/10/20 j) sur le panel basis_z>1.

On NE prédit PAS le jour exact (V106 : intrinsèquement dur). On estime une PROBABILITÉ conditionnelle par
horizon, en walk-forward strict, comparée à la BASE RATE. Covariables strictement causales (info < t) :
basis_z, vitesse de spread (Δz 5 j), rendement CBOT 10 j, ratio blé/maïs z, COT si présent. Cible : le
basis_z chute-t-il d'au moins 0.5 dans les h prochains jours ?

GARDE-FOUS (review) : panel = jours basis_z>1 (≈ V106), PAS les 42 trades ; walk-forward expanding ;
comparaison systématique à la base rate ; Brier + AUC ; **verdict par défaut WATCHLIST** (si AUC ≈ base rate,
on l'écrit). Jamais présenté comme un edge. Holdout intact. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V_DIR = ARTEFACTS_DIR / "hazard_compression"
V_DIR.mkdir(parents=True, exist_ok=True)
DROP = 0.5           # compression = basis_z chute d'au moins 0.5
HORIZONS = (5, 10, 20)
MIN_TRAIN = 200


def _features(df: pd.DataFrame) -> pd.DataFrame:
    z = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    cbot = pd.to_numeric(df.get("cbot_close"), errors="coerce")
    feat = pd.DataFrame(index=df.index)
    feat["basis_z"] = z
    feat["dz5"] = z - z.shift(5)
    feat["cbot_ret10"] = np.log(cbot / cbot.shift(10))
    if "corn_wheat_ratio" in df.columns:
        wc = pd.to_numeric(df["corn_wheat_ratio"], errors="coerce")
        if wc.notna().sum() > 200:
            feat["wc_z"] = (wc - wc.expanding(min_periods=120).mean()) / wc.expanding(min_periods=120).std()
    if "cot_mm_net" in df.columns:
        cot = pd.to_numeric(df["cot_mm_net"], errors="coerce")
        if cot.notna().sum() > 200:
            feat["cot_mm_net"] = cot
    return feat


def _target(df: pd.DataFrame, h: int) -> pd.Series:
    z = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    # min des h prochaines valeurs (causal : strictement après t)
    vals = z.to_numpy()
    n = len(vals)
    out = np.full(n, np.nan)
    for i in range(n):
        j = min(i + 1 + h, n)
        if i + 1 < n:
            out[i] = np.nanmin(vals[i + 1:j])
    fwd_min = pd.Series(out, index=z.index)
    return ((z - fwd_min) >= DROP).astype(float).where(fwd_min.notna())


def _walk_forward_auc(xs: np.ndarray, y: np.ndarray, dates: pd.DatetimeIndex) -> dict[str, Any]:
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import brier_score_loss, roc_auc_score
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        return {"available": False}
    n = len(y)
    if n < MIN_TRAIN + 50:
        return {"available": False, "reason": "panel trop court"}
    preds, truth = [], []
    step = max(20, (n - MIN_TRAIN) // 8)
    for start in range(MIN_TRAIN, n, step):
        tr = slice(0, start)
        te = slice(start, min(start + step, n))
        ytr = y[tr]
        if len(np.unique(ytr[~np.isnan(ytr)])) < 2:
            continue
        m = ~np.isnan(ytr)
        sc = StandardScaler().fit(xs[tr][m])
        clf = LogisticRegression(max_iter=200).fit(sc.transform(xs[tr][m]), ytr[m])
        yte = y[te]
        mt = ~np.isnan(yte)
        if mt.sum() == 0:
            continue
        p = clf.predict_proba(sc.transform(xs[te][mt]))[:, 1]
        preds.extend(p.tolist())
        truth.extend(yte[mt].tolist())
    if len(truth) < 50 or len(np.unique(truth)) < 2:
        return {"available": True, "verdict": "INSUFFICIENT", "n": len(truth)}
    truth_a, preds_a = np.array(truth), np.array(preds)
    return {"available": True, "n_oof": int(len(truth)), "base_rate": round(float(truth_a.mean()), 3),
            "auc": round(float(roc_auc_score(truth_a, preds_a)), 3),
            "brier": round(float(brier_score_loss(truth_a, preds_a)), 4)}


def run_v_hazard(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    feat = _features(df)
    z = feat["basis_z"]
    panel = z > 1.0
    if panel.sum() < MIN_TRAIN + 50:
        return {"version": "HAZARD-COMPRESSION", "verdict": "NO_DATA", "n_panel": int(panel.sum())}

    results = {}
    edge = False
    for h in HORIZONS:
        y = _target(df, h)
        sub = panel & feat.notna().all(axis=1) & y.notna()
        if sub.sum() < MIN_TRAIN + 50:
            results[f"h{h}"] = {"verdict": "TOO_FEW", "n": int(sub.sum())}
            continue
        xs = feat[sub].to_numpy()
        r = _walk_forward_auc(xs, y[sub].to_numpy(), df.index[sub])
        results[f"h{h}"] = r
        if r.get("auc") is not None and r["auc"] >= 0.62:
            edge = True

    verdict = "HAZARD_ADDS_SIGNAL" if edge else "WATCHLIST_NO_CLEAR_EDGE"
    out = {
        "version": "HAZARD-COMPRESSION",
        "verdict": verdict,
        "drop_threshold": DROP,
        "by_horizon": results,
        "features": list(feat.columns),
        "interpretation": (
            f"Hazard P(compression ≥{DROP} en h j) sur panel basis_z>1, walk-forward. Résultats : {results}. "
            + ("Au moins un horizon dépasse AUC 0.62 -> signal exploitable (à confirmer forward)." if edge else
               "Aucun horizon ne dépasse nettement la base rate (AUC≈base) -> WATCHLIST, cohérent V106 "
               "(timing dur, marché ~efficient). On NE présente pas ça comme un edge.")),
        "note": "Panel = jours actifs, PAS les 42 trades. Walk-forward expanding. Brier+AUC vs base rate. "
                "Holdout intact. sklearn optionnel.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V_DIR / "hazard_compression.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
