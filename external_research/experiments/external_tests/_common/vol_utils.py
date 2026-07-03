"""Utilitaires volatilité (EXT009 GARCH/EGARCH, EXT010 HAR).

Cible = volatilité réalisée h-jours forward : rv_h(t) = sqrt(sum_{i=1..h} r_{t+i}^2),
non annualisée. Prédicteurs/estimations en expandant strict (passé only). Comparaison :
RW de vol (rv_h passé), HAR, GARCH(1,1), EGARCH, GJR-GARCH. Métriques : RMSE/MAE de
vol, QLIKE sur la variance.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from ext_harness import HOLDOUT_START, load_market, target_dates_from_index


def daily_logret() -> pd.Series:
    px = load_market()["corn_close"].astype(float)
    return np.log(px).diff().dropna()


def future_rv(r: pd.Series, h: int) -> pd.Series:
    """Vol réalisée h-jours forward (indexée à t)."""
    r2 = r ** 2
    fwd = r2.shift(-1).rolling(h).sum().shift(-(h - 1))
    return np.sqrt(fwd)


def past_rv(r: pd.Series, window: int) -> pd.Series:
    return np.sqrt((r ** 2).rolling(window).sum())


def har_features(r: pd.Series) -> pd.DataFrame:
    """Composantes HAR : RV passées 5 / 22 / 66 jours (semaine/mois/trimestre)."""
    f = pd.DataFrame(index=r.index)
    f["rv_w"] = past_rv(r, 5)
    f["rv_m"] = past_rv(r, 22)
    f["rv_q"] = past_rv(r, 66)
    return f


def qlike(true_var: np.ndarray, pred_var: np.ndarray) -> float:
    """QLIKE = mean(log(pred_var) + true_var/pred_var). Plus bas = mieux."""
    eps = 1e-10
    pv = np.clip(pred_var, eps, None)
    return float(np.mean(np.log(pv) + true_var / pv))


def vol_metrics(true_vol: np.ndarray, pred_vol: np.ndarray) -> dict:
    err = pred_vol - true_vol
    rmse = float(np.sqrt(np.mean(err ** 2)))
    mae = float(np.mean(np.abs(err)))
    corr = float(np.corrcoef(true_vol, pred_vol)[0, 1]) if len(true_vol) > 2 else np.nan
    ql = qlike(true_vol ** 2, pred_vol ** 2)
    return dict(n=len(true_vol), rmse=rmse, mae=mae, corr=corr, qlike=ql)


EVAL_START = pd.Timestamp("2008-01-01")


def eval_index(r: pd.Series, h: int):
    """Dates d'évaluation : 2008→2023, cible définie, hors holdout."""
    idx = r.index
    tgt = target_dates_from_index(idx, h)  # vraie date i+h (5bis)
    mask = (idx >= EVAL_START) & (idx < HOLDOUT_START) & (tgt < HOLDOUT_START).to_numpy()
    return idx[mask]
