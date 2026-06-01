"""Tests DATA-EU-03 — FranceAgriMer / Agreste."""

from __future__ import annotations

import json
import pytest
import pandas as pd
from mais.collect.franceagrimer import build_franceagrimer_features, build_audit, save_franceagrimer


def test_build_returns_dataframe():
    df = build_franceagrimer_features()
    assert isinstance(df, pd.DataFrame)


def test_date_column_present():
    df = build_franceagrimer_features()
    if not df.empty:
        assert "Date" in df.columns


def test_fr_production_present():
    df = build_franceagrimer_features()
    if not df.empty:
        assert "fr_mais_production_kt_lag1" in df.columns


def test_fr_has_data():
    df = build_franceagrimer_features()
    if df.empty:
        pytest.skip("No data")
    n = df["fr_mais_production_kt_lag1"].notna().sum()
    assert n > 3000, f"France rows: {n}"


def test_data_starts_from_2000():
    df = build_franceagrimer_features()
    if df.empty:
        pytest.skip("No data")
    valid = df.dropna(subset=["fr_mais_production_kt_lag1"])
    assert valid["Date"].min().year >= 2000


def test_antileakage_first_row_nan():
    df = build_franceagrimer_features()
    if df.empty:
        pytest.skip("No data")
    assert pd.isna(df["fr_mais_production_kt_lag1"].iloc[0])


def test_audit_structure():
    df = build_franceagrimer_features()
    audit = build_audit(df)
    assert "source" in audit
    assert "features" in audit


def test_save_creates_json(tmp_path):
    out = save_franceagrimer(tmp_path / "test_franceagrimer.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "source" in data
    assert "note" in data
