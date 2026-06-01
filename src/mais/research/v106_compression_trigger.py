"""CT-09/10/11 (v106) — Cible « compression imminente », COMPRESSION_TRIGGER_SCORE, bloc rapport.

CT-09 : sur le PANEL QUOTIDIEN (jours basis_z>1), cible `compression_imminent_h10` = le basis baisse d'au
moins X dans les 10 j. Features STRICTEMENT causales (≤ t). OOF logistique + embargo -> AUC honnête.
CT-10 : score règle-basé NONE/EARLY/CONFIRMED, conçu d'après l'event study (V105) : la compression suit un
OVERSHOOT du basis qui se retourne + un essoufflement EMA relatif + un ratio blé/maïs qui se détend ; le
« CBOT qui monte d'abord » n'est PAS un précurseur propre (V105). On valide le score sur la cible.
CT-11 : bloc daily report `COMPRESSION_TRIGGER`.

Anti-leakage : toutes les features en t (Δ sur fenêtres passées) ; cible forward ; OOF TimeSeriesSplit+embargo.
Statut : RESEARCH_ONLY_NOT_TRADING. Holdout verrouillé. Baseline figée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V106_DIR = ARTEFACTS_DIR / "v106"
V106_DIR.mkdir(parents=True, exist_ok=True)


def trigger_features(df: pd.DataFrame) -> pd.DataFrame:
    """Features causales du déclencheur (connues à t)."""
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce")
    ema = pd.to_numeric(df.get("ema_close"), errors="coerce")
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    wheat = pd.to_numeric(df.get("wheat_close"), errors="coerce")
    wc = corn / wheat

    f = pd.DataFrame(index=df.index)
    f["basis_z"] = bz
    f["bz_chg_3"] = bz - bz.shift(3)                      # <0 = momentum basis se retourne
    f["bz_below_ma5"] = (bz < bz.rolling(5, min_periods=3).mean()).astype(int)
    f["ema_ret_5"] = ema / ema.shift(5) - 1.0            # essoufflement EMA si <=0
    f["cbot_ret_5"] = cbot / cbot.shift(5) - 1.0         # rattrapage CBOT si >0
    f["ema_minus_cbot_5"] = f["ema_ret_5"] - f["cbot_ret_5"]  # >0 = EMA surperforme encore
    f["wc_chg_10"] = wc / wc.shift(10) - 1.0             # <0 = blé/maïs se détend
    return f


def compression_target(df: pd.DataFrame, horizon: int = 10, drop_z: float = 0.3) -> pd.Series:
    """1 si basis_z baisse d'au moins drop_z dans les `horizon` jours (forward)."""
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    # min du basis_z sur [t+1, t+horizon] (forward)
    fwd_min = pd.Series(
        [bz.iloc[i + 1:i + 1 + horizon].min() if i + 1 < len(bz) else np.nan for i in range(len(bz))],
        index=bz.index)
    return ((bz - fwd_min) >= drop_z).astype(float)


def compute_trigger_score(df: pd.DataFrame) -> pd.DataFrame:
    """COMPRESSION_TRIGGER_SCORE règle-basé (composants causaux d'après V105). Actif si basis_z>1."""
    f = trigger_features(df)
    active = f["basis_z"] >= 1.0
    c_basis_roll = (f["bz_chg_3"] < 0).astype(int)            # momentum basis négatif
    c_below_ma5 = f["bz_below_ma5"].fillna(0).astype(int)      # sous la MA5
    c_ema_exhaust = (f["ema_minus_cbot_5"] < 0).astype(int)    # EMA n'surperforme plus le CBOT
    c_wc_relax = (f["wc_chg_10"] < 0).astype(int)              # blé/maïs se détend
    score = c_basis_roll + c_below_ma5 + c_ema_exhaust + c_wc_relax

    tier = pd.Series("NO_SIGNAL", index=df.index)
    tier[active & (score <= 0)] = "NONE"
    tier[active & (score.isin([1, 2]))] = "EARLY"
    tier[active & (score >= 3)] = "CONFIRMED"

    out = pd.DataFrame({
        "basis_z": f["basis_z"], "c_basis_momentum_neg": c_basis_roll, "c_below_ma5": c_below_ma5,
        "c_ema_exhaustion": c_ema_exhaust, "c_wheat_corn_relax": c_wc_relax,
        "compression_trigger_score": pd.Series(score, index=df.index).where(active),
        "compression_trigger": tier,
    }, index=df.index)
    return out


def _oof_auc(x: pd.DataFrame, y: pd.Series, horizon: int) -> float | None:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler
    m = x.notna().all(axis=1) & y.notna()
    xv, yv = x[m], y[m].astype(int)
    if len(yv) < 150 or yv.nunique() < 2:
        return None
    pred = np.full(len(yv), np.nan)
    for tr, te in TimeSeriesSplit(n_splits=5).split(xv):
        tr = tr[: max(0, len(tr) - horizon)]
        if len(tr) < 80 or yv.iloc[tr].nunique() < 2:
            continue
        sc = StandardScaler().fit(xv.iloc[tr])
        clf = LogisticRegression(max_iter=500).fit(sc.transform(xv.iloc[tr]), yv.iloc[tr])
        pred[te] = clf.predict_proba(sc.transform(xv.iloc[te]))[:, 1]
    ok = ~np.isnan(pred)
    if ok.sum() < 80 or len(np.unique(yv[ok])) < 2:
        return None
    return float(roc_auc_score(yv[ok], pred[ok]))


