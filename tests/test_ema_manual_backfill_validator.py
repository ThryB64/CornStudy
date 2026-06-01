from __future__ import annotations

import pandas as pd

from mais.collect.ema_manual_backfill_validator import validate_manual_backfill_frame


def test_valid_manual_backfill_frame() -> None:
    raw = pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-12-31"],
            "delivery": ["Nov 2024", "Jun 2024"],
            "settlement": [210.5, 215.0],
            "source_symbol": ["XBX24", "XBM24"],
            "canonical_contract_code": ["EMA_X2024", "EMA_M2024"],
        }
    )

    report = validate_manual_backfill_frame(raw, from_year=2024, to_year=2024)

    assert report["quality_ok"] is True
    assert report["importable_rows"] == 2
    assert report["legacy_or_non_current_rows"] == 0
    assert report["missing_harvest_nov"] == []


def test_short_history_fails() -> None:
    raw = pd.DataFrame(
        {
            "date": ["2024-06-01"],
            "contract_code": ["EMA_X2024"],
            "settlement": [210.5],
        }
    )

    report = validate_manual_backfill_frame(raw, from_year=2024, to_year=2024)

    assert report["quality_ok"] is False
    assert any("history starts after" in error for error in report["errors"])
    assert any("history ends before" in error for error in report["errors"])


def test_legacy_unconfirmed_fails() -> None:
    raw = pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-12-31"],
            "contract_code": ["EMA_F2024", "EMA_X2024"],
            "settlement": [210.5, 211.0],
            "import_verdict": ["legacy_or_ambiguous", "usable"],
            "active_month_status": ["legacy_or_ambiguous", "current_official"],
        }
    )

    report = validate_manual_backfill_frame(raw, from_year=2024, to_year=2024)

    assert report["quality_ok"] is False
    assert report["legacy_or_non_current_rows"] == 1
    assert report["unconfirmed_legacy_rows"] == 1


def test_missing_price_fails() -> None:
    raw = pd.DataFrame(
        {
            "date": ["2024-01-02"],
            "contract_code": ["EMA_X2024"],
        }
    )

    report = validate_manual_backfill_frame(raw, from_year=2024, to_year=2024)

    assert report["quality_ok"] is False
    assert any("missing price column" in error for error in report["errors"])
