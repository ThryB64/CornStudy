"""NB-EMA-12 — Prévision de prix EMA expérimental : modèle naïf + VECM + régression."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_price_forecast.json"
_HORIZONS = [5, 20, 60]


def _load_data() -> pd.DataFrame:
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    df = feats[feats["ema_front_price"].notna() & feats["cbot_eur_t"].notna()].copy()
    df = df[["Date", "ema_front_price", "cbot_eur_t", "ema_cbot_basis"]].sort_values("Date").reset_index(drop=True)
    return df


def _naive_benchmark(price: pd.Series, horizon: int) -> dict:
    """Random walk: forecast = current price. RMSE and MAPE vs naive."""
    y_true = price.shift(-horizon).dropna()
    y_pred = price[:len(y_true)]
    # Align
    aligned = pd.concat([y_true.reset_index(drop=True), y_pred.reset_index(drop=True)], axis=1).dropna()
    err = aligned.iloc[:, 0] - aligned.iloc[:, 1]
    rmse = float(np.sqrt((err ** 2).mean()))
    mape = float((err.abs() / aligned.iloc[:, 0].abs()).mean())
    return {"horizon": horizon, "model": "random_walk", "rmse": rmse, "mape": mape, "n": int(len(aligned))}


def _vecm_forecast(df: pd.DataFrame, horizon: int) -> dict:
    """VECM 1-step forecast iterated to horizon."""
    try:
        from statsmodels.tsa.vector_ar.vecm import VECM
        data = df[["ema_front_price", "cbot_eur_t"]].dropna()
        if len(data) < 100:
            return {"error": "insufficient_data"}
        # Walk-forward: train on 70%, evaluate on last 30%
        n = len(data)
        cutoff = int(n * 0.7)
        train = data.iloc[:cutoff]
        test = data.iloc[cutoff:]
        model = VECM(train, k_ar_diff=1, coint_rank=1, deterministic="n")
        fit = model.fit()
        # Forecast one step iteratively for horizon points
        forecasts = fit.predict(steps=min(horizon, len(test)))
        y_true = test["ema_front_price"].values[:len(forecasts)]
        y_pred = forecasts[:, 0]  # EMA column
        if len(y_true) == 0:
            return {"error": "no_test_data"}
        err = y_true - y_pred
        rmse = float(np.sqrt(np.mean(err ** 2)))
        mape = float(np.mean(np.abs(err / (y_true + 1e-8))))
        return {
            "horizon": horizon,
            "model": "VECM",
            "rmse": rmse,
            "mape": mape,
            "n_test": int(len(y_true)),
            "note": "VECM forecast expérimental. Non validé OOF complet.",
        }
    except ImportError:
        return {"error": "statsmodels_not_available"}
    except Exception as e:
        return {"error": str(e)[:80]}


def _basis_mean_reversion_forecast(df: pd.DataFrame, horizon: int) -> dict:
    """Forecast EMA via CBOT + basis mean-reversion : EMA_forecast = CBOT + basis_mean."""
    basis = df["ema_cbot_basis"]
    basis_mean = basis.expanding(min_periods=60).mean().shift(1)
    ema = df["ema_front_price"]
    cbot = df["cbot_eur_t"]
    # Forecast: EMA_t+H = CBOT_t + basis_mean_t (naive mean-reversion)
    y_true = ema.shift(-horizon).dropna()
    y_pred_cbot = cbot[:len(y_true)]
    y_pred_basis = basis_mean[:len(y_true)]
    y_pred = (y_pred_cbot + y_pred_basis).reset_index(drop=True)
    y_true = y_true.reset_index(drop=True)
    aligned = pd.concat([y_true, y_pred], axis=1).dropna()
    if len(aligned) < 10:
        return {"error": "insufficient_data"}
    err = aligned.iloc[:, 0] - aligned.iloc[:, 1]
    rmse = float(np.sqrt((err ** 2).mean()))
    mape = float((err.abs() / aligned.iloc[:, 0].abs()).mean())
    naive = _naive_benchmark(ema, horizon)
    improvement = float(1 - rmse / naive["rmse"]) if naive["rmse"] > 0 else float("nan")
    return {
        "horizon": horizon,
        "model": "basis_mean_reversion",
        "rmse": rmse,
        "mape": mape,
        "n": int(len(aligned)),
        "improvement_vs_naive": improvement,
        "note": "Expérimental. CBOT futur supposé connu. Non prédictif au sens strict.",
    }


def build_price_forecast() -> dict:
    df = _load_data()
    results: dict = {"horizons": _HORIZONS, "models": {}}

    for h in _HORIZONS:
        naive = _naive_benchmark(df["ema_front_price"], h)
        basis_mr = _basis_mean_reversion_forecast(df, h)
        vecm = _vecm_forecast(df, h) if h == 5 else {"skipped": f"VECM non itéré pour H={h}"}
        results["models"][f"H{h}"] = {
            "naive": naive,
            "basis_mean_reversion": basis_mr,
            "vecm": vecm,
        }

    best_improvement = max(
        (v["basis_mean_reversion"].get("improvement_vs_naive", float("nan")) for v in results["models"].values()
         if "error" not in v["basis_mean_reversion"]),
        default=float("nan"),
    )

    results["key_findings"] = {
        "best_model": "basis_mean_reversion",
        "best_improvement_vs_naive": float(best_improvement) if not np.isnan(best_improvement) else None,
        "note": "Résultats expérimentaux in-sample. CBOT futur non connu en pratique. Étude purement descriptive.",
    }
    return results


def save_price_forecast(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_price_forecast()

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
    out = save_price_forecast()
    print(f"Price forecast saved → {out}")
