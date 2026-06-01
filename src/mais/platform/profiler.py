"""Auto-profile any CSV/Parquet dataset for AutoML.

Returns a structured ProfileReport used by preprocessing and reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from mais.utils import get_logger

log = get_logger("mais.platform.profiler")

# Problem types
REGRESSION = "regression"
BINARY = "binary"
MULTICLASS = "multiclass"
ORDINAL = "ordinal"
TS_UNIVARIATE = "timeseries_univariate"
TS_MULTIVARIATE = "timeseries_multivariate"

# Split strategies
WALK_FORWARD = "walk_forward"
KFOLD = "kfold"
STRATIFIED = "stratified_kfold"

# Compatible model sets by problem type
_MODELS_REGRESSION = ["ridge", "rf", "hgb", "lgbm", "xgb"]
_MODELS_BINARY = ["logistic", "rf", "lgbm", "hgb"]
_MODELS_MULTICLASS = ["rf", "lgbm", "logistic"]
_MODELS_TS = ["seasonal_naive", "historical_mean", "ridge", "rf", "hgb", "lgbm"]

_COMPATIBLE: dict[str, list[str]] = {
    REGRESSION: _MODELS_REGRESSION,
    BINARY: _MODELS_BINARY,
    MULTICLASS: _MODELS_MULTICLASS,
    ORDINAL: _MODELS_MULTICLASS,
    TS_UNIVARIATE: _MODELS_TS,
    TS_MULTIVARIATE: _MODELS_TS,
}

_SPLIT: dict[str, str] = {
    REGRESSION: KFOLD,
    BINARY: STRATIFIED,
    MULTICLASS: STRATIFIED,
    ORDINAL: STRATIFIED,
    TS_UNIVARIATE: WALK_FORWARD,
    TS_MULTIVARIATE: WALK_FORWARD,
}


@dataclass
class ProfileReport:
    n_rows: int
    n_cols: int
    problem_type: str
    target_col: str
    date_col: str | None
    split_recommendation: str
    numeric_cols: list[str] = field(default_factory=list)
    categorical_cols: list[str] = field(default_factory=list)
    boolean_cols: list[str] = field(default_factory=list)
    id_cols: list[str] = field(default_factory=list)
    compatible_models: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_rate: dict[str, float] = field(default_factory=dict)
    n_unique_target: int = 0
    is_time_series: bool = False

    def summary(self) -> str:
        lines = [
            "ProfileReport",
            f"  rows={self.n_rows}  cols={self.n_cols}  problem_type={self.problem_type}",
            f"  target={self.target_col}  date_col={self.date_col}",
            f"  split={self.split_recommendation}",
            f"  numeric={len(self.numeric_cols)}  categorical={len(self.categorical_cols)}"
            f"  boolean={len(self.boolean_cols)}  id={len(self.id_cols)}",
            f"  compatible_models={self.compatible_models}",
        ]
        if self.warnings:
            lines.append(f"  warnings ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"    - {w}")
        return "\n".join(lines)


def _detect_date_col(df: pd.DataFrame) -> str | None:
    date_names = {"date", "datetime", "timestamp", "time", "week_ending", "period"}
    for c in df.columns:
        if str(c).lower() in date_names:
            try:
                pd.to_datetime(df[c], errors="raise")
                return c
            except Exception:
                continue
    # Heuristic: first column parseable as monotonic dates
    c0 = df.columns[0]
    try:
        s = pd.to_datetime(df[c0], errors="raise")
        if s.is_monotonic_increasing:
            return c0
    except Exception:
        pass
    return None


def _detect_problem_type(series: pd.Series, is_ts: bool, n_exogenous: int) -> tuple[str, int]:
    s = series.dropna()
    n_unique = int(s.nunique())

    if pd.api.types.is_bool_dtype(s) or n_unique == 2:
        return BINARY, 2

    if pd.api.types.is_numeric_dtype(s):
        if n_unique <= 2:
            return BINARY, n_unique
        if n_unique < 15 and _is_integer_like(s):
            # Could be ordinal
            vals = sorted(s.unique())
            if vals == list(range(min(vals), max(vals) + 1)):
                return ORDINAL, n_unique
            return MULTICLASS, n_unique
        # Numeric with many values → regression or TS
        if is_ts:
            return (TS_MULTIVARIATE if n_exogenous > 0 else TS_UNIVARIATE), n_unique
        return REGRESSION, n_unique

    # Categorical string
    if n_unique == 2:
        return BINARY, 2
    if n_unique < 30:
        return MULTICLASS, n_unique
    return REGRESSION, n_unique


def _is_integer_like(s: pd.Series) -> bool:
    try:
        return bool((s.dropna() == s.dropna().astype(int)).all())
    except Exception:
        return False


def _detect_id_cols(df: pd.DataFrame, date_col: str | None) -> list[str]:
    ids = []
    for c in df.columns:
        if c == date_col:
            continue
        sl = str(c).lower()
        if sl in {"id", "index", "key", "uuid", "rowid"} or sl.endswith("_id"):
            ids.append(c)
            continue
        if pd.api.types.is_object_dtype(df[c]) and df[c].nunique() == len(df):
            ids.append(c)
    return ids


def _build_warnings(
    df: pd.DataFrame,
    target_col: str,
    date_col: str | None,
    numeric_cols: list[str],
    missing_threshold: float = 0.20,
    corr_threshold: float = 0.97,
) -> list[str]:
    warnings: list[str] = []
    feature_cols = [c for c in numeric_cols if c != target_col and c != date_col]

    # Missing rate warnings
    for c in df.columns:
        if c == date_col:
            continue
        rate = float(df[c].isna().mean())
        if rate >= missing_threshold:
            warnings.append(f"high_missing_rate: {c} ({rate:.0%})")

    # Collinearity warning (cheap: only first 30 numeric features)
    if len(feature_cols) >= 2:
        sample = feature_cols[:30]
        sub = df[sample].dropna(axis=1)
        if len(sub.columns) >= 2:
            try:
                corr = sub.corr().abs()
                upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
                high_pairs = [
                    (c, r)
                    for c in upper.columns
                    for r in upper.index
                    if pd.notna(upper.loc[r, c]) and upper.loc[r, c] >= corr_threshold
                ]
                if high_pairs:
                    warnings.append(
                        f"high_collinearity: {len(high_pairs)} pairs ≥{corr_threshold:.0%}"
                        f" (e.g. {high_pairs[0][0]} × {high_pairs[0][1]})"
                    )
            except Exception:
                pass

    # Target imbalance for classification
    if target_col in df.columns:
        s = df[target_col].dropna()
        if not pd.api.types.is_numeric_dtype(s) or s.nunique() <= 10:
            vc = s.value_counts(normalize=True)
            if len(vc) >= 2 and vc.iloc[-1] < 0.10:
                warnings.append(f"class_imbalance: minority class {vc.index[-1]} = {vc.iloc[-1]:.1%}")

    return warnings


def profile_dataset(
    path: str | Path,
    target_col: str | None = None,
    date_col: str | None = None,
) -> ProfileReport:
    """Load a CSV/Parquet and return a ProfileReport.

    Parameters
    ----------
    path:       path to CSV or Parquet file
    target_col: column to predict; auto-detected if None
    date_col:   date column; auto-detected if None
    """
    path = Path(path)
    df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path, low_memory=False)

    log.info("profiler_loaded", path=str(path), rows=len(df), cols=df.shape[1])

    if date_col is None:
        date_col = _detect_date_col(df)
    is_ts = date_col is not None

    # Classify columns
    id_cols = _detect_id_cols(df, date_col)
    skip = set(id_cols) | ({date_col} if date_col else set())

    numeric_cols, categorical_cols, boolean_cols = [], [], []
    for c in df.columns:
        if c in skip:
            continue
        if pd.api.types.is_bool_dtype(df[c]):
            boolean_cols.append(c)
        elif pd.api.types.is_numeric_dtype(df[c]):
            numeric_cols.append(c)
        else:
            categorical_cols.append(c)

    # Auto-detect target
    if target_col is None:
        for c in df.columns:
            if str(c).lower() in {"target", "label", "y", "y_true"}:
                target_col = c
                break
        if target_col is None and (numeric_cols or boolean_cols):
            target_col = (numeric_cols + boolean_cols)[0]
    if target_col is None:
        target_col = df.columns[-1]

    n_exogenous = len([c for c in numeric_cols + boolean_cols if c != target_col])
    problem_type, n_unique = _detect_problem_type(df[target_col], is_ts, n_exogenous)
    split_rec = _SPLIT[problem_type]
    compatible = _COMPATIBLE.get(problem_type, _MODELS_REGRESSION)

    missing_rate = {
        c: float(df[c].isna().mean())
        for c in df.columns
        if c not in skip and df[c].isna().any()
    }
    warnings = _build_warnings(df, target_col, date_col, numeric_cols + boolean_cols)

    report = ProfileReport(
        n_rows=len(df),
        n_cols=df.shape[1],
        problem_type=problem_type,
        target_col=target_col,
        date_col=date_col,
        split_recommendation=split_rec,
        numeric_cols=numeric_cols,
        categorical_cols=categorical_cols,
        boolean_cols=boolean_cols,
        id_cols=id_cols,
        compatible_models=compatible,
        warnings=warnings,
        missing_rate=missing_rate,
        n_unique_target=n_unique,
        is_time_series=is_ts,
    )
    log.info(
        "profiler_done",
        problem_type=problem_type,
        target=target_col,
        warnings=len(warnings),
    )
    return report
