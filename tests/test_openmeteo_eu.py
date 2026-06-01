"""Tests DATA-EU-02 — Open-Meteo EU zones."""

from __future__ import annotations

import json
import pytest
import pandas as pd
import numpy as np
from mais.collect.openmeteo_eu import (
    build_openmeteo_eu_features,
    build_audit,
    CORN_ZONES_EU,
)


def test_6_zones_defined():
    assert len(CORN_ZONES_EU) == 6


def test_weights_sum_to_1():
    total = sum(z["weight"] for z in CORN_ZONES_EU.values())
    assert abs(total - 1.0) < 0.01, f"Weights sum to {total}"


def test_build_returns_dataframe():
    df = build_openmeteo_eu_features()
    assert isinstance(df, pd.DataFrame)


def test_date_column_present():
    df = build_openmeteo_eu_features()
    if not df.empty:
        assert "Date" in df.columns


def test_expected_features_present():
    df = build_openmeteo_eu_features()
    if not df.empty:
        for col in ["eu_gdd_cumul", "eu_heat_stress_days_4w", "eu_precip_deficit_30d"]:
            assert col in df.columns, f"Missing: {col}"


def test_data_starts_from_2010():
    df = build_openmeteo_eu_features()
    if not df.empty and "Date" in df.columns:
        assert df["Date"].min().year >= 2010


def test_audit_structure():
    df = build_openmeteo_eu_features()
    audit = build_audit(df)
    assert "n_zones" in audit
    assert "features" in audit
    if not df.empty:
        assert audit["n_zones"] >= 0


def test_antileakage_first_row_nan():
    """La première ligne des features doit être NaN (shift(1))."""
    df = build_openmeteo_eu_features()
    if df.empty:
        pytest.skip("No data collected (network unavailable)")
    assert pd.isna(df["eu_gdd_cumul"].iloc[0]), "First row should be NaN after shift(1)"
