from __future__ import annotations

import pandas as pd

from mais.collect import ema_contract_reference as ref


def test_map_official_barchart_symbol() -> None:
    row = ref.map_provider_symbol("XBM14", expiry_date="2014-06-05", current_year=2026)

    assert row["source"] == "barchart"
    assert row["source_symbol"] == "XBM14"
    assert row["canonical_contract_code"] == "EMA_M2014"
    assert row["month_code"] == "M"
    assert row["delivery_month"] == 6
    assert row["delivery_year"] == 2014
    assert row["expiry_date"] == "2014-06-05"
    assert row["last_trade_date"] == "2014-06-05"
    assert row["active_month_status"] == "historical_confirmed"
    assert row["import_verdict"] == "usable"


def test_map_current_official_barchart_symbol() -> None:
    row = ref.map_provider_symbol("XBX26", expiry_date="2026-11-05", current_year=2026)

    assert row["canonical_contract_code"] == "EMA_X2026"
    assert row["active_month_status"] == "current_official"
    assert row["import_verdict"] == "usable"


def test_january_is_legacy_and_not_importable() -> None:
    row = ref.map_provider_symbol("XBF14", expiry_date="2014-01-06", current_year=2026)

    assert row["canonical_contract_code"] is None
    assert row["month_code"] == "F"
    assert row["delivery_month"] == 1
    assert row["active_month_status"] == "legacy_or_ambiguous"
    assert row["import_verdict"] == "legacy_or_ambiguous"


def test_build_reference_default_universe() -> None:
    frame = ref.build_contract_reference(2014, 2015, current_year=2026)

    assert list(frame.columns) == ref.CONTRACT_REFERENCE_COLUMNS
    assert len(frame) == 10
    assert set(frame["source_symbol"]) == {
        "XBF14",
        "XBH14",
        "XBM14",
        "XBQ14",
        "XBX14",
        "XBF15",
        "XBH15",
        "XBM15",
        "XBQ15",
        "XBX15",
    }
    assert not frame.loc[frame["month_code"].eq("F"), "canonical_contract_code"].notna().any()
    assert not frame.loc[frame["month_code"].eq("F"), "import_verdict"].eq("usable").any()


def test_build_reference_from_barchart_rows() -> None:
    rows = [
        {
            "raw": {
                "symbol": "XBM14",
                "contractExpirationDate": "2014-06-05",
                "contractNameHistorical": "Corn June 2014 Futures",
            }
        },
        {
            "symbol": "XBF14",
            "contractExpirationDate": "2014-01-06",
            "contractNameHistorical": "Corn January 2014 Futures",
        },
    ]

    frame = ref.build_reference_from_barchart_rows(rows, current_year=2026)

    assert len(frame) == 2
    assert frame.loc[frame["source_symbol"].eq("XBM14"), "canonical_contract_code"].item() == "EMA_M2014"
    assert frame.loc[frame["source_symbol"].eq("XBF14"), "import_verdict"].item() == (
        "legacy_or_ambiguous"
    )


def test_validate_rejects_importable_legacy() -> None:
    frame = pd.DataFrame(
        [
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
                "import_verdict": "usable",
            }
        ]
    )

    try:
        ref.validate_contract_reference(frame)
    except ValueError as exc:
        assert "canonical contract code" in str(exc)
    else:
        raise AssertionError("Expected validation to reject importable legacy month")


def test_write_contract_reference_roundtrip(tmp_path) -> None:
    frame = ref.build_contract_reference(2014, 2014, current_year=2026)
    output = ref.write_contract_reference(frame, output_path=tmp_path / "ema_contract_reference.parquet")

    loaded = pd.read_parquet(output)
    assert len(loaded) == 5
    assert list(loaded.columns) == ref.CONTRACT_REFERENCE_COLUMNS

