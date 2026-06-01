"""Build the canonical EMA contract reference table.

The table keeps provider-specific symbols such as ``XBM14`` away from the
project's canonical contract codes such as ``EMA_M2014``. It also keeps
January/F contracts explicit as legacy/ambiguous rows so they cannot silently
enter final EMA series.
"""

from __future__ import annotations

import argparse
import re
from collections.abc import Iterable, Mapping
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from mais.paths import EMA_CONTRACT_REFERENCE

BARCHART_PROVIDER = "barchart"
BARCHART_ROOT = "XB"

CURRENT_OFFICIAL_EMA_MONTHS: dict[str, int] = {"H": 3, "M": 6, "Q": 8, "X": 11}
LEGACY_OR_INVESTIGATION_EMA_MONTHS: dict[str, int] = {"F": 1}
ALL_REFERENCE_MONTHS: dict[str, int] = {
    **LEGACY_OR_INVESTIGATION_EMA_MONTHS,
    **CURRENT_OFFICIAL_EMA_MONTHS,
}

REQUIRED_COLUMNS = [
    "source",
    "source_symbol",
    "canonical_contract_code",
    "month_code",
    "delivery_month",
    "delivery_year",
    "expiry_date",
    "last_trade_date",
    "active_month_status",
    "import_verdict",
]

OPTIONAL_COLUMNS = [
    "contract_name",
    "source_root",
    "source_confirmed",
]

CONTRACT_REFERENCE_COLUMNS = [*REQUIRED_COLUMNS, *OPTIONAL_COLUMNS]


def build_barchart_symbol(month_code: str, year: int) -> str:
    """Build a Barchart Euronext Corn symbol, e.g. ``XBM14``."""
    code = month_code.upper()
    if code not in ALL_REFERENCE_MONTHS:
        raise ValueError(f"Unsupported EMA month code for reference: {month_code}")
    if year < 2000 or year > 2099:
        raise ValueError(f"Expected a 2000-2099 year, got {year}")
    return f"{BARCHART_ROOT}{code}{year % 100:02d}"


def parse_barchart_symbol(source_symbol: str) -> tuple[str, int]:
    """Parse ``XB{month}{yy}`` into ``(month_code, delivery_year)``."""
    symbol = source_symbol.upper()
    match = re.fullmatch(rf"{BARCHART_ROOT}([A-Z])(\d{{2}})", symbol)
    if not match:
        raise ValueError(f"Unsupported Barchart EMA symbol: {source_symbol}")
    return match.group(1), 2000 + int(match.group(2))


def canonical_contract_code(month_code: str, delivery_year: int) -> str | None:
    """Return the project code for official months, otherwise ``None``."""
    code = month_code.upper()
    if code not in CURRENT_OFFICIAL_EMA_MONTHS:
        return None
    return f"EMA_{code}{delivery_year}"


def map_provider_symbol(
    source_symbol: str,
    *,
    provider: str = BARCHART_PROVIDER,
    expiry_date: str | date | datetime | int | float | None = None,
    last_trade_date: str | date | datetime | int | float | None = None,
    contract_name: str | None = None,
    source_confirmed: bool = True,
    current_year: int | None = None,
) -> dict[str, Any]:
    """Map one provider symbol into the canonical reference schema."""
    provider_key = provider.lower()
    if provider_key != BARCHART_PROVIDER:
        raise ValueError(f"Unsupported EMA contract provider: {provider}")

    month_code, delivery_year = parse_barchart_symbol(source_symbol)
    delivery_month = ALL_REFERENCE_MONTHS.get(month_code)
    if delivery_month is None:
        return _do_not_import_row(
            provider_key,
            source_symbol,
            month_code=month_code,
            delivery_year=delivery_year,
            expiry_date=expiry_date,
            last_trade_date=last_trade_date,
            contract_name=contract_name,
            source_confirmed=source_confirmed,
        )

    if month_code in LEGACY_OR_INVESTIGATION_EMA_MONTHS:
        active_month_status = "legacy_or_ambiguous"
        import_verdict = "legacy_or_ambiguous"
        canonical = None
    else:
        active_month_status = _official_month_status(delivery_year, current_year)
        import_verdict = "usable" if source_confirmed else "do_not_import"
        canonical = canonical_contract_code(month_code, delivery_year)

    return {
        "source": provider_key,
        "source_symbol": source_symbol.upper(),
        "canonical_contract_code": canonical,
        "month_code": month_code,
        "delivery_month": delivery_month,
        "delivery_year": delivery_year,
        "expiry_date": _normalize_date(expiry_date),
        "last_trade_date": _normalize_date(last_trade_date or expiry_date),
        "active_month_status": active_month_status,
        "import_verdict": import_verdict,
        "contract_name": contract_name,
        "source_root": BARCHART_ROOT,
        "source_confirmed": bool(source_confirmed),
    }


def build_reference_from_barchart_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    current_year: int | None = None,
) -> pd.DataFrame:
    """Build the reference table from Barchart ``futures.historical.byRoot`` rows."""
    mapped = []
    for row in rows:
        raw = row.get("raw") if isinstance(row.get("raw"), Mapping) else row
        source_symbol = _first_present(raw, row, "symbol")
        if not source_symbol:
            continue
        expiry_date = _first_present(raw, row, "contractExpirationDate", "tradeTime")
        contract_name = _first_present(raw, row, "contractNameHistorical", "contractName")
        mapped.append(
            map_provider_symbol(
                str(source_symbol),
                expiry_date=expiry_date,
                last_trade_date=expiry_date,
                contract_name=str(contract_name) if contract_name else None,
                current_year=current_year,
            )
        )
    return validate_contract_reference(pd.DataFrame(mapped))


