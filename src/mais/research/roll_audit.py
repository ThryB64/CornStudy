"""Roll audit for Euronext EMA continuous futures series."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.features.euronext_continuous import extract_roll_log
from mais.paths import EMA_FRONT_ADJUSTED, EMA_FRONT_RAW, EMA_ROLL_AUDIT, TARGETS_PARQUET

HORIZON_RE = re.compile(r"_h(?P<horizon>\d+)(?:$|_)")


def audit_rolls(
    front_raw: pd.DataFrame,
    front_adjusted: pd.DataFrame,
    *,
    avg_gap_alert_eur_t: float = 10.0,
    max_gap_alert_eur_t: float = 20.0,
) -> dict[str, Any]:
    """Audit EMA front raw vs adjusted roll consistency."""
    raw = _normalise_series(front_raw)
    adjusted = _normalise_series(front_adjusted)
    roll_log = extract_roll_log(raw)
    roll_log = roll_log.sort_values("date").reset_index(drop=True)

    if roll_log.empty:
        by_year: dict[str, int] = {}
        avg_gap_abs = np.nan
        max_gap_abs = np.nan
        max_gap_date = None
    else:
        abs_gap = pd.to_numeric(roll_log["roll_gap_eur_t"], errors="coerce").abs()
        roll_log["_abs_gap"] = abs_gap
        by_year = {
            str(int(year)): int(count)
            for year, count in roll_log.groupby(roll_log["date"].dt.year).size().items()
        }
        avg_gap_abs = float(abs_gap.mean())
        max_idx = abs_gap.idxmax()
        max_gap_abs = float(abs_gap.loc[max_idx])
        max_gap_date = roll_log.loc[max_idx, "date"].date().isoformat()

    invariant = _adjustment_invariant(raw, adjusted)
    avg_rolls_per_year = float(np.mean(list(by_year.values()))) if by_year else 0.0
    alerts: list[str] = []
    if not invariant["ok"]:
        alerts.append("adjustment_invariant_failed")
    if pd.notna(avg_gap_abs) and avg_gap_abs > avg_gap_alert_eur_t:
        alerts.append("average_roll_gap_above_threshold")
    if pd.notna(max_gap_abs) and max_gap_abs > max_gap_alert_eur_t:
        alerts.append("max_roll_gap_above_threshold")
    if len(roll_log) >= 8 and by_year and (avg_rolls_per_year < 2.0 or avg_rolls_per_year > 6.0):
        alerts.append("unexpected_rolls_per_year")

    verdict = "FAIL" if not invariant["ok"] else ("WARN" if alerts else "OK")
    return {
        "total_rolls": int(len(roll_log)),
        "rolls_per_year": by_year,
        "avg_rolls_per_year": avg_rolls_per_year,
        "average_roll_gap_abs_eur_t": None if pd.isna(avg_gap_abs) else avg_gap_abs,
        "max_roll_gap_abs_eur_t": None if pd.isna(max_gap_abs) else max_gap_abs,
        "max_roll_gap_date": max_gap_date,
        "adjustment_invariant": invariant,
        "alerts": alerts,
        "verdict": verdict,
        "roll_log": roll_log.drop(columns=["_abs_gap"], errors="ignore").to_dict(orient="records"),
    }


def check_targets_cross_rolls(
    targets: pd.DataFrame,
    roll_log: pd.DataFrame,
    *,
    target_columns: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Return potential target windows crossing roll dates.

    By default, only EMA/Euronext target columns are checked. Generic CBOT
    targets are intentionally ignored in DATA-EMA-08 because they were not
    built from the EMA continuous raw series.
    """
    if targets.empty or roll_log.empty:
        return []
    if "Date" in targets.columns:
        date_col = "Date"
    elif "date" in targets.columns:
        date_col = "date"
    else:
        raise ValueError("targets require a Date or date column")

    work = targets.copy()
    work[date_col] = pd.to_datetime(work[date_col]).dt.normalize()
    work = work.sort_values(date_col).reset_index(drop=True)
    dates = work[date_col]
    rolls = pd.to_datetime(roll_log["date"]).dt.normalize().sort_values().reset_index(drop=True)
    cols = target_columns if target_columns is not None else _infer_ema_target_columns(work)
    violations: list[dict[str, Any]] = []
    for col in cols:
        if col not in work.columns or "adjusted" in col.lower():
            continue
        horizon = _target_horizon(col)
        if horizon is None:
            continue
        last_start = max(len(work) - horizon - 1, -1)
        for idx in range(last_start + 1):
            start = dates.iloc[idx]
            end = dates.iloc[idx + horizon]
            crossed = rolls[(rolls > start) & (rolls <= end)]
            if crossed.empty:
                continue
            violations.append(
                {
                    "date": start.date().isoformat(),
                    "target_col": col,
                    "horizon": int(horizon),
                    "window_end": end.date().isoformat(),
                    "n_crossed_rolls": int(len(crossed)),
                    "first_roll_date": crossed.iloc[0].date().isoformat(),
                }
            )
    return violations


