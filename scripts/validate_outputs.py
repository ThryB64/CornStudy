#!/usr/bin/env python3
"""Strict V2 validation script.

This script validates the rebuilt base end-to-end and writes:
  - docs/VALIDATION_REPORT.md

Checks implemented
------------------
1. Absence of ghost columns
2. Absence of duplicate columns
3. Date alignment between features and targets
4. NaN rate per column
5. Coherence of targets y_logret_h5/h10/h20/h30
6. Obvious temporal leakage (reusing leakage audit)
7. Presence of outputs required by stacking and farmer advice
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.leakage.audit import audit_features_targets
from mais.paths import (
    ARTEFACTS_DIR,
    FEATURES_PARQUET,
    INTERIM_DIR,
    META_DB_PARQUET,
    PROCESSED_DIR,
    TARGETS_PARQUET,
)


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str


def _is_ghost_name(name: str) -> bool:
    s = str(name)
    if not s:
        return True
    if s.endswith(".1"):
        return True
    if s[0].isdigit():
        return True
    if s.startswith("-") and len(s) > 1 and s[1].isdigit():
        return True
    if s.lower().startswith("unnamed:"):
        return True
    return False


def _load_required() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not FEATURES_PARQUET.exists():
        raise FileNotFoundError(f"Missing: {FEATURES_PARQUET}")
    if not TARGETS_PARQUET.exists():
        raise FileNotFoundError(f"Missing: {TARGETS_PARQUET}")
    legacy_db = INTERIM_DIR / "database.parquet"
    if not legacy_db.exists():
        raise FileNotFoundError(f"Missing: {legacy_db}")
    features = pd.read_parquet(FEATURES_PARQUET)
    targets = pd.read_parquet(TARGETS_PARQUET)
    db = pd.read_parquet(legacy_db)
    return features, targets, db


def check_ghost_columns(features: pd.DataFrame, targets: pd.DataFrame) -> CheckResult:
    ghosts = [c for c in features.columns if _is_ghost_name(str(c))]
    ghosts += [c for c in targets.columns if _is_ghost_name(str(c)) and c != "Date"]
    ghosts = sorted(set(map(str, ghosts)))
    return CheckResult(
        name="Ghost Columns",
        passed=len(ghosts) == 0,
        details="None" if not ghosts else f"{len(ghosts)} found: {ghosts[:15]}",
    )


def check_duplicate_columns(features: pd.DataFrame, targets: pd.DataFrame) -> CheckResult:
    dup_f = features.columns[features.columns.duplicated()].tolist()
    dup_t = targets.columns[targets.columns.duplicated()].tolist()
    dup = sorted(set(map(str, dup_f + dup_t)))
    return CheckResult(
        name="Duplicate Columns",
        passed=len(dup) == 0,
        details="None" if not dup else f"{len(dup)} duplicates: {dup[:15]}",
    )


def check_date_alignment(features: pd.DataFrame, targets: pd.DataFrame) -> CheckResult:
    fd = pd.to_datetime(features["Date"]).dt.normalize()
    td = pd.to_datetime(targets["Date"]).dt.normalize()
    overlap = fd.isin(td).sum()
    threshold = int(0.95 * min(len(fd), len(td)))
    passed = overlap >= threshold
    return CheckResult(
        name="Date Alignment Features/Targets",
        passed=passed,
        details=f"overlap={overlap}, threshold={threshold}, features={len(fd)}, targets={len(td)}",
    )


def check_nan_rate(features: pd.DataFrame, targets: pd.DataFrame) -> tuple[CheckResult, pd.DataFrame]:
    all_df = pd.concat(
        [features.drop(columns=["Date"], errors="ignore"), targets.drop(columns=["Date"], errors="ignore")],
        axis=1,
    )
    nan_rates = all_df.isna().mean().sort_values(ascending=False)
    report = nan_rates.rename("nan_rate").reset_index().rename(columns={"index": "column"})
    very_high = report[report["nan_rate"] > 0.95]
    passed = len(very_high) == 0
    details = (
        "No column >95% NaN"
        if passed
        else f"{len(very_high)} columns >95% NaN (top: {very_high.head(10).to_dict(orient='records')})"
    )
    return CheckResult(name="NaN Rate by Column", passed=passed, details=details), report


def check_target_coherence(targets: pd.DataFrame, db: pd.DataFrame) -> CheckResult:
    required = ["y_logret_h5", "y_logret_h10", "y_logret_h20", "y_logret_h30"]
    missing = [c for c in required if c not in targets.columns]
    if missing:
        return CheckResult("Target Coherence y_logret_h*", False, f"Missing targets: {missing}")
    if "corn_close" not in db.columns:
        return CheckResult("Target Coherence y_logret_h*", False, "database.parquet missing corn_close")

    base = db[["Date", "corn_close"]].copy()
    base["Date"] = pd.to_datetime(base["Date"])
    base = base.sort_values("Date").drop_duplicates("Date", keep="last")
    tgt = targets[["Date"] + required].copy()
    tgt["Date"] = pd.to_datetime(tgt["Date"])
    m = tgt.merge(base, on="Date", how="inner")
    p = np.log(m["corn_close"].astype(float))
    errs: dict[str, float] = {}
    valid_counts: dict[str, int] = {}
    for h in [5, 10, 20, 30]:
        y_expected = p.shift(-h) - p
        col = f"y_logret_h{h}"
        diff = (m[col] - y_expected).abs()
        valid = diff.notna()
        valid_counts[col] = int(valid.sum())
        errs[col] = float(diff[valid].mean()) if valid.any() else float("nan")

    max_err = max(v for v in errs.values() if not np.isnan(v))
    passed = max_err < 1e-10
    details = f"mean_abs_error={errs}, valid_rows={valid_counts}"
    return CheckResult("Target Coherence y_logret_h*", passed, details)


def check_temporal_leakage(features: pd.DataFrame, targets: pd.DataFrame) -> CheckResult:
    audit = audit_features_targets(features, targets, write_report_to=None)
    details = (
        f"passed={audit.passed}, suspect={len(audit.suspect_names)}, "
        f"naming={len(audit.naming_violations)}, perfect_fit={len(audit.perfect_fit)}, "
        f"future_dep={len(audit.future_dependent)}"
    )
    return CheckResult("Obvious Temporal Leakage", audit.passed, details)


def check_required_outputs() -> CheckResult:
    needed = [
        FEATURES_PARQUET,
        TARGETS_PARQUET,
        ARTEFACTS_DIR / "training_summary.csv",
        META_DB_PARQUET,
        ARTEFACTS_DIR / "meta_predictions.parquet",
        ARTEFACTS_DIR / "predictions" / "y_logret_h20" / "ridge_reg.parquet",
    ]
    missing = [str(p) for p in needed if not p.exists()]
    return CheckResult(
        name="Required Outputs (stacking + advisor)",
        passed=len(missing) == 0,
        details="All present" if not missing else f"Missing: {missing}",
    )


def render_markdown(
    checks: list[CheckResult],
    nan_report: pd.DataFrame,
    out_path: Path,
    command_results: dict[str, str] | None = None,
) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    ok = sum(c.passed for c in checks)
    total = len(checks)
    status = "PASS" if ok == total else "FAIL"

    lines = []
    lines.append("# Validation Report")
    lines.append("")
    lines.append(f"- Generated at: `{ts}`")
    lines.append(f"- Overall status: **{status}** ({ok}/{total} checks passed)")
    lines.append("")

    if command_results:
        lines.append("## Command Execution Status")
        lines.append("")
        for cmd, result in command_results.items():
            badge = "PASS" if result.startswith("PASS") else "FAIL"
            lines.append(f"- `{cmd}`: **{badge}** - {result}")
        lines.append("")

    lines.append("## Validation Checks")
    lines.append("")
    for c in checks:
        badge = "PASS" if c.passed else "FAIL"
        lines.append(f"### {c.name}")
        lines.append(f"- Status: **{badge}**")
        lines.append(f"- Details: {c.details}")
        lines.append("")

    lines.append("## Top NaN Rates")
    lines.append("")
    top = nan_report.head(20).copy()
    if top.empty:
        lines.append("- No numeric columns to report.")
    else:
        lines.append("| Column | NaN rate |")
        lines.append("|---|---:|")
        for _, row in top.iterrows():
            lines.append(f"| `{row['column']}` | {row['nan_rate']:.4f} |")
    lines.append("")

    lines.append("## Conclusion")
    lines.append("")
    if status == "PASS":
        lines.append("- The rebuilt V2 base is technically consistent for the validated scope.")
        lines.append("- Next step can safely focus on data/source quality and model realism.")
    else:
        lines.append("- Validation failed on one or more strict checks.")
        lines.append("- Fix failing checks before adding any new feature.")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    features, targets, db = _load_required()
    checks: list[CheckResult] = []

    checks.append(check_ghost_columns(features, targets))
    checks.append(check_duplicate_columns(features, targets))
    checks.append(check_date_alignment(features, targets))
    nan_check, nan_report = check_nan_rate(features, targets)
    checks.append(nan_check)
    checks.append(check_target_coherence(targets, db))
    checks.append(check_temporal_leakage(features, targets))
    checks.append(check_required_outputs())

    report_path = Path("docs/VALIDATION_REPORT.md")
    render_markdown(checks, nan_report, report_path)

    for c in checks:
        mark = "PASS" if c.passed else "FAIL"
        print(f"[{mark}] {c.name}: {c.details}")
    print(f"\nReport written to: {report_path}")

    return 0 if all(c.passed for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