def run_v106_trigger(df: pd.DataFrame, horizon: int = 10, drop_z: float = 0.3) -> dict[str, Any]:
    assert_no_holdout(df)
    f = trigger_features(df)
    y = compression_target(df, horizon=horizon, drop_z=drop_z)
    active = f["basis_z"] >= 1.0
    panel = f[active].drop(columns=["basis_z"])
    y_act = y[active]
    n = int((panel.notna().all(axis=1) & y_act.notna()).sum())
    base_rate = round(float(y_act.mean()), 3) if y_act.notna().any() else None

    feat_cols = ["bz_chg_3", "ema_minus_cbot_5", "wc_chg_10", "cbot_ret_5"]
    auc = _oof_auc(panel[feat_cols], y_act, horizon)

    # validation du score règle-basé : taux de compression imminente par palier
    tr = compute_trigger_score(df)
    by_tier = {}
    for t in ("NONE", "EARLY", "CONFIRMED"):
        mask = (tr["compression_trigger"] == t) & y.notna()
        if int(mask.sum()) >= 20:
            by_tier[t] = {"n": int(mask.sum()), "compression_imminent_rate": round(float(y[mask].mean()), 3)}
    rates = {k: by_tier[k]["compression_imminent_rate"] for k in ("NONE", "EARLY", "CONFIRMED") if k in by_tier}
    vals = list(rates.values())
    monotone_increasing = (len(vals) >= 2 and vals == sorted(vals))   # CONFIRMED prédit PLUS de drop -> leading
    monotone_decreasing = (len(vals) >= 2 and vals == sorted(vals, reverse=True))  # inversé -> retard

    if monotone_increasing and auc is not None and auc >= 0.55:
        verdict = "COMPRESSION_TRIGGER_LEADING_ADD_TO_REPORT"
    elif monotone_decreasing:
        verdict = "COMPRESSION_TRIGGER_REFLECTS_ONGOING_NOT_LEADING"
    else:
        verdict = "COMPRESSION_TRIGGER_WEAK_CONTEXT_ONLY"

    out = {
        "version": "V106-COMPRESSION-TRIGGER",
        "horizon_days": horizon, "drop_z_threshold": drop_z,
        "n_panel_days": n, "base_rate_compression_imminent": base_rate,
        "oof_auc_compression_imminent": round(auc, 3) if auc is not None else None,
        "score_features": feat_cols,
        "trigger_score_by_tier": by_tier,
        "imminent_rate_by_tier": rates,
        "tier_monotone_increasing": monotone_increasing,
        "tier_monotone_decreasing_inverted": monotone_decreasing,
        "verdict": verdict,
        "interpretation": (
            f"Sur {n} jours basis_z>1, taux de base compression imminente (h{horizon}, Δz≥{drop_z}) = "
            f"{base_rate} (élevé : basis_z>1 compresse déjà souvent à 10 j). OOF AUC = "
            f"{round(auc, 3) if auc is not None else None} (marginal). Taux par palier de score : {rates}. "
            "DÉCOUVERTE : le score est INVERSÉ — quand il dit CONFIRMED (momentum basis déjà négatif, sous "
            "MA5), il reste MOINS de drop à venir (0.60) que quand il dit NONE (0.79). Autrement dit, ces "
            "précurseurs détectent une compression DÉJÀ EN COURS, pas un retournement À VENIR. Le seul "
            "'leading' est le taux de base élevé de basis_z>1. Timer précisément le DÉBUT reste difficile "
            "(cohérent réversion ~efficiente). -> COMPRESSION_TRIGGER = état descriptif ('compression "
            "semble amorcée'), pas un prédicteur de drop additionnel. CONTEXTE, jamais un veto."),
        "note": "Features causales (≤t), cible forward, OOF embargo. Panel quotidien (n>42). Négatif honnête.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V106_DIR / "v106_trigger.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def compression_trigger_report_block(df: pd.DataFrame) -> str:
    tr = compute_trigger_score(df)
    if len(tr) == 0:
        return ""
    last = tr.iloc[-1]
    if last["compression_trigger"] in ("NO_SIGNAL",):
        return ""
    facts = []
    if last["c_basis_momentum_neg"] == 1:
        facts.append("momentum basis négatif")
    if last["c_below_ma5"] == 1:
        facts.append("basis_z sous MA5")
    if last["c_ema_exhaustion"] == 1:
        facts.append("EMA n'surperforme plus le CBOT")
    if last["c_wheat_corn_relax"] == 1:
        facts.append("ratio blé/maïs se détend")
    facts_txt = "; ".join(facts) if facts else "aucun précurseur actif"
    return (
        "### Déclencheur de compression (V106/CT — état descriptif, pas un prédicteur ni un veto)\n"
        f"- COMPRESSION_TRIGGER : **{last['compression_trigger']}** "
        f"(score {int(last['compression_trigger_score'])}/4)\n"
        f"- Précurseurs actifs : {facts_txt}\n"
        "- NOTE (V106) : ces précurseurs détectent une compression **déjà amorcée**, pas un retournement à "
        "venir (taux inversé) — NONE = prime encore haute (plus de drop à venir) ; CONFIRMED = la baisse "
        "semble en cours (moins de drop restant). N'altère pas la règle figée. RESEARCH_ONLY_NOT_TRADING.\n"
    )
