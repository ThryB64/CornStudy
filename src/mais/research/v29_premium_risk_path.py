"""V29 — Exploration C (premium × risque drawdown CBOT) + D (chemin de compression).

Aucune nouvelle règle. On enrichit l'explication / les warnings de la baseline figée :
- Exploration C : le short premium est-il plus dangereux quand le risque de drawdown CBOT est élevé ?
  (le short premium = long CBOT relatif ; si le CBOT risque de chuter, la jambe CBOT souffre).
- Exploration D : classer chaque compression en CBOT_DRIVEN / EMA_DRIVEN / BOTH / ADVERSE
  (d(basis) = d(EMA) − d(CBOT_eur_t)). Confirme/affine la découverte V21 (compression surtout CBOT-driven).

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 retiré.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V29_DIR = ARTEFACTS_DIR / "v29"
V29_DIR.mkdir(parents=True, exist_ok=True)


def _drawdown_risk_score(df: pd.DataFrame, horizon: int = 40, drop: float = 0.08) -> pd.Series:
    """Proba OOF de drawdown CBOT (>=drop sur horizon) -> score par date (terciles en aval)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score  # noqa: F401  (cohérence d'import avec V23)
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler

    c = df["corn_close"].astype(float)
    ret = c.pct_change()
    feats = pd.DataFrame({
        "mom_20": c.pct_change(20),
        "mom_60": c.pct_change(60),
        "vol_20": ret.rolling(20).std(),
        "dist_high_120": c / c.rolling(120).max() - 1.0,
        "rsi_proxy": ret.rolling(14).apply(lambda x: (x > 0).mean(), raw=False),
    }, index=df.index)
    roll_max = c.rolling(horizon).max().shift(-horizon)
    y = ((c - roll_max) / c <= -drop).astype(float)
    mask = feats.notna().all(axis=1) & y.notna()
    x, yy = feats[mask], y[mask].astype(int)
    proba = pd.Series(np.nan, index=df.index)
    if len(yy) < 100 or yy.nunique() < 2:
        return proba
    p = pd.Series(np.nan, index=x.index)
    for tr, te in TimeSeriesSplit(n_splits=5).split(x):
        tr = tr[: max(0, len(tr) - horizon)]
        if len(tr) < 60 or yy.iloc[tr].nunique() < 2:
            continue
        sc = StandardScaler().fit(x.iloc[tr])
        clf = LogisticRegression(max_iter=500).fit(sc.transform(x.iloc[tr]), yy.iloc[tr])
        p.iloc[te] = clf.predict_proba(sc.transform(x.iloc[te]))[:, 1]
    proba.loc[p.index] = p.values
    return proba


