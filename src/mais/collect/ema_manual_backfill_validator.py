"""Validate manual historical Euronext EMA OHLC backfill files before import."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from mais.collect.euronext_ema_collector import (
    CURRENT_OFFICIAL_EMA_MONTHS,
    parse_provider_contract_label,
)

PRICE_ALIASES = ("settlement", "settle", "settl.", "close", "last")
CONTRACT_ALIASES = ("contract_code", "canonical_contract_code", "delivery", "contract_label")
VALID_IMPORT_VERDICTS = {"usable", "legacy_or_ambiguous", "do_not_import"}
VALID_ACTIVE_MONTH_STATUS = {"current_official", "historical_confirmed", "legacy_or_ambiguous"}


def validate_manual_backfill_csv(
    csv_path: str | Path,
    *,
    from_year: int = 2014,
    to_year: int = 2025,
) -> dict[str, Any]:
    """Validate one manual historical EMA CSV without importing it."""
    path = Path(csv_path)
    raw = pd.read_csv(path)
    report = validate_manual_backfill_frame(raw, from_year=from_year, to_year=to_year)
    report["path"] = str(path)
    return report


def validate_manual_backfill_frame(
    raw: pd.DataFrame,
    *,
    from_year: int = 2014,
    to_year: int = 2025,
) -> dict[str, Any]:
    """Return a strict validation report for a manual EMA historical CSV."""
    if from_year > to_year:
        raise ValueError("from_year must be <= to_year")

    df = _normalise_columns(raw)
    errors: list[str] = []
    warnings: list[str] = []

    if "date" not in df.columns:
        return _failure_report(raw, from_year, to_year, ["missing date column"])

    price_col = _first_present(df, PRICE_ALIASES)
    contract_col = _first_present(df, CONTRACT_ALIASES)
    if price_col is None:
        errors.append("missing price column: expected one of settlement/settle/close/last")
    if contract_col is None:
        errors.append("missing contract column: expected contract_code/canonical_contract_code/delivery")
    if errors:
        return _failure_report(raw, from_year, to_year, errors)

    assert price_col is not None
    assert contract_col is not None

    work = df.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce").dt.normalize()
    work["_price"] = pd.to_numeric(work[price_col], errors="coerce")
    work["_contract_code"] = work[contract_col].map(_normalise_contract_value)
    work["_month_code"] = work["_contract_code"].map(_month_code_from_contract)

    invalid_date_rows = int(work["date"].isna().sum())
    invalid_price_rows = int(work["_price"].isna().sum())
    invalid_contract_rows = int(work["_contract_code"].isna().sum())

    if invalid_date_rows:
        errors.append(f"{invalid_date_rows} rows have invalid dates")
    if invalid_price_rows:
        errors.append(f"{invalid_price_rows} rows have missing/non-numeric prices")
    if invalid_contract_rows:
        errors.append(f"{invalid_contract_rows} rows have invalid contract labels/codes")

    current_months = set(CURRENT_OFFICIAL_EMA_MONTHS)
    legacy_mask = ~work["_month_code"].isin(current_months)
    import_verdict = _string_series_or_default(
        work,
        "import_verdict",
        default_current="usable",
        default_legacy="legacy_or_ambiguous",
        legacy_mask=legacy_mask,
    )
    active_month_status = _string_series_or_default(
        work,
        "active_month_status",
        default_current="current_official",
        default_legacy="legacy_or_ambiguous",
        legacy_mask=legacy_mask,
    )

    invalid_import_verdict = sorted(set(import_verdict.dropna()) - VALID_IMPORT_VERDICTS)
    invalid_active_status = sorted(set(active_month_status.dropna()) - VALID_ACTIVE_MONTH_STATUS)
    if invalid_import_verdict:
        errors.append(f"invalid import_verdict values: {invalid_import_verdict}")
    if invalid_active_status:
        errors.append(f"invalid active_month_status values: {invalid_active_status}")

    confirmed_legacy = active_month_status.eq("historical_confirmed") & import_verdict.eq("usable")
    unconfirmed_legacy_rows = int((legacy_mask & ~confirmed_legacy).sum())
    if unconfirmed_legacy_rows:
        errors.append(
            f"{unconfirmed_legacy_rows} legacy/non-current rows require "
            "active_month_status=historical_confirmed and import_verdict=usable"
        )

    importable_mask = (
        work["date"].notna()
        & work["_price"].notna()
        & work["_contract_code"].notna()
        & import_verdict.eq("usable")
        & (~legacy_mask | confirmed_legacy)
    )
    importable = work[importable_mask].copy()

    min_date = _date_iso(importable["date"].min()) if not importable.empty else None
    max_date = _date_iso(importable["date"].max()) if not importable.empty else None
    expected_start_deadline = pd.Timestamp(from_year, 1, 31)
    expected_end_deadline = pd.Timestamp(to_year, 12, 1)
    if importable.empty:
        errors.append("no importable rows after validation")
    else:
        if importable["date"].min() > expected_start_deadline:
            errors.append(f"history starts after {expected_start_deadline.date().isoformat()}")
        if importable["date"].max() < expected_end_deadline:
            errors.append(f"history ends before {expected_end_deadline.date().isoformat()}")

    coverage_by_year = {
        str(year): int(importable[importable["date"].dt.year.eq(year)]["date"].nunique())
        for year in range(from_year, to_year + 1)
    }
    missing_years = [year for year, count in coverage_by_year.items() if count == 0]
    if missing_years:
        errors.append(f"missing years in importable rows: {missing_years}")

    contracts_found = sorted(str(code) for code in importable["_contract_code"].dropna().unique())
    missing_harvest_nov = [
        str(year) for year in range(from_year, to_year + 1) if f"EMA_X{year}" not in contracts_found
    ]
    if missing_harvest_nov:
        warnings.append(f"missing November harvest contracts: {missing_harvest_nov}")

    source_symbol_present = "source_symbol" in work.columns
    canonical_present = "canonical_contract_code" in work.columns
    if not source_symbol_present:
        warnings.append("source_symbol column missing; add it for provider traceability")
    if not canonical_present:
        warnings.append("canonical_contract_code column missing; contract_code will be used as fallback")

    report = {
        "quality_ok": not errors,
        "from_year": from_year,
        "to_year": to_year,
        "row_count": int(len(work)),
        "importable_rows": int(len(importable)),
        "invalid_date_rows": invalid_date_rows,
        "invalid_price_rows": invalid_price_rows,
        "invalid_contract_rows": invalid_contract_rows,
        "legacy_or_non_current_rows": int(legacy_mask.sum()),
        "unconfirmed_legacy_rows": unconfirmed_legacy_rows,
        "min_date": min_date,
        "max_date": max_date,
        "coverage_by_year": coverage_by_year,
        "contracts_found_count": len(contracts_found),
        "contracts_found_sample": contracts_found[:20],
        "missing_harvest_nov": missing_harvest_nov,
        "source_symbol_present": source_symbol_present,
        "canonical_contract_code_present": canonical_present,
        "errors": errors,
        "warnings": warnings,
    }
    return report


def _normalise_columns(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]
    return df


def _first_present(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        key = candidate.strip().lower().replace(" ", "_")
        if key in df.columns:
            return key
    return None


def _normalise_contract_value(value: Any) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.upper().startswith("EMA_"):
        code = text.upper()
        return code if _month_code_from_contract(code) else None
    try:
        return parse_provider_contract_label(text, allow_legacy=True)
    except ValueError:
        return None


def _month_code_from_contract(contract_code: str | None) -> str | None:
    if not contract_code:
        return None
    match = pd.Series([contract_code]).str.extract(r"^EMA_([A-Z])\d{4}$", expand=False).iloc[0]
    if pd.isna(match):
        return None
    return str(match)


def _string_series_or_default(
    df: pd.DataFrame,
    column: str,
    *,
    default_current: str,
    default_legacy: str,
    legacy_mask: pd.Series,
) -> pd.Series:
    if column in df.columns:
        return df[column].fillna("").astype(str).str.strip()
    return pd.Series(
        [default_legacy if bool(is_legacy) else default_current for is_legacy in legacy_mask],
        index=df.index,
    )


def _date_iso(value: Any) -> str | None:
    if pd.isna(value):
        return None
    return pd.Timestamp(value).date().isoformat()


def _failure_report(raw: pd.DataFrame, from_year: int, to_year: int, errors: list[str]) -> dict[str, Any]:
    return {
        "quality_ok": False,
        "from_year": from_year,
        "to_year": to_year,
        "row_count": int(len(raw)),
        "importable_rows": 0,
        "invalid_date_rows": 0,
        "invalid_price_rows": 0,
        "invalid_contract_rows": 0,
        "legacy_or_non_current_rows": 0,
        "unconfirmed_legacy_rows": 0,
        "min_date": None,
        "max_date": None,
        "coverage_by_year": {},
        "contracts_found_count": 0,
        "contracts_found_sample": [],
        "missing_harvest_nov": [],
        "source_symbol_present": False,
        "canonical_contract_code_present": False,
        "errors": errors,
        "warnings": [],
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for manual EMA backfill validation."""
    parser = argparse.ArgumentParser(description="Validate an EMA historical OHLC CSV")
    parser.add_argument("csv_path")
    parser.add_argument("--from-year", type=int, default=2014)
    parser.add_argument("--to-year", type=int, default=2025)
    args = parser.parse_args(argv)

    report = validate_manual_backfill_csv(
        args.csv_path,
        from_year=args.from_year,
        to_year=args.to_year,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["quality_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "validate_manual_backfill_csv",
    "validate_manual_backfill_frame",
]
