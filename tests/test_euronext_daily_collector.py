from __future__ import annotations

import json
from datetime import date

import pandas as pd
import pytest

import mais.collect.euronext_contracts_daily as daily

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
      <td>Jun 2026</td><td>213.50</td><td>214.00</td><td>214.00</td>
      <td>17:35</td><td>3.50</td><td>746</td><td>211.00</td><td>214.25</td>
      <td>209.75</td><td>210.50</td><td>4,448</td>
    </tr>
    <tr>
      <td>Aug 2026</td><td>218.00</td><td>218.50</td><td>218.25</td>
      <td>17:35</td><td>3.25</td><td>0</td><td>216.00</td><td>219.25</td>
      <td>215.75</td><td>216.50</td><td>100</td>
    </tr>
  </tbody>
</table>
"""


def test_parse_contract_label_current_official_months() -> None:
    with pytest.raises(ValueError):
        daily.parse_contract_label("Jan 2027")
    assert daily.parse_contract_label("Mar 2027") == "EMA_H2027"
    assert daily.parse_contract_label("Jun 2026") == "EMA_M2026"
    assert daily.parse_contract_label("Aug 2026") == "EMA_Q2026"
    assert daily.parse_contract_label("Nov 2026") == "EMA_X2026"


def test_download_active_contracts_from_validated_endpoint_html() -> None:
    contracts = daily.download_active_contracts(html=SAMPLE_HTML)

    assert len(contracts) == 2
    assert contracts[0]["contract_code"] == "EMA_M2026"
    assert contracts[0]["canonical_contract_code"] == "EMA_M2026"
    assert contracts[0]["source_symbol"] == "EMA_M2026"
    assert contracts[0]["month_code"] == "M"
    assert contracts[0]["active_month_status"] == "current_official"
    assert contracts[0]["import_verdict"] == "usable"
    assert contracts[0]["settlement"] == 210.5
    assert contracts[0]["quality_flag"] == "ok"
    assert contracts[1]["quality_flag"] == "low_liquidity"


def test_normalise_contract_daily_frame_recovers_official_metadata() -> None:
    raw = pd.DataFrame(
        [
            {
                "date": "2026-05-19",
                "contract_code": "EMA_M2026",
                "source": "euronext_ajax_prices",
                "settlement": 210.5,
                "last": 214.0,
                "expiry_date": "2026-06-01",
                "open_interest": 4448,
                "volume": 746,
            }
        ]
    )
    reference = pd.DataFrame(
        [
            {
                "canonical_contract_code": "EMA_M2026",
                "last_trade_date": "2026-06-05",
            }
        ]
    )

    fixed = daily.normalise_contract_daily_frame(raw, reference_frame=reference)

    assert fixed.loc[0, "month_code"] == "M"
    assert fixed.loc[0, "canonical_contract_code"] == "EMA_M2026"
    assert fixed.loc[0, "import_verdict"] == "usable"
    assert fixed.loc[0, "close_or_last"] == 210.5
    assert fixed.loc[0, "expiry_date"] == "2026-06-05"
    assert not bool(fixed.loc[0, "expiry_estimated"])
    assert fixed.loc[0, "days_to_expiry"] == 17


def test_normalise_contract_daily_frame_marks_estimated_expiry_without_reference() -> None:
    raw = pd.DataFrame(
        [
            {
                "date": "2026-05-19",
                "contract_code": "EMA_Q2026",
                "source": "euronext_ajax_prices",
                "settlement": 216.5,
                "expiry_date": "2026-08-01",
            }
        ]
    )

    fixed = daily.normalise_contract_daily_frame(raw, reference_frame=pd.DataFrame())

    assert fixed.loc[0, "month_code"] == "Q"
    assert fixed.loc[0, "canonical_contract_code"] == "EMA_Q2026"
    assert fixed.loc[0, "close_or_last"] == 216.5
    assert bool(fixed.loc[0, "expiry_estimated"])


def test_snapshot_creates_json_and_keeps_real_over_proxy(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(daily, "EMA_CONTRACTS_RAW_DIR", tmp_path)
    snapshot_date = date(2026, 5, 19)
    real_contract = daily.download_active_contracts(html=SAMPLE_HTML)[0]
    proxy_contract = {**real_contract, "settlement": 1.0, "source": "proxy_cbot", "is_proxy": True}

    daily.save_daily_snapshot(snapshot_date, [real_contract])
    path = daily.save_daily_snapshot(snapshot_date, [proxy_contract])

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["date"] == "2026-05-19"
    assert payload["contracts"][0]["source"] == "euronext_ajax_prices"
    assert payload["contracts"][0]["settlement"] == 210.5


def test_daily_parquet_incremental_append_and_priority(tmp_path, monkeypatch) -> None:
    parquet_path = tmp_path / "ema_contract_daily.parquet"
    monkeypatch.setattr(daily, "EMA_CONTRACT_DAILY", parquet_path)
    snapshot_date = date(2026, 5, 19)
    real_contract = daily.download_active_contracts(html=SAMPLE_HTML)[0]
    proxy_contract = {**real_contract, "settlement": 1.0, "source": "proxy_cbot", "is_proxy": True}

    assert daily.update_contract_daily_parquet(snapshot_date, [proxy_contract]) == 1
    assert daily.update_contract_daily_parquet(snapshot_date, [real_contract]) == 1

    saved = pd.read_parquet(parquet_path)
    assert len(saved) == 1
    assert saved.loc[0, "settlement"] == 210.5
    assert not bool(saved.loc[0, "is_proxy"])


def test_canonicalise_contract_daily_parquet_in_place(tmp_path) -> None:
    parquet_path = tmp_path / "ema_contract_daily.parquet"
    pd.DataFrame(
        [
            {
                "date": "2026-05-19",
                "contract_code": "EMA_M2026",
                "source": "euronext_ajax_prices",
                "settlement": 210.5,
            }
        ]
    ).to_parquet(parquet_path, index=False)

    rows = daily.canonicalise_contract_daily_parquet(parquet_path)

    saved = pd.read_parquet(parquet_path)
    assert rows == 1
    assert saved.loc[0, "month_code"] == "M"
    assert saved.loc[0, "canonical_contract_code"] == "EMA_M2026"
    assert saved.loc[0, "close_or_last"] == 210.5


def test_quality_flag_set_correctly() -> None:
    assert daily.quality_flag({"is_proxy": True}) == "proxy_cbot"
    assert daily.quality_flag({"settlement": None, "is_proxy": False}) == "settlement_missing"
    assert daily.quality_flag({"settlement": 210.0, "open_interest": None}) == "oi_missing"
    assert daily.quality_flag({"settlement": 210.0, "open_interest": 100, "volume": 10}) == "low_liquidity"
    assert daily.quality_flag({"settlement": 210.0, "open_interest": 1000, "volume": 10}) == "ok"
