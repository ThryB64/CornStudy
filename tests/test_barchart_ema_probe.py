from __future__ import annotations

import pandas as pd

from mais.collect import barchart_ema_probe as probe

FAKE_USABLE_HTML = """
<html>
  <head><title>Corn Historical Prices - Barchart.com</title></head>
  <body>
    <script>
      window.data = {"currentSymbol":{"symbol":"XBQ10","symbolRoot":"XB",
      "exchange":"Euronext","symbolName":"Corn","contractName":"Corn (Aug '10)",
      "pointValue":"EUR 50"},"dynamicAssets":{}};
    </script>
    <div class="historical-download">Download</div>
    <table id="historical-prices">
      <tr><th>Date</th><th>Open</th><th>High</th><th>Low</th><th>Last</th>
      <th>Volume</th><th>Open Interest</th></tr>
      <tr><td>2010-01-04</td><td>130</td><td>131</td><td>129</td><td>130.5</td>
      <td>12</td><td>34</td></tr>
    </table>
  </body>
</html>
"""

FAKE_METADATA_ONLY_HTML = """
<html>
  <head><title>Corn Historical Prices - Barchart.com</title></head>
  <body>
    <script>
      window.data = {"currentSymbol":{"symbol":"XBH14","symbolRoot":"XB",
      "exchange":"Euronext","symbolName":"Corn","contractName":"Corn (Mar '14)",
      "pointValue":"EUR 50"},"dynamicAssets":{}};
    </script>
    <div>historical-download</div>
  </body>
</html>
"""


def test_probe_report_produced(tmp_path) -> None:
    results = [
        probe.probe_barchart_symbol("XBQ10", html=FAKE_USABLE_HTML),
        probe.probe_barchart_symbol("XBH14", html=FAKE_METADATA_ONLY_HTML),
    ]

    csv_path, report_path = probe.write_probe_outputs(
        results,
        results_path=tmp_path / "barchart_probe_results.csv",
        report_path=tmp_path / "barchart_probe_report.txt",
    )

    saved = pd.read_csv(csv_path)
    assert csv_path.exists()
    assert report_path.exists()
    assert set(probe.PROBE_COLUMNS).issubset(saved.columns)
    assert "Decision:" in report_path.read_text(encoding="utf-8")


def test_probe_throttle_respected() -> None:
    sleeps: list[float] = []

    def fetcher(symbol: str) -> tuple[int, str]:
        return 200, FAKE_USABLE_HTML.replace("XBQ10", symbol)

    results = probe.probe_symbols(
        ["XBH10", "XBM10", "XBQ10"],
        throttle_sec=2.0,
        fetcher=fetcher,
        sleeper=sleeps.append,
    )

    assert len(results) == 3
    assert sleeps == [2.0, 2.0]


def test_january_flag_separate() -> None:
    result = probe.probe_barchart_symbol(
        "XBF14",
        html=FAKE_USABLE_HTML.replace("XBQ10", "XBF14"),
    )

    assert result["canonical_contract_code"] is None
    assert result["active_month_status"] == "legacy_or_ambiguous"
    assert result["import_verdict"] == "legacy_or_ambiguous"
    assert result["verdict"] == "legacy_or_ambiguous"


def test_symbol_mapping() -> None:
    assert probe.build_barchart_symbol("Q", 2010) == "XBQ10"
    assert probe.canonical_contract_code("XBX14") == "EMA_X2014"
    assert probe.canonical_contract_code("XBF14") is None