def write_roll_audit_report(
    front_raw: pd.DataFrame,
    front_adjusted: pd.DataFrame,
    *,
    targets: pd.DataFrame | None = None,
    output_path: Path = EMA_ROLL_AUDIT,
) -> dict[str, Any]:
    """Run the audit and write a plain-text report."""
    audit = audit_rolls(front_raw, front_adjusted)
    roll_log = pd.DataFrame(audit["roll_log"])
    target_violations = (
        check_targets_cross_rolls(targets, roll_log)
        if targets is not None and not roll_log.empty
        else []
    )
    has_ema_targets = bool(_infer_ema_target_columns(targets)) if targets is not None else False
    target_status = (
        "PENDING_NO_EMA_TARGETS"
        if targets is None or not has_ema_targets
        else ("WARN" if target_violations else "OK")
    )
    verdict = audit["verdict"]
    if target_violations and verdict == "OK":
        verdict = "WARN"
    report = _format_report(audit, target_violations, target_status, verdict)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return {
        "audit": audit,
        "target_violations": target_violations,
        "target_status": target_status,
        "verdict": verdict,
        "report_path": str(output_path),
    }


def run_roll_audit(
    *,
    front_raw_path: Path = EMA_FRONT_RAW,
    front_adjusted_path: Path = EMA_FRONT_ADJUSTED,
    targets_path: Path = TARGETS_PARQUET,
    output_path: Path = EMA_ROLL_AUDIT,
) -> dict[str, Any]:
    """Load default EMA files, run audit and write the report."""
    front_raw = pd.read_parquet(front_raw_path)
    front_adjusted = pd.read_parquet(front_adjusted_path)
    targets = pd.read_parquet(targets_path) if targets_path.exists() else None
    return write_roll_audit_report(
        front_raw,
        front_adjusted,
        targets=targets,
        output_path=output_path,
    )


def _normalise_series(series: pd.DataFrame) -> pd.DataFrame:
    out = series.copy()
    if "date" not in out.columns and "Date" in out.columns:
        out["date"] = out["Date"]
    if "date" not in out.columns:
        raise ValueError("EMA series require a date column")
    out["date"] = pd.to_datetime(out["date"]).dt.normalize()
    return out.sort_values("date").reset_index(drop=True)


def _adjustment_invariant(raw: pd.DataFrame, adjusted: pd.DataFrame) -> dict[str, Any]:
    required = {"date", "price", "roll_adjustment"}
    missing_raw = required - set(raw.columns)
    if missing_raw:
        return {"ok": False, "max_abs_error": None, "missing": sorted(missing_raw)}
    if "adjusted_price" not in adjusted.columns:
        return {"ok": False, "max_abs_error": None, "missing": ["adjusted_price"]}
    merged = raw[["date", "price", "roll_adjustment"]].merge(
        adjusted[["date", "adjusted_price"]],
        on="date",
        how="inner",
    )
    if merged.empty:
        return {"ok": False, "max_abs_error": None, "missing": ["matching_dates"]}
    expected_adjustment = pd.to_numeric(merged["roll_adjustment"], errors="coerce").fillna(0.0).cumsum()
    actual_adjustment = (
        pd.to_numeric(merged["price"], errors="coerce")
        - pd.to_numeric(merged["adjusted_price"], errors="coerce")
    )
    error = (actual_adjustment - expected_adjustment).abs()
    max_abs_error = float(error.max()) if error.notna().any() else np.nan
    return {
        "ok": bool(pd.notna(max_abs_error) and max_abs_error <= 1e-8),
        "max_abs_error": None if pd.isna(max_abs_error) else max_abs_error,
        "n_checked": int(len(merged)),
    }


