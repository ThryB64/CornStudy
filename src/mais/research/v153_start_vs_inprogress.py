"""V153 — Séparation stricte START (prédictif) vs IN_PROGRESS (descriptif).

Découverte V106 : l'ancien « COMPRESSION_TRIGGER_SCORE » est en réalité un score d'AVANCEMENT (inversé),
pas un score de DÉPART. On acte donc le renommage conceptuel :

  - COMPRESSION_PROGRESS_SCORE = score descriptif (= l'ancien V106, « la compression semble amorcée »).
  - START_TRIGGER_SCORE        = score PRÉDICTIF du DÉBUT futur, évalué sur variables ex ante seulement.

Labels (panel quotidien, basis_z>1) construits SANS lookahead :
  - start_event[τ] = 1 er jour où basis_z est retombé de >= DROP_Z depuis son pic glissant (déf. A V104),
    avec anti-rebond (pas de nouveau start dans les LOCKOUT jours suivants).
  - START_h{H}  = un start_event survient dans [t+1, t+H] ET aucun start_event dans [t-LOCKOUT, t]
                  (« départ futur, pas déjà parti »).
  - INPROG_h{H} = basis_z baisse d'au moins DROP_Z (cumulé) dans [t+1, t+H] (compression additionnelle).

Anti-leakage : features ≤ t (V106), cibles forward, OOF TimeSeriesSplit + embargo. Baseline figée.
RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.research.v106_compression_trigger import compute_trigger_score, trigger_features

V153_DIR = ARTEFACTS_DIR / "v153"
V153_DIR.mkdir(parents=True, exist_ok=True)

DROP_Z = 0.3       # déf. A : baisse de basis_z depuis le pic
PEAK_WIN = 20      # fenêtre du pic glissant (trailing)
LOCKOUT = 10       # anti-rebond : pas de nouveau start dans les 10 j


def compression_progress_score(df: pd.DataFrame) -> pd.DataFrame:
    """Renommage conceptuel de l'ancien trigger V106 -> score d'AVANCEMENT (descriptif)."""
    tr = compute_trigger_score(df).rename(columns={
        "compression_trigger_score": "compression_progress_score",
        "compression_trigger": "compression_progress",
    })
    return tr


def start_events(df: pd.DataFrame, drop_z: float = DROP_Z, peak_win: int = PEAK_WIN,
                 lockout: int = LOCKOUT) -> pd.Series:
    """1 le jour d'un DÉBUT de compression (déf. A, anti-rebond). Causal (pic glissant trailing)."""
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    trailing_peak = bz.rolling(peak_win, min_periods=3).max()
    is_drop = (trailing_peak - bz) >= drop_z
    ev = pd.Series(0, index=df.index)
    last = -10**9
    bz_vals = bz.to_numpy()
    drop_vals = is_drop.to_numpy()
    for i in range(len(df)):
        if i - last <= lockout:
            continue
        if bool(drop_vals[i]) and not np.isnan(bz_vals[i]):
            ev.iloc[i] = 1
            last = i
    return ev


def start_label(df: pd.DataFrame, horizon: int, lockout: int = LOCKOUT) -> pd.Series:
    """START_h{H} : un start_event dans [t+1,t+H] ET pas de start récent dans [t-lockout,t] (ex-ante)."""
    ev = start_events(df).to_numpy()
    n = len(ev)
    out = np.full(n, np.nan)
    for i in range(n):
        already = ev[max(0, i - lockout):i + 1].sum() > 0
        if already:
            out[i] = 0.0  # déjà parti -> pas un « départ futur »
            continue
        if i + 1 < n:
            fut = ev[i + 1:min(n, i + 1 + horizon)].sum() > 0
            out[i] = 1.0 if fut else 0.0
    return pd.Series(out, index=df.index)


def inprog_label(df: pd.DataFrame, horizon: int, drop_z: float = DROP_Z) -> pd.Series:
    """INPROG_h{H} : basis_z baisse d'au moins drop_z (cumulé) dans [t+1,t+H] (compression additionnelle)."""
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    fwd_min = pd.Series(
        [bz.iloc[i + 1:i + 1 + horizon].min() if i + 1 < len(bz) else np.nan for i in range(len(bz))],
        index=bz.index)
    return ((bz - fwd_min) >= drop_z).astype(float)


