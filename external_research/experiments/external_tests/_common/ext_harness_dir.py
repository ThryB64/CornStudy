"""Harnais directionnel commun (étape 5, P2).

Cible = SIGNE du log-retour CBOT t→t+h (1=hausse, 0=baisse). Walk-forward
expandant, refit annuel purgé, standardisation/imputation train-only, holdout
2024+ exclu. Modèles à `predict_proba` (LogReg L2 par défaut). Métriques :
DA, balanced accuracy, ROC-AUC, Brier, précision/rappel UP&DOWN, matrice de
confusion, calibration, stabilité 2 sous-périodes, test binomial vs classe
majoritaire, bootstrap par blocs de la DA.

L'objectif de l'étape 5 est la DIRECTION/risque, pas le RMSE.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from ext_harness import (  # noqa: F401
    BASE_COLS,
    HOLDOUT_START,
    RESULTS,
    load_market,
    target_dates_from_index,
)
from scipy.stats import binomtest
from sklearn.linear_model import LogisticRegression

MIN_TRAIN = 750
EVAL_START = pd.Timestamp("2008-01-01")


def logret_target(px: pd.Series, h: int) -> pd.Series:
    logp = np.log(px)
    return logp.shift(-h) - logp


def default_logit():
    return LogisticRegression(C=1.0, max_iter=1000)  # L2 par défaut


def walk_forward_clf(X: pd.DataFrame, r_cont: pd.Series, cols: list[str], h: int,
                     make_model=default_logit, eval_start=EVAL_START,
                     min_train=MIN_TRAIN):
    """Refit annuel expandant. Retourne dict(dates, y_true, prob_up, coef)."""
    df = X[cols].copy()
    df["__r"] = r_cont
    df["__tgt"] = target_dates_from_index(X.index, h)  # vraie date i+h (5bis)
    df = df.dropna(subset=cols + ["__r"])
    df = df[(df.index < HOLDOUT_START) & (df["__tgt"] < HOLDOUT_START)]
    df["__y"] = (df["__r"] > 0).astype(int)
    if len(df) < min_train + 60:
        return None

    years = range(max(eval_start.year, df.index[0].year + 3), HOLDOUT_START.year)
    dates, ytrue, prob, coefs = [], [], [], []
    for yr in years:
        bound = pd.Timestamp(f"{yr}-01-01")
        nxt = pd.Timestamp(f"{yr + 1}-01-01")
        tr = df[df["__tgt"] < bound]
        te = df[(df.index >= bound) & (df.index < nxt)]
        if len(tr) < min_train or len(te) == 0 or tr["__y"].nunique() < 2:
            continue
        Xtr = tr[cols].to_numpy(float)
        med = np.nanmedian(Xtr, axis=0)
        Xtr = np.where(np.isfinite(Xtr), Xtr, med)
        m, sd = Xtr.mean(0), Xtr.std(0)
        sd[sd == 0] = 1.0
        Xtr_s = (Xtr - m) / sd
        model = make_model()
        model.fit(Xtr_s, tr["__y"].to_numpy(int))
        Xte = te[cols].to_numpy(float)
        Xte = np.where(np.isfinite(Xte), Xte, med)
        Xte_s = (Xte - m) / sd
        p = model.predict_proba(Xte_s)[:, 1]
        dates.extend(te.index)
        ytrue.extend(te["__y"].to_numpy(int))
        prob.extend(p)
        if hasattr(model, "coef_"):
            coefs.append(np.abs(model.coef_.ravel()))
    if not dates:
        return None
    imp = dict(zip(cols, np.mean(coefs, axis=0), strict=False)) if coefs else {}
    return dict(dates=np.array(dates), y_true=np.array(ytrue),
                prob_up=np.array(prob), coef=imp)


def _safe_auc(y, p):
    try:
        from sklearn.metrics import roc_auc_score
        return float(roc_auc_score(y, p)) if len(np.unique(y)) > 1 else np.nan
    except Exception:
        return np.nan


def dir_metrics(y_true: np.ndarray, prob_up: np.ndarray, thr=0.5) -> dict:
    pred = (prob_up >= thr).astype(int)
    n = len(y_true)
    acc = float((pred == y_true).mean())
    base_rate = float(y_true.mean())
    maj = max(base_rate, 1 - base_rate)        # accuracy d'un modèle classe-majoritaire
    # balanced accuracy
    accs = []
    for cls in (0, 1):
        msk = y_true == cls
        if msk.sum():
            accs.append((pred[msk] == cls).mean())
    bacc = float(np.mean(accs)) if accs else np.nan
    brier = float(np.mean((prob_up - y_true) ** 2))
    auc = _safe_auc(y_true, prob_up)
    tp = int(((pred == 1) & (y_true == 1)).sum())
    fp = int(((pred == 1) & (y_true == 0)).sum())
    tn = int(((pred == 0) & (y_true == 0)).sum())
    fn = int(((pred == 0) & (y_true == 1)).sum())
    prec_up = tp / (tp + fp) if (tp + fp) else np.nan
    rec_up = tp / (tp + fn) if (tp + fn) else np.nan
    prec_dn = tn / (tn + fn) if (tn + fn) else np.nan
    rec_dn = tn / (tn + fp) if (tn + fp) else np.nan
    # test binomial : la DA bat-elle la classe majoritaire ?
    n_correct = int((pred == y_true).sum())
    try:
        p_bin = binomtest(n_correct, n, maj, alternative="greater").pvalue
    except Exception:
        p_bin = np.nan
    return dict(n=n, da=acc, base_rate=base_rate, majority_acc=maj,
                da_vs_majority=acc - maj, balanced_acc=bacc, roc_auc=auc,
                brier=brier, precision_up=prec_up, recall_up=rec_up,
                precision_down=prec_dn, recall_down=rec_dn,
                tp=tp, fp=fp, tn=tn, fn=fn, p_binom_vs_majority=float(p_bin))


def block_bootstrap_da(y_true, pred, n_boot=1000, block=20, seed=0):
    rng = np.random.default_rng(seed)
    n = len(y_true)
    correct = (pred == y_true).astype(float)
    nblocks = int(np.ceil(n / block))
    das = []
    starts_max = max(n - block, 1)
    for _ in range(n_boot):
        idx = []
        for _ in range(nblocks):
            s = rng.integers(0, starts_max)
            idx.extend(range(s, min(s + block, n)))
        idx = np.array(idx[:n])
        das.append(correct[idx].mean())
    das = np.array(das)
    return float(np.percentile(das, 2.5)), float(np.percentile(das, 97.5))


def calibration_table(y_true, prob_up, bins=10) -> pd.DataFrame:
    df = pd.DataFrame({"y": y_true, "p": prob_up})
    df["bin"] = pd.qcut(df["p"], bins, labels=False, duplicates="drop")
    g = df.groupby("bin").agg(mean_pred=("p", "mean"), obs_freq=("y", "mean"),
                              n=("y", "size")).reset_index()
    return g


def subperiod_da(res: dict) -> dict:
    d = np.array(sorted(res["dates"]))
    mid = d[len(d) // 2]
    out = {}
    pred = (res["prob_up"] >= 0.5).astype(int)
    for label, msk in (("first_half", res["dates"] < mid),
                       ("second_half", res["dates"] >= mid)):
        if msk.sum() < 20:
            continue
        out[label] = float((pred[msk] == res["y_true"][msk]).mean())
    return out
