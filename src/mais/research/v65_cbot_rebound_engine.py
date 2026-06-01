"""V65 — CBOT rebound engine : prédire la capacité de RATTRAPAGE du CBOT (moteur de compression).

La compression du basis est surtout CBOT-driven (V21/V35). CBOT_SUPPORT (V41) est règle-basé ; on teste ici
si un modèle OOF HONNÊTE (logistique régularisée, TimeSeriesSplit + embargo) prédit mieux le rebond/drawdown
CBOT à partir de features causales standard. Si oui -> enrichir CBOT_SUPPORT ; sinon -> garder le règle-basé.

Features causales (shift(1)) : distance à la SMA50, momentum 5/20j, RSI14, volatilité 20j, drawdown 60j,
managed-money net (causal), ratio maïs/blé, ratio maïs/soja, momentum USD.
Cibles : rebond CBOT (ret forward > 0) à h=10/20/40 ; on rapporte aussi le drawdown.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V65_DIR = ARTEFACTS_DIR / "v65"
V65_DIR.mkdir(parents=True, exist_ok=True)


def rebound_features(df: pd.DataFrame) -> pd.DataFrame:
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    sma = pd.to_numeric(df.get("corn_sma_50"), errors="coerce")
    soy = pd.to_numeric(df.get("soy_close"), errors="coerce")
    usd = pd.to_numeric(df.get("usd_index_close"), errors="coerce")
    mm = pd.to_numeric(df.get("cot_mm_net_pct_oi_x"), errors="coerce")
    f = pd.DataFrame(index=df.index)
    f["dist_sma50"] = corn / sma - 1.0
    f["mom20"] = pd.to_numeric(df.get("corn_logret_20d"), errors="coerce")
    f["mom5"] = pd.to_numeric(df.get("corn_logret_5d"), errors="coerce")
    f["rsi14"] = pd.to_numeric(df.get("corn_rsi_14"), errors="coerce")
    f["vol20"] = pd.to_numeric(df.get("corn_realized_vol_20"), errors="coerce")
    f["drawdown60"] = corn / corn.rolling(60, min_periods=20).max() - 1.0
    f["mm_net"] = mm
    f["corn_wheat"] = pd.to_numeric(df.get("corn_wheat_ratio"), errors="coerce")
    f["corn_soy"] = corn / soy
    f["usd_mom20"] = usd / usd.shift(20) - 1.0
    return f.shift(1)  # anti-leakage


def _oof_proba(x: pd.DataFrame, y: pd.Series, horizon: int) -> tuple[np.ndarray, pd.Index] | None:
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler
    mask = x.notna().all(axis=1) & y.notna()
    xv, yv = x[mask], y[mask].astype(int)
    if len(yv) < 250 or yv.nunique() < 2:
        return None
    pred = np.full(len(yv), np.nan)
    for tr, te in TimeSeriesSplit(n_splits=5).split(xv):
        tr = tr[: max(0, len(tr) - horizon)]  # embargo
        if len(tr) < 120 or yv.iloc[tr].nunique() < 2:
            continue
        sc = StandardScaler().fit(xv.iloc[tr])
        clf = LogisticRegression(max_iter=600, C=0.5).fit(sc.transform(xv.iloc[tr]), yv.iloc[tr])
        pred[te] = clf.predict_proba(sc.transform(xv.iloc[te]))[:, 1]
    return pred, xv.index


def _auc(pred: np.ndarray, y: pd.Series) -> float | None:
    from sklearn.metrics import roc_auc_score
    ok = ~np.isnan(pred)
    if ok.sum() < 120 or len(np.unique(y[ok])) < 2:
        return None
    return float(roc_auc_score(y[ok], pred[ok]))


def run_v65_rebound(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    x = rebound_features(df)
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    if x.notna().all(axis=1).sum() < 300:
        return {"version": "V65-CBOT-REBOUND", "verdict": "NO_DATA"}

    results = {}
    oof_store = {}
    for h in (10, 20, 40):
        y_up = (corn.shift(-h) / corn - 1.0 > 0).astype(float)
        r = _oof_proba(x, y_up, h)
        if r is None:
            continue
        pred, idx = r
        auc = _auc(pred, y_up.reindex(idx).reset_index(drop=True))
        base = float(y_up.reindex(idx).mean())
        results[f"rebound_h{h}"] = {"oof_auc": round(auc, 3) if auc is not None else None,
                                    "base_rate_up": round(base, 3),
                                    "n": int((~np.isnan(pred)).sum())}
        oof_store[h] = pd.Series(pred, index=idx)

    # apport potentiel à CBOT_SUPPORT : la proba de rebond OOF h20 distingue-t-elle l'ADVERSE
    # des trades short-premium ? (un rebond CBOT probable => compression plus fiable => moins d'ADVERSE)
    adverse_link = {}
    if 20 in oof_store:
        from mais.research.v32_adverse_path_research import build_adverse_frame
        adv = build_adverse_frame(df)
        if len(adv) >= 15:
            entry = pd.to_datetime(adv["entry_date"])
            p = oof_store[20].reindex(entry)
            v = adv.assign(p_rebound=p.to_numpy()).dropna(subset=["p_rebound"])
            if len(v) >= 15:
                thr = v["p_rebound"].median()
                hi = v[v["p_rebound"] >= thr]
                lo = v[v["p_rebound"] < thr]
                adverse_link = {
                    "n": int(len(v)),
                    "adverse_rate_high_rebound_prob": round(float(hi["adverse"].mean()), 3) if len(hi) else None,
                    "adverse_rate_low_rebound_prob": round(float(lo["adverse"].mean()), 3) if len(lo) else None,
                    "high_rebound_prob_lowers_adverse": bool(
                        len(hi) and len(lo) and hi["adverse"].mean() < lo["adverse"].mean()),
                }

    aucs = [v["oof_auc"] for v in results.values() if v.get("oof_auc") is not None]
    best_auc = max(aucs) if aucs else None
    useful = bool(best_auc is not None and best_auc >= 0.55)
    if useful:
        verdict = "CBOT_REBOUND_OOF_USEFUL_ADD_TO_CBOT_SUPPORT"
    elif best_auc is not None:
        verdict = "CBOT_REBOUND_OOF_WEAK_KEEP_RULE_BASED_SUPPORT"
    else:
        verdict = "NO_DATA"

    out = {
        "version": "V65-CBOT-REBOUND",
        "oof_by_horizon": results,
        "best_oof_auc": round(best_auc, 3) if best_auc is not None else None,
        "adverse_link_h20": adverse_link,
        "features": list(x.columns),
        "verdict": verdict,
        "interpretation": (
            f"Meilleure OOF AUC rebond CBOT = {round(best_auc, 3) if best_auc is not None else None} "
            "(seuil utilité 0.55). Le rebond CBOT direction reste difficile à prédire (cohérent marché "
            "efficient), MAIS la proba OOF peut servir de NUANCE au CBOT_SUPPORT règle-basé si elle abaisse "
            "l'ADVERSE des signaux. On ne remplace pas le règle-basé (robuste, interprétable) par un modèle ; "
            "on l'utilise comme contexte additionnel seulement si l'apport OOF est net."),
        "note": "OOF logistique régularisée + embargo. Pas de fit sur les 42 trades. Négatif documenté si faible.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V65_DIR / "v65_cbot_rebound.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
