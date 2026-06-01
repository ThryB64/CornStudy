from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

import mais.collect.euronext_backfill as backfill


def test_normalise_manual_backfill_schema() -> None:
    raw = pd.DataFrame(
        {
            "date": ["2024-01-02"],
            "delivery": ["Nov 2024"],
            "settlement": [210.5],
            "volume": [100],
            "open_interest": [1200],
        }
    )

    result = backfill.normalise_manual_backfill(raw)

    assert result.loc[0, "contract_code"] == "EMA_X2024"
    assert result.loc[0, "canonical_contract_code"] == "EMA_X2024"
    assert result.loc[0, "source_symbol"] == "Nov 2024"
    assert result.loc[0, "month_code"] == "X"
    assert result.loc[0, "active_month_status"] == "current_official"
    assert result.loc[0, "import_verdict"] == "usable"
    assert result.loc[0, "contract_month"] == 11
    assert result.loc[0, "source"] == "manual_backfill"
    assert result.loc[0, "quality_flag"] == "ok"


def test_normalise_chart_history() -> None:
    payload = [{"time": "2026-05-18 01:00", "price": 210.5, "volume": 2221}]
    contract = {
        "contract_code": "EMA_M2026",
        "contract_month": 6,
        "contract_year": 2026,
        "expiry_date": "2026-06-01",
        "delivery": "Jun 2026",
    }

    result = backfill.normalise_chart_history(
        payload,
        contract,
        from_date=date(2026, 1, 1),
        to_date=date(2026, 12, 31),
    )

    assert result.loc[0, "contract_code"] == "EMA_M2026"
    assert result.loc[0, "settlement"] == 210.5
    assert result.loc[0, "source"] == "euronext_chart_history"
    assert result.loc[0, "quality_flag"] == "oi_missing"


def test_normalise_barchart_history_close_or_last() -> None:
    payload = {
        "data": [
            {
                "raw": {
                    "tradeTime": "2014-06-05",
                    "openPrice": 167.5,
                    "highPrice": 168.0,
                    "lowPrice": 165.75,
                    "lastPrice": 168.0,
                    "volume": 540,
                    "openInterest": 0,
                }
            }
        ]
    }
    contract = {
        "source_symbol": "XBM14",
        "canonical_contract_code": "EMA_M2014",
        "month_code": "M",
        "delivery_month": 6,
        "delivery_year": 2014,
        "expiry_date": "2014-06-05",
        "active_month_status": "historical_confirmed",
        "import_verdict": "usable",
    }

    result = backfill.normalise_barchart_history(
        payload,
        contract,
        from_date=date(2014, 1, 1),
        to_date=date(2014, 12, 31),
    )

    assert result.loc[0, "contract_code"] == "EMA_M2014"
    assert result.loc[0, "source_symbol"] == "XBM14"
    assert result.loc[0, "close"] == 168.0
    assert result.loc[0, "last"] == 168.0
    assert result.loc[0, "close_or_last"] == 168.0
    assert pd.isna(result.loc[0, "settlement"])
    assert result.loc[0, "source"] == "barchart_proxy_exploratory"
    assert result.loc[0, "quality_flag"] == "settlement_missing"


def test_collect_barchart_history_uses_only_usable_contracts(monkeypatch) -> None:
    reference = pd.DataFrame(
        [
            {
                "source": "barchart",
                "source_symbol": "XBM14",
                "canonical_contract_code": "EMA_M2014",
                "month_code": "M",
                "delivery_month": 6,
                "delivery_year": 2014,
                "expiry_date": "2014-06-05",
                "last_trade_date": "2014-06-05",
                "active_month_status": "historical_confirmed",
                "import_verdict": "usable",
            },
            {
                "source": "barchart",
                "source_symbol": "XBF14",
                "canonical_contract_code": None,
                "month_code": "F",
                "delivery_month": 1,
                "delivery_year": 2014,
                "expiry_date": "2014-01-06",
                "last_trade_date": "2014-01-06",
                "active_month_status": "legacy_or_ambiguous",
                "import_verdict": "legacy_or_ambiguous",
            },
        ]
    )
    requested: list[str] = []

    def fake_fetch(
        symbol: str,
        *,
        session: object,
        max_retries: int,
        sleeper: object,
    ) -> tuple[dict[str, object], int, int, str]:
        requested.append(symbol)
        return (
            {
                "data": [
                    {
                        "raw": {
                            "tradeTime": "2014-06-05",
                            "openPrice": 167.5,
                            "highPrice": 168.0,
                            "lowPrice": 165.75,
                            "lastPrice": 168.0,
                            "volume": 540,
                            "openInterest": 0,
                        }
                    }
                ]
            },
            200,
            0,
            "",
        )

    monkeypatch.setattr(backfill, "fetch_barchart_history_payload_with_retries", fake_fetch)

    result = backfill.collect_barchart_history(
        date(2014, 1, 1),
        date(2014, 12, 31),
        reference_frame=reference,
        session=(object(), {}),
    )

    assert requested == ["XBM14"]
    assert result["contract_code"].tolist() == ["EMA_M2014"]


