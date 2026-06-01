"""Probe possible long continuous Euronext EMA corn price series."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

import pandas as pd

from mais.paths import EMA_CONTINUOUS_PROBE_REPORT, EMA_CONTINUOUS_PROBE_RESULTS

YFINANCE_CANDIDATES = ("EMA=F", "ZCE=F")
BARCHART_CANDIDATES = ("XB*0", "XB00", "XB1!", "EMA1!", "EMA1")
PROBE_COLUMNS = [
    "provider",
    "symbol",
    "url",
    "http_status",
    "rows",
    "start_date",
    "end_date",
    "price_column",
    "title_detected",
    "exchange_detected",
    "symbol_root_detected",
    "has_historical_table",
    "has_download_button",
    "n_rows_visible",
    "verdict",
    "notes",
]


def probe_yfinance_symbol(symbol: str, *, min_rows: int = 2500) -> dict[str, Any]:
    """Probe a continuous symbol through yfinance without writing any data."""
    notes = []
    try:
        import yfinance as yf
    except ImportError:
        return _base_result(
            provider="yfinance",
            symbol=symbol,
            verdict="unavailable",
            notes="yfinance not installed",
        )
    try:
        raw = yf.download(
            symbol,
            period="max",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
    except Exception as exc:
        return _base_result(
            provider="yfinance",
            symbol=symbol,
            verdict="unavailable",
            notes=f"download_error={exc}",
        )
    if raw is None or raw.empty:
        return _base_result(provider="yfinance", symbol=symbol, verdict="unavailable", notes="empty")
    frame = raw.reset_index()
    price_col = _find_price_column(frame)
    if price_col is None:
        return _base_result(
            provider="yfinance",
            symbol=symbol,
            rows=len(frame),
            verdict="empty_or_short",
            notes="no close/settlement column",
        )
    date_col = _find_date_column(frame)
    dates = pd.to_datetime(frame[date_col], errors="coerce") if date_col else pd.Series(dtype="datetime64[ns]")
    rows = int(frame[price_col].notna().sum())
    if rows < min_rows:
        notes.append(f"rows<{min_rows}")
    verdict = "usable_continuous" if rows >= min_rows else "empty_or_short"
    return _base_result(
        provider="yfinance",
        symbol=symbol,
        rows=rows,
        start_date=_date_iso(dates.min()) if not dates.empty else None,
        end_date=_date_iso(dates.max()) if not dates.empty else None,
        price_column=str(price_col),
        verdict=verdict,
        notes="; ".join(notes),
    )


def probe_barchart_continuous_symbol(symbol: str, *, html: str | None = None) -> dict[str, Any]:
    """Probe a possible Barchart continuous series page."""
    url = _barchart_url(symbol)
    status = 200
    if html is None:
        status, html = _fetch_html(url)
    title = _extract_title(html)
    root = _extract_json_string_field(html, "symbolRoot")
    exchange = _extract_json_string_field(html, "exchange")
    has_table = _has_visible_historical_table(html)
    has_download = _has_download_signal(html)
    n_rows = _count_visible_table_rows(html)
    page_exists = status == 200 and ("barchart" in title.lower() or root or exchange)
    if has_table and n_rows > 0:
        verdict = "usable_continuous"
    elif page_exists:
        verdict = "page_exists_no_download"
    else:
        verdict = "unavailable"
    return _base_result(
        provider="barchart",
        symbol=symbol,
        url=url,
        http_status=status,
        title_detected=title,
        exchange_detected=exchange,
        symbol_root_detected=root,
        has_historical_table=has_table,
        has_download_button=has_download,
        n_rows_visible=n_rows,
        verdict=verdict,
    )


def probe_all_candidates() -> list[dict[str, Any]]:
    """Probe all configured continuous-series candidates."""
    results = [probe_yfinance_symbol(symbol) for symbol in YFINANCE_CANDIDATES]
    results.extend(probe_barchart_continuous_symbol(symbol) for symbol in BARCHART_CANDIDATES)
    return results


def write_probe_outputs(
    results: list[dict[str, Any]],
    *,
    results_path: Path = EMA_CONTINUOUS_PROBE_RESULTS,
    report_path: Path = EMA_CONTINUOUS_PROBE_REPORT,
) -> tuple[Path, Path]:
    """Write the probe CSV and readable report."""
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
    """Build a readable decision report."""
    verdict_counts = Counter(str(row.get("verdict")) for row in results)
    usable = [row for row in results if row.get("verdict") == "usable_continuous"]
    if usable:
        decision = (
            "Au moins une serie continue longue semble exploitable. "
            "La marquer provider_rolled_continuous avant tout benchmark."
        )
    else:
        decision = (
            "Aucune serie continue longue exploitable en acces public automatique. "
            "Un export fournisseur/API reste requis."
        )
    lines = [
        "EMA CONTINUOUS SERIES PROBE REPORT",
        f"Generated at UTC: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Candidates tested: {len(results)}",
        "Verdicts:",
        *[f"  {key}: {value}" for key, value in sorted(verdict_counts.items())],
        "",
        "Rows:",
        *[
            f"  {row.get('provider')}:{row.get('symbol')} -> {row.get('verdict')} "
            f"rows={row.get('rows')} range={row.get('start_date')}..{row.get('end_date')}"
            for row in results
        ],
        "",
        "Decision:",
        f"  {decision}",
        "",
        "Important rule:",
        "  A provider-rolled continuous series can test the EMA pivot, but cannot replace contract-level backfill for rolls/curve features.",
        "",
    ]
    return "\n".join(lines)


def _base_result(
    *,
    provider: str,
    symbol: str,
    verdict: str,
    url: str | None = None,
    http_status: int | None = None,
    rows: int = 0,
    start_date: str | None = None,
    end_date: str | None = None,
    price_column: str | None = None,
    title_detected: str | None = None,
    exchange_detected: str | None = None,
    symbol_root_detected: str | None = None,
    has_historical_table: bool = False,
    has_download_button: bool = False,
    n_rows_visible: int = 0,
    notes: str = "",
) -> dict[str, Any]:
    return {
        "provider": provider,
        "symbol": symbol,
        "url": url,
        "http_status": http_status,
        "rows": rows,
        "start_date": start_date,
        "end_date": end_date,
        "price_column": price_column,
        "title_detected": title_detected,
        "exchange_detected": exchange_detected,
        "symbol_root_detected": symbol_root_detected,
        "has_historical_table": has_historical_table,
        "has_download_button": has_download_button,
        "n_rows_visible": n_rows_visible,
        "verdict": verdict,
        "notes": notes,
    }


def _barchart_url(symbol: str) -> str:
    return f"https://www.barchart.com/futures/quotes/{quote(symbol, safe='')}/historical-prices"


def _fetch_html(url: str, timeout: int = 20) -> tuple[int, str]:
    request = Request(
        url,
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
    except Exception as exc:
        return 0, str(exc)


def _find_price_column(frame: pd.DataFrame) -> str | tuple[str, ...] | None:
    for col in frame.columns:
        key = "_".join(str(part).lower() for part in col) if isinstance(col, tuple) else str(col).lower()
        if key in {"adj close", "adj_close", "close", "settlement", "last"} or key.endswith("_close"):
            return col
    return None


def _find_date_column(frame: pd.DataFrame) -> str | tuple[str, ...] | None:
    for col in frame.columns:
        key = "_".join(str(part).lower() for part in col) if isinstance(col, tuple) else str(col).lower()
        if key in {"date", "datetime"}:
            return col
    return None


def _extract_title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return _squash(unescape(re.sub(r"<[^>]+>", " ", match.group(1))))


def _extract_json_string_field(html: str, key: str) -> str | None:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*"((?:\\.|[^"\\])*)"', html)
    if not match:
        return None
    return unescape(match.group(1))


def _has_visible_historical_table(html: str) -> bool:
    text = html.lower()
    return "<table" in text and "historical" in text and ("open interest" in text or "volume" in text)


def _has_download_signal(html: str) -> bool:
    text = html.lower()
    return "historical-download" in text or "downloadlimit" in text or "download" in text


def _count_visible_table_rows(html: str) -> int:
    if "<table" not in html.lower():
        return 0
    return max(0, len(re.findall(r"<tr\b", html, flags=re.IGNORECASE)) - 1)


def _date_iso(value: Any) -> str | None:
    if pd.isna(value):
        return None
    return pd.Timestamp(value).date().isoformat()


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for DATA-EMA-13."""
    parser = argparse.ArgumentParser(description="Probe long continuous EMA series candidates")
    parser.parse_args(argv)
    results = probe_all_candidates()
    results_path, report_path = write_probe_outputs(results)
    print(f"Wrote {results_path}")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
