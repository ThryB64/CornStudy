"""Probe Barchart pages for expired Euronext EMA corn contracts."""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

from mais.paths import EMA_BARCHART_PROBE_REPORT, EMA_BARCHART_PROBE_RESULTS

BARCHART_ROOT = "XB"
VALID_EMA_MONTHS = ("H", "M", "Q", "X")
LEGACY_MONTHS_TO_PROBE = ("F",)
MONTHS_TO_PROBE = (*VALID_EMA_MONTHS, *LEGACY_MONTHS_TO_PROBE)
BARCHART_URL_TEMPLATE = "https://www.barchart.com/futures/quotes/{symbol}/historical-prices"

PROBE_COLUMNS = [
    "source_symbol",
    "canonical_contract_code",
    "import_verdict",
    "active_month_status",
    "year",
    "month_code",
    "url",
    "http_status",
    "title_detected",
    "exchange_detected",
    "symbol_root_detected",
    "contract_name_detected",
    "has_historical_table",
    "has_download_button",
    "first_date_detected",
    "last_date_detected",
    "fields_detected",
    "open_interest_available",
    "n_rows_visible",
    "verdict",
    "error",
]


def build_barchart_symbol(month_code: str, year: int) -> str:
    """Build a Barchart expired-futures symbol such as ``XBQ10``."""
    code = month_code.upper()
    if code not in MONTHS_TO_PROBE:
        raise ValueError(f"Unsupported Barchart EMA probe month: {month_code}")
    if year < 2000 or year > 2099:
        raise ValueError(f"Expected a 2000-2099 year, got {year}")
    return f"{BARCHART_ROOT}{code}{year % 100:02d}"


def parse_barchart_symbol(symbol: str) -> tuple[str, int]:
    """Return ``(month_code, four_digit_year)`` for a Barchart XB symbol."""
    match = re.fullmatch(rf"{BARCHART_ROOT}([A-Z])(\d{{2}})", symbol.upper())
    if not match:
        raise ValueError(f"Unsupported Barchart EMA symbol: {symbol}")
    month_code = match.group(1)
    year = 2000 + int(match.group(2))
    return month_code, year


def canonical_contract_code(symbol: str) -> str | None:
    """Map a Barchart symbol to the project canonical code when importable."""
    month_code, year = parse_barchart_symbol(symbol)
    if month_code not in VALID_EMA_MONTHS:
        return None
    return f"EMA_{month_code}{year}"


def build_probe_symbols(
    start_year: int = 2010,
    end_year: int = 2026,
    *,
    include_january: bool = True,
) -> list[str]:
    """Build the default DATA-EMA-09 probe symbol universe."""
    symbols = [
        build_barchart_symbol(month, year)
        for year in range(start_year, end_year + 1)
        for month in VALID_EMA_MONTHS
    ]
    if include_january:
        symbols.extend(
            build_barchart_symbol("F", year)
            for year in range(start_year, min(end_year, 2020) + 1)
        )
    return symbols


