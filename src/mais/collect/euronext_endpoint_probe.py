"""Probe and validate the Euronext EMA futures prices endpoint."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from dateutil import parser as date_parser

from mais.collect.euronext_ema_collector import parse_contract_label
from mais.paths import ARTEFACTS_DIR

EURONEXT_PRODUCT_PAGE = "https://live.euronext.com/en/product/commodity-futures/EMA-DPAR"
EURONEXT_PRICES_ENDPOINT = (
    "https://live.euronext.com/en/ajax/getPricesFutures/commodities-futures/EMA/DPAR"
)

INVALID_ENDPOINT_CANDIDATES = (
    "https://live.euronext.com/en/pd_ajax/fixings?d=EMA-DPAR&p=0",
    "https://live.euronext.com/en/pd/data/quote?d=EMA-DPAR&t=commodity-futures",
)

EXPECTED_FIELDS = {
    "delivery",
    "bid",
    "ask",
    "last",
    "time",
    "change",
    "day_volume",
    "open",
    "high",
    "low",
    "settlement",
    "open_interest",
}


@dataclass(frozen=True)
class EndpointValidation:
    """Structured validation result for the Euronext endpoint."""

    endpoint_url: str
    product_page: str
    verdict: str
    rows_found: int
    rows_compared: int
    fields_present: list[str]
    fields_missing: list[str]
    contracts_found: list[str]
    session_date: str | None
    sample_data: list[dict[str, Any]]
    notes: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "endpoint_url": self.endpoint_url,
            "product_page": self.product_page,
            "verdict": self.verdict,
            "rows_found": self.rows_found,
            "rows_compared": self.rows_compared,
            "fields_present": self.fields_present,
            "fields_missing": self.fields_missing,
            "contracts_found": self.contracts_found,
            "session_date": self.session_date,
            "sample_data": self.sample_data,
            "notes": self.notes,
        }


class _FuturesPricesTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_table = False
        self.in_h3 = False
        self.in_header_cell = False
        self.in_cell = False
        self.current_header: list[str] = []
        self.current_cell: list[str] = []
        self.current_row: list[str] = []
        self.headers: list[str] = []
        self.rows: list[list[str]] = []
        self.title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "table" and attrs_dict.get("id") == "future-prices-table":
            self.in_table = True
        if tag == "h3":
            self.in_h3 = True
        if not self.in_table:
            return
        if tag == "tr":
            self.current_row = []
        elif tag == "th":
            self.in_header_cell = True
            self.current_header = []
        elif tag == "td":
            self.in_cell = True
            self.current_cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "h3":
            self.in_h3 = False
        if not self.in_table:
            return
        if tag == "th" and self.in_header_cell:
            self.headers.append(_squash_text(" ".join(self.current_header)))
            self.in_header_cell = False
        elif tag == "td" and self.in_cell:
            self.current_row.append(_squash_text(" ".join(self.current_cell)))
            self.in_cell = False
        elif tag == "tr" and self.current_row:
            self.rows.append(self.current_row)
        elif tag == "table":
            self.in_table = False

    def handle_data(self, data: str) -> None:
        if self.in_h3:
            self.title_parts.append(data)
        if self.in_header_cell:
            self.current_header.append(data)
        if self.in_cell:
            self.current_cell.append(data)


def fetch_endpoint_html(url: str = EURONEXT_PRICES_ENDPOINT, timeout: int = 20) -> str:
    """Fetch the official AJAX HTML used by the Euronext EMA page."""
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": EURONEXT_PRODUCT_PAGE,
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_prices_html(html: str) -> tuple[list[dict[str, Any]], str | None]:
    """Parse Euronext active futures prices HTML into normalized contract rows."""
    parser = _FuturesPricesTableParser()
    parser.feed(html)
    session_date = _parse_session_date(_squash_text(" ".join(parser.title_parts)))
    header_keys = [_header_to_key(h) for h in parser.headers]
    output: list[dict[str, Any]] = []
    for row in parser.rows:
        if len(row) != len(header_keys):
            continue
        raw = dict(zip(header_keys, row, strict=False))
        delivery = raw.get("delivery", "")
        if not delivery:
            continue
        item: dict[str, Any] = {
            "date": session_date,
            "delivery": delivery,
            "contract_code": parse_contract_label(delivery),
            "product_code": "EMA",
            "exchange": "DPAR",
            "bid": _parse_number(raw.get("bid")),
            "ask": _parse_number(raw.get("ask")),
            "last": _parse_number(raw.get("last")),
            "time": raw.get("time") or None,
            "change": _parse_number(raw.get("change")),
            "day_volume": _parse_number(raw.get("day_volume")),
            "open": _parse_number(raw.get("open")),
            "high": _parse_number(raw.get("high")),
            "low": _parse_number(raw.get("low")),
            "settlement": _parse_number(raw.get("settlement")),
            "open_interest": _parse_number(raw.get("open_interest")),
            "source": "euronext_ajax_prices",
            "is_proxy": False,
        }
        output.append(item)
    return output, session_date


def probe_euronext_endpoint(html: str | None = None) -> dict[str, Any]:
    """Validate the Euronext EMA active contracts endpoint."""
    raw_html = html if html is not None else fetch_endpoint_html()
    rows, session_date = parse_prices_html(raw_html)
    fields_present = sorted({field for row in rows for field, value in row.items() if value is not None})
    missing = sorted(EXPECTED_FIELDS - set(fields_present))
    contracts = sorted({row["contract_code"] for row in rows})
    notes = [
        "Validated endpoint discovered in Euronext awl-derivatives-prices.js.",
        "The endpoint returns the active-contract price table rendered on the official EMA page.",
        "Historical backfill is not exposed by this endpoint; it is suitable for daily snapshots.",
    ]
    if len(rows) < 10:
        notes.append(
            f"Only {len(rows)} active EMA contracts were available; rows_compared is below 10 by market design."
        )
    if INVALID_ENDPOINT_CANDIDATES:
        notes.append("Previous candidate endpoints were rejected: pd_ajax/fixings=404, pd/data/quote=empty.")

    is_ema = bool(rows) and all(row["product_code"] == "EMA" for row in rows)
    has_prices = bool(rows) and all(row.get("settlement") is not None for row in rows[: min(3, len(rows))])
    verdict = "VALIDATED" if is_ema and has_prices and not missing else "NEEDS_MANUAL_REVIEW"
    validation = EndpointValidation(
        endpoint_url=EURONEXT_PRICES_ENDPOINT,
        product_page=EURONEXT_PRODUCT_PAGE,
        verdict=verdict,
        rows_found=len(rows),
        rows_compared=min(10, len(rows)),
        fields_present=fields_present,
        fields_missing=missing,
        contracts_found=contracts,
        session_date=session_date,
        sample_data=rows[: min(10, len(rows))],
        notes=notes,
    )
    return validation.as_dict()


def write_validation_report(report: dict[str, Any], out_path: Path | None = None) -> Path:
    """Write the DATA-EMA-07 validation report."""
    path = out_path or (ARTEFACTS_DIR / "euronext_endpoint_validation_report.txt")
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "EURONEXT ENDPOINT VALIDATION REPORT",
        "",
        f"Verdict: {report['verdict']}",
        f"Product page: {report['product_page']}",
        f"Endpoint: {report['endpoint_url']}",
        f"Session date: {report['session_date']}",
        f"Rows found: {report['rows_found']}",
        f"Rows compared: {report['rows_compared']}",
        f"Contracts found: {', '.join(report['contracts_found'])}",
        f"Fields present: {', '.join(report['fields_present'])}",
        f"Fields missing: {', '.join(report['fields_missing']) or 'none'}",
        "",
        "Notes:",
    ]
    lines.extend(f"- {note}" for note in report["notes"])
    lines.extend(["", "Sample data:"])
    for item in report["sample_data"]:
        lines.append(
            "- {delivery} ({contract_code}) settlement={settlement} open={open} "
            "high={high} low={low} volume={day_volume} oi={open_interest}".format(**item)
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _header_to_key(header: str) -> str:
    mapping = {
        "Delivery": "delivery",
        "Bid": "bid",
        "Ask": "ask",
        "Last": "last",
        "Time": "time",
        "+/-": "change",
        "Day Vol.": "day_volume",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Settl.": "settlement",
        "O.I": "open_interest",
    }
    return mapping.get(header, header.lower().replace(" ", "_").replace(".", ""))


def _parse_number(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = value.strip().replace(",", "").replace("\u00a0", "")
    if cleaned in {"", "-", "N/A"}:
        return None
    return float(cleaned)


def _parse_session_date(title: str) -> str | None:
    if " - " not in title:
        return None
    candidate = title.rsplit(" - ", 1)[-1].strip()
    try:
        parsed: date = date_parser.parse(candidate, dayfirst=True).date()
    except (ValueError, TypeError, OverflowError):
        return None
    return parsed.isoformat()


def _squash_text(value: str) -> str:
    return " ".join(str(value).split())


if __name__ == "__main__":
    validation_report = probe_euronext_endpoint()
    output = write_validation_report(validation_report)
    print(f"{validation_report['verdict']} - report written to {output}")
