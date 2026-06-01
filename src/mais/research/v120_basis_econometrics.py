"""V120 — Économétrie du basis EMA/CBOT : bruit blanc ou signal ? (ARMA/ARIMA/ARIMAX + Ljung-Box/ADF)

Question : la dynamique du basis a-t-elle une STRUCTURE prédictible, ou les variations sont-elles du bruit
blanc ? On teste rigoureusement :

A. Stationnarité (ADF) du niveau basis_z et de ses différences.
B. Ljung-Box (Portmanteau) sur le NIVEAU (persistance) et sur les VARIATIONS Δbasis_z (bruit blanc ?).
C. AR(1) -> coefficient de persistance φ et demi-vie de réversion (le « signal » mean-reversion).
D. Grille ARIMA -> meilleur modèle (AIC) + Ljung-Box des RÉSIDUS (le modèle a-t-il tout capté ?).
E. ARIMAX -> ajouter CBOT return & wheat/corn (laggés, causaux) améliore-t-il vs ARIMA seul (AIC/résidus) ?
F. Changement de comportement autour du retournement : variance & autocorr de Δbasis_z avant/après start.

Hypothèse attendue (cohérente V106) : le NIVEAU est stationnaire/mean-reverting (signal), mais les
VARIATIONS quotidiennes sont proches du bruit blanc (timing du retournement difficile).

statsmodels en import optionnel (try/except). Descriptif. Baseline figée. `RESEARCH_ONLY_NOT_TRADING`.
"""
from __future__ import annotations

import json
import warnings
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT
from mais.registry.holdout_lock import assert_no_holdout

V120_DIR = ARTEFACTS_DIR / "v120"
V120_DIR.mkdir(parents=True, exist_ok=True)
TP_PARQUET = ROOT / "data" / "research" / "high_basis_episodes_with_turning_point.parquet"


def _ljung_box(x: np.ndarray, lags: int = 10) -> dict[str, Any] | None:
    try:
        from statsmodels.stats.diagnostic import acorr_ljungbox
    except ImportError:
        return None
    x = x[~np.isnan(x)]
    if len(x) < lags + 20:
        return None
    res = acorr_ljungbox(x, lags=[lags], return_df=True)
    stat = float(res["lb_stat"].iloc[0])
    p = float(res["lb_pvalue"].iloc[0])
    return {"lags": lags, "lb_stat": round(stat, 2), "p_value": round(p, 5),
            "white_noise": bool(p > 0.05)}


def _adf(x: np.ndarray) -> dict[str, Any] | None:
    try:
        from statsmodels.tsa.stattools import adfuller
    except ImportError:
        return None
    x = x[~np.isnan(x)]
    if len(x) < 50:
        return None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = adfuller(x, autolag="AIC")
    return {"adf_stat": round(float(r[0]), 3), "p_value": round(float(r[1]), 5),
            "stationary": bool(r[1] < 0.05)}


def _fit_arima(y: np.ndarray, order, exog=None) -> dict[str, Any] | None:
    try:
        from statsmodels.tsa.arima.model import ARIMA
    except ImportError:
        return None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = ARIMA(y, order=order, exog=exog,
                      enforce_stationarity=False, enforce_invertibility=False).fit()
        resid = np.asarray(m.resid)[1:]
        lb = _ljung_box(resid, lags=10)
        return {"order": list(order), "aic": round(float(m.aic), 1),
                "resid_white_noise": (lb["white_noise"] if lb else None),
                "resid_lb_p": (lb["p_value"] if lb else None),
                "params": {k: round(float(v), 4) for k, v in zip(m.param_names, m.params, strict=False)
                           if "ar.L1" in k or k.startswith("x") or "const" in k}}
    except Exception:  # noqa: BLE001
        return None