def _infer_ema_target_columns(targets: pd.DataFrame | None) -> list[str]:
    if targets is None or targets.empty:
        return []
    cols: list[str] = []
    for col in targets.columns:
        lower = col.lower()
        if not lower.startswith("y_"):
            continue
        if ("ema" in lower or "euronext" in lower) and _target_horizon(col) is not None:
            cols.append(col)
    return cols


def _target_horizon(column: str) -> int | None:
    match = HORIZON_RE.search(column)
    return int(match.group("horizon")) if match else None


def _format_report(
    audit: dict[str, Any],
    target_violations: list[dict[str, Any]],
    target_status: str,
    verdict: str,
) -> str:
    rolls_per_year = audit["rolls_per_year"]
    max_gap = audit["max_roll_gap_abs_eur_t"]
    avg_gap = audit["average_roll_gap_abs_eur_t"]
    lines = [
        f"ROLL AUDIT REPORT - {date.today().isoformat()}",
        "",
        "Front continuous RAW vs ADJUSTED",
        f"  Total rolls detected: {audit['total_rolls']}",
        f"  Years with rolls: {len(rolls_per_year)}",
        f"  Average rolls/year: {audit['avg_rolls_per_year']:.2f}",
        f"  Average absolute roll gap: {_fmt_float(avg_gap)} EUR/t",
        f"  Max absolute roll gap: {_fmt_float(max_gap)} EUR/t",
        f"  Max gap date: {audit['max_roll_gap_date'] or 'NA'}",
        f"  Adjustment invariant: {'PASS' if audit['adjustment_invariant']['ok'] else 'FAIL'}",
        f"  Alerts: {', '.join(audit['alerts']) if audit['alerts'] else 'none'}",
        "",
        "Rolls per year",
    ]
    if rolls_per_year:
        lines.extend(f"  {year}: {count}" for year, count in rolls_per_year.items())
    else:
        lines.append("  none")
    lines.extend(["", "Roll details"])
    for item in audit["roll_log"]:
        lines.append(
            "  "
            f"{pd.Timestamp(item['date']).date().isoformat()}: "
            f"{item['old_contract']} -> {item['new_contract']}, "
            f"gap={_fmt_float(item['roll_gap_eur_t'])} EUR/t"
        )
    if not audit["roll_log"]:
        lines.append("  none")
    lines.extend(
        [
            "",
            "Targets crossing rolls",
            f"  Status: {target_status}",
            f"  Potential windows crossing rolls: {len(target_violations)}",
        ]
    )
    for item in target_violations[:20]:
        lines.append(
            "  "
            f"{item['date']} {item['target_col']} h{item['horizon']} "
            f"crosses {item['first_roll_date']}"
        )
    if len(target_violations) > 20:
        lines.append(f"  ... {len(target_violations) - 20} additional windows omitted")
    lines.extend(
        [
            "",
            f"Verdict: {verdict}",
            "",
            "Notes:",
            "- Raw series keep observed prices and are suitable for farmer-facing levels.",
            "- Adjusted series are required for returns/features crossing roll dates.",
            "- Barchart proxy-derived EMA data remains exploratory until replaced by an official source.",
        ]
    )
    return "\n".join(lines) + "\n"


def _fmt_float(value: Any) -> str:
    if value is None or pd.isna(value):
        return "NA"
    return f"{float(value):.3f}"