def build_contract_reference(
    start_year: int = 2010,
    end_year: int = 2026,
    *,
    include_legacy: bool = True,
    legacy_end_year: int = 2022,
    current_year: int | None = None,
) -> pd.DataFrame:
    """Build a deterministic Barchart-based reference universe."""
    rows: list[dict[str, Any]] = []
    months = list(CURRENT_OFFICIAL_EMA_MONTHS)
    if include_legacy:
        months = [*LEGACY_OR_INVESTIGATION_EMA_MONTHS, *months]

    for year in range(start_year, end_year + 1):
        for month_code in months:
            if month_code in LEGACY_OR_INVESTIGATION_EMA_MONTHS and year > legacy_end_year:
                continue
            rows.append(
                map_provider_symbol(
                    build_barchart_symbol(month_code, year),
                    current_year=current_year,
                )
            )

    return validate_contract_reference(pd.DataFrame(rows))


def validate_contract_reference(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate and order an EMA contract reference table."""
    missing = [col for col in REQUIRED_COLUMNS if col not in frame.columns]
    if missing:
        raise ValueError(f"Missing EMA contract reference columns: {missing}")

    validated = frame.copy()
    for col in CONTRACT_REFERENCE_COLUMNS:
        if col not in validated.columns:
            validated[col] = None
    validated = validated[CONTRACT_REFERENCE_COLUMNS]

    duplicate_symbols = validated["source_symbol"][validated["source_symbol"].duplicated()].unique()
    if len(duplicate_symbols):
        raise ValueError(f"Duplicate EMA source symbols: {sorted(duplicate_symbols)}")

    importable = validated["import_verdict"] == "usable"
    bad_importable = validated[importable & validated["canonical_contract_code"].isna()]
    if not bad_importable.empty:
        raise ValueError("Importable EMA contracts must have a canonical contract code")

    legacy_importable = validated[
        validated["month_code"].isin(LEGACY_OR_INVESTIGATION_EMA_MONTHS)
        & (validated["import_verdict"] == "usable")
    ]
    if not legacy_importable.empty:
        raise ValueError("Legacy EMA months cannot be importable by default")

    official = validated["month_code"].isin(CURRENT_OFFICIAL_EMA_MONTHS)
    bad_official_status = validated[
        official & ~validated["active_month_status"].isin(["current_official", "historical_confirmed"])
    ]
    if not bad_official_status.empty:
        raise ValueError("Official EMA months must be current_official or historical_confirmed")

    return validated.sort_values(["delivery_year", "delivery_month", "source_symbol"]).reset_index(
        drop=True
    )


def write_contract_reference(
    frame: pd.DataFrame,
    *,
    output_path: Path = EMA_CONTRACT_REFERENCE,
) -> Path:
    """Write the reference table as parquet."""
    validated = validate_contract_reference(frame)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    validated.to_parquet(output_path, index=False)
    return output_path


def _official_month_status(delivery_year: int, current_year: int | None) -> str:
    reference_year = date.today().year if current_year is None else current_year
    if delivery_year >= reference_year:
        return "current_official"
    return "historical_confirmed"


def _do_not_import_row(
    provider: str,
    source_symbol: str,
    *,
    month_code: str,
    delivery_year: int,
    expiry_date: str | date | datetime | int | float | None,
    last_trade_date: str | date | datetime | int | float | None,
    contract_name: str | None,
    source_confirmed: bool,
) -> dict[str, Any]:
    return {
        "source": provider,
        "source_symbol": source_symbol.upper(),
        "canonical_contract_code": None,
        "month_code": month_code,
        "delivery_month": None,
        "delivery_year": delivery_year,
        "expiry_date": _normalize_date(expiry_date),
        "last_trade_date": _normalize_date(last_trade_date or expiry_date),
        "active_month_status": "legacy_or_ambiguous",
        "import_verdict": "do_not_import",
        "contract_name": contract_name,
        "source_root": BARCHART_ROOT,
        "source_confirmed": bool(source_confirmed),
    }


def _normalize_date(value: str | date | datetime | int | float | None) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, int | float):
        return datetime.fromtimestamp(value, tz=timezone.utc).date().isoformat()

    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    return text


def _first_present(
    primary: Mapping[str, Any],
    fallback: Mapping[str, Any],
    *keys: str,
) -> Any:
    for mapping in (primary, fallback):
        for key in keys:
            value = mapping.get(key)
            if value not in (None, ""):
                return value
    return None


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for DATA-EMA-10."""
    parser = argparse.ArgumentParser(description="Build EMA contract reference table")
    parser.add_argument("--start-year", type=int, default=2010)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--legacy-end-year", type=int, default=2022)
    parser.add_argument("--no-legacy", action="store_true")
    parser.add_argument("--output", type=Path, default=EMA_CONTRACT_REFERENCE)
    args = parser.parse_args(argv)

    frame = build_contract_reference(
        args.start_year,
        args.end_year,
        include_legacy=not args.no_legacy,
        legacy_end_year=args.legacy_end_year,
    )
    path = write_contract_reference(frame, output_path=args.output)
    print(f"Wrote {path}")
    print(f"Rows: {len(frame)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
