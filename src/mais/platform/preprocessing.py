"""Generic preprocessing pipeline for the AutoML platform.

Handles: imputation, encoding, scaling, temporal features, lags,
rolling windows, and anti-leakage shift(horizon).
All transformations are fitted on train, applied on any split.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

from mais.platform.profiler import (
    ProfileReport,
)
from mais.utils import get_logger

log = get_logger("mais.platform.preprocessing")

_DEFAULT_LAGS = [1, 5, 10, 21]
_DEFAULT_ROLLS = [5, 21]


@dataclass
class PreprocessingConfig:
    lags: list[int] = field(default_factory=lambda: list(_DEFAULT_LAGS))
    rolls: list[int] = field(default_factory=lambda: list(_DEFAULT_ROLLS))
    horizon: int = 1
    drop_quasi_constant: bool = True
    quasi_constant_threshold: float = 1e-4
    max_missing_col: float = 0.80
    imputer_numeric: str = "median"
    use_scaling: bool | None = None   # None = auto (True for linear tasks)
    use_onehot: bool | None = None    # None = auto (True for linear tasks)
    drop_id_cols: bool = True
    add_temporal_features: bool = True


class GenericPreprocessor:
    """Fit-transform pipeline for AutoML.

    Usage::

        prep = GenericPreprocessor(profile)
        X_train, y_train = prep.fit_transform(df_train)
        X_test, y_test  = prep.transform(df_test)
    """

    def __init__(
        self,
        profile: ProfileReport,
        config: PreprocessingConfig | None = None,
        linear_model: bool = False,
    ) -> None:
        self.profile = profile
        self.config = config or PreprocessingConfig(horizon=1)
        self.linear_model = linear_model

        self._num_imputer: SimpleImputer | None = None
        self._cat_imputer: SimpleImputer | None = None
        self._cat_encoder: OrdinalEncoder | None = None
        self._scaler: StandardScaler | None = None
        self._drop_cols: list[str] = []
        self._feature_cols: list[str] = []
        self._fitted = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit_transform(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        """Fit on df, return (X, y)."""
        work = df.copy()
        target = self.profile.target_col
        date_col = self.profile.date_col

        y = work[target].copy()
        work = work.drop(columns=[target])

        # Drop ID and date (keep date separately for temporal features)
        if self.config.drop_id_cols:
            work = work.drop(columns=[c for c in self.profile.id_cols if c in work.columns])

        work = self._add_temporal_features(work, date_col)
        if date_col and date_col in work.columns:
            work = work.drop(columns=[date_col])

        # Drop columns with too many NaNs
        high_nan = [
            c for c in work.columns
            if work[c].isna().mean() > self.config.max_missing_col
        ]
        work = work.drop(columns=high_nan)
        self._drop_cols = high_nan

        # Add lags + rolling for time series
        if self.profile.is_time_series:
            work = self._add_lags_rolling(work, df, date_col, target, fit=True)
            # Anti-leakage: shift target-derived features by horizon
            work = self._apply_leakage_shift(work, target)

        # Separate numeric and categorical
        num_cols = [c for c in work.columns if pd.api.types.is_numeric_dtype(work[c])]
        cat_cols = [c for c in work.columns if c not in num_cols]

        # Impute numeric
        if num_cols:
            self._num_imputer = SimpleImputer(strategy=self.config.imputer_numeric)
            arr = self._num_imputer.fit_transform(work[num_cols])
            work[num_cols] = arr

        # Encode + impute categorical
        if cat_cols:
            self._cat_imputer = SimpleImputer(strategy="most_frequent")
            work[cat_cols] = self._cat_imputer.fit_transform(work[cat_cols])
            use_onehot = self.config.use_onehot if self.config.use_onehot is not None else self.linear_model
            if use_onehot:
                dummies = pd.get_dummies(work[cat_cols], drop_first=True, dtype=float)
                work = pd.concat([work.drop(columns=cat_cols), dummies], axis=1)
            else:
                self._cat_encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
                work[cat_cols] = self._cat_encoder.fit_transform(work[cat_cols])

        # Drop quasi-constant
        if self.config.drop_quasi_constant:
            variances = work.var(numeric_only=True)
            qc = variances[variances < self.config.quasi_constant_threshold].index.tolist()
            work = work.drop(columns=qc)
            self._drop_cols += qc

        # Scale (linear models)
        use_scaling = self.config.use_scaling if self.config.use_scaling is not None else self.linear_model
        if use_scaling:
            self._scaler = StandardScaler()
            arr = self._scaler.fit_transform(work)
            work = pd.DataFrame(arr, columns=work.columns, index=work.index)

        self._feature_cols = list(work.columns)
        self._fitted = True
        log.info(
            "preprocessor_fit",
            features=len(self._feature_cols),
            dropped_high_nan=len(high_nan),
        )
        return work, y

    def transform(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        """Apply fitted pipeline to df, return (X, y)."""
        if not self._fitted:
            raise RuntimeError("Call fit_transform first")
        work = df.copy()
        target = self.profile.target_col
        date_col = self.profile.date_col

        y = work[target].copy() if target in work.columns else pd.Series(dtype=float)
        if target in work.columns:
            work = work.drop(columns=[target])

        if self.config.drop_id_cols:
            work = work.drop(columns=[c for c in self.profile.id_cols if c in work.columns])

        work = self._add_temporal_features(work, date_col)
        if date_col and date_col in work.columns:
            work = work.drop(columns=[date_col])

        work = work.drop(columns=[c for c in self._drop_cols if c in work.columns])

        if self.profile.is_time_series:
            work = self._add_lags_rolling(work, df, date_col, target, fit=False)
            work = self._apply_leakage_shift(work, target)

        num_cols = [c for c in work.columns if pd.api.types.is_numeric_dtype(work[c])]
        cat_cols = [c for c in work.columns if c not in num_cols]

        if self._num_imputer and num_cols:
            cols_in = [c for c in self._num_imputer.feature_names_in_ if c in work.columns]
            work[cols_in] = self._num_imputer.transform(work[cols_in]) if cols_in else work[cols_in]

        if cat_cols and self._cat_imputer:
            cols_in = [c for c in work.columns if c in cat_cols]
            if cols_in:
                work[cols_in] = self._cat_imputer.transform(work[cols_in])
            if self._cat_encoder:
                cols_enc = [c for c in cat_cols if c in work.columns]
                if cols_enc:
                    work[cols_enc] = self._cat_encoder.transform(work[cols_enc])

        if self._scaler:
            cols_to_scale = [c for c in self._feature_cols if c in work.columns]
            if cols_to_scale:
                arr = self._scaler.transform(work[cols_to_scale])
                work[cols_to_scale] = arr

        # Align to fitted feature columns
        for c in self._feature_cols:
            if c not in work.columns:
                work[c] = 0.0
        work = work[self._feature_cols]
        return work, y

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _add_temporal_features(self, df: pd.DataFrame, date_col: str | None) -> pd.DataFrame:
        if not self.config.add_temporal_features or not date_col or date_col not in df.columns:
            return df
        dates = pd.to_datetime(df[date_col], errors="coerce")
        df = df.copy()
        df["_tf_year"] = dates.dt.year
        df["_tf_month"] = dates.dt.month
        df["_tf_dayofweek"] = dates.dt.dayofweek
        df["_tf_week"] = dates.dt.isocalendar().week.astype(int)
        return df

    def _add_lags_rolling(
        self,
        work: pd.DataFrame,
        original: pd.DataFrame,
        date_col: str | None,
        target: str,
        fit: bool,
    ) -> pd.DataFrame:
        work = work.copy()
        src = original[target] if target in original.columns else pd.Series(dtype=float)
        for lag in self.config.lags:
            work[f"_lag_{target}_{lag}"] = src.shift(lag).values
        for roll in self.config.rolls:
            work[f"_roll_mean_{target}_{roll}"] = src.rolling(roll).mean().shift(1).values
            work[f"_roll_std_{target}_{roll}"] = src.rolling(roll).std().shift(1).values
        return work

    def _apply_leakage_shift(self, work: pd.DataFrame, target: str) -> pd.DataFrame:
        h = self.config.horizon
        if h <= 1:
            return work
        cols_future = [c for c in work.columns if target in c and not c.startswith("_lag_")]
        for c in cols_future:
            work[c] = work[c].shift(h)
        return work

    @property
    def feature_names(self) -> list[str]:
        return list(self._feature_cols)

    def summary(self) -> str:
        return (
            f"GenericPreprocessor fitted={self._fitted} "
            f"features={len(self._feature_cols)} "
            f"dropped={len(self._drop_cols)} "
            f"scaler={self._scaler is not None}"
        )
