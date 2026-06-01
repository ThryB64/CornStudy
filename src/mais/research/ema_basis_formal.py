"""NB-EMA-07 — Basis formel EMA/CBOT : stationnarité, AR(1), demi-vie, régimes HMM, arbitrage."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_basis_formal.json"


def _load_basis() -> pd.DataFrame:
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    df = feats[feats["ema_cbot_basis"].notna()][["Date", "ema_cbot_basis"]].copy()
    return df.sort_values("Date").reset_index(drop=True)


def _adf_kpss(series: pd.Series) -> dict:
    try:
        from statsmodels.tsa.stattools import adfuller, kpss
        adf_res = adfuller(series.dropna(), autolag="AIC")
        try:
            kpss_res = kpss(series.dropna(), regression="c", nlags="auto")
            kpss_out = {
                "stat": float(kpss_res[0]),
                "p_value": float(kpss_res[1]),
                "verdict": "stationary" if kpss_res[1] > 0.05 else "non_stationary",
            }
        except Exception:
            kpss_out = {"error": "kpss_failed"}
        return {
            "adf": {
                "stat": float(adf_res[0]),
                "p_value": float(adf_res[1]),
                "n_lags": int(adf_res[2]),
                "verdict": "stationary" if adf_res[1] < 0.05 else "non_stationary",
            },
            "kpss": kpss_out,
        }
    except ImportError:
        return {"error": "statsmodels_not_available"}


def _ar1_fit(series: pd.Series) -> dict:
    """Ajuste AR(1) par OLS : basis[t] = phi * basis[t-1] + c + eps."""
    y = series.values[1:]
    x = series.values[:-1]
    # OLS
    x_c = np.column_stack([np.ones(len(x)), x])
    coefs, _, _, _ = np.linalg.lstsq(x_c, y, rcond=None)
    intercept, phi = float(coefs[0]), float(coefs[1])
    y_hat = x_c @ coefs
    resid = y - y_hat
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = float(1 - ss_res / ss_tot)
    # Half-life: ln(2) / ln(1/phi) = -ln(2) / ln(phi)
    if 0 < phi < 1:
        half_life = float(-np.log(2) / np.log(phi))
    elif phi >= 1:
        half_life = float("inf")
    else:
        half_life = float("nan")
    return {
        "phi": phi,
        "intercept": intercept,
        "r2": r2,
        "half_life_days": half_life,
        "mean_reversion_rate": float(1 - phi),
    }


def _hmm_regimes(series: pd.Series) -> dict:
    try:
        from hmmlearn import hmm
        x_hmm = series.values.reshape(-1, 1)
        model = hmm.GaussianHMM(n_components=2, covariance_type="full", n_iter=100, random_state=42)
        model.fit(x_hmm)
        states = model.predict(x_hmm)
        means = model.means_.flatten().tolist()
        covs = [float(np.sqrt(c[0][0])) for c in model.covars_]
        labels = {0: "low_basis" if means[0] < means[1] else "high_basis",
                  1: "high_basis" if means[0] < means[1] else "low_basis"}
        return {
            "n_components": 2,
            "state_means": [float(m) for m in means],
            "state_stds": covs,
            "state_labels": labels,
            "pct_state_0": float((states == 0).mean()),
            "pct_state_1": float((states == 1).mean()),
        }
    except ImportError:
        return {"error": "hmmlearn_not_available"}
    except Exception as e:
        return {"error": str(e)[:100]}


def _mean_reversion_hit_rate(series: pd.Series, z_threshold: float = 2.0, horizon: int = 20) -> dict:
    mu = series.mean()
    sigma = series.std()
    z = (series - mu) / sigma
    hits = 0
    total = 0
    for i in range(len(z) - horizon):
        if abs(z.iloc[i]) >= z_threshold:
            total += 1
            future = series.iloc[i + 1:i + horizon + 1]
            reverted = ((series.iloc[i] > mu) and (future < mu + sigma).any()) or \
                       ((series.iloc[i] < mu) and (future > mu - sigma).any())
            if reverted:
                hits += 1
    hit_rate = float(hits / max(total, 1))
    return {
        "z_threshold": z_threshold,
        "horizon_days": horizon,
        "n_extreme_events": total,
        "n_reverted": hits,
        "hit_rate": hit_rate,
    }


def _basis_arbitrage_backtest(df: pd.DataFrame, z_entry: float = 2.0, z_exit: float = 0.5) -> dict:
    """Backtest simple mean-reversion : long EMA / short CBOT quand basis dévie > z_entry σ."""
    basis = df["ema_cbot_basis"].copy()
    mu = basis.mean()
    sigma = basis.std()
    z = (basis - mu) / sigma

    position = 0
    entry_basis = 0.0
    pnl_list = []
    trade_count = 0

    for i in range(1, len(z)):
        zi = z.iloc[i]
        if position == 0:
            if zi >= z_entry:
                position = -1  # basis trop haut → short basis (sell EMA, buy CBOT)
                entry_basis = basis.iloc[i]
            elif zi <= -z_entry:
                position = 1  # basis trop bas → long basis (buy EMA, sell CBOT)
                entry_basis = basis.iloc[i]
        else:
            if abs(zi) <= z_exit:
                exit_basis = basis.iloc[i]
                pnl = position * (exit_basis - entry_basis)
                pnl_list.append(float(pnl))
                trade_count += 1
                position = 0

    if not pnl_list:
        return {"error": "no_trades", "z_entry": z_entry, "z_exit": z_exit}

    arr = np.array(pnl_list)
    return {
        "z_entry": z_entry,
        "z_exit": z_exit,
        "n_trades": trade_count,
        "total_pnl_eur_t": float(arr.sum()),
        "mean_pnl_per_trade": float(arr.mean()),
        "pct_winning_trades": float((arr > 0).mean()),
        "max_loss": float(arr.min()),
        "max_gain": float(arr.max()),
        "note": "Backtest simple sans coûts de transaction ni contrainte de liquidité. Non validé OOF.",
    }


def build_basis_formal() -> dict:
    df = _load_basis()
    basis = df["ema_cbot_basis"]

    stationarity = _adf_kpss(basis)
    ar1 = _ar1_fit(basis)
    hmm = _hmm_regimes(basis)
    hit_rate_z2_h20 = _mean_reversion_hit_rate(basis, z_threshold=2.0, horizon=20)
    hit_rate_z2_h60 = _mean_reversion_hit_rate(basis, z_threshold=2.0, horizon=60)
    backtest = _basis_arbitrage_backtest(df)

    basis_stats = {
        "n": int(len(basis)),
        "mean": float(basis.mean()),
        "std": float(basis.std()),
        "min": float(basis.min()),
        "max": float(basis.max()),
        "pct_positive": float((basis > 0).mean()),
        "period_start": str(df["Date"].min().date()),
        "period_end": str(df["Date"].max().date()),
    }

    return {
        "basis_stats": basis_stats,
        "stationarity": stationarity,
        "ar1": ar1,
        "hmm_regimes": hmm,
        "mean_reversion_H20": hit_rate_z2_h20,
        "mean_reversion_H60": hit_rate_z2_h60,
        "arbitrage_backtest": backtest,
        "key_findings": {
            "adf_basis_verdict": stationarity.get("adf", {}).get("verdict"),
            "kpss_basis_verdict": stationarity.get("kpss", {}).get("verdict"),
            "ar1_phi": ar1["phi"],
            "ar1_half_life_days": ar1["half_life_days"],
            "mean_reversion_hit_rate_H20": hit_rate_z2_h20["hit_rate"],
            "mean_reversion_hit_rate_H60": hit_rate_z2_h60["hit_rate"],
            "backtest_pct_winning": backtest.get("pct_winning_trades"),
            "basis_mean_eur_t": basis_stats["mean"],
        },
    }


def save_basis_formal(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_basis_formal()

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
    out = save_basis_formal()
    print(f"Basis formal saved → {out}")