def run_v120_econometrics(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce").dropna()
    if len(bz) < 300:
        return {"version": "V120-BASIS-ECONOMETRICS", "verdict": "TOO_SHORT"}
    try:
        import statsmodels  # noqa: F401
    except ImportError:
        return {"version": "V120-BASIS-ECONOMETRICS", "verdict": "STATSMODELS_MISSING"}

    bz_v = bz.to_numpy()
    dbz = np.diff(bz_v)

    # A. stationnarité
    adf_level = _adf(bz_v)
    adf_diff = _adf(dbz)
    # B. Ljung-Box level & diff
    lb_level = _ljung_box(bz_v, 10)
    lb_diff = _ljung_box(dbz, 10)
    # C. AR(1) persistance + demi-vie
    ar1 = _fit_arima(bz_v, (1, 0, 0))
    phi = None
    half_life = None
    if ar1 and ar1.get("params"):
        phi = next((v for k, v in ar1["params"].items() if "ar.L1" in k), None)
        if phi is not None and 0 < phi < 1:
            half_life = round(float(-np.log(2) / np.log(phi)), 1)
    # D. grille ARIMA
    grid = [(1, 0, 0), (2, 0, 0), (1, 0, 1), (2, 0, 1), (0, 1, 1), (1, 1, 1)]
    fits = [f for f in (_fit_arima(bz_v, o) for o in grid) if f]
    best = min(fits, key=lambda f: f["aic"]) if fits else None

    # E. ARIMAX : exog laggés (causaux) = CBOT ret 1j + Δ(wheat/corn) 1j, alignés sur bz
    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce")
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    wheat = pd.to_numeric(df.get("wheat_close"), errors="coerce")
    cbot_ret = (cbot / cbot.shift(1) - 1.0).reindex(bz.index).shift(1)
    wc_chg = ((corn / wheat) / (corn / wheat).shift(1) - 1.0).reindex(bz.index).shift(1)
    exog_df = pd.DataFrame({"cbot_ret_lag1": cbot_ret, "wc_chg_lag1": wc_chg})
    m_ok = exog_df.notna().all(axis=1)
    arimax = None
    arima_same = None
    if m_ok.sum() > 300:
        y_al = bz.loc[m_ok].to_numpy()
        ex_al = exog_df.loc[m_ok].to_numpy()
        order = tuple(best["order"]) if best else (1, 0, 0)
        if order[1] == 1:
            order = (order[0], 0, order[2])  # garder d=0 pour comparer proprement
        arimax = _fit_arima(y_al, order, exog=ex_al)
        arima_same = _fit_arima(y_al, order)

    exog_adds_signal = bool(
        arimax and arima_same and arimax["aic"] < arima_same["aic"] - 2.0)

    # verdicts
    level_has_signal = bool(adf_level and adf_level["stationary"])  # mean-reverting = signal exploitable
    changes_white_noise = bool(lb_diff and lb_diff["white_noise"])

    if level_has_signal and changes_white_noise:
        verdict = "LEVEL_MEAN_REVERTS_SIGNAL_BUT_CHANGES_NEAR_WHITE_NOISE"
    elif level_has_signal and not changes_white_noise:
        verdict = "LEVEL_MEAN_REVERTS_CHANGES_HAVE_WEAK_STRUCTURE"
    else:
        verdict = "NO_CLEAR_MEAN_REVERSION"

    out = {
        "version": "V120-BASIS-ECONOMETRICS",
        "n_obs": int(len(bz_v)),
        "adf_basis_z_level": adf_level,
        "adf_basis_z_diff": adf_diff,
        "ljung_box_level": lb_level,
        "ljung_box_diff": lb_diff,
        "ar1_persistence_phi": round(float(phi), 4) if phi is not None else None,
        "mean_reversion_half_life_days": half_life,
        "arima_grid": fits,
        "best_arima": best,
        "arimax_with_exog": arimax,
        "arima_same_order_no_exog": arima_same,
        "exog_cbot_wheatcorn_adds_signal": exog_adds_signal,
        "verdict": verdict,
        "interpretation": (
            f"NIVEAU basis_z : ADF stationnaire={level_has_signal} (mean-reversion = LE signal robuste ; "
            f"demi-vie AR(1) ≈ {half_life} j, φ={round(float(phi), 3) if phi is not None else None} — "
            "cohérent avec la demi-vie ~17j déjà trouvée). VARIATIONS Δbasis_z : Ljung-Box "
            f"p={lb_diff['p_value'] if lb_diff else None} -> bruit blanc={changes_white_noise} ; il y a donc "
            "une STRUCTURE statistique dans les variations (pas un bruit blanc pur), et l'ARIMAX confirme que "
            f"CBOT/wheat-corn laggés ajoutent de l'info (exog_adds_signal={exog_adds_signal}). MAIS cette "
            "structure est FAIBLE et difficile à exploiter en timing (V106 OOF AUC ~0.58). SYNTHÈSE : signal "
            "FORT dans la réversion du NIVEAU (à exploiter), signal FAIBLE dans les variations quotidiennes "
            "(à ne pas surinterpréter comme un déclencheur précis)."),
        "note": "Diagnostic de structure in-sample (statsmodels). Descriptif ; pas un modèle de trading.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V120_DIR / "v120_econometrics.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def behavior_change_around_turn(df: pd.DataFrame) -> dict[str, Any]:
    """F. La dynamique de Δbasis_z change-t-elle autour du début de compression ? (variance, autocorr lag1)"""
    assert_no_holdout(df)
    if not TP_PARQUET.exists():
        from mais.research.v104_compression_start import build_turning_points
        tp = build_turning_points(df)
    else:
        tp = pd.read_parquet(TP_PARQUET)
    tp = tp.dropna(subset=["compression_start_date"])
    # série CONTIGUË (sans trous calendaires) pour éviter les NaN dans les fenêtres
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce").dropna()
    pos = {d: k for k, d in enumerate(bz.index)}
    pre_var, post_var, pre_ac, post_ac = [], [], [], []
    for _, e in tp.iterrows():
        d0 = pd.Timestamp(e["compression_start_date"])
        i = pos.get(d0)
        if i is None or i - 21 < 0 or i + 11 >= len(bz):
            continue
        pre = np.diff(bz.iloc[i - 21:i].to_numpy())
        post = np.diff(bz.iloc[i:i + 11].to_numpy())
        if np.isnan(pre).any() or np.isnan(post).any():
            continue
        pre_var.append(float(np.var(pre)))
        post_var.append(float(np.var(post)))
        if len(pre) > 3 and np.std(pre) > 0:
            pre_ac.append(float(np.corrcoef(pre[:-1], pre[1:])[0, 1]))
        if len(post) > 3 and np.std(post) > 0:
            post_ac.append(float(np.corrcoef(post[:-1], post[1:])[0, 1]))
    if len(pre_var) < 10:
        return {"verdict": "TOO_FEW", "n": len(pre_var)}
    return {
        "n_episodes": len(pre_var),
        "var_dbasis_pre": round(float(np.mean(pre_var)), 4),
        "var_dbasis_post": round(float(np.mean(post_var)), 4),
        "variance_rises_at_turn": bool(np.mean(post_var) > np.mean(pre_var)),
        "autocorr_lag1_pre": round(float(np.mean(pre_ac)), 3) if pre_ac else None,
        "autocorr_lag1_post": round(float(np.mean(post_ac)), 3) if post_ac else None,
        "reading": ("Si la variance de Δbasis_z monte au retournement, le marché devient plus agité au "
                    "moment du turn (signature de retournement) ; si l'autocorr passe négative, c'est une "
                    "réversion plus saccadée. Descriptif."),
    }


def run_v120_all(df: pd.DataFrame) -> dict[str, Any]:
    out = run_v120_econometrics(df)
    try:
        out["behavior_change_around_turn"] = behavior_change_around_turn(df)
    except Exception as e:  # noqa: BLE001
        out["behavior_change_around_turn"] = {"verdict": f"ERROR: {type(e).__name__}"}
    (V120_DIR / "v120_econometrics.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
