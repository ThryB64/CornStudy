from __future__ import annotations

import sys
import types

import pandas as pd

from mais.collect import ema_continuous_series_probe as probe

FAKE_BARCHART_HTML = """
<html>
  <head><title>Corn Continuous Historical Prices - Barchart.com</title></head>
  <body>
    <script>
      window.data = {"currentSymbol":{"symbol":"XB*0","symbolRoot":"XB",
      "exchange":"Euronext","symbolName":"Corn","contractName":"Corn Continuous"}};
    </script>
    <div class="historical-download">Download</div>
  </body>
</html>
"""


def test_probe_yfinance_symbol_usable(monkeypatch) -> None:
    dates = pd.date_range("2010-01-01", periods=2600, freq="B")
    fake_yf = types.SimpleNamespace(
        download=lambda *args, **kwargs: pd.DataFrame({"Date": dates, "Close": range(len(dates))})
    )
    monkeypatch.setitem(sys.modules, "yfinance", fake_yf)

    result = probe.probe_yfinance_symbol("EMA=F", min_rows=2500)

    assert result["verdict"] == "usable_continuous"
    assert result["rows"] == 2600
    assert result["start_date"] == "2010-01-01"


def test_probe_yfinance_symbol_short(monkeypatch) -> None:
    dates = pd.date_range("2024-01-01", periods=10, freq="B")
    fake_yf = types.SimpleNamespace(
        download=lambda *args, **kwargs: pd.DataFrame({"Date": dates, "Close": range(len(dates))})
    )
    monkeypatch.setitem(sys.modules, "yfinance", fake_yf)

    result = probe.probe_yfinance_symbol("EMA=F", min_rows=2500)

    assert result["verdict"] == "empty_or_short"
    assert "rows<2500" in result["notes"]


def test_probe_barchart_metadata_only() -> None:
    result = probe.probe_barchart_continuous_symbol("XB*0", html=FAKE_BARCHART_HTML)

    assert result["verdict"] == "page_exists_no_download"
    assert result["exchange_detected"] == "Euronext"
    assert result["symbol_root_detected"] == "XB"
    assert result["has_download_button"] is True


def test_write_probe_outputs(tmp_path) -> None:
    results = [
        probe.probe_barchart_continuous_symbol("XB*0", html=FAKE_BARCHART_HTML),
        {
            "provider": "yfinance",
            "symbol": "EMA=F",
            "verdict": "empty_or_short",
            "rows": 0,
        },
    ]

    csv_path, report_path = probe.write_probe_outputs(
        results,
        results_path=tmp_path / "ema_continuous_probe_results.csv",
        report_path=tmp_path / "ema_continuous_probe_report.txt",
    )

    saved = pd.read_csv(csv_path)
    assert set(probe.PROBE_COLUMNS).issubset(saved.columns)
    assert "Decision:" in report_path.read_text(encoding="utf-8")