def run_premium_x_drawdown(df: pd.DataFrame) -> dict[str, Any]:
    """Exploration C : segmenter les trades short premium par tier de risque drawdown CBOT."""
    assert_no_holdout(df)
    from mais.research.v17_research_indicator import build_trades_detailed
    tdf = build_trades_detailed(df)
    if len(tdf) < 10:
        return {"version": "V29-C-PREMIUM-X-DRAWDOWN", "verdict": "TOO_FEW", "n": int(len(tdf))}
    risk = _drawdown_risk_score(df)
    if risk.notna().sum() < 50:
        return {"version": "V29-C-PREMIUM-X-DRAWDOWN", "verdict": "NO_RISK_SCORE"}
    valid = risk.dropna()
    t1, t2 = valid.quantile(0.33), valid.quantile(0.66)

    def _tier(d):
        r = risk.reindex([pd.Timestamp(d)]).iloc[0]
        if pd.isna(r):
            return "unknown"
        return "low" if r < t1 else "medium" if r < t2 else "high"

    tdf = tdf.copy()
    tdf["drawdown_risk"] = tdf["entry_date"].map(_tier)
    seg = {}
    for tier in ["low", "medium", "high"]:
        sub = tdf[tdf["drawdown_risk"] == tier]
        if len(sub) == 0:
            continue
        seg[tier] = {
            "n": int(len(sub)),
            "win_rate": round(float(sub["win"].mean()), 3),
            "mean_pnl": round(float(sub["pnl_z0_max90_sl20"].mean()), 2),
            "share_stopped": round(float(sub["stopped"].mean()), 3),
            "mean_mae": round(float(sub["mae"].mean()), 2),
        }
    high, low = seg.get("high", {}), seg.get("low", {})
    warning = None
    if high.get("n", 0) >= 4 and low.get("n", 0) >= 4:
        if high["mean_pnl"] < low["mean_pnl"] - 3 or high["win_rate"] < low["win_rate"] - 0.15:
            warning = ("CONFIRMÉ : short premium plus dangereux quand drawdown_risk CBOT élevé "
                       "-> CBOT_DRAWDOWN_RISK devient un warning informatif pertinent.")
        else:
            warning = ("NON CONFIRMÉ : pas de dégradation nette sous drawdown_risk élevé "
                       "-> garder drawdown_risk comme contexte, pas comme veto (anti sur-filtrage V15/V23).")
    out = {
        "version": "V29-C-PREMIUM-X-DRAWDOWN",
        "n_trades": int(len(tdf)),
        "by_drawdown_risk": seg,
        "warning_verdict": warning or "trop peu de trades par tier pour conclure",
        "verdict": "PREMIUM_X_DRAWDOWN_DONE",
    }
    (V29_DIR / "premium_x_drawdown.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_compression_path(df: pd.DataFrame) -> dict[str, Any]:
    """Exploration D : classer chaque compression en CBOT_DRIVEN / EMA_DRIVEN / BOTH / ADVERSE."""
    assert_no_holdout(df)
    from mais.research.v17_research_indicator import build_trades_detailed
    tdf = build_trades_detailed(df)
    if len(tdf) < 10:
        return {"version": "V29-D-COMPRESSION-PATH", "verdict": "TOO_FEW", "n": int(len(tdf))}
    ema = df["ema_close"]
    cbot = df["cbot_eur_t"]

    def _classify(row):
        e0, e1 = ema.get(pd.Timestamp(row["entry_date"])), ema.get(pd.Timestamp(row["exit_date"]))
        c0, c1 = cbot.get(pd.Timestamp(row["entry_date"])), cbot.get(pd.Timestamp(row["exit_date"]))
        if any(pd.isna(v) for v in (e0, e1, c0, c1)):
            return "unknown", np.nan, np.nan, np.nan
        d_ema, d_cbot = e1 - e0, c1 - c0
        d_basis = d_ema - d_cbot
        if d_basis >= 0:
            label = "ADVERSE"
        else:
            cbot_contrib = max(d_cbot, 0.0)      # CBOT hausse comprime le basis
            ema_contrib = max(-d_ema, 0.0)       # EMA baisse comprime le basis
            if cbot_contrib > 1.5 * ema_contrib:
                label = "CBOT_DRIVEN"
            elif ema_contrib > 1.5 * cbot_contrib:
                label = "EMA_DRIVEN"
            else:
                label = "BOTH"
        return label, round(float(d_basis), 2), round(float(d_cbot), 2), round(float(d_ema), 2)

    cls = tdf.apply(lambda r: _classify(r), axis=1, result_type="expand")
    cls.columns = ["path", "d_basis", "d_cbot", "d_ema"]
    tdf = pd.concat([tdf, cls], axis=1)
    counts = tdf["path"].value_counts().to_dict()
    n_known = int((tdf["path"] != "unknown").sum())
    compressions = tdf[tdf["path"].isin(["CBOT_DRIVEN", "EMA_DRIVEN", "BOTH"])]
    share_cbot = (float((compressions["path"] == "CBOT_DRIVEN").mean())
                  if len(compressions) else None)
    by_path = {}
    for p in ["CBOT_DRIVEN", "EMA_DRIVEN", "BOTH", "ADVERSE"]:
        sub = tdf[tdf["path"] == p]
        if len(sub):
            by_path[p] = {"n": int(len(sub)), "win_rate": round(float(sub["win"].mean()), 3),
                          "mean_pnl": round(float(sub["pnl_z0_max90_sl20"].mean()), 2)}
    out = {
        "version": "V29-D-COMPRESSION-PATH",
        "n_trades": int(len(tdf)),
        "path_counts": {str(k): int(v) for k, v in counts.items()},
        "share_cbot_driven_among_compressions": round(share_cbot, 3) if share_cbot is not None else None,
        "by_path": by_path,
        "n_known": n_known,
        "verdict": "COMPRESSION_PATH_DONE",
        "interpretation": ("Confirme V21 si la part CBOT_DRIVEN domine : la prime se normalise surtout "
                           "par rattrapage CBOT (short premium ≈ long CBOT relatif)."),
    }
    (V29_DIR / "compression_path.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_v29_all(df: pd.DataFrame) -> dict[str, Any]:
    c = run_premium_x_drawdown(df)
    d = run_compression_path(df)
    out = {"version": "V29-EXPLORATION-C-D", "premium_x_drawdown": c, "compression_path": d,
           "status": "RESEARCH_ONLY_NOT_TRADING"}
    (V29_DIR / "v29_summary.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
