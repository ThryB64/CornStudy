"""V121 — Modèle PERFORMANT sur le basis_z (stationnaire) : bat-il le naïf, et reste-t-il du bruit blanc ?

V120 a montré : niveau stationnaire (mean-reversion, demi-vie ~17j) = signal ; variations à structure faible.
Ici on POUSSE le modèle : évaluation OUT-OF-SAMPLE walk-forward (fenêtre expandante, OLS récursif rapide) de
plusieurs modèles prédisant basis_z à h=1/5/10 :
  - RW   : marche aléatoire (prévision = dernière valeur)
  - MEAN : moyenne expandante (réversion totale instantanée)
  - AR1  : basis_z_t = c + φ·basis_z_{t-1}                      (réversion)
  - ARIMAX : AR1 + exog laggés (CBOT ret, Δwheat/corn, [ENSO])  (réversion + variables explicatives)
On mesure RMSE OOS + skill vs RW, la précision directionnelle, et la BLANCHEUR des résidus OOS (Ljung-Box) :
si le modèle est bon, il bat le naïf ET ses résidus sont ~bruit blanc.

OLS récursif (numpy) = rapide et strictement causal (chaque prévision n'utilise que le passé). statsmodels
seulement pour Ljung-Box (optionnel). Descriptif. Baseline figée. `RESEARCH_ONLY_NOT_TRADING`.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V121_DIR = ARTEFACTS_DIR / "v121"
V121_DIR.mkdir(parents=True, exist_ok=True)
MIN_TRAIN = 250


def _build(df: pd.DataFrame) -> pd.DataFrame:
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce")
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    wheat = pd.to_numeric(df.get("wheat_close"), errors="coerce")
    wc = corn / wheat
    d = pd.DataFrame({
        "bz": bz,
        "cbot_ret_lag1": (cbot / cbot.shift(1) - 1.0).shift(1),
        "wc_chg_lag1": (wc / wc.shift(1) - 1.0).shift(1),
        "bz_lag1": bz.shift(1),
    }).dropna()
    return d


def _ols(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    xb = np.column_stack([np.ones(len(x)), x])
    beta, *_ = np.linalg.lstsq(xb, y, rcond=None)
    return beta


def _walk_forward(d: pd.DataFrame, exog_cols: list[str], horizon: int) -> dict[str, np.ndarray]:
    """OLS récursif expandant : prédit bz à t+h. Retourne prédictions alignées + réalisé."""
    bz = d["bz"].to_numpy()
    lag1 = d["bz_lag1"].to_numpy()
    exog = d[exog_cols].to_numpy() if exog_cols else None
    n = len(d)
    preds = np.full(n, np.nan)
    real = np.full(n, np.nan)
    for t in range(MIN_TRAIN, n - horizon):
        # entraîne sur [0, t) : bz[k] ~ lag1[k] (+ exog[k])
        xtr = np.column_stack([lag1[:t], exog[:t]]) if exog is not None else lag1[:t].reshape(-1, 1)
        ytr = bz[:t]
        beta = _ols(xtr, ytr)
        # prévision h pas : itère l'AR (exog futur inconnu -> 0)
        z = bz[t - 1]
        for _ in range(horizon):
            row = [1.0, z] + ([0.0] * len(exog_cols) if exog_cols else [])
            z = float(np.dot(beta, row))
        preds[t + horizon - 1] = z
        real[t + horizon - 1] = bz[t + horizon - 1]
    ok = ~np.isnan(preds)
    return {"pred": preds[ok], "real": real[ok], "idx": np.where(ok)[0]}


def _rmse(pred: np.ndarray, real: np.ndarray) -> float:
    return float(np.sqrt(np.mean((pred - real) ** 2)))


def _ljung_box_white(resid: np.ndarray, lags: int = 10) -> bool | None:
    try:
        from statsmodels.stats.diagnostic import acorr_ljungbox
    except ImportError:
        return None
    r = resid[~np.isnan(resid)]
    if len(r) < lags + 20:
        return None
    p = float(acorr_ljungbox(r, lags=[lags], return_df=True)["lb_pvalue"].iloc[0])
    return bool(p > 0.05)


def run_v121_forecast(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    d = _build(df)
    if len(d) < MIN_TRAIN + 100:
        return {"version": "V121-BASIS-FORECAST", "verdict": "TOO_SHORT", "n": int(len(d))}

    bz = d["bz"].to_numpy()
    exp_mean = pd.Series(bz).expanding(min_periods=MIN_TRAIN).mean().to_numpy()

    results = {}
    for h in (1, 5, 10):
        ar = _walk_forward(d, [], h)
        ax = _walk_forward(d, ["cbot_ret_lag1", "wc_chg_lag1"], h)
        idx = ar["idx"]
        # benchmarks alignés sur les mêmes indices
        rw_pred = bz[idx - h]                      # marche aléatoire = valeur connue à t (h pas avant t+h-? )
        mean_pred = exp_mean[idx - h]
        real = ar["real"]
        rmse = {
            "RW": _rmse(rw_pred, real),
            "MEAN": _rmse(mean_pred[~np.isnan(mean_pred)], real[~np.isnan(mean_pred)]),
            "AR1": _rmse(ar["pred"], real),
            "ARIMAX": _rmse(ax["pred"], ax["real"]),
        }
        skill_ar = round(1 - rmse["AR1"] / rmse["RW"], 4)
        skill_ax = round(1 - rmse["ARIMAX"] / rmse["RW"], 4)
        # précision directionnelle (signe de la variation prévue vs réalisée), AR1
        dpred = ar["pred"] - bz[idx - h]
        dreal = real - bz[idx - h]
        da = float(np.mean(np.sign(dpred) == np.sign(dreal)))
        results[f"h{h}"] = {
            "rmse": {k: round(v, 4) for k, v in rmse.items()},
            "skill_AR1_vs_RW": skill_ar,
            "skill_ARIMAX_vs_RW": skill_ax,
            "exog_adds_oos": bool(rmse["ARIMAX"] < rmse["AR1"] - 1e-4),
            "directional_accuracy_AR1": round(da, 3),
        }

    # résidus OOS 1-step du meilleur (ARIMAX) -> bruit blanc ?
    ax1 = _walk_forward(d, ["cbot_ret_lag1", "wc_chg_lag1"], 1)
    resid = ax1["real"] - ax1["pred"]
    resid_white = _ljung_box_white(resid, 10)

    h1 = results["h1"]
    model_beats_rw = bool(h1["skill_AR1_vs_RW"] > 0 or results["h5"]["skill_AR1_vs_RW"] > 0)
    if model_beats_rw and resid_white:
        verdict = "MODEL_BEATS_NAIVE_RESIDUALS_WHITE"
    elif model_beats_rw:
        verdict = "MODEL_BEATS_NAIVE_RESIDUALS_NOT_FULLY_WHITE"
    else:
        verdict = "MODEL_NO_BETTER_THAN_NAIVE"

    out = {
        "version": "V121-BASIS-FORECAST",
        "n_obs": int(len(d)), "min_train": MIN_TRAIN,
        "by_horizon": results,
        "oos_residuals_white_noise_arimax_h1": resid_white,
        "model_beats_naive": model_beats_rw,
        "verdict": verdict,
        "interpretation": (
            f"OOS walk-forward (OLS récursif). h1 : skill AR1 vs RW = {h1['skill_AR1_vs_RW']}, "
            f"ARIMAX vs RW = {h1['skill_ARIMAX_vs_RW']}, exog aide OOS = {h1['exog_adds_oos']}. "
            f"h5 skill AR1 = {results['h5']['skill_AR1_vs_RW']}, h10 = {results['h10']['skill_AR1_vs_RW']}. "
            f"Résidus OOS 1-step (ARIMAX) bruit blanc = {resid_white}. "
            "Lecture : pour une série mean-reverting, l'AR/ARIMAX doit battre la marche aléatoire surtout à "
            "h>1 (la réversion devient prévisible) ; si les résidus OOS sont blancs, le modèle a capté le "
            "signal exploitable. C'est la version 'performante' attendue du modèle sur le basis."),
        "note": "OLS récursif causal (chaque prévision n'utilise que le passé). Exog futur=0 (inconnu). "
                "Descriptif ; pas un système de trading.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V121_DIR / "v121_forecast.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
