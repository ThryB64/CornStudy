"""Concrete adapters: baselines + linear ML (no heavy deps)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .base import ModelAdapter

# ---------------------------------------------------------------------------
# Baselines
# ---------------------------------------------------------------------------


class NaiveLastAdapter(ModelAdapter):
    """Predict that next return = last return seen."""

    def fit(self, x, y, x_val=None, y_val=None):
        self._last = float(y.dropna().iloc[-1]) if len(y.dropna()) else 0.0
        self._fitted = True
        return self

    def predict(self, x):
        return np.full(len(x), self._last, dtype=float)


class NaiveDriftAdapter(ModelAdapter):
    """Predict the average return seen so far."""

    def fit(self, x, y, x_val=None, y_val=None):
        self._mean = float(y.dropna().mean()) if len(y.dropna()) else 0.0
        self._fitted = True
        return self

    def predict(self, x):
        return np.full(len(x), self._mean, dtype=float)


class EMABaselineAdapter(ModelAdapter):
    """EMA(span=20) of the target."""

    def fit(self, x, y, x_val=None, y_val=None):
        span = int(self.params.get("span", 20))
        s = y.dropna()
        if len(s) == 0:
            self._mu = 0.0
        else:
            self._mu = float(s.ewm(span=span, adjust=False).mean().iloc[-1])
        self._fitted = True
        return self

    def predict(self, x):
        return np.full(len(x), self._mu, dtype=float)


class AR1BaselineAdapter(ModelAdapter):
    """y_{t+1} = phi * y_t + (1-phi) * mean."""

    def fit(self, x, y, x_val=None, y_val=None):
        s = y.dropna().reset_index(drop=True)
        if len(s) < 30:
            self._phi, self._mu = 0.0, 0.0
        else:
            x_lag = s.shift(1).iloc[1:]
            x_now = s.iloc[1:]
            mask = x_lag.notna() & x_now.notna()
            cov = ((x_lag[mask] - x_lag[mask].mean()) * (x_now[mask] - x_now[mask].mean())).sum()
            var = ((x_lag[mask] - x_lag[mask].mean()) ** 2).sum()
            self._phi = float(cov / var) if var > 0 else 0.0
            self._mu = float(s.mean())
            self._last = float(s.iloc[-1])
        self._fitted = True
        return self

    def predict(self, x):
        if not self._fitted:
            return np.zeros(len(x), dtype=float)
        return np.full(len(x), self._phi * self._last + (1 - self._phi) * self._mu)


# ---------------------------------------------------------------------------
# Linear ML
# ---------------------------------------------------------------------------


class _SklearnLinearAdapter(ModelAdapter):
    """Shared logic for Ridge/Lasso/ElasticNet."""

    estimator_cls: type | None = None

    def _build(self):
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler

        est = self.estimator_cls(**self._estimator_kwargs())
        return Pipeline([
            ("scaler", StandardScaler(with_mean=True, with_std=True)),
            ("est", est),
        ])

    def _estimator_kwargs(self) -> dict:
        return dict(self.params)

    def _clean_x(self, x: pd.DataFrame) -> pd.DataFrame:
        return x.select_dtypes(include=[np.number]).fillna(0.0)

    def fit(self, x, y, x_val=None, y_val=None):
        xc = self._clean_x(x)
        mask = y.notna()
        xc = xc.loc[mask]
        yc = y.loc[mask]
        self._cols = list(xc.columns)
        self._pipe = self._build()
        self._pipe.fit(xc.values, yc.values)
        self._fitted = True
        return self

    def predict(self, x):
        xc = self._clean_x(x)[self._cols].fillna(0.0)
        return self._pipe.predict(xc.values)


class RidgeAdapter(_SklearnLinearAdapter):
    @property
    def estimator_cls(self):
        from sklearn.linear_model import Ridge
        return Ridge


class LassoAdapter(_SklearnLinearAdapter):
    @property
    def estimator_cls(self):
        from sklearn.linear_model import Lasso
        return Lasso


class ElasticNetAdapter(_SklearnLinearAdapter):
    @property
    def estimator_cls(self):
        from sklearn.linear_model import ElasticNet
        return ElasticNet
