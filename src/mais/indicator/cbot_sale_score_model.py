"""Modèles parcimonieux du score de vente (étape 7).

Un logit L2 par horizon (H40 = WASDE stocks-to-use ; H90 = Crop Condition), plus une
prévision de volatilité HAR et un gate « décile haut de vol ». Tout est entraîné/calibré sur
**les données ≤ 2023 uniquement** (frontière holdout 2024+) : standardisation, imputation et
seuil de gate sont estimés sur le train et **gelés**. Cible directionnelle = vraie ligne de
marché `index[i+h]` (purge anti-fuite). Aucun tuning sur le holdout.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from mais.indicator import cbot_sale_score_features as feats


@dataclass
class FittedLogit:
    horizon: int
    cols: list[str]
    coef: np.ndarray
    intercept: float
    mean: np.ndarray
    sd: np.ndarray
    impute: np.ndarray
    base_rate: float
    n_train: int

    def predict_proba_up(self, df: pd.DataFrame) -> pd.Series:
        x = df[self.cols].to_numpy(float)
        x = np.where(np.isfinite(x), x, self.impute)
        xs = (x - self.mean) / self.sd
        z = xs @ self.coef + self.intercept
        return pd.Series(1.0 / (1.0 + np.exp(-z)), index=df.index)


def _train_mask(df: pd.DataFrame, h: int, holdout_start: pd.Timestamp,
                cols: list[str]) -> pd.Series:
    """Lignes d'entraînement : décision ET cible strictement avant le holdout, features ok."""
    tgt = feats.target_dates_from_index(df.index, h)
    y = feats.direction_target(df["corn_close"], h)
    ok = df[cols].notna().all(axis=1) & y.notna()
    return ok & (df.index < holdout_start) & (tgt < holdout_start).to_numpy()


def fit_logit(df: pd.DataFrame, cols: list[str], h: int,
              holdout_start: pd.Timestamp, c: float = 1.0) -> FittedLogit:
    mask = _train_mask(df, h, holdout_start, cols)
    tr = df[mask]
    y = feats.direction_target(df["corn_close"], h)[mask].to_numpy(int)
    x = tr[cols].to_numpy(float)
    impute = np.nanmedian(x, axis=0)
    x = np.where(np.isfinite(x), x, impute)
    mean, sd = x.mean(0), x.std(0)
    sd[sd == 0] = 1.0
    model = LogisticRegression(C=c, max_iter=1000)
    model.fit((x - mean) / sd, y)
    return FittedLogit(h, list(cols), model.coef_.ravel(), float(model.intercept_[0]),
                       mean, sd, impute, float(y.mean()), int(mask.sum()))


def walk_forward_proba(df: pd.DataFrame, cols: list[str], h: int,
                       holdout_start: pd.Timestamp, eval_start: pd.Timestamp,
                       min_train: int, c: float = 1.0) -> dict:
    """DA pré-2024 walk-forward (contexte recherche, PAS le holdout)."""
    tgt = feats.target_dates_from_index(df.index, h)
    y = feats.direction_target(df["corn_close"], h)
    ok = df[cols].notna().all(axis=1) & y.notna()
    sub = df[ok & (df.index < holdout_start) & (tgt < holdout_start).to_numpy()].copy()
    suby = y[sub.index]
    subtgt = tgt[sub.index]
    dates, ytrue, prob = [], [], []
    for yr in range(max(eval_start.year, sub.index[0].year + 3), holdout_start.year):
        bound = pd.Timestamp(f"{yr}-01-01")
        nxt = pd.Timestamp(f"{yr + 1}-01-01")
        tr = sub[subtgt < bound]
        te = sub[(sub.index >= bound) & (sub.index < nxt)]
        if len(tr) < min_train or len(te) == 0 or suby[tr.index].nunique() < 2:
            continue
        xtr = tr[cols].to_numpy(float)
        med = np.nanmedian(xtr, 0)
        xtr = np.where(np.isfinite(xtr), xtr, med)
        mu, sd = xtr.mean(0), xtr.std(0)
        sd[sd == 0] = 1.0
        model = LogisticRegression(C=c, max_iter=1000)
        model.fit((xtr - mu) / sd, suby[tr.index].to_numpy(int))
        xte = te[cols].to_numpy(float)
        xte = np.where(np.isfinite(xte), xte, med)
        prob.extend(model.predict_proba((xte - mu) / sd)[:, 1])
        ytrue.extend(suby[te.index].to_numpy(int))
        dates.extend(te.index)
    return {"dates": np.array(dates), "y_true": np.array(ytrue), "prob_up": np.array(prob)}


