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

Operational note
----------------
``walk_forward_cqr`` refits quantile models + conformal dilation on each study-style
walk-forward block (embargo, ``test_size=252``). Calibration rows sit immediately
before each test block; default ``cal_ratio=0.20``. The dilation uses a discrete
rank quantile ``ceil((n+1)(1-alpha))`` on calibration scores.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.meta.cqr")


def _finite_sample_residual_quantile(scores: np.ndarray, miscoverage: float) -> float:
    """Discrete upper envelope S_(k) with k = ceil((n+1)(1-miscoverage)), Romano et al. style."""
    arr = np.asarray(scores, dtype=float)
    arr = arr[np.isfinite(arr)]
    n = len(arr)
    if n == 0:
        return 0.0
    s = np.sort(arr)
    k = int(np.ceil((n + 1) * (1.0 - miscoverage)))
    k = min(max(k, 1), n)
    return float(max(0.0, s[k - 1]))


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

    def fit(
        self,
        x_train: pd.DataFrame,
        y_train: pd.Series,
        x_cal: pd.DataFrame,
        y_cal: pd.Series,
    ) -> CQRModel:
        """Fit quantile models on train, calibrate conformal correction on cal."""
        from sklearn.impute import SimpleImputer

        imp = SimpleImputer(strategy="median", keep_empty_features=True)
        x_tr = imp.fit_transform(x_train)
        x_cal_arr = imp.transform(x_cal)
        self._imp = imp

        y_tr = np.asarray(y_train, dtype=float)
        y_cal_vals = np.asarray(y_cal, dtype=float)

        self._lo_model.fit(x_tr, y_tr)
        self._hi_model.fit(x_tr, y_tr)

        lo_cal = self._lo_model.predict(x_cal_arr)
        hi_cal = self._hi_model.predict(x_cal_arr)

        scores = np.maximum(lo_cal - y_cal_vals, y_cal_vals - hi_cal)
        n = len(scores)
        self._e = max(0.0, _finite_sample_residual_quantile(scores, self.alpha))
        self._fitted = True
        log.info(
            "cqr_calibrated",
            e=round(self._e, 5),
            coverage=self.coverage,
            n_cal=n,
        )
        return self

    def predict_intervals(self, x_in: pd.DataFrame) -> pd.DataFrame:
        """Return a DataFrame with columns: q_lo, q_hi, midpoint."""
        if not self._fitted:
            raise RuntimeError("Call fit() before predict_intervals()")
        x_mat = self._imp.transform(x_in)
        lo = self._lo_model.predict(x_mat) - self._e
        hi = self._hi_model.predict(x_mat) + self._e
        return pd.DataFrame(
            {
                "q_lo": lo,
                "q_hi": hi,
                "midpoint": (lo + hi) / 2.0,
            },
            index=x_in.index,
        )


def _iter_walk_windows(
    n: int,
    horizon: int,
    initial_ratio: float,
    test_size: int,
    min_train_positions: int,
) -> list[tuple[int, int, int]]:
    """Windows aligned with study walk-forward: (train_hi_exclusive, test_start, test_end).

    Rows [train_hi, test_start) form an embargo gap (length ~ horizon).
    Calibration lives in [cal_lo, train_hi); strict train in [0, cal_lo).
    """
    emb = max(int(horizon), 10)
    out: list[tuple[int, int, int]] = []
    if n < 600:
        cut = int(0.75 * n)
        train_hi = max(1, cut - emb)
        test_end = n
        lo_thr = min(min_train_positions, max(80, n // 4))
        if test_end - cut >= 40 and train_hi >= lo_thr:
            out.append((train_hi, cut, test_end))
        return out
    start = int(n * initial_ratio)
    while start < n:
        train_hi = max(1, start - emb)
        test_end = min(n, start + test_size)
        if test_end - start >= 40 and train_hi >= min_train_positions:
            out.append((train_hi, start, test_end))
        start += test_size
    return out


def walk_forward_cqr(
    features: pd.DataFrame,
    targets: pd.DataFrame,
    factor_cols: list[str],
    target_col: str,
    horizon: int,
    coverage: float = 0.90,
    initial_ratio: float = 0.60,
    cal_ratio: float = 0.20,
    test_size: int = 252,
    min_train_rows: int = 500,
    min_cal_rows: int = 120,
) -> pd.DataFrame:
    """Walk-forward CQR: refit quantiles + conformal dilation each test block.

    Each fold uses strict train → calibration (tail of pre-test history) → embargo → test,
    mirroring the embargo logic of the professional study walk-forward.
    """
    date_col = "Date"
    merged = features.merge(targets[[date_col, target_col]], on=date_col, how="inner")
    merged = merged.dropna(subset=[target_col]).reset_index(drop=True)
    n = len(merged)
    if n < 400:
        log.warning("cqr_too_few_rows", n=n)
        return pd.DataFrame()

    cal_len = max(int(round(n * cal_ratio)), min_cal_rows)
    windows = _iter_walk_windows(n, horizon, initial_ratio, test_size, min_train_rows)

    from sklearn.impute import SimpleImputer

    frames: list[pd.DataFrame] = []
    for train_hi, test_start, test_end in windows:
        cal_lo = train_hi - cal_len
        if cal_lo < min_train_rows:
            continue
        if train_hi <= cal_lo:
            continue
        train = merged.iloc[:cal_lo]
        cal = merged.iloc[cal_lo:train_hi]
        test = merged.iloc[test_start:test_end]
        if len(cal) < min_cal_rows or len(test) < 20:
            continue

        imp = SimpleImputer(strategy="median", keep_empty_features=True)
        x_train_raw = train[factor_cols].replace([np.inf, -np.inf], np.nan)
        imp.fit(x_train_raw)
        x_train_df = pd.DataFrame(
            imp.transform(x_train_raw),
            columns=factor_cols,
            index=train.index,
        )
        x_cal_df = pd.DataFrame(
            imp.transform(cal[factor_cols].replace([np.inf, -np.inf], np.nan)),
            columns=factor_cols,
            index=cal.index,
        )
        x_test_df = pd.DataFrame(
            imp.transform(test[factor_cols].replace([np.inf, -np.inf], np.nan)),
            columns=factor_cols,
            index=test.index,
        )

        cqr = CQRModel(coverage=coverage)
        cqr.fit(x_train_df, train[target_col], x_cal_df, cal[target_col])
        preds = cqr.predict_intervals(x_test_df)
        y_true = test[target_col].values
        frames.append(
            pd.DataFrame(
                {
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
                }
            )
        )

    if not frames:
        log.warning("cqr_no_valid_fold", n=n, horizon=horizon)
        return pd.DataFrame()

    result = pd.concat(frames, ignore_index=True)
    actual_cov = float(result["covered"].mean())
    log.info(
        "cqr_walk_forward_done",
        horizon=horizon,
        target=target_col,
        n_test=len(result),
        n_folds=len(frames),
        cal_ratio=cal_ratio,
        actual_coverage=round(actual_cov, 3),
        target_coverage=coverage,
    )
    return result
