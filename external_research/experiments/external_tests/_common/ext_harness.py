"""Harnais commun des experiences P1 (etape 4).

Question unique posee a chaque famille fondamentale : ajoutee a un modele de
marche minimal (BASE), apporte-t-elle un gain robuste sur le log-retour CBOT
t -> t+h ? Protocole : walk-forward expandant, refit annuel, Ridge alpha fixe
ex ante, standardisation + imputation estimees sur le TRAIN uniquement.

Anti-fuite (anti_leak_rules.md) :
- chaque famille est fournie deja datee a sa disponibilite reelle ;
- standardisation/imputation jamais sur tout le dataset (train-only) ;
- aucune selection de variable globale ; refit annuel purge (target_date du
  train strictement anterieure a la frontiere de prediction) ;
- holdout 2024+ exclu de toute evaluation (regle 12).

Comparaison : BASE vs BASE+FAMILLE. Reference absolue = RW (pred 0 sur le
log-retour) reportee dans EXT025.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "data"
RESULTS = ROOT / "external_research" / "results" / "external_tests"

HORIZONS = [5, 20, 40, 90]
ALPHA = 10.0                       # fixe ex ante, aucun tuning
MIN_TRAIN = 750                    # ~3 ans avant la 1re prediction
HOLDOUT_START = pd.Timestamp("2024-01-01")
EVAL_START = pd.Timestamp("2008-01-01")


def load_market() -> pd.DataFrame:
    """CBOT quotidien + features de marche BASE. Index = Date (datetime)."""
    m = pd.read_parquet(DATA / "interim" / "market.parquet")
    m["Date"] = pd.to_datetime(m["Date"])
    m = m.sort_values("Date").set_index("Date")
    px = m["corn_close"].astype(float)
    logp = np.log(px)
    out = pd.DataFrame(index=m.index)
    out["corn_close"] = px
    out["base_ret_5d"] = logp.diff(5)
    out["base_ret_20d"] = logp.diff(20)
    out["base_vol_20"] = logp.diff().rolling(20).std()
    doy = out.index.dayofyear.to_numpy()
    out["base_sin"] = np.sin(2 * np.pi * doy / 365.25)
    out["base_cos"] = np.cos(2 * np.pi * doy / 365.25)
    return out


BASE_COLS = ["base_ret_5d", "base_ret_20d", "base_vol_20", "base_sin", "base_cos"]


def make_target(px: pd.Series, h: int) -> pd.Series:
    """Log-retour t -> t+h, indexe sur t (date de decision)."""
    logp = np.log(px)
    return logp.shift(-h) - logp


def target_dates_from_index(index: pd.DatetimeIndex, h: int) -> pd.Series:
    """Vraie date de la cible a horizon h : index[i+h] (lignes de marche),
    PAS index[i] + h jours calendaires. La cible est shift(-h) sur des lignes
    de marche ; ~252 seances/an => h lignes ~ 1.45*h jours calendaires. Utiliser
    les jours calendaires sous-estimait la date cible de ~45% et laissait des
    decisions de fin 2023 dont la cible reelle tombe en 2024 entrer dans
    l'evaluation (fuite holdout). Corrige a l'etape 5 bis."""
    return pd.Series(index, index=index).shift(-h)


def _dm_test(e1: np.ndarray, e2: np.ndarray, h: int) -> tuple[float, float]:
    """Diebold-Mariano sur perte quadratique, variance HAC (lag h-1).
    d = loss_base - loss_fam ; DM>0 et p faible => famille meilleure."""
    d = e1 ** 2 - e2 ** 2
    d = d[np.isfinite(d)]
    n = len(d)
    if n < 30:
        return np.nan, np.nan
    dbar = d.mean()
    lag = max(h - 1, 0)
    gamma0 = np.var(d, ddof=0)
    var = gamma0
    for k in range(1, lag + 1):
        if k >= n:
            break
        w = 1.0 - k / (lag + 1.0)
        cov = np.cov(d[k:], d[:-k], ddof=0)[0, 1]
        var += 2.0 * w * cov
    if var <= 0:
        return np.nan, np.nan
    dm = dbar / np.sqrt(var / n)
    from scipy.stats import norm
    p = 2.0 * (1.0 - norm.cdf(abs(dm)))
    return float(dm), float(p)


def _balanced_acc(y_true_sign: np.ndarray, y_pred_sign: np.ndarray) -> float:
    accs = []
    for cls in (-1, 1):
        m = y_true_sign == cls
        if m.sum() == 0:
            continue
        accs.append((y_pred_sign[m] == cls).mean())
    return float(np.mean(accs)) if accs else np.nan


def _metrics(actual: np.ndarray, pred: np.ndarray) -> dict:
    err = pred - actual
    rmse = float(np.sqrt(np.mean(err ** 2)))
    mae = float(np.mean(np.abs(err)))
    ss_res = np.sum(err ** 2)
    ss_tot = np.sum((actual - actual.mean()) ** 2)
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else np.nan
    st, sp = np.sign(actual), np.sign(pred)
    da = float(np.mean(st == sp))
    bacc = _balanced_acc(st, sp)
    up = st > 0
    hit = float(np.mean(sp[up] > 0)) if up.sum() else np.nan
    return {"rmse": rmse, "mae": mae, "r2": r2, "da": da,
            "balanced_acc": bacc, "hit_ratio_up": hit, "n": int(len(actual))}


def _walk_forward(X: pd.DataFrame, y: pd.Series, cols: list[str], h: int,
                  eval_start: pd.Timestamp):
    """Refit annuel expandant. Retourne (dates, actual, pred, importance)."""
    df = X[cols].copy()
    df["__y"] = y
    df["__tgt_date"] = target_dates_from_index(X.index, h)  # vraie date i+h (5bis)
    df = df.dropna(subset=cols + ["__y"])
    df = df[df.index < HOLDOUT_START]
    df = df[df["__tgt_date"] < HOLDOUT_START]
    if len(df) < MIN_TRAIN + 60:
        return None

    years = range(max(eval_start.year, df.index[0].year + 3), HOLDOUT_START.year)
    dates, actual, pred = [], [], []
    coefs = []
    for yr in years:
        bound = pd.Timestamp(f"{yr}-01-01")
        nxt = pd.Timestamp(f"{yr + 1}-01-01")
        train = df[df["__tgt_date"] < bound]            # purge: cible realisee avant
        test = df[(df.index >= bound) & (df.index < nxt)]
        if len(train) < MIN_TRAIN or len(test) == 0:
            continue
        Xtr = train[cols].to_numpy(float)
        ytr = train["__y"].to_numpy(float)
        mu = np.nanmedian(Xtr, axis=0)
        Xtr = np.where(np.isfinite(Xtr), Xtr, mu)
        m = Xtr.mean(0)
        sd = Xtr.std(0)
        sd[sd == 0] = 1.0
        Xtr_s = (Xtr - m) / sd
        model = Ridge(alpha=ALPHA)
        model.fit(Xtr_s, ytr)
        coefs.append(np.abs(model.coef_))
        Xte = test[cols].to_numpy(float)
        Xte = np.where(np.isfinite(Xte), Xte, mu)
        Xte_s = (Xte - m) / sd
        yhat = model.predict(Xte_s)
        dates.extend(test.index)
        actual.extend(test["__y"].to_numpy(float))
        pred.extend(yhat)
    if not dates:
        return None
    imp = dict(zip(cols, np.mean(coefs, axis=0), strict=False)) if coefs else {}
    return (np.array(dates), np.array(actual), np.array(pred), imp)


def evaluate_family(exp_id: str, results_dir_name: str,
                    fam_features: pd.DataFrame, fam_cols: list[str],
                    horizons=HORIZONS, eval_start=EVAL_START,
                    feature_dictionary: dict | None = None,
                    notes: str = "") -> pd.DataFrame:
    """Evalue BASE vs BASE+FAMILLE et ecrit les CSV standard.

    fam_features : DataFrame indexe Date, deja date a sa disponibilite reelle,
    aligne sur le calendrier marche par reindex+ffill par l'appelant ou ici.
    """
    out_dir = RESULTS / results_dir_name
    out_dir.mkdir(parents=True, exist_ok=True)

    mkt = load_market()
    fam = fam_features.reindex(mkt.index).ffill()
    X = mkt.join(fam[fam_cols])

    metric_rows, comp_rows, imp_rows = [], [], []
    for h in horizons:
        y = make_target(mkt["corn_close"], h)
        base = _walk_forward(X, y, BASE_COLS, h, eval_start)
        full = _walk_forward(X, y, BASE_COLS + fam_cols, h, eval_start)
        if base is None or full is None:
            continue
        # aligner sur dates communes
        db, ab, pb, _ = base
        dfu, af, pf, impf = full
        common = np.intersect1d(db, dfu)
        if len(common) < 30:
            continue
        bi = np.isin(db, common)
        fi = np.isin(dfu, common)
        mb = _metrics(ab[bi], pb[bi])
        mf = _metrics(af[fi], pf[fi])
        dm, p = _dm_test(pb[bi] - ab[bi], pf[fi] - af[fi], h)
        for tag, mm in (("BASE", mb), ("BASE+FAM", mf)):
            metric_rows.append({"experiment": exp_id, "horizon": h, "model": tag, **mm})
        metric_rows.append({"experiment": exp_id, "horizon": h, "model": "DELTA",
                            "rmse": mf["rmse"] - mb["rmse"],
                            "mae": mf["mae"] - mb["mae"],
                            "r2": mf["r2"] - mb["r2"],
                            "da": mf["da"] - mb["da"],
                            "balanced_acc": mf["balanced_acc"] - mb["balanced_acc"],
                            "hit_ratio_up": (mf["hit_ratio_up"] - mb["hit_ratio_up"]),
                            "n": mf["n"], "dm_stat": dm, "dm_pvalue": p,
                            "rmse_pct": (mf["rmse"] - mb["rmse"]) / mb["rmse"] * 100})
        # stabilite : 2 sous-periodes
        d_common = np.array(sorted(common))
        mid = d_common[len(d_common) // 2]
        for label, mask_fn in (("first_half", lambda d, m=mid: d < m),
                               ("second_half", lambda d, m=mid: d >= m)):
            for tag, (dd, aa, pp, _ok) in (("BASE", base), ("BASE+FAM", full)):
                sel = np.isin(dd, common) & mask_fn(dd)
                if sel.sum() < 20:
                    continue
                mm = _metrics(aa[sel], pp[sel])
                comp_rows.append({"experiment": exp_id, "horizon": h,
                                  "period": label, "model": tag, **mm})
        for c, v in impf.items():
            imp_rows.append({"experiment": exp_id, "horizon": h,
                             "feature": c, "abs_coef": v,
                             "is_family": c in fam_cols})

    met = pd.DataFrame(metric_rows)
    met.to_csv(out_dir / f"metrics_{exp_id}.csv", index=False)
    pd.DataFrame(comp_rows).to_csv(out_dir / f"comparison_{exp_id}.csv", index=False)
    pd.DataFrame(imp_rows).to_csv(out_dir / f"importance_{exp_id}.csv", index=False)
    feats = X[fam_cols].dropna(how="all")
    feats.to_csv(out_dir / f"features_{exp_id}.csv")
    if feature_dictionary:
        pd.DataFrame([{"feature": k, "description": v}
                      for k, v in feature_dictionary.items()]).to_csv(
            out_dir / f"{exp_id}_feature_dictionary.csv", index=False)
    return met


def verdict_from_delta(met: pd.DataFrame) -> str:
    """KEEP/IMPROVE/REJECT selon les criteres du plan (ext_harness).

    Direction-aware : dm_stat>0 ET rmse_pct<0 = famille meilleure. Une
    significativite DM avec rmse_pct>0 signifie famille SIGNIFICATIVEMENT pire.
    """
    d = met[met["model"] == "DELTA"]
    if d.empty:
        return "REJECT"
    better = (d["dm_stat"] > 0) & (d["dm_pvalue"] < 0.10) & (d["rmse_pct"] < 0)
    keep = better & (d["da"] > 0.02)
    if keep.any():
        return "KEEP_CANDIDATE"  # a confirmer par stabilite 2 sous-periodes
    soft = ((d["da"] > 0.01) & (d["rmse_pct"] < 0.3)) | better
    if soft.any():
        return "IMPROVE"
    return "REJECT"
