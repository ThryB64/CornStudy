"""Auto-profile any CSV/Parquet dataset.

The point: 'plug n play' was the user's stated goal. Instead of letting
40 incompatible models run silently and crash, the profiler:

  1. Loads the file
  2. Detects whether it's a time series (Date column or sortable index)
  3. Detects each column's role (target candidate, numeric feature, categorical, bool)
  4. For each candidate target, detects task type (regression/binary/multiclass)
  5. Returns the list of compatible models from the registry

This is the ROUTER mentioned in the audit's section 6.2.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.models import ModelRequirement, ModelTask, get_compatible_models
from mais.utils import read_table


@dataclass
class DatasetProfile:
    n_rows: int
    n_cols: int
    is_time_series: bool
    date_col: str | None
    numeric_cols: list[str] = field(default_factory=list)
    boolean_cols: list[str] = field(default_factory=list)
    categorical_cols: list[str] = field(default_factory=list)
    candidate_targets: dict[str, dict[str, Any]] = field(default_factory=dict)
    requirements: set[ModelRequirement] = field(default_factory=set)
    missing_rate: dict[str, float] = field(default_factory=dict)
    high_cardinality_cols: list[str] = field(default_factory=list)
    suggested_preprocessing: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Dataset profile",
            f"  rows = {self.n_rows}, cols = {self.n_cols}",
            f"  time_series = {self.is_time_series}, date_col = {self.date_col}",
            f"  numeric = {len(self.numeric_cols)}, bool = {len(self.boolean_cols)}, "
            f"categorical = {len(self.categorical_cols)}",
            f"  requirements = {sorted(r.value for r in self.requirements)}",
            f"  high_cardinality = {len(self.high_cardinality_cols)}",
            f"",
            "Suggested preprocessing:",
            *[f"  - {s}" for s in self.suggested_preprocessing],
            f"",
            f"Candidate targets ({len(self.candidate_targets)}):",
        ]
        for col, info in self.candidate_targets.items():
            lines.append(f"  - {col:30s} task={info['task']:12s} "
                          f"unique={info['n_unique']} compatible_models={info['n_compatible']}")
        return "\n".join(lines)


def _detect_date_column(df: pd.DataFrame) -> str | None:
    for c in df.columns:
        if str(c).lower() in {"date", "datetime", "timestamp", "time"}:
            try:
                _ = pd.to_datetime(df[c], errors="raise")
                return c
            except Exception:
                continue
    # Try parsing first column
    c0 = df.columns[0]
    try:
        s = pd.to_datetime(df[c0], errors="raise")
        if s.is_monotonic_increasing:
            return c0
    except Exception:
        pass
    return None


def _classify_target(s: pd.Series) -> tuple[ModelTask, int]:
    s = s.dropna()
    if pd.api.types.is_bool_dtype(s):
        return ModelTask.BINARY, 2
    if pd.api.types.is_numeric_dtype(s):
        nu = s.nunique()
        if nu == 2:
            return ModelTask.BINARY, 2
        if nu < 12 and (s.astype(int) == s).all():
            return ModelTask.MULTICLASS, nu
        return ModelTask.REGRESSION, nu
    nu = s.nunique()
    if nu == 2:
        return ModelTask.BINARY, 2
    if nu < 30:
        return ModelTask.MULTICLASS, nu
    return ModelTask.REGRESSION, nu


def profile_dataset(path: str | Path) -> str:
    df = read_table(path)
    return _profile_to_summary(df, path)


def profile_dataset_json(path: str | Path) -> str:
    df = read_table(path)
    profile = build_profile(df)
    data = asdict(profile)
    data["requirements"] = sorted(r.value for r in profile.requirements)
    return json.dumps(data, ensure_ascii=True, indent=2)


def _profile_to_summary(df: pd.DataFrame, path) -> str:
    profile = build_profile(df)
    p = Path(path) if path else Path(".")
    return profile.summary() + (
        f"\n\nFile: {p}\n"
        f"Use `mais train --target <name> --model <name>` to train one of these.\n"
    )


def build_profile(df: pd.DataFrame) -> DatasetProfile:
    date_col = _detect_date_column(df)
    is_ts = date_col is not None

    profile = DatasetProfile(
        n_rows=len(df), n_cols=df.shape[1],
        is_time_series=is_ts, date_col=date_col,
    )

    for c in df.columns:
        if c == date_col:
            continue
        s = df[c]
        profile.missing_rate[str(c)] = float(s.isna().mean())
        if pd.api.types.is_bool_dtype(s):
            profile.boolean_cols.append(c)
        elif pd.api.types.is_numeric_dtype(s):
            profile.numeric_cols.append(c)
        else:
            profile.categorical_cols.append(c)
            if s.nunique(dropna=True) > min(100, max(20, len(df) // 20)):
                profile.high_cardinality_cols.append(c)

    if is_ts:
        profile.suggested_preprocessing.append("Use walk-forward validation with chronological splits.")
    if profile.categorical_cols:
        profile.suggested_preprocessing.append("One-hot encode low-cardinality categoricals; target/hash encode high-cardinality columns.")
    if any(v > 0.2 for v in profile.missing_rate.values()):
        profile.suggested_preprocessing.append("Add missingness indicators for columns with >20% missing values.")
    if profile.numeric_cols:
        skewed = []
        for c in profile.numeric_cols:
            s = pd.to_numeric(df[c], errors="coerce").dropna()
            if len(s) > 20 and abs(float(s.skew())) > 2:
                skewed.append(c)
        if skewed:
            profile.suggested_preprocessing.append(f"Consider log/yeo-johnson transforms for skewed numeric columns: {', '.join(skewed[:8])}.")

    profile.requirements = {ModelRequirement.EXOGENOUS}
    if is_ts:
        profile.requirements.add(ModelRequirement.TIME_INDEX)

    # Candidate targets: numeric or boolean columns starting with y_ or marked
    candidates = []
    for c in df.columns:
        if c == date_col:
            continue
        sc = str(c).lower()
        if sc.startswith("y_") or sc in {"target", "label", "y"}:
            candidates.append(c)
    if not candidates:
        # No obvious naming - everything numeric is a candidate
        candidates = profile.numeric_cols + profile.boolean_cols

    for c in candidates:
        task, nu = _classify_target(df[c])
        compatible = get_compatible_models(task, profile.requirements, profile.n_rows)
        profile.candidate_targets[c] = {
            "task": task.value, "n_unique": nu, "n_compatible": len(compatible),
            "compatible": compatible[:10],
        }

    return profile
