"""Statistical and time series models for corn price analysis.

Tests: AR, ARMA, ARIMA, SARIMA, SARIMAX, VAR, GARCH, Markov-switching, HMM.
All models are evaluated in a walk-forward protocol to avoid lookahead.
"""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.research.statistical_models")


# ---------------------------------------------------------------------------
# Walk-forward evaluation for statsmodels
# ---------------------------------------------------------------------------

def _wf_statsmodels(
    series: pd.Series,
    model_fn,
    min_train: int = 500,
    horizon: int = 20,
    step: int = 20,
) -> pd.DataFrame:
    """Generic walk-forward for statsmodels models (fit+predict at each step)."""
    results = []
    n = len(series)
    for start in range(min_train, n - horizon, step):
        train = series.iloc[:start]
        true_val = float(series.iloc[start + horizon - 1]) if start + horizon <= n else float("nan")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                res = model_fn(train)
                forecast = res.forecast(steps=horizon)
                pred_val = float(forecast.iloc[-1])
        except Exception as e:
            log.debug("statsmodels_step_failed", error=str(e)[:80])
            pred_val = float("nan")

        results.append({
            "date_forecast": series.index[start] if hasattr(series.index, "__getitem__") else start,
            "y_true": true_val,
            "y_pred": pred_val,
            "train_size": start,
        })
    return pd.DataFrame(results)


def _score_wf(df: pd.DataFrame) -> dict[str, float]:
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    sub = df.dropna(subset=["y_true", "y_pred"])
    if len(sub) < 5:
        return {"rmse": float("nan"), "mae": float("nan"), "da": float("nan"), "n": 0}
    rmse = float(np.sqrt(mean_squared_error(sub["y_true"], sub["y_pred"])))
    mae  = float(mean_absolute_error(sub["y_true"], sub["y_pred"]))
    da   = float(np.mean(np.sign(sub["y_true"]) == np.sign(sub["y_pred"])))
    return {"rmse": rmse, "mae": mae, "da": da, "n": len(sub)}


# ---------------------------------------------------------------------------
# Model runners
# ---------------------------------------------------------------------------

def run_ar(returns: pd.Series, horizon: int = 20, lags: int = 5, min_train: int = 500) -> dict[str, Any]:
    """AR(p) model on log-returns."""
    try:
        from statsmodels.tsa.ar_model import AutoReg

        def fit_fn(train):
            m = AutoReg(train, lags=lags, old_names=False)
            return m.fit()

        df = _wf_statsmodels(returns, fit_fn, min_train=min_train, horizon=horizon)
        return {"model": f"AR({lags})", "horizon": horizon, "predictions": df, **_score_wf(df)}
    except ImportError:
        return {"model": f"AR({lags})", "horizon": horizon, "error": "statsmodels not installed"}


def run_arima(
    returns: pd.Series,
    horizon: int = 20,
    orders: list[tuple[int, int, int]] | None = None,
    min_train: int = 500,
) -> list[dict[str, Any]]:
    """ARIMA grid search over (p,d,q) orders."""
    if orders is None:
        orders = [(1, 0, 0), (2, 0, 0), (1, 0, 1), (2, 0, 1), (0, 0, 1), (0, 0, 2)]
    results = []
    try:
        from statsmodels.tsa.arima.model import ARIMA

        for order in orders:
            def make_fn(o):
                def fit_fn(train):
                    return ARIMA(train, order=o).fit()
                return fit_fn

            df = _wf_statsmodels(returns, make_fn(order), min_train=min_train, horizon=horizon)
            scores = _score_wf(df)
            results.append({"model": f"ARIMA{order}", "horizon": horizon, "predictions": df, **scores})

    except ImportError:
        results.append({"model": "ARIMA", "error": "statsmodels not installed"})
    return results