HAR_COLS = ["rv_w", "rv_m", "rv_q"]


def har_train_mask(df: pd.DataFrame, h: int, holdout_start: pd.Timestamp) -> pd.Series:
    """Lignes d'entraînement HAR : la VRAIE date de la vol future (index[i+h]) doit être
    strictement avant le holdout. Sans cette purge, des fenêtres de vol de fin 2023 (qui
    agrègent des retours de 2024) fuiteraient dans l'estimation (correction post-revue)."""
    yfut = feats.future_realized_vol(df["logret"], h)
    tgt = feats.target_dates_from_index(df.index, h)
    ok = df[HAR_COLS].notna().all(axis=1) & yfut.notna()
    return ok & (df.index < holdout_start) & (tgt < holdout_start).to_numpy()


def har_vol_forecast(df: pd.DataFrame, h: int,
                     holdout_start: pd.Timestamp) -> pd.Series:
    """Prévision HAR de la vol réalisée h-jours : OLS [1,rv_w,rv_m,rv_q] fit sur ≤2023, purgé."""
    yfut = feats.future_realized_vol(df["logret"], h)
    mask = har_train_mask(df, h, holdout_start)
    tr = df[mask]
    xtr = np.column_stack([np.ones(len(tr)), tr[HAR_COLS].to_numpy(float)])
    beta, *_ = np.linalg.lstsq(xtr, yfut[mask].to_numpy(float), rcond=None)
    xall = np.column_stack([np.ones(len(df)), df[HAR_COLS].to_numpy(float)])
    pred = np.clip(xall @ beta, 1e-9, None)
    return pd.Series(pred, index=df.index)


def frozen_vol_gate(pred_vol: pd.Series, holdout_start: pd.Timestamp,
                    q: float) -> float:
    """Seuil de gate = quantile q de la vol prévue sur ≤2023 (gelé)."""
    pre = pred_vol[pred_vol.index < holdout_start].dropna()
    return float(pre.quantile(q))


def dir_metrics(y_true: np.ndarray, prob_up: np.ndarray, thr: float = 0.5) -> dict:
    from sklearn.metrics import roc_auc_score
    y_true = np.asarray(y_true, float)
    pred = (prob_up >= thr).astype(int)
    n = len(y_true)
    if n == 0:
        return {"n": 0}
    acc = float((pred == y_true).mean())
    base = float(y_true.mean())
    maj = max(base, 1 - base)
    accs = [float((pred[y_true == cls] == cls).mean()) for cls in (0, 1) if (y_true == cls).any()]
    bacc = float(np.mean(accs)) if accs else np.nan
    brier = float(np.mean((prob_up - y_true) ** 2))
    try:
        auc = float(roc_auc_score(y_true, prob_up)) if len(np.unique(y_true)) > 1 else np.nan
    except Exception:
        auc = np.nan
    tp = int(((pred == 1) & (y_true == 1)).sum())
    fp = int(((pred == 1) & (y_true == 0)).sum())
    tn = int(((pred == 0) & (y_true == 0)).sum())
    fn = int(((pred == 0) & (y_true == 1)).sum())
    # rappels orientés VENTE : la classe "baisse" = 0
    prec_up = tp / (tp + fp) if (tp + fp) else np.nan
    rec_up = tp / (tp + fn) if (tp + fn) else np.nan
    prec_dn = tn / (tn + fn) if (tn + fn) else np.nan
    rec_dn = tn / (tn + fp) if (tn + fp) else np.nan
    return {"n": n, "da": acc, "base_rate": base, "majority_acc": maj,
            "da_vs_majority": acc - maj, "balanced_acc": bacc, "roc_auc": auc, "brier": brier,
            "precision_up": prec_up, "recall_up": rec_up,
            "precision_down": prec_dn, "recall_down": rec_dn,
            "tp": tp, "fp": fp, "tn": tn, "fn": fn}