def fetch_barchart_html(symbol: str, timeout: int = 20) -> tuple[int, str]:
    """Fetch one Barchart historical-prices page."""
    request = Request(
        BARCHART_URL_TEMPLATE.format(symbol=symbol),
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml",
            "Referer": "https://www.barchart.com/futures",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return int(response.status), response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        return int(exc.code), body
    except URLError as exc:
        return 0, str(exc.reason)


def probe_barchart_symbol(
    symbol: str,
    *,
    html: str | None = None,
    http_status: int | None = None,
    timeout: int = 20,
) -> dict[str, Any]:
    """Probe one Barchart expired contract page and classify access."""
    source_symbol = symbol.upper()
    month_code, year = parse_barchart_symbol(source_symbol)
    url = BARCHART_URL_TEMPLATE.format(symbol=source_symbol)
    error = ""
    if html is None:
        status, html = fetch_barchart_html(source_symbol, timeout=timeout)
    else:
        status = 200 if http_status is None else http_status

    metadata = _extract_current_symbol_metadata(html)
    title = _extract_title(html)
    fields = _detect_fields(html)
    first_date, last_date = _detect_date_range(html)
    has_table = _has_visible_historical_table(html)
    has_download = _has_download_signal(html)
    n_rows = _count_visible_table_rows(html)

    if status == 0:
        error = html[:250]
    canonical = canonical_contract_code(source_symbol)
    active_status = "current_official" if month_code in VALID_EMA_MONTHS else "legacy_or_ambiguous"
    page_matches_ema = (
        status == 200
        and metadata.get("symbolRoot") == BARCHART_ROOT
        and metadata.get("exchange") == "Euronext"
        and "Corn" in str(metadata.get("symbolName") or metadata.get("contractName") or title)
    )

    if month_code not in VALID_EMA_MONTHS:
        verdict = "legacy_or_ambiguous" if status == 200 else "unavailable"
        import_verdict = "legacy_or_ambiguous"
    elif not page_matches_ema:
        verdict = "unavailable"
        import_verdict = "do_not_import"
    elif has_table and {"open", "high", "low", "volume"}.issubset(fields):
        verdict = "usable"
        import_verdict = "usable"
    else:
        verdict = "page_exists_no_download"
        import_verdict = "do_not_import"

    return {
        "source_symbol": source_symbol,
        "canonical_contract_code": canonical,
        "import_verdict": import_verdict,
        "active_month_status": active_status,
        "year": year,
        "month_code": month_code,
        "url": url,
        "http_status": status,
        "title_detected": title,
        "exchange_detected": metadata.get("exchange"),
        "symbol_root_detected": metadata.get("symbolRoot"),
        "contract_name_detected": metadata.get("contractName"),
        "has_historical_table": has_table,
        "has_download_button": has_download,
        "first_date_detected": first_date,
        "last_date_detected": last_date,
        "fields_detected": ",".join(sorted(fields)),
        "open_interest_available": "open_interest" in fields,
        "n_rows_visible": n_rows,
        "verdict": verdict,
        "error": error,
    }


def probe_symbols(
    symbols: list[str],
    *,
    throttle_sec: float = 2.0,
    fetcher: Callable[[str], tuple[int, str]] | None = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> list[dict[str, Any]]:
    """Probe many symbols with a mandatory delay between HTTP requests."""
    results: list[dict[str, Any]] = []
    for idx, symbol in enumerate(symbols):
        if idx > 0 and throttle_sec > 0:
            sleeper(throttle_sec)
        if fetcher is None:
            results.append(probe_barchart_symbol(symbol))
        else:
            status, html = fetcher(symbol)
            results.append(probe_barchart_symbol(symbol, html=html, http_status=status))
    return results


def write_probe_outputs(
    results: list[dict[str, Any]],
    *,
    results_path: Path = EMA_BARCHART_PROBE_RESULTS,
    report_path: Path = EMA_BARCHART_PROBE_REPORT,
) -> tuple[Path, Path]:
    """Write CSV results and a readable DATA-EMA-09 decision report."""
    results_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(results)
    for col in PROBE_COLUMNS:
        if col not in frame.columns:
            frame[col] = None
    frame = frame[PROBE_COLUMNS]
    frame.to_csv(results_path, index=False)
    report_path.write_text(build_probe_report(results), encoding="utf-8")
    return results_path, report_path


def build_probe_report(results: list[dict[str, Any]]) -> str:
    """Build a compact readable summary of probe coverage and decision."""
    verdict_counts = Counter(str(row["verdict"]) for row in results)
    import_counts = Counter(str(row["import_verdict"]) for row in results)
    month_lines = []
    for month in MONTHS_TO_PROBE:
        rows = [row for row in results if row["month_code"] == month]
        years = sorted(int(row["year"]) for row in rows if row["http_status"] == 200)
        if years:
            coverage = f"{min(years)}-{max(years)} ({len(years)} pages HTTP 200)"
        else:
            coverage = "aucune page HTTP 200"
        month_lines.append(f"  {month}: {coverage}")

    field_rows = [row for row in results if row["fields_detected"]]
    fields = sorted({field for row in field_rows for field in str(row["fields_detected"]).split(",") if field})
    usable = [row for row in results if row["verdict"] == "usable" and row["month_code"] in VALID_EMA_MONTHS]
    page_only = [
        row for row in results
        if row["verdict"] == "page_exists_no_download" and row["month_code"] in VALID_EMA_MONTHS
    ]
    if usable:
        decision = "Barchart peut alimenter DATA-EMA-02 pour les symboles usable detectes."
    elif page_only:
        decision = (
            "Barchart expose les pages/metadonnees EMA, mais les donnees historiques "
            "ne sont pas visibles en HTML public. API OnDemand/Premier ou telechargement "
            "manuel requis avant DATA-EMA-02."
        )
    else:
        decision = "Barchart non utilisable en acces public pour DATA-EMA-02."

    lines = [
        "BARCHART EMA PROBE REPORT",
        f"Generated at UTC: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Symbols tested: {len(results)}",
        "Verdicts:",
        *[f"  {key}: {value}" for key, value in sorted(verdict_counts.items())],
        "Import verdicts:",
        *[f"  {key}: {value}" for key, value in sorted(import_counts.items())],
        "",
        "Coverage by month:",
        *month_lines,
        "",
        f"Fields detected: {', '.join(fields) if fields else 'none'}",
        f"Open interest detected: {any(row['open_interest_available'] for row in results)}",
        "",
        "Decision:",
        f"  {decision}",
        "",
        "Important rule:",
        "  XBF/F remains legacy_or_ambiguous and is not imported by default.",
        "",
    ]
    return "\n".join(lines)


def _extract_current_symbol_metadata(html: str) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for key in ("symbol", "symbolRoot", "exchange", "symbolName", "contractName", "pointValue"):
        value = _extract_json_string_field(html, key)
        if value is not None:
            metadata[key] = value
    return metadata


def _extract_json_string_field(html: str, key: str) -> str | None:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*"((?:\\.|[^"\\])*)"', html)
    if not match:
        return None
    try:
        return str(json.loads(f'"{match.group(1)}"'))
    except json.JSONDecodeError:
        return unescape(match.group(1))