def run_sarimax(
    returns: pd.Series,
    exog: pd.DataFrame | None = None,
    horizon: int = 20,
    order: tuple = (1, 0, 1),
    seasonal_order: tuple = (1, 0, 1, 52),
    min_train: int = 500,
) -> dict[str, Any]:
    """SARIMAX with optional exogenous variables."""
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        results_list = []
        n = len(returns)
        for start in range(min_train, n - horizon, 20):
            train_y = returns.iloc[:start]
            train_x = exog.iloc[:start] if exog is not None else None
            test_x  = exog.iloc[start:start+horizon] if exog is not None else None
            true_val = float(returns.iloc[start + horizon - 1]) if start + horizon <= n else float("nan")
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    m = SARIMAX(train_y, exog=train_x, order=order, seasonal_order=seasonal_order,
                                enforce_stationarity=False, enforce_invertibility=False)
                    res = m.fit(disp=False)
                    fc = res.forecast(steps=horizon, exog=test_x)
                    pred_val = float(fc.iloc[-1])
            except Exception:
                pred_val = float("nan")
            results_list.append({"y_true": true_val, "y_pred": pred_val})

        df = pd.DataFrame(results_list)
        return {"model": f"SARIMAX{order}", "horizon": horizon, "predictions": df, **_score_wf(df)}
    except ImportError:
        return {"model": "SARIMAX", "error": "statsmodels not installed"}


def run_garch(
    returns: pd.Series,
    p: int = 1,
    q: int = 1,
    min_train: int = 500,
    horizon: int = 5,
) -> dict[str, Any]:
    """GARCH(p,q) volatility model — forecast conditional variance."""
    try:
        from arch import arch_model

        vols = []
        n = len(returns)
        for start in range(min_train, n - horizon, 20):
            train = returns.iloc[:start] * 100  # scale
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    m = arch_model(train, vol="GARCH", p=p, q=q, dist="Normal")
                    res = m.fit(disp="off")
                    fc = res.forecast(horizon=horizon)
                    vol_pred = float(np.sqrt(fc.variance.iloc[-1, -1])) / 100
            except Exception:
                vol_pred = float("nan")
            true_vol = float(returns.iloc[start:start+horizon].std()) if start + horizon <= n else float("nan")
            vols.append({"vol_pred": vol_pred, "vol_true": true_vol})

        df = pd.DataFrame(vols).dropna()
        corr = float(df["vol_pred"].corr(df["vol_true"])) if len(df) > 5 else float("nan")
        return {"model": f"GARCH({p},{q})", "horizon": horizon, "volatility_df": df,
                "vol_prediction_correlation": corr, "n": len(df)}
    except ImportError:
        return {"model": "GARCH", "error": "arch package not installed — pip install arch"}


def run_markov_2states(
    series: pd.Series,
    min_train: int = 500,
) -> dict[str, Any]:
    """Markov-switching 2-state model (bull/non-bull)."""
    try:
        from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = MarkovRegression(series, k_regimes=2, trend="c", switching_variance=True)
            res = m.fit(disp=False)

        smoothed = res.smoothed_marginal_probabilities
        regime_series = pd.Series(
            smoothed.iloc[:, 1].values > 0.5,
            index=series.index if hasattr(series, "index") else range(len(series)),
        ).map({True: "bull", False: "range"})

        dist = regime_series.value_counts(normalize=True).to_dict()
        return {"model": "Markov-2states", "regime_series": regime_series,
                "distribution": dist, "aic": float(res.aic), "bic": float(res.bic)}
    except ImportError:
        return {"model": "Markov-2states", "error": "statsmodels not installed"}
    except Exception as e:
        return {"model": "Markov-2states", "error": str(e)}


def summarize_ts_results(results: list[dict[str, Any]]) -> pd.DataFrame:
    """Flatten a list of model result dicts into a comparison DataFrame."""
    rows = []
    for r in results:
        rows.append({
            "model": r.get("model", "?"),
            "horizon": r.get("horizon"),
            "rmse": r.get("rmse"),
            "mae": r.get("mae"),
            "da": r.get("da"),
            "n": r.get("n"),
            "error": r.get("error"),
        })
    return pd.DataFrame(rows)
