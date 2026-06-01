"""Tests DATA-EU-01 — EC MARS collecteur Eurostat."""

from __future__ import annotations

import json
import pytest
import pandas as pd
from mais.collect.ec_mars import build_ec_mars_features, build_audit, save_ec_mars


def test_build_returns_dataframe():
    df = build_ec_mars_features()
    assert isinstance(df, pd.DataFrame)


def test_date_column_present():
    df = build_ec_mars_features()
    if not df.empty:
        assert "Date" in df.columns


def test_lag1_features_present():
    df = build_ec_mars_features()
    if not df.empty:
        assert "ec_mars_production_eu_kt_lag1" in df.columns


def test_production_has_data():
    df = build_ec_mars_features()
    if df.empty:
        pytest.skip("No data (network unavailable)")
    n = df["ec_mars_production_eu_kt_lag1"].notna().sum()
    assert n > 1000, f"Too few valid rows: {n}"


def test_antileakage_first_row_nan():
    df = build_ec_mars_features()
    if df.empty:
        pytest.skip("No data")
    assert pd.isna(df["ec_mars_production_eu_kt_lag1"].iloc[0])


def test_data_starts_from_2010():
    df = build_ec_mars_features()
    if df.empty:
        pytest.skip("No data")
    valid = df.dropna(subset=["ec_mars_production_eu_kt_lag1"])
    if len(valid):
        assert valid["Date"].min().year >= 2010


def test_audit_structure():
    df = build_ec_mars_features()
    audit = build_audit(df)
    assert "source" in audit
    assert "features" in audit


def test_save_creates_json(tmp_path):
    out = save_ec_mars(tmp_path / "test_ec_mars.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "source" in data
    assert "note" in data
