"""ABC for all model adapters.

A ``ModelAdapter`` exposes 4 methods:

  * ``fit(X_train, y_train, X_val=None, y_val=None)``
  * ``predict(X)``                -> point forecast
  * ``predict_quantiles(X, qs)``  -> dict of quantile forecasts (None if unsupported)
  * ``get_params() / set_params(**)``  -> sklearn-style introspection

The walk-forward engine and Optuna only need this interface to work with any
model in the registry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import numpy as np
import pandas as pd


class ModelTask(str, Enum):
    REGRESSION = "regression"
    BINARY = "binary"
    MULTICLASS = "multiclass"
    ORDINAL = "ordinal"
    QUANTILE = "quantile"


class ModelRequirement(str, Enum):
    TIME_INDEX = "time_index"          # rows must be ordered chronologically
    EXOGENOUS = "exogenous"            # uses X covariates
    PANEL = "panel"                    # multiple cross-sectional units
    META_FEATURES = "meta_features"    # uses base-model predictions
    BASE_PREDICTIONS = "base_predictions"


@dataclass
class ModelMeta:
    name: str
    group: str                          # baseline | classical_ts | ml | dl | meta
    task_types: list[ModelTask]
    requires: list[ModelRequirement]
    min_samples: int = 100
    max_samples: Optional[int] = None
    legacy_path: Optional[str] = None   # path to legacy implementation


class ModelAdapter(ABC):
    """Uniform interface for every model."""

    meta: ModelMeta

    def __init__(self, **params: Any) -> None:
        self.params = dict(params)
        self._fitted = False

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series,
             X_val: Optional[pd.DataFrame] = None,
             y_val: Optional[pd.Series] = None) -> "ModelAdapter":
        ...

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        ...

    def predict_quantiles(self, X: pd.DataFrame,
                           quantiles: list[float] = (0.1, 0.5, 0.9)) -> Optional[dict]:
        """Override for models that natively output quantiles."""
        return None

    def predict_proba(self, X: pd.DataFrame) -> Optional[np.ndarray]:
        """Override for classification models."""
        return None

    def get_params(self) -> dict[str, Any]:
        return dict(self.params)

    def set_params(self, **params: Any) -> "ModelAdapter":
        self.params.update(params)
        return self

    def __repr__(self) -> str:
        return f"<{self.meta.name} fitted={self._fitted} params={self.params}>"
