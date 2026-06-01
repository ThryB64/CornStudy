from __future__ import annotations

import pandas as pd

from mais.collect.world_collector import (
    brazil_safrinha_pressure_flag,
    build_world_signal_features,
    normalise_argentina,
    normalise_asia_tenders,
    normalise_brazil_fob,
    normalise_conab_brazil,
    normalise_ukraine_exports,
)


def test_normalise_conab_brazil_columns():
    raw = pd.DataFrame(
        {
            "Date": ["2024-06-01"],
            "production_mt": [120.5],
            "safrinha_production_mt": [91.2],
            "export_forecast_mt": [38.0],
            "harvest_progress_pct": [72.0],
        }
    )

    result = normalise_conab_brazil(raw)

    assert "brazil_conab_production_mt" in result.columns
    assert "brazil_safrinha_progress_pct" in result.columns


def test_brazil_safrinha_pressure_flag():
    dates = pd.Series(pd.to_datetime(["2024-06-15", "2024-07-15", "2024-12-15"]))
    progress = pd.Series([70.0, 90.0, 40.0])

    flags = brazil_safrinha_pressure_flag(dates, progress)

    assert flags.tolist() == [1, -1, 0]


def test_normalise_brazil_fob_builds_spread():
    raw = pd.DataFrame(
        {
            "Date": ["2024-01-01"],
            "fob_paranagua_usd_t": [210.0],
            "us_fob_gulf_usd_t": [225.0],
        }
    )

    result = normalise_brazil_fob(raw)

    assert result["brazil_us_fob_spread"].iloc[0] == -15.0


def test_argentina_ukraine_importer_normalisers():
    argentina = normalise_argentina(pd.DataFrame({"Date": ["2024-04-01"], "production_mt": [51.0]}))
    ukraine = normalise_ukraine_exports(pd.DataFrame({"Date": ["2024-04-01"], "exports_mt": [2.4], "corridor_status": [0]}))
    tenders = normalise_asia_tenders(
        pd.DataFrame({"Date": ["2024-04-01"], "japan_tenders_mt": [0.5], "korea_tenders_mt": [0.2]})
    )

    assert "argentina_bolsa_production_mt" in argentina.columns
    assert "ukraine_export_pace_mt" in ukraine.columns
    assert "asia_importer_tenders_mt" in tenders.columns


def test_build_world_signal_features():
    conab = normalise_conab_brazil(
        pd.DataFrame({"Date": ["2024-07-01"], "harvest_progress_pct": [60.0]})
    )
    ukraine = normalise_ukraine_exports(
        pd.DataFrame({"Date": ["2024-07-01"], "corridor_status": [0]})
    )

    result = build_world_signal_features([conab, ukraine])

    assert result["brazil_safrinha_pressure_flag"].iloc[0] == 1
    assert result["uncertain_ukraine_risk"].iloc[0] == 1
