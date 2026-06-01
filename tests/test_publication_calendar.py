"""Tests V7-DATA-CAL — Calendrier de publication des données."""

import pytest

from mais.data.publication_calendar import (
    all_sources,
    get_frequency,
    get_lag,
    get_notes,
    minimum_shift,
)


def test_all_lags_positive():
    for source in all_sources():
        assert get_lag(source) >= 1, f"{source}: lag must be >= 1"


def test_minimum_shift_at_least_one():
    for source in all_sources():
        assert minimum_shift(source) >= 1


def test_known_sources():
    assert get_lag("wasde") >= 1
    assert get_lag("ec_mars") >= 14
    assert get_lag("eurostat_comext") >= 30
    assert get_lag("cot") == 3
    assert get_lag("eia_weekly") == 4


def test_conservative_vs_min():
    assert get_lag("ec_mars", conservative=True) >= get_lag("ec_mars", conservative=False)
    assert get_lag("wasde", conservative=True) >= get_lag("wasde", conservative=False)


def test_unknown_source_raises():
    with pytest.raises(KeyError):
        get_lag("unknown_source_xyz")


def test_frequency_returned():
    freq = get_frequency("wasde")
    assert isinstance(freq, str) and len(freq) > 0


def test_notes_returned():
    notes = get_notes("cot")
    assert isinstance(notes, str) and len(notes) > 0


def test_all_sources_nonempty():
    assert len(all_sources()) >= 10
