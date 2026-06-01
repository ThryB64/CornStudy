from __future__ import annotations

from mais.collect.euronext_endpoint_probe import (
    parse_prices_html,
    probe_euronext_endpoint,
    write_validation_report,
)

SAMPLE_HTML = """
<div class="card-header"><h3>Prices - 19 May 2026</h3></div>
<table id="future-prices-table">
  <thead>
    <tr>
      <th>Delivery</th><th>Bid</th><th>Ask</th><th>Last</th><th>Time</th>
      <th>+/-</th><th>Day Vol.</th><th>Open</th><th>High</th><th>Low</th>
      <th>Settl.</th><th>O.I</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><a>Jun 2026</a></td><td>213.50</td><td>214.00</td><td>214.00</td>
      <td>17:35</td><td>3.50</td><td>746</td><td>211.00</td><td>214.25</td>
      <td>209.75</td><td>210.50</td><td>4,448</td>
    </tr>
    <tr>
      <td><a>Aug 2026</a></td><td>218.00</td><td>218.50</td><td>218.25</td>
      <td>17:35</td><td>3.25</td><td>231</td><td>216.00</td><td>219.25</td>
      <td>215.75</td><td>216.50</td><td>1,502</td>
    </tr>
  </tbody>
</table>
"""


def test_parse_prices_html_extracts_contract_rows() -> None:
    rows, session_date = parse_prices_html(SAMPLE_HTML)

    assert session_date == "2026-05-19"
    assert rows[0]["contract_code"] == "EMA_M2026"
    assert rows[0]["settlement"] == 210.50
    assert rows[0]["open_interest"] == 4448.0
    assert rows[1]["contract_code"] == "EMA_Q2026"


def test_probe_euronext_endpoint_validates_sample_html() -> None:
    report = probe_euronext_endpoint(SAMPLE_HTML)

    assert report["verdict"] == "VALIDATED"
    assert report["rows_found"] == 2
    assert "EMA_M2026" in report["contracts_found"]
    assert report["fields_missing"] == []


def test_write_validation_report(tmp_path) -> None:
    report = probe_euronext_endpoint(SAMPLE_HTML)
    out = write_validation_report(report, tmp_path / "report.txt")

    text = out.read_text(encoding="utf-8")
    assert "Verdict: VALIDATED" in text
    assert "Jun 2026 (EMA_M2026)" in text
