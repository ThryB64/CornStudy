from __future__ import annotations

import pandas as pd

from mais.collect import barchart_contract_download_probe as probe

FAKE_CONTRACT_HTML = """
<html>
  <head><title>Corn Historical Prices - Barchart.com</title></head>
  <body>
    <script>
      window.data = {"currentSymbol":{"symbol":"XBM26","symbolRoot":"XB",
      "exchange":"Euronext","symbolName":"Corn","contractName":"Corn (Jun '26)"}};
      window.more = {"quotes":{"historicalFutures":true},"limits":{"downloadLimit":20}};
    </script>
    <div class="historical-download">Download</div>
  </body>
</html>
"""

FAKE_TABLE_HTML = """
<html>
  <head><title>Corn Historical Prices - Barchart.com</title></head>
  <body>
    <script>
      window.data = {"currentSymbol":{"symbol":"XBM26","symbolRoot":"XB",
      "exchange":"Euronext","symbolName":"Corn","contractName":"Corn (Jun '26)"}};
    </script>
    <table id="historical">
      <tr><th>Date</th><th>Open</th><th>High</th><th>Low</th><th>Volume</th><th>Open Interest</th></tr>
      <tr><td>2026-01-02</td><td>200</td><td>201</td><td>199</td><td>10</td><td>20</td></tr>
    </table>
  </body>
</html>
"""


def test_probe_contract_symbol_metadata_download_signal() -> None:
    result = probe.probe_contract_symbol("XBM26", html=FAKE_CONTRACT_HTML)

    assert result["verdict"] == "page_exists_no_download"
    assert result["exchange_detected"] == "Euronext"
    assert result["symbol_root_detected"] == "XB"
    assert result["has_download_button"] is True
    assert result["historical_api_signal"] is True


def test_probe_contract_symbol_visible_rows() -> None:
    result = probe.probe_contract_symbol("XBM26", html=FAKE_TABLE_HTML)

    assert result["verdict"] == "downloadable_public"
    assert result["has_historical_table"] is True
    assert result["n_rows_visible"] == 1


def test_write_probe_outputs(tmp_path) -> None:
    results = [probe.probe_contract_symbol("XBM26", html=FAKE_CONTRACT_HTML)]

    csv_path, report_path = probe.write_probe_outputs(
        results,
        results_path=tmp_path / "barchart_contract_download_results.csv",
        report_path=tmp_path / "barchart_contract_download_report.txt",
    )

    saved = pd.read_csv(csv_path)
    assert set(probe.RESULT_COLUMNS).issubset(saved.columns)
    assert "Decision:" in report_path.read_text(encoding="utf-8")
