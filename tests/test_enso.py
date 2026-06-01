import numpy as np
import pandas as pd
import pytest

from mais.collect.enso import (
    CollectorError,
    DataQualityError,
    build_enso_features,
    parse_oni_table,
    validate_oni_coverage,
)


def _oni_monthly(start="2010-01-01", periods=180):
    dates = pd.date_range(start, periods=periods, freq="MS")
    values = np.sin(np.arange(periods) / 8.0)
    return pd.DataFrame({"Date": dates, "enso_oni_index": values})


def test_enso_collection_coverage():
    df = _oni_monthly("2010-01-01", 156)
    validate_oni_coverage(df)


def test_enso_parser_raises_on_format_change():
    bad = pd.DataFrame({"foo": [1], "bar": [2]})
    with pytest.raises(CollectorError):
        parse_oni_table([bad])


def test_enso_regime_distribution():
    monthly = _oni_monthly()
    daily = pd.bdate_range("2010-01-04", "2012-12-31")
    features = build_enso_features(monthly, daily)
    regimes = features["enso_regime"].dropna()
    assert set(regimes.unique()).issubset({-1.0, 0.0, 1.0})
    assert regimes.notna().all()


def test_enso_flag_coherent():
    monthly = pd.DataFrame(
        {
            "Date": pd.date_range("2010-01-01", periods=12, freq="MS"),
            "enso_oni_index": [0.6] * 6 + [-0.7] * 6,
        }
    )
    features = build_enso_features(monthly, pd.date_range("2010-01-01", "2010-12-31", freq="B"))
    both = (features["enso_el_nino_flag"] == 1.0) & (features["enso_la_nina_flag"] == 1.0)
    assert not both.any()


def test_enso_empty_series_raises():
    monthly = pd.DataFrame({"Date": pd.date_range("2010-01-01", periods=12, freq="MS"), "enso_oni_index": np.nan})
    with pytest.raises(DataQualityError):
        build_enso_features(monthly, pd.date_range("2010-01-01", periods=20, freq="B"))
