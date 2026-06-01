from __future__ import annotations

from datetime import date, datetime

import pandas as pd

from mais.leakage.availability import (
    apply_availability_shift,
    filter_available_as_of,
    first_available_datetime,
    is_available,
)


def test_wasde_not_available_same_day_before_publication() -> None:
    publish = datetime(2026, 5, 12, 12, 0)

    assert not is_available("usda_wasde", publish, datetime(2026, 5, 12, 10, 0))
    assert is_available("usda_wasde", publish, datetime(2026, 5, 12, 18, 1))


def test_cot_available_monday_after_friday() -> None:
    publish = date(2026, 5, 15)

    assert not is_available("cftc_cot", publish, date(2026, 5, 17))
    assert is_available("cftc_cot", publish, date(2026, 5, 18))


def test_euronext_available_next_morning() -> None:
    publish = date(2026, 5, 19)

    assert not is_available("euronext_settlement", publish, date(2026, 5, 19))
    assert is_available("euronext_settlement", publish, date(2026, 5, 20))


def test_shift_applied_correctly_to_dataframe() -> None:
    df = pd.DataFrame({"Date": ["2026-05-19", "2026-05-20"], "ema_front_price": [210.5, 211.0]})

    shifted = apply_availability_shift(df, "euronext_settlement")

    assert shifted["Date"].dt.strftime("%Y-%m-%d").tolist() == ["2026-05-20", "2026-05-21"]
    assert shifted["ema_front_price"].tolist() == [210.5, 211.0]


def test_ec_mars_month_and_day_lag() -> None:
    available = first_available_datetime("ec_mars_bulletin", date(2026, 5, 15))

    assert available.date() == date(2026, 7, 15)


def test_filter_available_as_of() -> None:
    df = pd.DataFrame({"Date": ["2026-05-15", "2026-05-22"], "cot_mm_net": [1.0, 2.0]})

    filtered = filter_available_as_of(df, "cftc_cot", date(2026, 5, 20))

    assert filtered["cot_mm_net"].tolist() == [1.0]
