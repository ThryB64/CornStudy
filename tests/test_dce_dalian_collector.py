from __future__ import annotations

import pandas as pd

from mais.collect.dce_dalian_collector import build_china_import_incentive, normalise_dce_corn


def test_normalise_dce_corn_manual_columns():
    raw = pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-03"],
            "Close": [2450.0, 2460.0],
            "Volume": [1000, 1100],
        }
    )

    result = normalise_dce_corn(raw)

    assert "dce_corn_close_cny_t" in result.columns
    assert "dce_corn_volume" in result.columns
    assert result["dce_corn_close_cny_t"].tolist() == [2450.0, 2460.0]


def test_china_import_incentive_positive_when_dce_above_parity():
    dce = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
            "dce_corn_close_cny_t": [2450.0, 1800.0],
        }
    )

    result = build_china_import_incentive(
        dce,
        cbot_usd_t=pd.Series([220.0, 220.0]),
        usd_cny=pd.Series([7.0, 7.0]),
        pacific_freight_usd_t=45.0,
        port_handling_usd_t=12.0,
    )

    assert result["china_import_incentive"].iloc[0] > 0
    assert result["china_import_incentive_flag"].iloc[0] == 1
    assert result["china_import_incentive"].iloc[1] < 0
    assert result["china_import_incentive_flag"].iloc[1] == 0
