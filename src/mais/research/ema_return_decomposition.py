"""NB-EMA-05 — Décomposition du retour EMA : OLS global, rolling 260j, par régime.

Décomposition descriptive/contemporaine : les régresseurs ne sont PAS décalés.
Pour une utilisation prédictive, tous les régresseurs doivent être shift(1).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_return_decomposition.json"
_RESIDUAL_OUTPUT = _STUDY_DIR / "ema_residual_series.parquet"
_ROLLING_WINDOW = 260


def _build_dataset() -> pd.DataFrame:
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    sub = feats[feats["ema_front_price"].notna() & feats["cbot_eur_t"].notna()].copy()
    sub = sub.sort_values("Date").reset_index(drop=True)
    sub["ema_ret"] = sub["ema_front_price"].pct_change()
    sub["cbot_ret"] = sub["cbot_eur_t"].pct_change()
    sub["basis_chg"] = sub["ema_cbot_basis"].diff()
    # Volatility regime via rolling vol quantile
    sub["roll_vol_60"] = sub["ema_ret"].rolling(60).std() * np.sqrt(252)
    vol_median = sub["roll_vol_60"].median()
    sub["regime"] = (sub["roll_vol_60"] > vol_median).map({True: "high_vol", False: "low_vol"})
    return sub.dropna(subset=["ema_ret", "cbot_ret"]).reset_index(drop=True)


def _ols_fit(y: np.ndarray, x_data: np.ndarray) -> dict:
    try:
        import statsmodels.api as sm
        from statsmodels.regression.linear_model import OLS
        xc = sm.add_constant(x_data)
        res = OLS(y, xc).fit()
        coefs = res.params.tolist()
        pvals = res.pvalues.tolist()
        return {
            "r2": float(res.rsquared),
            "n": int(res.nobs),
            "coefs": coefs,
            "pvalues": pvals,
            "residuals": res.resid.tolist(),
        }
    except ImportError:
        # Fallback: numpy lstsq
        xc = np.column_stack([np.ones(len(x_data)), x_data])
        coefs, _, _, _ = np.linalg.lstsq(xc, y, rcond=None)
        y_hat = xc @ coefs
        ss_res = float(np.sum((y - y_hat) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        return {"r2": r2, "n": int(len(y)), "coefs": coefs.tolist(), "residuals": (y - y_hat).tolist()}


def _global_ols(df: pd.DataFrame) -> dict:
    sub = df[["ema_ret", "cbot_ret", "basis_chg"]].dropna()
    y = sub["ema_ret"].values

    # Incremental R²: model 1 (CBOT only) → model 2 (CBOT + basis)
    fit1 = _ols_fit(y, sub["cbot_ret"].values.reshape(-1, 1))
    fit2 = _ols_fit(y, sub[["cbot_ret", "basis_chg"]].values)

    # Correlation entre régresseurs
    corr_regressors = float(sub["cbot_ret"].corr(sub["basis_chg"]))

    return {
        "model_cbot_only": {"r2": fit1["r2"], "n": fit1["n"], "coef_cbot": fit1["coefs"][1] if len(fit1["coefs"]) > 1 else float("nan")},
        "model_cbot_basis": {
            "r2": fit2["r2"],
            "n": fit2["n"],
            "coef_cbot": fit2["coefs"][1] if len(fit2["coefs"]) > 1 else float("nan"),
            "coef_basis": fit2["coefs"][2] if len(fit2["coefs"]) > 2 else float("nan"),
        },
        "incremental_r2_basis": float(fit2["r2"] - fit1["r2"]),
        "corr_regressors_cbot_basis": corr_regressors,
        "note": "Décomposition descriptive/contemporaine. Non prédictive (régresseurs non décalés).",
        "residuals_global": fit2.get("residuals", []),
    }


def _rolling_ols_r2(df: pd.DataFrame, window: int) -> dict:
    sub = df[["Date", "ema_ret", "cbot_ret", "basis_chg"]].dropna().reset_index(drop=True)
    r2_series = []
    coef_cbot = []
    coef_basis = []
    for i in range(window, len(sub) + 1):
        window_df = sub.iloc[i - window:i]
        y = window_df["ema_ret"].values
        x_win = window_df[["cbot_ret", "basis_chg"]].values
        try:
            xc = np.column_stack([np.ones(len(y)), x_win])
            coefs, _, _, _ = np.linalg.lstsq(xc, y, rcond=None)
            y_hat = xc @ coefs
            ss_res = np.sum((y - y_hat) ** 2)
            ss_tot = np.sum((y - y.mean()) ** 2)
            r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
        except Exception:
            r2, coefs = float("nan"), [float("nan")] * 3
        r2_series.append(r2)
        coef_cbot.append(float(coefs[1]) if len(coefs) > 1 else float("nan"))
        coef_basis.append(float(coefs[2]) if len(coefs) > 2 else float("nan"))

    r2_arr = np.array([x for x in r2_series if not np.isnan(x)])
    return {
        "window_days": window,
        "n_windows": len(r2_series),
        "mean_r2": float(np.nanmean(r2_arr)) if len(r2_arr) else float("nan"),
        "min_r2": float(np.nanmin(r2_arr)) if len(r2_arr) else float("nan"),
        "max_r2": float(np.nanmax(r2_arr)) if len(r2_arr) else float("nan"),
        "std_r2": float(np.nanstd(r2_arr)) if len(r2_arr) else float("nan"),
        "mean_coef_cbot": float(np.nanmean(coef_cbot)),
        "mean_coef_basis": float(np.nanmean(coef_basis)),
    }


def _by_regime_ols(df: pd.DataFrame) -> dict:
    result: dict = {}
    for regime in df["regime"].dropna().unique():
        sub = df[df["regime"] == regime][["ema_ret", "cbot_ret", "basis_chg"]].dropna()
        if len(sub) < 50:
            result[regime] = {"error": "insufficient_data", "n": int(len(sub))}
            continue
        y = sub["ema_ret"].values
        x_reg = sub[["cbot_ret", "basis_chg"]].values
        fit = _ols_fit(y, x_reg)
        result[regime] = {
            "n": fit["n"],
            "r2": fit["r2"],
            "coef_cbot": fit["coefs"][1] if len(fit["coefs"]) > 1 else float("nan"),
            "coef_basis": fit["coefs"][2] if len(fit["coefs"]) > 2 else float("nan"),
        }
    return result


def build_return_decomposition() -> dict:
    df = _build_dataset()
    global_res = _global_ols(df)
    rolling_res = _rolling_ols_r2(df, _ROLLING_WINDOW)
    regime_res = _by_regime_ols(df)

    # Save residual series
    sub = df[["Date", "ema_ret", "cbot_ret", "basis_chg"]].dropna().reset_index(drop=True)
    residuals = global_res.pop("residuals_global", [])
    if residuals and len(residuals) == len(sub):
        residual_df = sub[["Date"]].copy()
        residual_df["ema_residual"] = residuals
        _RESIDUAL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        residual_df.to_parquet(_RESIDUAL_OUTPUT, index=False)

    return {
        "n_obs": int(len(df)),
        "period_start": str(df["Date"].min().date()),
        "period_end": str(df["Date"].max().date()),
        "global_ols": global_res,
        "rolling_ols_260d": rolling_res,
        "by_regime": regime_res,
        "key_findings": {
            "r2_cbot_only": global_res["model_cbot_only"]["r2"],
            "r2_cbot_basis": global_res["model_cbot_basis"]["r2"],
            "incremental_r2_basis": global_res["incremental_r2_basis"],
            "corr_regressors": global_res["corr_regressors_cbot_basis"],
            "mean_rolling_r2_260d": rolling_res["mean_r2"],
            "r2_high_vol_regime": regime_res.get("high_vol", {}).get("r2"),
            "r2_low_vol_regime": regime_res.get("low_vol", {}).get("r2"),
            "decomposition_note": "Descriptive/contemporaine. Régresseurs non décalés. Non utilisable directement pour prédiction.",
        },
    }


def save_return_decomposition(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_return_decomposition()

    def _convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return str(obj.date())
        raise TypeError(f"Not serialisable: {type(obj)}")

    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=_convert)
    return path


if __name__ == "__main__":
    out = save_return_decomposition()
    print(f"Return decomposition saved → {out}")
