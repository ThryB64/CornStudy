"""V161 — parité d'import COMEXT : décodeur JSON-stat + lag de publication (offline)."""
from __future__ import annotations

import pandas as pd

from mais.collect.comext_unit_value import decode_jsonstat
from mais.research.v161_import_parity import build_parity_series


def _jsonstat():
    # 2 partenaires × 2 indicateurs × 2 mois ; ordre des dims : partner, indicators, time
    return {
        "id": ["partner", "indicators", "time"],
        "size": [2, 2, 2],
        "dimension": {
            "partner": {"category": {"index": {"UA": 0, "BR": 1}}},
            "indicators": {"category": {"index": {"VALUE_IN_EUROS": 0, "QUANTITY_IN_100KG": 1}}},
            "time": {"category": {"index": {"2025-01": 0, "2025-02": 1}}},
        },
        # lin = partner*4 + indicator*2 + time
        "value": {"0": 2.0e8, "1": 2.1e8, "2": 1.0e7, "3": 1.05e7,
                  "4": 5.0e7, "5": 6.0e7, "6": 2.5e6, "7": 3.0e6},
    }


def test_decode_jsonstat_linear_index():
    df = decode_jsonstat(_jsonstat())
    assert len(df) == 8
    ua_val_jan = df[(df["partner"] == "UA") & (df["indicator"] == "VALUE_IN_EUROS")
                    & (df["month"] == "2025-01")]["value"].iloc[0]
    assert ua_val_jan == 2.0e8
    br_qty_feb = df[(df["partner"] == "BR") & (df["indicator"] == "QUANTITY_IN_100KG")
                    & (df["month"] == "2025-02")]["value"].iloc[0]
    assert br_qty_feb == 3.0e6


def test_parity_series_respects_publication_lag():
    daily = pd.DataFrame({
        "Date": pd.date_range("2025-01-01", "2025-05-30", freq="B"),
    })
    daily["cbot_eur_t"] = 150.0
    daily["ema_cbot_basis"] = 60.0
    daily["ema_cbot_basis_zscore_52w"] = 1.0
    comext = pd.DataFrame({
        "month": ["2025-01"], "partner": ["EXT_EU27_2020"],
        "value_eur": [2.0e8], "qty_t": [1.0e6], "unit_value_eur_t": [200.0],
    })
    panel = build_parity_series(daily, comext)
    known = panel[panel["parity_premium"].notna()]
    # mois de janvier disponible seulement à partir de fin janvier + 60 j (~1er avril)
    assert known["Date"].min() >= pd.Timestamp("2025-03-30")
    # parité = 200 - 150 = 50 ; résidu = 60 - 50 = 10
    assert abs(known["parity_premium"].iloc[0] - 50.0) < 1e-9
    assert abs(known["parity_residual"].iloc[0] - 10.0) < 1e-9
