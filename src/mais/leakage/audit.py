"""Automated anti-leakage audit.

Five independent checks (each one is a unit test in tests/unit/test_leakage.py):

1. SHAPE_ALIGNMENT     features and targets share the same date index.
2. NAMING_CONVENTION   no feature column starts with ``y_`` (reserved for targets).
3. PERFECT_FIT         no feature column has |corr| > threshold with any target on the
                       overlap window (threshold default 0.97). High corr usually means
                       the feature is a transformation of the future target.
4. FUTURE_FUNCTION     for each feature, run a single-row check: shifting the underlying
                       series by -1 should NOT improve correlation with the target. In
                       other words, the feature value at time t must not depend on
                       prices/data at time > t.
5. SUSPECT_NAMES       no header that looks like a number (legacy bug: ``5.98``) or that
                       ends with ``.1`` (pandas merge collision).

The audit returns a ``LeakageAudit`` dataclass and writes a parquet report to
``data/metadata/anti_leakage_audit.parquet``. ``mais audit-leakage`` exits with
non-zero status when any check fails.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import LEAKAGE_AUDIT_PARQUET
from mais.utils import get_logger, write_parquet

log = get_logger("mais.leakage")


_SUSPECT_NUMERIC_HEADER = re.compile(r"^-?\d")
_TARGET_PREFIX = "y_"


@dataclass
class LeakageAudit:
    n_features: int = 0
    n_targets: int = 0
    suspect_names: list[str] = field(default_factory=list)
    naming_violations: list[str] = field(default_factory=list)
    perfect_fit: list[tuple[str, str, float]] = field(default_factory=list)
    future_dependent: list[tuple[str, str, float]] = field(default_factory=list)
    shape_misalignment: bool = False
    rows_features: int = 0
    rows_targets: int = 0

    @property
    def passed(self) -> bool:
        return (
            not self.shape_misalignment
            and not self.suspect_names
            and not self.naming_violations
            and not self.perfect_fit
            and not self.future_dependent
        )

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"[{status}] features={self.n_features} targets={self.n_targets} "
            f"suspect_names={len(self.suspect_names)} "
            f"naming={len(self.naming_violations)} "
            f"perfect_fit={len(self.perfect_fit)} "
            f"future_dep={len(self.future_dependent)}"
        )


def _is_suspect_name(name: str) -> bool:
    s = str(name)
    if not s:
        return True
    if _SUSPECT_NUMERIC_HEADER.match(s):
        return True
    if s.endswith(".1"):  # pandas merge collision artefact
        return True
    if s.lower() in {"unnamed: 0", "unnamed:_0", "index"}:
        return True
    return False


def _safe_corr(x: pd.Series, y: pd.Series) -> float:
    common = x.notna() & y.notna()
    if common.sum() < 30:
        return np.nan
    a = x[common].astype(float).values
    b = y[common].astype(float).values
    if a.std() == 0 or b.std() == 0:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def audit_features_targets(
    features: pd.DataFrame,
    targets: pd.DataFrame,
    date_col: str = "Date",
    perfect_fit_threshold: float = 0.97,
    future_fn_min_improvement: float = 0.05,
    write_report_to: Path | str | None = LEAKAGE_AUDIT_PARQUET,
) -> LeakageAudit:
    """Run the 5 anti-leakage checks and return a ``LeakageAudit``.

    Parameters
    ----------
    features
        DataFrame with ``date_col`` and feature columns. None should start with ``y_``.
    targets
        DataFrame with ``date_col`` and target columns. All should start with ``y_``.
    perfect_fit_threshold
        Maximum allowed |corr(feature_t, target_t)| over the same-date overlap.
        Above that, the feature is suspected of being a transformation of the future.
    future_fn_min_improvement
        For check 4, if shifting the feature by -1 (i.e. peeking 1 step into the future)
        improves |corr| with the target by more than this delta, the feature is flagged.
    """
    audit = LeakageAudit()

    # ---- Check 5: suspect names ----
    audit.suspect_names = [c for c in features.columns if _is_suspect_name(str(c))]
    audit.suspect_names += [c for c in targets.columns if _is_suspect_name(str(c)) and c != date_col]

    # ---- Check 2: naming convention ----
    audit.naming_violations = [
        c for c in features.columns if c != date_col and str(c).startswith(_TARGET_PREFIX)
    ]
    feature_cols = [
        c for c in features.columns
        if c != date_col and not str(c).startswith(_TARGET_PREFIX)
    ]
    target_cols = [c for c in targets.columns if c != date_col and str(c).startswith(_TARGET_PREFIX)]
    audit.n_features = len(feature_cols)
    audit.n_targets = len(target_cols)
    audit.rows_features = len(features)
    audit.rows_targets = len(targets)

    # ---- Check 1: shape alignment ----
    if date_col not in features.columns or date_col not in targets.columns:
        audit.shape_misalignment = True
        log.warning("date_col_missing", date_col=date_col)
    else:
        f_dates = pd.to_datetime(features[date_col]).dt.normalize()
        t_dates = pd.to_datetime(targets[date_col]).dt.normalize()
        overlap = f_dates.isin(t_dates).sum()
        if overlap < 0.95 * min(len(f_dates), len(t_dates)):
            audit.shape_misalignment = True
            log.warning("shape_misalignment", overlap=int(overlap),
                        n_f=len(f_dates), n_t=len(t_dates))

    if audit.shape_misalignment:
        if write_report_to:
            _write_report(audit, write_report_to)
        return audit

    merged = features.merge(targets, on=date_col, how="inner", suffixes=("", "_tgt"))

    # ---- Check 3: perfect fit (suspicious correlation) ----
    for tcol in target_cols:
        if tcol not in merged:
            continue
        for fcol in feature_cols:
            if fcol not in merged:
                continue
            r = _safe_corr(merged[fcol], merged[tcol])
            if not np.isnan(r) and abs(r) >= perfect_fit_threshold:
                audit.perfect_fit.append((fcol, tcol, round(r, 4)))

    # ---- Check 4: future-function dependency (cheap proxy) ----
    # For each feature, compare corr(feature_t, target_t) vs corr(feature_{t+1}, target_t).
    # If the second is strictly larger by `future_fn_min_improvement`, the feature
    # already encodes some of the future information that the target uses.
    for tcol in target_cols:
        if tcol not in merged:
            continue
        y = merged[tcol]
        for fcol in feature_cols:
            if fcol not in merged:
                continue
            x = merged[fcol]
            base = _safe_corr(x, y)
            shifted = _safe_corr(x.shift(-1), y)
            if (
                not np.isnan(base)
                and not np.isnan(shifted)
                and abs(shifted) - abs(base) > future_fn_min_improvement
                and abs(shifted) > 0.10
            ):
                audit.future_dependent.append((fcol, tcol, round(abs(shifted) - abs(base), 4)))

    log.info("leakage_audit_done", **{
        "passed": audit.passed,
        "suspect_names": len(audit.suspect_names),
        "naming_violations": len(audit.naming_violations),
        "perfect_fit": len(audit.perfect_fit),
        "future_dependent": len(audit.future_dependent),
    })

    if write_report_to:
        _write_report(audit, write_report_to)
    return audit


def _write_report(audit: LeakageAudit, path: Path | str) -> None:
    rows = []
    for n in audit.suspect_names:
        rows.append({"check": "suspect_name", "feature": n, "target": None, "score": None})
    for n in audit.naming_violations:
        rows.append({"check": "naming_violation", "feature": n, "target": None, "score": None})
    for f, t, r in audit.perfect_fit:
        rows.append({"check": "perfect_fit", "feature": f, "target": t, "score": r})
    for f, t, r in audit.future_dependent:
        rows.append({"check": "future_dependent", "feature": f, "target": t, "score": r})
    if audit.shape_misalignment:
        rows.append({"check": "shape_misalignment", "feature": None, "target": None, "score": None})
    df = pd.DataFrame(rows, columns=["check", "feature", "target", "score"])
    write_parquet(df, path)
