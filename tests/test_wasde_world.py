"""Tests DATA-WORLD-01 — WASDE EU + Ukraine."""

from __future__ import annotations

import json
import pytest
import pandas as pd
from mais.collect.wasde_world import build_wasde_world_features, build_audit, save_wasde_world


def test_build_returns_dataframe():
    df = build_wasde_world_features()
    assert isinstance(df, pd.DataFrame)


def test_date_column_present():
    df = build_wasde_world_features()
    if not df.empty:
        assert "Date" in df.columns


def test_eu_features_present():
    df = build_wasde_world_features()
    if not df.empty:
        assert "wasde_eu_production_mt_lag1" in df.columns
        assert "wasde_eu_ending_stocks_mt_lag1" in df.columns


def test_ukraine_features_present():
    df = build_wasde_world_features()
    if not df.empty:
        assert "wasde_ukraine_production_mt_lag1" in df.columns


def test_eu_has_data():
    df = build_wasde_world_features()
    if df.empty:
        pytest.skip("No data")
    n = df["wasde_eu_production_mt_lag1"].notna().sum()
    assert n > 500, f"EU rows: {n}"


def test_antileakage_first_row_nan():
    df = build_wasde_world_features()
    if df.empty:
        pytest.skip("No data")
    assert pd.isna(df["wasde_eu_production_mt_lag1"].iloc[0])


def test_audit_structure():
    df = build_wasde_world_features()
    audit = build_audit(df)
    assert "source" in audit
    assert "features" in audit


def test_save_creates_json(tmp_path):
    out = save_wasde_world(tmp_path / "test_wasde_world.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "source" in data
    assert "note" in data
