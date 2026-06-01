"""Targeted Barchart contract download probe for Euronext EMA symbols."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pandas as pd

from mais.paths import (
    EMA_BARCHART_CONTRACT_DOWNLOAD_REPORT,
    EMA_BARCHART_CONTRACT_DOWNLOAD_RESULTS,
)

DEFAULT_SYMBOLS = ("XBM26", "XBQ26", "XBX26", "XBM14")
BARCHART_URL_TEMPLATE = "https://www.barchart.com/futures/quotes/{symbol}/historical-prices"
RESULT_COLUMNS = [
    "source_symbol",
    "url",
    "http_status",
    "title_detected",
    "exchange_detected",
    "symbol_root_detected",
    "contract_name_detected",
    "has_download_button",
    "has_historical_table",
    "n_rows_visible",
    "download_endpoint_signals",
    "historical_api_signal",
    "verdict",
    "notes",
]


def probe_contract_symbol(symbol: str, *, html: str | None = None) -> dict[str, Any]:
    """Probe one Barchart EMA contract page for public OHLC downloadability."""
    source_symbol = symbol.upper()
    url = BARCHART_URL_TEMPLATE.format(symbol=source_symbol)
    status = 200
    if html is None:
        status, html = _fetch_html(url)
    title = _extract_title(html)
    root = _extract_json_string_field(html, "symbolRoot")
    exchange = _extract_json_string_field(html, "exchange")
    contract_name = _extract_json_string_field(html, "contractName")
    has_download = _has_download_signal(html)
    has_table = _has_visible_historical_table(html)
    n_rows = _count_visible_table_rows(html)
    endpoint_signals = _download_endpoint_signals(html)
    historical_api_signal = "historicalFutures" in html or "historical-futures" in html
    page_exists = status == 200 and root == "XB" and exchange == "Euronext"
    if page_exists and has_table and n_rows > 0:
        verdict = "downloadable_public"
        notes = "visible historical rows detected"
    elif page_exists and has_download:
        verdict = "page_exists_no_download"
        notes = "download UI/API signal detected, but no public rows visible"
    elif page_exists:
        verdict = "page_exists_metadata_only"
        notes = "metadata found, no download signal"
    else:
        verdict = "unavailable"
        notes = "page not usable for EMA contract download"
    return {
        "source_symbol": source_symbol,
        "url": url,
        "http_status": status,
        "title_detected": title,
        "exchange_detected": exchange,
        "symbol_root_detected": root,
        "contract_name_detected": contract_name,
        "has_download_button": has_download,
        "has_historical_table": has_table,
        "n_rows_visible": n_rows,
        "download_endpoint_signals": ",".join(endpoint_signals),
        "historical_api_signal": historical_api_signal,
        "verdict": verdict,
        "notes": notes,
    }


def probe_default_symbols(symbols: tuple[str, ...] = DEFAULT_SYMBOLS) -> list[dict[str, Any]]:
    """Probe the short targeted DATA-EMA-14 symbol set."""
    return [probe_contract_symbol(symbol) for symbol in symbols]


def write_probe_outputs(
    results: list[dict[str, Any]],
    *,
    results_path: Path = EMA_BARCHART_CONTRACT_DOWNLOAD_RESULTS,
    report_path: Path = EMA_BARCHART_CONTRACT_DOWNLOAD_REPORT,
) -> tuple[Path, Path]:
    """Write CSV and text report."""
    results_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(results)
    for col in RESULT_COLUMNS:
        if col not in frame.columns:
            frame[col] = None
    frame = frame[RESULT_COLUMNS]
    frame.to_csv(results_path, index=False)
    report_path.write_text(build_probe_report(results), encoding="utf-8")
    return results_path, report_path


def build_probe_report(results: list[dict[str, Any]]) -> str:
    """Build readable targeted-contract report."""
    counts = Counter(str(row["verdict"]) for row in results)
    if any(row["verdict"] == "downloadable_public" for row in results):
        decision = "Au moins un contrat a des lignes historiques publiques visibles."
    elif any(row["verdict"] == "page_exists_no_download" for row in results):
        decision = (
            "Les pages contrats existent avec signaux download/API, mais aucune ligne OHLC "
            "publique n'est visible. Compte/API Barchart requis."
        )
    else:
        decision = "Aucun téléchargement contrat par contrat exploitable en accès public."
    lines = [
        "BARCHART CONTRACT DOWNLOAD PROBE REPORT",
        f"Generated at UTC: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Symbols tested: {', '.join(row['source_symbol'] for row in results)}",
        "Verdicts:",
        *[f"  {key}: {value}" for key, value in sorted(counts.items())],
        "",
        "Details:",
        *[
            f"  {row['source_symbol']}: {row['verdict']} status={row['http_status']} "
            f"download={row['has_download_button']} rows={row['n_rows_visible']} "
            f"contract={row.get('contract_name_detected')}"
            for row in results
        ],
        "",
        "Decision:",
        f"  {decision}",
        "",
    ]
    return "\n".join(lines)


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


def _extract_title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return _squash(unescape(re.sub(r"<[^>]+>", " ", match.group(1))))


def _extract_json_string_field(html: str, key: str) -> str | None:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*"((?:\\.|[^"\\])*)"', html)
    if not match:
        return None
    try:
        return str(json.loads(f'"{match.group(1)}"'))
    except json.JSONDecodeError:
        return unescape(match.group(1))


def _has_download_signal(html: str) -> bool:
    text = html.lower()
    return "historical-download" in text or "downloadlimit" in text or "download" in text


def _has_visible_historical_table(html: str) -> bool:
    text = html.lower()
    return "<table" in text and "historical" in text and ("open interest" in text or "volume" in text)


def _count_visible_table_rows(html: str) -> int:
    if "<table" not in html.lower():
        return 0
    return max(0, len(re.findall(r"<tr\b", html, flags=re.IGNORECASE)) - 1)


def _download_endpoint_signals(html: str) -> list[str]:
    text = html.lower()
    signals = []
    for signal in ("historical-download", "downloadlimit", "historicalfutures", "core-api"):
        if signal in text:
            signals.append(signal)
    return signals


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for DATA-EMA-14."""
    parser = argparse.ArgumentParser(description="Probe targeted Barchart EMA contract downloads")
    parser.add_argument("symbols", nargs="*", default=list(DEFAULT_SYMBOLS))
    args = parser.parse_args(argv)
    results = probe_default_symbols(tuple(args.symbols))
    results_path, report_path = write_probe_outputs(results)
    print(f"Wrote {results_path}")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
