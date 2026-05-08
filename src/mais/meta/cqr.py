"""Conformalized Quantile Regression (CQR).

CQR (Angelopoulos et al. 2022) combines:
1. A quantile regression base model (LightGBM with alpha/1-alpha quantile
   objectives) that produces asymmetric intervals [q_lo, q_hi].
2. A conformal calibration step that adjusts the interval width using a
   held-out calibration set, guaranteeing marginal coverage >= 1 - alpha.

This is distinct from the symmetric split-conformal already in meta/conformal.py:
- conformal.py : (point_pred ± q_absolute_residual) — symmetric, uses any model
- cqr.py       : asymmetric intervals calibrated to quantile residuals

References
----------
Angelopoulos et al. (2022) "Conformal Risk Control"
Romano et al. (2019) "Conformalized Quantile Regression"
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.meta.cqr")


def _build_quantile_model(alpha: float, n_estimators: int = 200):
    """Build a LightGBM quantile regressor for a given alpha level."""
    try:
        import lightgbm as lgb
        return lgb.LGBMRegressor(
            objective="quantile",
            alpha=alpha,
            n_estimators=n_estimators,
            learning_rate=0.05,
            num_leaves=15,
            min_child_samples=40,
            lambda_l2=1.0,
            feature_fraction=0.8,
            verbose=-1,
            random_state=42,
        )
    except ImportError:
        from sklearn.ensemble import GradientBoostingRegressor
        return GradientBoostingRegressor(
            loss="quantile",
            alpha=alpha,
            n_estimators=n_estimators,
            max_depth=3,
            learning_rate=0.05,
            random_state=42,
        )


class CQRModel:
    """Conformalized Quantile Regression model.

    Fits two quantile regressors (for alpha/2 and 1-alpha/2 quantiles) on the
    training set, then calibrates the conformal correction E on the calibration
    set so that P(y in [q_lo - E, q_hi + E]) >= 1 - alpha.
    """

    def __init__(self, coverage: float = 0.90, n_estimators: int = 200):
        if not 0 < coverage < 1:
            raise ValueError(f"coverage must be in (0,1), got {coverage}")
        self.coverage = coverage
        self.alpha = 1.0 - coverage
        self._lo_model = _build_quantile_model(self.alpha / 2, n_estimators)
        self._hi_model = _build_quantile_model(1.0 - self.alpha / 2, n_estimators)
        self._e: float = 0.0
        self._fitted = False

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series,
            X_cal: pd.DataFrame, y_cal: pd.Series) -> "CQRModel":
        """Fit quantile models on train, calibrate conformal correction on cal."""
        from sklearn.impute import SimpleImputer
        imp = SimpleImputer(strategy="median")
        Xtr = imp.fit_transform(X_train)
        Xcal = imp.transform(X_cal)
        self._imp = imp

        y_tr = np.asarray(y_train, dtype=float)
        y_cal_arr = np.asarray(y_cal, dtype=float)

        self._lo_model.fit(Xtr, y_tr)
        self._hi_model.fit(Xtr, y_tr)

        lo_cal = self._lo_model.predict(Xcal)
        hi_cal = self._hi_model.predict(Xcal)

        # Conformity score: max(lo - y, y - hi)  (how much the interval needs to grow)
        scores = np.maximum(lo_cal - y_cal_arr, y_cal_arr - hi_cal)
        n = len(scores)
        # Finite-sample adjusted quantile level
        q_level = min(1.0, (1.0 - self.alpha) * (1.0 + 1.0 / n))
        self._e = max(0.0, float(np.quantile(scores, q_level)))
        self._fitted = True
        log.info("cqr_calibrated", e=round(self._e, 5),
                 coverage=self.coverage, n_cal=n)
        return self

    def predict_intervals(self, X: pd.DataFrame) -> pd.DataFrame:
        """Return a DataFrame with columns: q_lo, q_hi, midpoint."""
        if not self._fitted:
            raise RuntimeError("Call fit() before predict_intervals()")
        Xp = self._imp.transform(X)
        lo = self._lo_model.predict(Xp) - self._e
        hi = self._hi_model.predict(Xp) + self._e
        return pd.DataFrame({
            "q_lo": lo,
            "q_hi": hi,
            "midpoint": (lo + hi) / 2.0,
        }, index=X.index)


def walk_forward_cqr(
    features: pd.DataFrame,
    targets: pd.DataFrame,
    factor_cols: list[str],
    target_col: str,
    horizon: int,
    coverage: float = 0.90,
    initial_ratio: float = 0.60,
    cal_ratio: float = 0.15,
) -> pd.DataFrame:
    """Walk-forward CQR evaluation.

    Splits: train [0 .. train_end] → calibration [train_end .. cal_end] → test [cal_end .. n]
    Returns a DataFrame with: Date, y_true, q_lo, q_hi, midpoint, covered.
    """
    date_col = "Date"
    merged = features.merge(targets[[date_col, target_col]], on=date_col, how="inner")
    merged = merged.dropna(subset=[target_col]).reset_index(drop=True)
    n = len(merged)
    if n < 400:
        log.warning("cqr_too_few_rows", n=n)
        return pd.DataFrame()

    train_end = int(n * initial_ratio)
    cal_end = train_end + int(n * cal_ratio)
    if cal_end >= n - 20:
        log.warning("cqr_not_enough_test", n=n)
        return pd.DataFrame()

    train = merged.iloc[:train_end]
    cal = merged.iloc[train_end:cal_end]
    test = merged.iloc[cal_end:]

    from sklearn.impute import SimpleImputer
    imp = SimpleImputer(strategy="median")
    # Fit imputer on train
    X_train = train[factor_cols].replace([np.inf, -np.inf], np.nan)
    imp.fit(X_train)
    X_cal = pd.DataFrame(imp.transform(cal[factor_cols].replace([np.inf, -np.inf], np.nan)),
                         columns=factor_cols, index=cal.index)
    X_test = pd.DataFrame(imp.transform(test[factor_cols].replace([np.inf, -np.inf], np.nan)),
                          columns=factor_cols, index=test.index)

    cqr = CQRModel(coverage=coverage)
    cqr.fit(
        pd.DataFrame(imp.transform(X_train), columns=factor_cols),
        train[target_col],
        X_cal,
        cal[target_col],
    )

    preds = cqr.predict_intervals(X_test)
    y_true = test[target_col].values
    result = pd.DataFrame({
        date_col: test[date_col].values,
        "y_true": y_true,
        "q_lo": preds["q_lo"].values,
        "q_hi": preds["q_hi"].values,
        "midpoint": preds["midpoint"].values,
        "covered": (y_true >= preds["q_lo"].values) & (y_true <= preds["q_hi"].values),
        "interval_width": preds["q_hi"].values - preds["q_lo"].values,
        "horizon": horizon,
        "target": target_col,
        "coverage_target": coverage,
    })
    actual_cov = float(result["covered"].mean())
    log.info("cqr_walk_forward_done",
             horizon=horizon, target=target_col, n_test=len(result),
             actual_coverage=round(actual_cov, 3), target_coverage=coverage)
    return result
