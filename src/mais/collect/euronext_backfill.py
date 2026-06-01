"""Historical backfill for Euronext EMA futures contracts."""

from __future__ import annotations

import json
import time
from datetime import date as date_cls
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen

import numpy as np
import pandas as pd

from mais.collect.ema_contract_reference import (
    BARCHART_ROOT,
    build_contract_reference,
    build_reference_from_barchart_rows,
    validate_contract_reference,
)
from mais.collect.euronext_contracts_daily import (
    download_active_contracts,
    normalise_contract_daily_frame,
    quality_flag,
)
from mais.collect.euronext_ema_collector import (
    CURRENT_OFFICIAL_EMA_MONTHS,
    EMA_CONTRACT_MONTHS,
    parse_contract_label,
)
from mais.paths import ARTEFACTS_DIR, EMA_BACKFILL_DIR, EMA_CONTRACT_DAILY, EMA_CONTRACT_REFERENCE
from mais.utils import get_logger

log = get_logger("mais.collect.euronext_backfill")

MANUAL_BACKFILL_FILENAME = "ema_historical_contracts.csv"
BACKFILL_COVERAGE_REPORT = ARTEFACTS_DIR / "backfill_coverage_report.json"
BARCHART_XB_EOD_COVERAGE_CONTRACTS = (
    ARTEFACTS_DIR / "euronext" / "barchart_xb_eod_coverage_contracts.csv"
)
BARCHART_XB_EOD_COVERAGE_BY_YEAR = (
    ARTEFACTS_DIR / "euronext" / "barchart_xb_eod_coverage_by_year.csv"
)
BARCHART_XB_EOD_COVERAGE_REPORT = (
    ARTEFACTS_DIR / "euronext" / "barchart_xb_eod_coverage_report.txt"
)
CHART_ENDPOINT_TEMPLATE = (
    "https://live.euronext.com/en/intraday_historical/settlements/getChartData/"
    "EMA-DPAR/max"
)
SOURCE_RANK = {
    "euronext_ajax_prices": 40,
    "euronext_chart_history": 35,
    "manual_backfill": 30,
    "barchart_proxy_exploratory": 25,
    "barchart": 20,
    "proxy_cbot": 10,
}
BARCHART_PRICE_HISTORY_URL = "https://www.barchart.com/futures/quotes/{symbol}/price-history/historical"
BARCHART_QUOTES_ENDPOINT = "https://www.barchart.com/proxies/core-api/v1/quotes/get"
BARCHART_HISTORICAL_ENDPOINT = "https://www.barchart.com/proxies/core-api/v1/historical/get"
BARCHART_LIST_FIELDS = "contractExpirationDate.format(Y-m-d),symbol,contractNameHistorical,lastPrice,tradeTime"
BARCHART_HISTORY_FIELDS = (
    "tradeTime.format(m/d/Y),openPrice,highPrice,lowPrice,lastPrice,"
    "priceChange,percentChange,volume,openInterest"
)
BARCHART_COVERAGE_UNIVERSES = ("strict_official", "exploratory_with_F")


def backfill_from_scraper(
    from_date: date_cls,
    to_date: date_cls,
    throttle_sec: float = 2.0,
) -> int:
    """Backfill history available from Euronext chart data for active contracts."""
    contracts = download_active_contracts()
    frames: list[pd.DataFrame] = []
    for contract in contracts:
        frame = download_contract_history(contract, from_date=from_date, to_date=to_date)
        if not frame.empty:
            frames.append(frame)
        if throttle_sec > 0:
            time.sleep(throttle_sec)
    if not frames:
        _write_coverage_report(pd.DataFrame(), from_date, to_date, source="euronext_chart_history")
        return 0
    history = pd.concat(frames, ignore_index=True, sort=False)
    written = _merge_into_contract_daily(history)
    _write_coverage_report(history, from_date, to_date, source="euronext_chart_history")
    return written


def backfill_from_barchart(
    from_date: date_cls,
    to_date: date_cls,
    *,
    throttle_sec: float = 2.0,
    max_retries: int = 3,
    reference_frame: pd.DataFrame | None = None,
) -> int:
    """Backfill Barchart public web EOD rows for validated EMA contracts."""
    history = collect_barchart_history(
        from_date,
        to_date,
        throttle_sec=throttle_sec,
        max_retries=max_retries,
        reference_frame=reference_frame,
    )
    if history.empty:
        _write_coverage_report(pd.DataFrame(), from_date, to_date, source="barchart_proxy_exploratory")
        return 0
    written = _merge_into_contract_daily(history)
    _write_coverage_report(history, from_date, to_date, source="barchart_proxy_exploratory")
    return written


def collect_barchart_history(
    from_date: date_cls,
    to_date: date_cls,
    *,
    throttle_sec: float = 2.0,
    max_retries: int = 3,
    reference_frame: pd.DataFrame | None = None,
    session: tuple[Any, dict[str, str]] | None = None,
    sleeper: Any = time.sleep,
) -> pd.DataFrame:
    """Collect Barchart web EOD rows without writing them."""
    opener, headers = session or open_barchart_session()
    reference = _load_or_build_barchart_reference(
        from_date,
        to_date,
        session=(opener, headers),
        reference_frame=reference_frame,
    )
    usable = reference[reference["import_verdict"].eq("usable")].copy()
    frames: list[pd.DataFrame] = []
    for idx, contract in usable.iterrows():
        if idx > 0 and throttle_sec > 0:
            sleeper(throttle_sec)
        payload, http_status, retry_count, error = fetch_barchart_history_payload_with_retries(
            str(contract["source_symbol"]),
            session=(opener, headers),
            max_retries=max_retries,
            sleeper=sleeper,
        )
        if http_status != 200 or error:
            log.warning(
                "barchart_history_contract_skipped",
                symbol=str(contract["source_symbol"]),
                http_status=http_status,
                retry_count=retry_count,
                error=error,
            )
            continue
        frame = normalise_barchart_history(
            payload,
            contract.to_dict(),
            from_date=from_date,
            to_date=to_date,
        )
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True, sort=False)


