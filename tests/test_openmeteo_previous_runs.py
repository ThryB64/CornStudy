"""V140-DATA — collecteur Open-Meteo Previous Runs (parsing + revision tape, offline)."""
from __future__ import annotations

import pandas as pd

from mais.collect import openmeteo_previous_runs as pr


def _mock_daily():
    # 2 dates de validité, lead 0..2 pour tmax ; previous_dayN = prévision plus ancienne
    return {
        "time": ["2026-06-08", "2026-06-09"],
        "temperature_2m_max": [30.0, 31.0],                 # lead 0 (run du jour)
        "temperature_2m_max_previous_day1": [29.0, 30.0],   # lead 1
        "temperature_2m_max_previous_day2": [27.0, 28.0],   # lead 2
        "precipitation_sum": [0.0, 5.0],
        "precipitation_sum_previous_day1": [1.0, 4.0],
        "precipitation_sum_previous_day2": [2.0, 3.0],
    }


def test_parse_long_format_anti_leakage():
    rows = pr.parse_previous_runs(_mock_daily(), zone="iowa")
    df = pd.DataFrame(rows)
    assert set(df["variable"]) == {"tmax", "precip"}
    # issue_date = valid_date - lead_day
    r = df[(df["variable"] == "tmax") & (df["valid_date"] == "2026-06-09") & (df["lead_day"] == 2)].iloc[0]
    assert r["issue_date"] == "2026-06-07"
    assert r["value"] == 28.0


def test_revision_tape_signs():
    df = pd.DataFrame(pr.parse_previous_runs(_mock_daily(), zone="iowa"))
    tape = pr.revision_tape(df)
    # tmax valid 2026-06-08 : lead2=27 -> lead1=29 -> lead0=30 : révisions à la hausse
    sub = tape[(tape["variable"] == "tmax") & (tape["valid_date"] == "2026-06-08")]
    revs = dict(zip(sub["from_lead"], sub["revision"], strict=False))
    assert revs[2] == 2.0   # lead1 - lead2 = 29 - 27
    assert revs[1] == 1.0   # lead0 - lead1 = 30 - 29
    # issue_date de la révision from_lead=1 (-> to_lead 0) = valid (connue le jour J)
    row = sub[sub["from_lead"] == 1].iloc[0]
    assert row["issue_date"] == "2026-06-08"


def test_empty_returns_waiting():
    out = pr.fetch_previous_runs(zones={}, write=False)
    assert out["verdict"] == "WAITING_DATA"
