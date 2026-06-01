from __future__ import annotations

import pandas as pd

from mais.collect.eu_fundamentals_collector import (
    build_eu_fundamental_features,
    normalise_agreste_france,
    normalise_ec_mars,
    normalise_franceagrimer,
)


def test_normalise_ec_mars_columns():
    result = normalise_ec_mars(
        pd.DataFrame(
            {
                "Date": ["2024-06-15"],
                "yield_estimate_tha": [7.4],
                "production_estimate_mt": [62.0],
            }
        )
    )

    assert "eu_yield_estimate_tha" in result.columns
    assert "eu_production_estimate_mt" in result.columns


def test_normalise_agreste_and_franceagrimer():
    agreste = normalise_agreste_france(
        pd.DataFrame({"Date": ["2024-07-01"], "good_excellent_pct": [72.0], "corn_harvested_pct": [5.0]})
    )
    fam = normalise_franceagrimer(
        pd.DataFrame({"Date": ["2024-07-01"], "ending_stocks_mt": [2.1], "export_pace_mt": [0.4]})
    )

    assert "france_ge_pct" in agreste.columns
    assert "france_ending_stocks_mt" in fam.columns


def test_build_eu_fundamental_features_lagged():
    mars = normalise_ec_mars(
        pd.DataFrame(
            {
                "Date": ["2024-06-15", "2024-07-15"],
                "production_estimate_mt": [62.0, 60.5],
            }
        )
    )
    agreste = normalise_agreste_france(
        pd.DataFrame(
            {
                "Date": ["2024-06-15", "2024-07-15"],
                "ge_pct": [75.0, 70.0],
            }
        )
    )

    result = build_eu_fundamental_features([mars, agreste])

    assert "eu_production_estimate_mt_lag1" in result.columns
    assert "eu_production_revision_mt" in result.columns
    assert "france_ge_momentum_1w" in result.columns
    assert pd.isna(result["eu_production_estimate_mt_lag1"].iloc[0])
    assert result["eu_production_estimate_mt_lag1"].iloc[1] == 62.0