def open_barchart_session() -> tuple[Any, dict[str, str]]:
    """Open a Barchart web session and return an opener plus API headers."""
    cookie_jar = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookie_jar))
    page_url = BARCHART_PRICE_HISTORY_URL.format(symbol="XBM26")
    request = Request(
        page_url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml",
            "Referer": "https://www.barchart.com/futures",
        },
    )
    with opener.open(request, timeout=30) as response:
        response.read(1000)
    xsrf_token = next((unquote(cookie.value) for cookie in cookie_jar if cookie.name == "XSRF-TOKEN"), None)
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
        "Referer": page_url,
        "X-Requested-With": "XMLHttpRequest",
    }
    if xsrf_token:
        headers["X-XSRF-TOKEN"] = xsrf_token
    return opener, headers


def fetch_barchart_contract_rows(
    *,
    session: tuple[Any, dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    """Fetch the Barchart historical contract list for root ``XB``."""
    opener, headers = session or open_barchart_session()
    params = urlencode(
        {
            "fields": BARCHART_LIST_FIELDS,
            "list": f"futures.historical.byRoot({BARCHART_ROOT})",
            "orderBy": "contractExpirationDate",
            "orderDir": "asc",
            "limit": "500",
            "meta": "field.shortName,field.type",
            "raw": "1",
        }
    )
    payload = _fetch_barchart_json(f"{BARCHART_QUOTES_ENDPOINT}?{params}", opener, headers)
    return list(payload.get("data") or [])


def fetch_barchart_history_payload(
    source_symbol: str,
    *,
    session: tuple[Any, dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Fetch Barchart EOD rows for one provider symbol."""
    opener, headers = session or open_barchart_session()
    request_headers = dict(headers)
    request_headers["Referer"] = BARCHART_PRICE_HISTORY_URL.format(symbol=source_symbol)
    params = urlencode(
        {
            "symbol": source_symbol,
            "fields": BARCHART_HISTORY_FIELDS,
            "type": "eod",
            "orderBy": "tradeTime",
            "orderDir": "asc",
            "method": "historical",
            "limit": "65",
            "meta": "field.shortName,field.type",
            "raw": "1",
        }
    )
    return _fetch_barchart_json(f"{BARCHART_HISTORICAL_ENDPOINT}?{params}", opener, request_headers)


def run_barchart_eod_coverage(
    from_date: date_cls = date_cls(2010, 1, 1),
    to_date: date_cls | None = None,
    *,
    throttle_sec: float = 3.0,
    max_retries: int = 3,
    session: tuple[Any, dict[str, str]] | None = None,
    sleeper: Any = time.sleep,
) -> dict[str, Any]:
    """Validate Barchart XB EOD coverage without writing processed data."""
    end = to_date or date_cls.today()
    opener, headers = session or open_barchart_session()
    contract_rows = fetch_barchart_contract_rows(session=(opener, headers))
    reference = build_reference_from_barchart_rows(contract_rows, current_year=date_cls.today().year)
    reference = reference[reference["delivery_year"].between(from_date.year, end.year)].copy()
    if reference.empty:
        reference = build_contract_reference(from_date.year, end.year, current_year=date_cls.today().year)

    contract_summaries: list[dict[str, Any]] = []
    dates_by_universe: dict[str, set[date_cls]] = {name: set() for name in BARCHART_COVERAGE_UNIVERSES}
    request_rows = _barchart_coverage_request_rows(reference)
    for idx, request_row in enumerate(request_rows):
        if idx > 0 and throttle_sec > 0:
            sleeper(throttle_sec)
        payload, http_status, retry_count, error = fetch_barchart_history_payload_with_retries(
            str(request_row["source_symbol"]),
            session=(opener, headers),
            max_retries=max_retries,
            sleeper=sleeper,
        )
        summary, dates = summarise_barchart_history_payload(
            payload,
            request_row,
            from_date=from_date,
            to_date=end,
            http_status=http_status,
            retry_count=retry_count,
            error=error,
        )
        contract_summaries.append(summary)
        for universe in str(request_row["universes"]).split("|"):
            if universe:
                dates_by_universe[universe].update(dates)

    contracts_df = pd.DataFrame(contract_summaries)
    by_year_df = build_barchart_coverage_by_year(
        dates_by_universe,
        from_date=from_date,
        to_date=end,
        contracts_df=contracts_df,
    )
    verdict = decide_barchart_coverage_verdict(by_year_df)
    report_text = build_barchart_coverage_report(
        contracts_df,
        by_year_df,
        verdict=verdict,
        from_date=from_date,
        to_date=end,
        throttle_sec=throttle_sec,
        max_retries=max_retries,
    )
    write_barchart_coverage_outputs(contracts_df, by_year_df, report_text)
    return {
        "verdict": verdict,
        "contracts_path": str(BARCHART_XB_EOD_COVERAGE_CONTRACTS),
        "by_year_path": str(BARCHART_XB_EOD_COVERAGE_BY_YEAR),
        "report_path": str(BARCHART_XB_EOD_COVERAGE_REPORT),
        "contracts": int(len(contracts_df)),
        "period_rows": int(len(by_year_df)),
    }


def fetch_barchart_history_payload_with_retries(
    source_symbol: str,
    *,
    session: tuple[Any, dict[str, str]] | None = None,
    max_retries: int = 3,
    sleeper: Any = time.sleep,
) -> tuple[dict[str, Any], int, int, str]:
    """Fetch one Barchart history payload with exponential retry on 429."""
    opener, headers = session or open_barchart_session()
    request_headers = dict(headers)
    request_headers["Referer"] = BARCHART_PRICE_HISTORY_URL.format(symbol=source_symbol)
    params = urlencode(
        {
            "symbol": source_symbol,
            "fields": BARCHART_HISTORY_FIELDS,
            "type": "eod",
            "orderBy": "tradeTime",
            "orderDir": "asc",
            "method": "historical",
            "limit": "65",
            "meta": "field.shortName,field.type",
            "raw": "1",
        }
    )
    url = f"{BARCHART_HISTORICAL_ENDPOINT}?{params}"
    last_error = ""
    for attempt in range(max_retries + 1):
        try:
            payload, status = _request_barchart_json(url, opener, request_headers)
            return payload, status, attempt, ""
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            last_error = body[:250] or str(exc)
            if exc.code != 429 or attempt >= max_retries:
                return {}, int(exc.code), attempt, last_error
            sleeper(2**attempt)
        except URLError as exc:
            last_error = str(exc.reason)
            if attempt >= max_retries:
                return {}, 0, attempt, last_error
            sleeper(2**attempt)
    return {}, 0, max_retries, last_error


def summarise_barchart_history_payload(
    payload: dict[str, Any],
    contract: dict[str, Any],
    *,
    from_date: date_cls,
    to_date: date_cls,
    http_status: int,
    retry_count: int,
    error: str = "",
) -> tuple[dict[str, Any], set[date_cls]]:
    """Summarise one Barchart contract payload for coverage reports."""
    parsed_rows: list[dict[str, Any]] = []
    dates: set[date_cls] = set()
    for row in payload.get("data") or []:
        raw = row.get("raw") if isinstance(row.get("raw"), dict) else row
        trade_date = pd.to_datetime(raw.get("tradeTime"), errors="coerce")
        if pd.isna(trade_date):
            continue
        day = trade_date.date()
        if day < from_date or day > to_date:
            continue
        parsed = {
            "date": day,
            "open": _numeric(raw.get("openPrice")),
            "high": _numeric(raw.get("highPrice")),
            "low": _numeric(raw.get("lowPrice")),
            "close_or_last": _numeric(raw.get("lastPrice")),
            "volume": _numeric(raw.get("volume")),
            "open_interest": _numeric(raw.get("openInterest")),
        }
        parsed_rows.append(parsed)
        dates.add(day)

    if http_status in {401, 403}:
        verdict = "auth_error"
    elif http_status == 429:
        verdict = "rate_limited"
    elif http_status != 200:
        verdict = "http_error"
    elif not parsed_rows:
        verdict = "empty"
    elif all(row["close_or_last"] is not None for row in parsed_rows):
        verdict = "usable"
    else:
        verdict = "missing_price"

    first = parsed_rows[0] if parsed_rows else {}
    last = parsed_rows[-1] if parsed_rows else {}
    volume_non_null = sum(row["volume"] is not None for row in parsed_rows)
    oi_non_null = sum(row["open_interest"] is not None for row in parsed_rows)
    summary = {
        "source_symbol": contract.get("source_symbol"),
        "canonical_contract_code": contract.get("canonical_contract_code"),
        "month_code": contract.get("month_code"),
        "delivery_year": contract.get("delivery_year"),
        "delivery_month": contract.get("delivery_month"),
        "active_month_status": contract.get("active_month_status"),
        "import_verdict": contract.get("import_verdict"),
        "universes": contract.get("universes"),
        "n_rows": len(parsed_rows),
        "first_date": first.get("date").isoformat() if first else None,
        "last_date": last.get("date").isoformat() if last else None,
        "first_open": first.get("open"),
        "first_high": first.get("high"),
        "first_low": first.get("low"),
        "first_close_or_last": first.get("close_or_last"),
        "last_open": last.get("open"),
        "last_high": last.get("high"),
        "last_low": last.get("low"),
        "last_close_or_last": last.get("close_or_last"),
        "volume_non_null": volume_non_null,
        "open_interest_non_null": oi_non_null,
        "http_status": http_status,
        "retry_count": retry_count,
        "verdict": verdict,
        "error": error,
    }
    return summary, dates


def build_barchart_coverage_by_year(
    dates_by_universe: dict[str, set[date_cls]],
    *,
    from_date: date_cls,
    to_date: date_cls,
    contracts_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build calendar-year and crop-year coverage rows."""
    rows: list[dict[str, Any]] = []
    for universe in BARCHART_COVERAGE_UNIVERSES:
        dates = dates_by_universe.get(universe, set())
        for period_type, periods in (
            ("calendar_year", _calendar_periods(from_date, to_date)),
            ("crop_year", _crop_year_periods(from_date, to_date)),
        ):
            for label, start, end, complete in periods:
                business_days = pd.bdate_range(start, end)
                covered = sorted(day for day in dates if start <= day <= end and day.weekday() < 5)
                coverage_pct = round(len(set(covered)) / len(business_days) * 100, 3) if len(business_days) else 0.0
                row = {
                    "universe": universe,
                    "period_type": period_type,
                    "year": label,
                    "period_start": start.isoformat(),
                    "period_end": end.isoformat(),
                    "period_complete": complete,
                    "business_days": int(len(business_days)),
                    "covered_days": int(len(set(covered))),
                    "coverage_pct": coverage_pct,
                    "longest_gap_days": _longest_gap_days(covered),
                    "contracts_found": _contracts_found_for_period(
                        contracts_df,
                        universe=universe,
                        start=start,
                        end=end,
                    ),
                }
                rows.append(row)
    return pd.DataFrame(rows)


def decide_barchart_coverage_verdict(by_year: pd.DataFrame) -> str:
    """Classify Barchart coverage according to DATA-EMA-02 rules."""
    crop = by_year[(by_year["period_type"] == "crop_year") & by_year["period_complete"]]
    strict_ok = crop[
        (crop["universe"] == "strict_official") & (crop["coverage_pct"] >= 90.0)
    ]
    exploratory_ok = crop[
        (crop["universe"] == "exploratory_with_F") & (crop["coverage_pct"] >= 90.0)
    ]
    if len(strict_ok) >= 8:
        return "GO"
    if len(exploratory_ok) >= 8:
        return "GO_EXPLORATORY"
    return "NO_GO"


def build_barchart_coverage_report(
    contracts_df: pd.DataFrame,
    by_year_df: pd.DataFrame,
    *,
    verdict: str,
    from_date: date_cls,
    to_date: date_cls,
    throttle_sec: float,
    max_retries: int,
) -> str:
    """Build a readable Barchart coverage report."""
    lines = [
        "BARCHART XB EOD COVERAGE REPORT",
        f"Generated at UTC: {pd.Timestamp.utcnow().isoformat()}",
        f"Date range: {from_date.isoformat()} -> {to_date.isoformat()}",
        f"Throttle seconds: {throttle_sec}",
        f"Max retries: {max_retries}",
        f"Verdict: {verdict}",
        "",
        "Rules:",
        "  strict_official = H/M/Q/X only",
        "  exploratory_with_F = F/H/M/Q/X",
        "  lastPrice is close_or_last, not official settlement",
        "  F contracts remain legacy_or_ambiguous and cannot enter final series by default",
        "",
        "Contract verdicts:",
    ]
    if contracts_df.empty:
        lines.append("  no contracts tested")
    else:
        verdict_counts = contracts_df["verdict"].value_counts().sort_index()
        lines.extend(f"  {key}: {value}" for key, value in verdict_counts.items())
        retry_count = int(contracts_df["retry_count"].sum())
        lines.append(f"  total_retries: {retry_count}")
    lines.extend(["", "Coverage by complete crop year:"])
    crop = by_year_df[
        (by_year_df["period_type"] == "crop_year") & by_year_df["period_complete"]
    ].copy()
    for universe in BARCHART_COVERAGE_UNIVERSES:
        subset = crop[crop["universe"] == universe]
        ok_years = int((subset["coverage_pct"] >= 90.0).sum()) if not subset.empty else 0
        avg = round(float(subset["coverage_pct"].mean()), 3) if not subset.empty else 0.0
        lines.append(f"  {universe}: years>=90%={ok_years}, avg_coverage={avg}%")
    lines.extend(
        [
            "",
            "Next action:",
            "  GO: DATA-EMA-02 can import Barchart proxy as source=barchart_proxy_exploratory.",
            "  GO_EXPLORATORY: only use F-inclusive history for diagnostics, not final series.",
            "  NO_GO: keep DATA-EMA-02 blocked until official/API source.",
            "",
        ]
    )
    return "\n".join(lines)


def write_barchart_coverage_outputs(
    contracts_df: pd.DataFrame,
    by_year_df: pd.DataFrame,
    report_text: str,
) -> tuple[Path, Path, Path]:
    """Write Barchart coverage artefacts under ``artefacts/euronext``."""
    BARCHART_XB_EOD_COVERAGE_CONTRACTS.parent.mkdir(parents=True, exist_ok=True)
    contracts_df.to_csv(BARCHART_XB_EOD_COVERAGE_CONTRACTS, index=False)
    by_year_df.to_csv(BARCHART_XB_EOD_COVERAGE_BY_YEAR, index=False)
    BARCHART_XB_EOD_COVERAGE_REPORT.write_text(report_text, encoding="utf-8")
    return (
        BARCHART_XB_EOD_COVERAGE_CONTRACTS,
        BARCHART_XB_EOD_COVERAGE_BY_YEAR,
        BARCHART_XB_EOD_COVERAGE_REPORT,
    )


def backfill_from_manual(csv_path: Path | None = None) -> int:
    """Load a manual historical EMA contracts CSV into ``ema_contract_daily.parquet``."""
    path = csv_path or (EMA_BACKFILL_DIR / MANUAL_BACKFILL_FILENAME)
    if not path.exists():
        raise FileNotFoundError(f"Manual EMA backfill not found: {path}")
    raw = pd.read_csv(path)
    history = normalise_manual_backfill(raw)
    written = _merge_into_contract_daily(history)
    _write_coverage_report(
        history,
        pd.to_datetime(history["date"]).dt.date.min(),
        pd.to_datetime(history["date"]).dt.date.max(),
        source="manual_backfill",
    )
    return written


def run_full_backfill(
    from_date: date_cls = date_cls(2014, 1, 1),
    to_date: date_cls | None = None,
    *,
    manual: Path | None = None,
    throttle_sec: float = 2.0,
) -> dict[str, Any]:
    """Run manual, scraper, then Barchart backfill and return the coverage report."""
    end = to_date or date_cls.today()
    source_used = "none"
    rows = 0
    manual_path = manual or (EMA_BACKFILL_DIR / MANUAL_BACKFILL_FILENAME)
    if manual_path.exists():
        rows = backfill_from_manual(manual_path)
        source_used = "manual_backfill"
    else:
        rows = backfill_from_barchart(from_date, end, throttle_sec=throttle_sec)
        source_used = "barchart_proxy_exploratory" if rows else "none"
        if rows == 0:
            rows = backfill_from_scraper(from_date, end, throttle_sec=throttle_sec)
            source_used = "euronext_chart_history" if rows else "none"
    report = json.loads(BACKFILL_COVERAGE_REPORT.read_text(encoding="utf-8"))
    report["rows_written"] = rows
    report["source_used"] = source_used
    BACKFILL_COVERAGE_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def download_contract_history(
    contract: dict[str, Any],
    *,
    from_date: date_cls,
    to_date: date_cls,
) -> pd.DataFrame:
    """Download chart history for one active contract and normalize it."""
    md = _maturity_param(contract)
    params = urlencode({"fOrO": "F", "md": md, "cOrP": "", "sp": ""})
    url = f"{CHART_ENDPOINT_TEMPLATE}?{params}"
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": (
                "https://live.euronext.com/en/product/commodities-futures/"
                f"EMA-DPAR/instrument?Class_symbol=EMA&Class_exchange=DPAR&fOrO=F&md={md}"
            ),
        },
    )
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    return normalise_chart_history(payload, contract, from_date=from_date, to_date=to_date)


def normalise_chart_history(
    payload: list[dict[str, Any]],
    contract: dict[str, Any],
    *,
    from_date: date_cls,
    to_date: date_cls,
) -> pd.DataFrame:
    """Normalize Euronext chart JSON rows to the contract daily schema."""
    if not payload:
        return pd.DataFrame()
    df = pd.DataFrame(payload)
    df["date"] = pd.to_datetime(df["time"]).dt.normalize()
    df = df[(df["date"].dt.date >= from_date) & (df["date"].dt.date <= to_date)].copy()
    if df.empty:
        return pd.DataFrame()
    base = _contract_base(contract)
    for key, value in base.items():
        df[key] = value
    price = pd.to_numeric(df["price"], errors="coerce")
    df["open"] = price
    df["high"] = price
    df["low"] = price
    df["last"] = price
    df["close"] = price
    df["close_or_last"] = price
    df["settlement"] = price
    df["volume"] = pd.to_numeric(df.get("volume"), errors="coerce")
    df["open_interest"] = np.nan
    df["source"] = "euronext_chart_history"
    df["is_proxy"] = False
    df["quality_flag"] = "oi_missing"
    df["days_to_expiry"] = (
        pd.to_datetime(df["expiry_date"]) - pd.to_datetime(df["date"])
    ).dt.days.astype(int)
    return _schema_columns(df)


def normalise_barchart_history(
    payload: dict[str, Any],
    contract: dict[str, Any],
    *,
    from_date: date_cls,
    to_date: date_cls,
) -> pd.DataFrame:
    """Normalize Barchart web EOD payload rows to the contract daily schema."""
    rows = payload.get("data") if isinstance(payload, dict) else None
    if not rows:
        return pd.DataFrame()
    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        raw = row.get("raw") if isinstance(row.get("raw"), dict) else row
        trade_date = pd.to_datetime(raw.get("tradeTime"), errors="coerce")
        if pd.isna(trade_date):
            continue
        day = trade_date.date()
        if day < from_date or day > to_date:
            continue
        close_or_last = _numeric(raw.get("lastPrice"))
        if close_or_last is None:
            continue
        normalized_rows.append(
            {
                "date": pd.Timestamp(day),
                "open": _numeric(raw.get("openPrice")),
                "high": _numeric(raw.get("highPrice")),
                "low": _numeric(raw.get("lowPrice")),
                "last": close_or_last,
                "close": close_or_last,
                "close_or_last": close_or_last,
                "settlement": np.nan,
                "volume": _numeric(raw.get("volume")),
                "open_interest": _numeric(raw.get("openInterest")),
            }
        )
    if not normalized_rows:
        return pd.DataFrame()
    df = pd.DataFrame(normalized_rows)
    base = _contract_base_from_reference(contract)
    for key, value in base.items():
        df[key] = value
    df["source"] = "barchart_proxy_exploratory"
    df["is_proxy"] = False
    df["quality_flag"] = "settlement_missing"
    df["days_to_expiry"] = (
        pd.to_datetime(df["expiry_date"]) - pd.to_datetime(df["date"])
    ).dt.days.astype(int)
    return _schema_columns(df)


def normalise_manual_backfill(raw: pd.DataFrame) -> pd.DataFrame:
    """Normalize a manually downloaded historical contracts CSV."""
    df = raw.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    rename = {
        "delivery": "contract_label",
        "settle": "settlement",
        "settl.": "settlement",
        "oi": "open_interest",
        "o.i": "open_interest",
        "day_vol.": "volume",
        "day_volume": "volume",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    if "date" not in df.columns:
        raise ValueError("Manual EMA backfill requires a date column")
    if "contract_code" not in df.columns:
        label_col = "contract_label" if "contract_label" in df.columns else None
        if label_col is None:
            raise ValueError("Manual EMA backfill requires contract_code or delivery")
        df["contract_code"] = df[label_col].map(parse_contract_label)
    if "canonical_contract_code" not in df.columns:
        df["canonical_contract_code"] = df["contract_code"]
    else:
        df["canonical_contract_code"] = df["canonical_contract_code"].fillna(df["contract_code"])
    if "source_symbol" not in df.columns:
        df["source_symbol"] = df.get("contract_label", df["contract_code"])
    current_month_codes = set(CURRENT_OFFICIAL_EMA_MONTHS)
    df["month_code"] = df["contract_code"].astype(str).str.split("_", n=1).str[1].str[0]
    if "active_month_status" not in df.columns:
        df["active_month_status"] = np.where(
            df["month_code"].isin(current_month_codes),
            "current_official",
            "legacy_or_ambiguous",
        )
    if "import_verdict" not in df.columns:
        df["import_verdict"] = np.where(
            df["month_code"].isin(current_month_codes),
            "usable",
            "legacy_or_ambiguous",
        )
    legacy_mask = ~df["month_code"].isin(current_month_codes)
    confirmed_legacy = (
        df["active_month_status"].eq("historical_confirmed")
        & df["import_verdict"].eq("usable")
    )
    if bool((legacy_mask & ~confirmed_legacy).any()):
        bad = sorted(df.loc[legacy_mask & ~confirmed_legacy, "contract_code"].astype(str).unique())
        raise ValueError(f"Legacy EMA contracts require confirmed reference before import: {bad}")
    df = df[df["import_verdict"].eq("usable")].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    for col in ["open", "high", "low", "settlement", "volume", "open_interest"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "settlement" not in df.columns:
        raise ValueError("Manual EMA backfill requires settlement prices")
    for col in ("open", "high", "low"):
        if col not in df.columns:
            df[col] = df["settlement"]
    if "volume" not in df.columns:
        df["volume"] = np.nan
    if "open_interest" not in df.columns:
        df["open_interest"] = np.nan
    for idx, row in df.iterrows():
        code = str(row["contract_code"])
        month_code = code.split("_", 1)[1][0]
        year = int(code[-4:])
        month = EMA_CONTRACT_MONTHS[month_code]
        contract_month = row.get("contract_month", month)
        contract_year = row.get("contract_year", year)
        df.loc[idx, "contract_month"] = int(contract_month) if pd.notna(contract_month) else month
        df.loc[idx, "contract_year"] = int(contract_year) if pd.notna(contract_year) else year
        expiry = row.get("expiry_date")
        df.loc[idx, "expiry_date"] = pd.to_datetime(expiry).date().isoformat() if pd.notna(expiry) else date_cls(year, month, 1).isoformat()
    df["product"] = "EMA"
    df["product_code"] = "EMA"
    df["close"] = df["settlement"]
    df["last"] = df["settlement"]
    df["close_or_last"] = df["settlement"]
    df["currency"] = "EUR"
    df["unit"] = "EUR/t"
    df["lot_size"] = 50
    df["source"] = df.get("source", "manual_backfill")
    df["is_proxy"] = df.get("is_proxy", False)
    df["days_to_expiry"] = (
        pd.to_datetime(df["expiry_date"]) - pd.to_datetime(df["date"])
    ).dt.days.astype(int)
    df["quality_flag"] = df.apply(lambda row: quality_flag(row.to_dict()), axis=1)
    return _schema_columns(df)


def load_manual_backfill_if_exists() -> pd.DataFrame | None:
    """Return the normalized manual backfill if the expected file exists."""
    path = EMA_BACKFILL_DIR / MANUAL_BACKFILL_FILENAME
    if not path.exists():
        return None
    return normalise_manual_backfill(pd.read_csv(path))


def build_coverage_report(df: pd.DataFrame, from_date: date_cls, to_date: date_cls, *, source: str) -> dict[str, Any]:
    """Compute historical coverage metrics for EMA contracts."""
    business_days = pd.bdate_range(from_date, to_date)
    if df.empty:
        covered_dates = pd.DatetimeIndex([])
        contracts: list[str] = []
        proxy_pct = 0.0
        observed_start = None
        observed_end = None
    else:
        covered_dates = pd.DatetimeIndex(pd.to_datetime(df["date"]).dropna().unique())
        contracts = sorted(str(c) for c in df["contract_code"].dropna().unique())
        proxy_pct = float(pd.Series(df.get("is_proxy", False)).astype(bool).mean())
        observed_start = pd.Timestamp(covered_dates.min()).date().isoformat()
        observed_end = pd.Timestamp(covered_dates.max()).date().isoformat()
    covered_in_range = covered_dates[(covered_dates >= business_days.min()) & (covered_dates <= business_days.max())]
    missing = business_days.difference(covered_in_range)
    years = range(from_date.year, to_date.year + 1)
    harvest = {str(year): f"EMA_X{year}" in contracts for year in years}
    required_years = range(from_date.year, min(to_date.year, 2025) + 1)
    harvest_requirement_met = all(harvest[str(year)] for year in required_years)
    coverage_pct = (
        round(float(len(covered_in_range) / len(business_days) * 100), 3)
        if len(business_days)
        else 0.0
    )
    meets_2014_requirement = (
        from_date >= date_cls(2014, 1, 1)
        and coverage_pct >= 80.0
        and harvest_requirement_met
        and observed_start is not None
        and pd.Timestamp(observed_start).date() <= from_date
    )
    coverage_status = "OK" if meets_2014_requirement else "PARTIAL_REQUIRES_MANUAL_BACKFILL"
    return {
        "source": source,
        "date_range": [from_date.isoformat(), to_date.isoformat()],
        "observed_date_range": [observed_start, observed_end],
        "total_days": int(len(business_days)),
        "covered_days": int(len(covered_in_range)),
        "coverage_pct": coverage_pct,
        "coverage_status": coverage_status,
        "meets_2014_requirement": meets_2014_requirement,
        "manual_backfill_expected_path": str(EMA_BACKFILL_DIR / MANUAL_BACKFILL_FILENAME),
        "contracts_found": contracts,
        "missing_periods": _missing_periods(missing),
        "harvest_nov_coverage": harvest,
        "proxy_pct": round(proxy_pct, 6),
        "endpoint_limitation": (
            "Euronext public chart/settlement endpoints expose recent history for currently "
            "active maturities only. Expired historical contracts require a manual historical "
            "CSV or paid data provider."
        ),
    }


def _write_coverage_report(df: pd.DataFrame, from_date: date_cls, to_date: date_cls, *, source: str) -> Path:
    report = build_coverage_report(df, from_date, to_date, source=source)
    BACKFILL_COVERAGE_REPORT.parent.mkdir(parents=True, exist_ok=True)
    BACKFILL_COVERAGE_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return BACKFILL_COVERAGE_REPORT


def _merge_into_contract_daily(history: pd.DataFrame) -> int:
    if history.empty:
        return 0
    EMA_CONTRACT_DAILY.parent.mkdir(parents=True, exist_ok=True)
    incoming = normalise_contract_daily_frame(history)
    incoming["date"] = pd.to_datetime(incoming["date"]).dt.normalize()
    if EMA_CONTRACT_DAILY.exists():
        existing = normalise_contract_daily_frame(pd.read_parquet(EMA_CONTRACT_DAILY))
        existing["date"] = pd.to_datetime(existing["date"]).dt.normalize()
        combined = pd.concat([existing, incoming], ignore_index=True, sort=False)
    else:
        combined = incoming
    combined = normalise_contract_daily_frame(combined)
    combined["_source_rank"] = combined["source"].map(SOURCE_RANK).fillna(0)
    combined["_proxy_rank"] = (~combined["is_proxy"].fillna(False).astype(bool)).astype(int)
    combined = combined.sort_values(["date", "contract_code", "_proxy_rank", "_source_rank"])
    combined = combined.drop_duplicates(["date", "contract_code"], keep="last")
    combined = combined.drop(columns=["_source_rank", "_proxy_rank"])
    combined = combined.sort_values(["date", "contract_code"]).reset_index(drop=True)
    combined.to_parquet(EMA_CONTRACT_DAILY, index=False)
    return int(len(incoming))


def _load_or_build_barchart_reference(
    from_date: date_cls,
    to_date: date_cls,
    *,
    session: tuple[Any, dict[str, str]],
    reference_frame: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if reference_frame is not None:
        reference = validate_contract_reference(reference_frame)
    elif EMA_CONTRACT_REFERENCE.exists():
        reference = validate_contract_reference(pd.read_parquet(EMA_CONTRACT_REFERENCE))
    else:
        rows = fetch_barchart_contract_rows(session=session)
        reference = build_reference_from_barchart_rows(rows, current_year=date_cls.today().year)
        if reference.empty:
            reference = build_contract_reference(
                from_date.year,
                to_date.year,
                current_year=date_cls.today().year,
            )
    year_mask = reference["delivery_year"].between(from_date.year, to_date.year)
    return reference[year_mask].reset_index(drop=True)


def _fetch_barchart_json(url: str, opener: Any, headers: dict[str, str]) -> dict[str, Any]:
    request = Request(url, headers=headers)
    try:
        with opener.open(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        raise RuntimeError(f"Barchart request failed ({exc.code}): {body[:250]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Barchart request failed: {exc.reason}") from exc


def _request_barchart_json(
    url: str,
    opener: Any,
    headers: dict[str, str],
) -> tuple[dict[str, Any], int]:
    request = Request(url, headers=headers)
    with opener.open(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
        return payload, int(response.status)


def _barchart_coverage_request_rows(reference: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, row in reference.iterrows():
        month_code = str(row["month_code"])
        universes = []
        if month_code in CURRENT_OFFICIAL_EMA_MONTHS:
            universes.append("strict_official")
            universes.append("exploratory_with_F")
        elif month_code == "F":
            universes.append("exploratory_with_F")
        if not universes:
            continue
        record = row.to_dict()
        record["universes"] = "|".join(universes)
        rows.append(record)
    return rows


def _contract_base(contract: dict[str, Any]) -> dict[str, Any]:
    code = str(contract["contract_code"])
    month_code = code.split("_", 1)[1][0]
    year = int(code[-4:])
    month = int(contract.get("contract_month") or EMA_CONTRACT_MONTHS[month_code])
    expiry = contract.get("expiry_date") or date_cls(year, month, 1).isoformat()
    return {
        "contract_code": code,
        "source_symbol": contract.get("source_symbol") or code,
        "canonical_contract_code": contract.get("canonical_contract_code") or code,
        "month_code": month_code,
        "active_month_status": contract.get("active_month_status") or "current_official",
        "import_verdict": contract.get("import_verdict") or "usable",
        "product": "EMA",
        "product_code": "EMA",
        "contract_month": month,
        "contract_year": year,
        "expiry_date": expiry,
        "delivery": contract.get("delivery"),
        "currency": "EUR",
        "unit": "EUR/t",
        "lot_size": 50,
    }


def _contract_base_from_reference(contract: dict[str, Any]) -> dict[str, Any]:
    month_code = str(contract["month_code"])
    year = int(contract["delivery_year"])
    month = int(contract["delivery_month"])
    fallback_expiry = date_cls(year, month, 1).isoformat()
    expiry = _first_non_missing(contract.get("expiry_date"), contract.get("last_trade_date"), fallback_expiry)
    canonical = _first_non_missing(contract.get("canonical_contract_code"))
    if canonical is None:
        raise ValueError(f"Cannot import EMA contract without canonical code: {contract}")
    return {
        "contract_code": canonical,
        "source_symbol": contract.get("source_symbol") or canonical,
        "canonical_contract_code": canonical,
        "month_code": month_code,
        "active_month_status": contract.get("active_month_status") or "historical_confirmed",
        "import_verdict": contract.get("import_verdict") or "usable",
        "product": "EMA",
        "product_code": "EMA",
        "contract_month": month,
        "contract_year": year,
        "expiry_date": pd.to_datetime(expiry).date().isoformat(),
        "delivery": contract.get("contract_name"),
        "currency": "EUR",
        "unit": "EUR/t",
        "lot_size": 50,
    }


def _maturity_param(contract: dict[str, Any]) -> str:
    month = int(contract["contract_month"])
    year = int(contract["contract_year"])
    return f"01-{month:02d}-{year}"


def _numeric(value: Any) -> float | None:
    if value in (None, "", "N/A"):
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def _calendar_periods(
    from_date: date_cls,
    to_date: date_cls,
) -> list[tuple[int, date_cls, date_cls, bool]]:
    periods: list[tuple[int, date_cls, date_cls, bool]] = []
    for year in range(from_date.year, to_date.year + 1):
        raw_start = date_cls(year, 1, 1)
        raw_end = date_cls(year, 12, 31)
        start = max(from_date, raw_start)
        end = min(to_date, raw_end)
        periods.append((year, start, end, start == raw_start and end == raw_end))
    return periods


def _crop_year_periods(
    from_date: date_cls,
    to_date: date_cls,
) -> list[tuple[int, date_cls, date_cls, bool]]:
    first_crop_year = from_date.year + 1 if from_date.month >= 9 else from_date.year
    last_crop_year = to_date.year + 1 if to_date.month >= 9 else to_date.year
    periods: list[tuple[int, date_cls, date_cls, bool]] = []
    for crop_year in range(first_crop_year, last_crop_year + 1):
        raw_start = date_cls(crop_year - 1, 9, 1)
        raw_end = date_cls(crop_year, 8, 31)
        start = max(from_date, raw_start)
        end = min(to_date, raw_end)
        periods.append((crop_year, start, end, start == raw_start and end == raw_end))
    return periods


def _longest_gap_days(days: list[date_cls]) -> int:
    if len(days) < 2:
        return 0
    unique_days = sorted(set(days))
    return max((b - a).days for a, b in zip(unique_days, unique_days[1:], strict=False))


def _contracts_found_for_period(
    contracts_df: pd.DataFrame | None,
    *,
    universe: str,
    start: date_cls,
    end: date_cls,
) -> str:
    if contracts_df is None or contracts_df.empty:
        return ""
    frame = contracts_df.copy()
    frame = frame[frame["universes"].astype(str).str.contains(universe, regex=False)]
    first = pd.to_datetime(frame["first_date"], errors="coerce")
    last = pd.to_datetime(frame["last_date"], errors="coerce")
    mask = first.notna() & last.notna() & (last.dt.date >= start) & (first.dt.date <= end)
    return ",".join(sorted(str(symbol) for symbol in frame.loc[mask, "source_symbol"].dropna().unique()))


def _first_non_missing(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        try:
            if pd.isna(value):
                continue
        except TypeError:
            pass
        if value == "":
            continue
        return value
    return None


def _schema_columns(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "date",
        "contract_code",
        "source_symbol",
        "canonical_contract_code",
        "month_code",
        "active_month_status",
        "import_verdict",
        "product",
        "product_code",
        "contract_month",
        "contract_year",
        "expiry_date",
        "days_to_expiry",
        "delivery",
        "open",
        "high",
        "low",
        "last",
        "close",
        "settlement",
        "close_or_last",
        "volume",
        "open_interest",
        "currency",
        "unit",
        "lot_size",
        "source",
        "is_proxy",
        "quality_flag",
    ]
    for col in columns:
        if col not in df.columns:
            df[col] = np.nan
    return df[columns].sort_values(["date", "contract_code"]).reset_index(drop=True)


def _missing_periods(missing: pd.DatetimeIndex) -> list[dict[str, str]]:
    if missing.empty:
        return []
    periods: list[dict[str, str]] = []
    start = missing[0]
    prev = missing[0]
    for current in missing[1:]:
        if (current - prev).days > 3:
            periods.append({"from": start.date().isoformat(), "to": prev.date().isoformat(), "reason": "source_unavailable"})
            start = current
        prev = current
    periods.append({"from": start.date().isoformat(), "to": prev.date().isoformat(), "reason": "source_unavailable"})
    return periods


__all__ = [
    "BACKFILL_COVERAGE_REPORT",
    "MANUAL_BACKFILL_FILENAME",
    "backfill_from_barchart",
    "backfill_from_manual",
    "backfill_from_scraper",
    "build_coverage_report",
    "collect_barchart_history",
    "download_contract_history",
    "fetch_barchart_contract_rows",
    "fetch_barchart_history_payload",
    "load_manual_backfill_if_exists",
    "normalise_barchart_history",
    "normalise_chart_history",
    "normalise_manual_backfill",
    "open_barchart_session",
    "run_full_backfill",
]
