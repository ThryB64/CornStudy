"""Tests V7-02 — Purged CV avec embargo."""

import numpy as np
import pandas as pd
import pytest

from mais.walkforward.purged_cv import (
    ALL_PROTOCOLS,
    block_bootstrap,
    classic,
    embargo_2h,
    embargo_h,
    get_protocol,
    leave_one_crop_year,
    leave_one_crisis,
    leave_one_year,
    non_overlap,
    purged_kfold,
)


def _make_dates(n: int = 600) -> pd.DatetimeIndex:
    return pd.date_range("2012-01-01", periods=n, freq="B")


def test_classic_produces_splits():
    dates = _make_dates()
    splits = list(classic(len(dates), n_splits=3))
    assert len(splits) == 3
    for train, test in splits:
        assert len(train) > 0
        assert len(test) > 0


def test_embargo_h_removes_contaminated():
    dates = _make_dates()
    embargo = 90
    splits = list(embargo_h(dates, embargo_days=embargo, n_splits=3))
    for train, test in splits:
        train_end = dates[train[-1]]
        for ti in test:
            assert dates[ti] > train_end + pd.Timedelta(days=embargo)


def test_embargo_2h_larger_than_embargo_h():
    dates = _make_dates(500)
    H = 60
    splits_h = list(embargo_h(dates, H, n_splits=3))
    splits_2h = list(embargo_2h(dates, H, n_splits=3))
    # 2H embargo → moins d'observations en test (ou autant)
    total_test_h = sum(len(t) for _, t in splits_h)
    total_test_2h = sum(len(t) for _, t in splits_2h)
    assert total_test_2h <= total_test_h


def test_non_overlap_stride():
    dates = _make_dates(300)
    splits = list(non_overlap(dates, horizon_days=20, n_splits=3))
    assert len(splits) >= 1


def test_leave_one_year_isolation():
    dates = _make_dates(800)
    for train, test in leave_one_year(dates):
        test_years = set(dates[test].year)
        train_years = set(dates[train].year)
        assert len(test_years) == 1
        assert test_years.isdisjoint(train_years)


def test_leave_one_crop_year_isolation():
    dates = _make_dates(800)
    splits = list(leave_one_crop_year(dates))
    assert len(splits) >= 2
    for train, test in splits:
        assert len(train) >= 50


def test_leave_one_crisis_known_periods():
    dates = _make_dates(3500)  # ~2012-2025
    splits = list(leave_one_crisis(dates))
    assert len(splits) >= 1


def test_purged_kfold_no_embargo_violation():
    dates = _make_dates(500)
    embargo = 90
    for train, test in purged_kfold(dates, embargo_days=embargo, n_splits=4):
        test_dates = dates[test]
        train_dates = dates[train]
        for td in test_dates:
            # Pas de date train dans la fenêtre embargo autour du test
            near_test = (train_dates >= td - pd.Timedelta(days=embargo)) & \
                        (train_dates <= td + pd.Timedelta(days=embargo))
            assert not near_test.any(), f"Violation embargo: date test {td}"


def test_get_protocol_all_names():
    dates = pd.date_range("2010-01-01", periods=3500, freq="B")  # ~2010-2023, couvre crises 2012/2020/2022
    for proto_name in ALL_PROTOCOLS:
        splits = list(get_protocol(proto_name, dates, horizon_days=40, n_splits=3))
        assert len(splits) >= 1, f"{proto_name} produit 0 splits"


def test_get_protocol_unknown_raises():
    dates = _make_dates()
    with pytest.raises(ValueError, match="inconnu"):
        list(get_protocol("nonexistent_protocol", dates))


def test_no_train_test_overlap_classic():
    dates = _make_dates()
    for train, test in classic(len(dates), n_splits=3):
        assert len(set(train) & set(test)) == 0