def _oof_auc(x: pd.DataFrame, y: pd.Series, horizon: int) -> tuple[float | None, int]:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler
    m = x.notna().all(axis=1) & y.notna()
    xv, yv = x[m], y[m].astype(int)
    if len(yv) < 120 or yv.nunique() < 2:
        return None, int(len(yv))
    pred = np.full(len(yv), np.nan)
    for tr, te in TimeSeriesSplit(n_splits=5).split(xv):
        tr = tr[: max(0, len(tr) - horizon)]   # embargo = horizon
        if len(tr) < 60 or yv.iloc[tr].nunique() < 2:
            continue
        sc = StandardScaler().fit(xv.iloc[tr])
        clf = LogisticRegression(max_iter=500).fit(sc.transform(xv.iloc[tr]), yv.iloc[tr])
        pred[te] = clf.predict_proba(sc.transform(xv.iloc[te]))[:, 1]
    ok = ~np.isnan(pred)
    if ok.sum() < 60 or len(np.unique(yv[ok])) < 2:
        return None, int(ok.sum())
    return float(roc_auc_score(yv[ok], pred[ok])), int(ok.sum())


def run_v153(df: pd.DataFrame, horizon: int = 10) -> dict[str, Any]:
    """Compare START (prédictif, panel non-déjà-parti) vs IN_PROGRESS (descriptif) en OOF purgé."""
    f = trigger_features(df)
    active = f["basis_z"] >= 1.0
    feat_cols = ["bz_chg_3", "ema_minus_cbot_5", "wc_chg_10", "cbot_ret_5"]

    # univers START : jours actifs (le label encode déjà « pas déjà parti »)
    y_start = start_label(df, horizon)
    start_panel_mask = active
    xs = f[start_panel_mask][feat_cols]
    ys = y_start[start_panel_mask]
    start_base = round(float(ys.mean()), 3) if ys.notna().any() else None
    auc_start, n_start = _oof_auc(xs, ys, horizon)

    # univers IN_PROGRESS : tous les jours actifs
    y_inp = inprog_label(df, horizon)
    xi = f[active][feat_cols]
    yi = y_inp[active]
    inp_base = round(float(yi.mean()), 3) if yi.notna().any() else None
    auc_inp, n_inp = _oof_auc(xi, yi, horizon)

    start_beats_base = (auc_start is not None and auc_start >= 0.58)
    verdict = ("START_SCORE_PREDICTIVE_ADD_TO_REPORT" if start_beats_base
               else "START_TIMING_REMAINS_HARD_DESCRIPTIVE_ONLY")

    out = {
        "version": "V153-START-VS-INPROGRESS",
        "horizon_days": horizon, "drop_z": DROP_Z, "lockout_days": LOCKOUT,
        "rename": {"old": "COMPRESSION_TRIGGER_SCORE", "descriptive_now": "COMPRESSION_PROGRESS_SCORE",
                   "predictive_target": "START_TRIGGER_SCORE"},
        "n_start_events": int(start_events(df).sum()),
        "START": {"n_oof": n_start, "base_rate": start_base,
                  "oof_auc": round(auc_start, 3) if auc_start is not None else None},
        "INPROG": {"n_oof": n_inp, "base_rate": inp_base,
                   "oof_auc": round(auc_inp, 3) if auc_inp is not None else None},
        "verdict": verdict,
        "interpretation": (
            "START = départ FUTUR (panel non-déjà-parti) ; IN_PROGRESS = compression additionnelle. "
            "Si AUC(START) ne bat pas franchement son base rate, le TIMING du départ reste difficile "
            "(cohérent V106/V35) et le score reste DESCRIPTIF. Aucune fusion avec la baseline figée."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V153_DIR / "v153_start_vs_inprogress.json").write_text(json.dumps(out, indent=2, default=str),
                                                            encoding="utf-8")
    return out