def _extract_title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return _squash(unescape(re.sub(r"<[^>]+>", " ", match.group(1))))


def _detect_fields(html: str) -> set[str]:
    text = unescape(html).lower()
    fields: set[str] = set()
    mapping = {
        "open": ("open",),
        "high": ("high",),
        "low": ("low",),
        "settlement": ("settlement", "settle"),
        "close": ("close", "last"),
        "volume": ("volume",),
        "open_interest": ("open interest", "open_interest"),
    }
    for field, needles in mapping.items():
        if any(needle in text for needle in needles):
            fields.add(field)
    return fields


def _detect_date_range(html: str) -> tuple[str | None, str | None]:
    dates = re.findall(r"\b(?:20\d{2}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/20\d{2})\b", html)
    if not dates:
        return None, None
    return dates[0], dates[-1]


def _has_visible_historical_table(html: str) -> bool:
    text = html.lower()
    return "<table" in text and "historical" in text and ("open interest" in text or "volume" in text)


def _has_download_signal(html: str) -> bool:
    text = html.lower()
    return "historical-download" in text or "downloadlimit" in text or "download" in text


def _count_visible_table_rows(html: str) -> int:
    if "<table" not in html.lower():
        return 0
    rows = re.findall(r"<tr\b", html, flags=re.IGNORECASE)
    return max(0, len(rows) - 1)


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for DATA-EMA-09."""
    parser = argparse.ArgumentParser(description="Probe Barchart expired EMA corn contracts")
    parser.add_argument("--start-year", type=int, default=2010)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--throttle-sec", type=float, default=2.0)
    parser.add_argument("--no-january", action="store_true")
    args = parser.parse_args(argv)

    symbols = build_probe_symbols(
        args.start_year,
        args.end_year,
        include_january=not args.no_january,
    )
    results = probe_symbols(symbols, throttle_sec=args.throttle_sec)
    results_path, report_path = write_probe_outputs(results)
    print(f"Wrote {results_path}")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