def test_summarise_barchart_history_payload_contract_fields() -> None:
    payload = {
        "data": [
            {
                "raw": {
                    "tradeTime": "2014-06-05",
                    "openPrice": "167.50",
                    "highPrice": "168.00",
                    "lowPrice": "165.75",
                    "lastPrice": "168.00",
                    "volume": "540",
                    "openInterest": "0",
                }
            }
        ]
    }
    contract = {
        "source_symbol": "XBM14",
        "canonical_contract_code": "EMA_M2014",
        "month_code": "M",
        "delivery_year": 2014,
        "delivery_month": 6,
        "active_month_status": "historical_confirmed",
        "import_verdict": "usable",
        "universes": "strict_official|exploratory_with_F",
    }

    summary, dates = backfill.summarise_barchart_history_payload(
        payload,
        contract,
        from_date=date(2014, 1, 1),
        to_date=date(2014, 12, 31),
        http_status=200,
        retry_count=2,
    )

    assert summary["verdict"] == "usable"
    assert summary["n_rows"] == 1
    assert summary["first_close_or_last"] == 168.0
    assert summary["volume_non_null"] == 1
    assert summary["open_interest_non_null"] == 1
    assert summary["retry_count"] == 2
    assert dates == {date(2014, 6, 5)}


def test_decide_barchart_coverage_verdict_go() -> None:
    rows = []
    for year in range(2014, 2022):
        rows.append(
            {
                "universe": "strict_official",
                "period_type": "crop_year",
                "year": year,
                "period_complete": True,
                "coverage_pct": 92.0,
            }
        )
        rows.append(
            {
                "universe": "exploratory_with_F",
                "period_type": "crop_year",
                "year": year,
                "period_complete": True,
                "coverage_pct": 95.0,
            }
        )

    assert backfill.decide_barchart_coverage_verdict(pd.DataFrame(rows)) == "GO"


def test_decide_barchart_coverage_verdict_exploratory() -> None:
    rows = []
    for year in range(2014, 2022):
        rows.append(
            {
                "universe": "strict_official",
                "period_type": "crop_year",
                "year": year,
                "period_complete": True,
                "coverage_pct": 80.0,
            }
        )
        rows.append(
            {
                "universe": "exploratory_with_F",
                "period_type": "crop_year",
                "year": year,
                "period_complete": True,
                "coverage_pct": 95.0,
            }
        )

    assert backfill.decide_barchart_coverage_verdict(pd.DataFrame(rows)) == "GO_EXPLORATORY"


def test_build_coverage_report_harvest_nov() -> None:
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
            "contract_code": ["EMA_X2024", "EMA_M2024"],
            "is_proxy": [False, False],
        }
    )

    report = backfill.build_coverage_report(
        df,
        date(2024, 1, 1),
        date(2024, 1, 5),
        source="manual_backfill",
    )

    assert report["covered_days"] == 2
    assert report["harvest_nov_coverage"]["2024"] is True
    assert report["proxy_pct"] == 0.0
    assert report["coverage_status"] == "PARTIAL_REQUIRES_MANUAL_BACKFILL"
    assert report["meets_2014_requirement"] is False
    assert report["observed_date_range"] == ["2024-01-02", "2024-01-03"]


def test_backfill_from_manual_writes_parquet_and_report(tmp_path, monkeypatch) -> None:
    manual = tmp_path / "ema_historical_contracts.csv"
    manual.write_text(
        "date,delivery,settlement,volume,open_interest\n"
        "2024-01-02,Nov 2024,210.5,100,1200\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(backfill, "EMA_CONTRACT_DAILY", tmp_path / "ema_contract_daily.parquet")
    monkeypatch.setattr(backfill, "BACKFILL_COVERAGE_REPORT", tmp_path / "coverage.json")

    rows = backfill.backfill_from_manual(manual)

    saved = pd.read_parquet(tmp_path / "ema_contract_daily.parquet")
    assert rows == 1
    assert saved.loc[0, "contract_code"] == "EMA_X2024"
    assert (tmp_path / "coverage.json").exists()


def test_load_manual_backfill_if_exists(tmp_path, monkeypatch) -> None:
    backfill_dir = tmp_path / "manual_backfill"
    backfill_dir.mkdir()
    (backfill_dir / backfill.MANUAL_BACKFILL_FILENAME).write_text(
        "date,delivery,settlement\n2024-01-02,Jun 2024,210.5\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(backfill, "EMA_BACKFILL_DIR", backfill_dir)

    result = backfill.load_manual_backfill_if_exists()

    assert result is not None
    assert result.loc[0, "contract_code"] == "EMA_M2024"


def test_manual_backfill_rejects_legacy_without_reference() -> None:
    raw = pd.DataFrame(
        {
            "date": ["2024-01-02"],
            "contract_code": ["EMA_F2024"],
            "settlement": [210.5],
            "volume": [100],
            "open_interest": [1200],
            "import_verdict": ["legacy_or_ambiguous"],
            "active_month_status": ["legacy_or_ambiguous"],
        }
    )

    with pytest.raises(ValueError, match="Legacy EMA contracts"):
        backfill.normalise_manual_backfill(raw)
