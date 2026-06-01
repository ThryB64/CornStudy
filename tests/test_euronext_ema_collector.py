from __future__ import annotations

import pandas as pd
import pytest

from mais.collect.euronext_ema_collector import (
    normalise_ema_history,
    parse_contract_label,
    parse_provider_contract_label,
    validate_ema_history,
)


def test_contract_month_code_mapping():
    assert parse_contract_label("Jun 2026") == "EMA_M2026"
    assert parse_contract_label("Aug 2026") == "EMA_Q2026"
    assert parse_contract_label("Nov 2026") == "EMA_X2026"
    assert parse_contract_label("Mar 2027") == "EMA_H2027"
    with pytest.raises(ValueError):
        parse_contract_label("Jan 2027")


def test_provider_contract_month_code_mapping_can_investigate_legacy():
    assert parse_provider_contract_label("Jan 2027", allow_legacy=True) == "EMA_F2027"
    with pytest.raises(ValueError):
        parse_provider_contract_label("Jan 2027")


def test_normalise_manual_euronext_export():
    raw = pd.DataFrame(
        {
            "Date": ["2024-01-02", "2024-01-03"],
            "Open": [205.0, 206.0],
            "High": [207.0, 208.0],
            "Low": [204.0, 205.0],
            "Settlement": [206.5, 207.5],
            "Volume": [100, 120],
        }
    )

    result = normalise_ema_history(raw)

    assert list(result.columns) == ["Date", "ema_open", "ema_high", "ema_low", "ema_close", "ema_volume"]
    assert result["ema_close"].tolist() == [206.5, 207.5]


def test_validate_ema_history_quality_flags_short_history():
    raw = pd.DataFrame(
        {
            "Date": pd.bdate_range("2024-01-01", periods=20),
            "Close": range(20),
        }
    )

    quality = validate_ema_history(raw, min_rows=3500)

    assert quality["n_rows"] == 20
    assert quality["quality_ok"] is False
