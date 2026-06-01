"""Tests DATA-EU-04 — ETS CO₂ et TTF enrichi."""

from __future__ import annotations

import json
import pytest
import pandas as pd
from mais.collect.eu_carbon import build_eu_carbon_features, build_audit, save_eu_carbon


def test_build_returns_dataframe():
    df = build_eu_carbon_features()
    assert isinstance(df, pd.DataFrame)


def test_date_column_present():
    df = build_eu_carbon_features()
    assert "Date" in df.columns


def test_ttf_column_present():
    df = build_eu_carbon_features()
    assert "ttf_eur_mwh" in df.columns


def test_ttf_has_data():
    df = build_eu_carbon_features()
    n = df["ttf_eur_mwh"].notna().sum()
    assert n > 1000, f"TTF rows: {n}"


def test_zscore_columns_exist():
    df = build_eu_carbon_features()
    for col in ["ttf_zscore_52w", "ttf_return_1d"]:
        assert col in df.columns, f"Missing: {col}"


def test_antileakage_zscore_starts_null():
    """z-score doit être NaN pendant les min_periods premières lignes (shift(1) + expanding)."""
    df = build_eu_carbon_features()
    ttf_z = df["ttf_zscore_52w"]
    # Le z-score doit avoir des NaN au début
    assert ttf_z.iloc[:52].isna().any(), "z-score should have NaN during warmup"


def test_audit_structure():
    df = build_eu_carbon_features()
    audit = build_audit(df)
    assert "ttf_eur_mwh" in audit
    assert audit["ttf_eur_mwh"]["available"] is True
    assert audit["ttf_eur_mwh"]["n"] > 0


def test_save_creates_json(tmp_path):
    out = save_eu_carbon(tmp_path / "test_audit.json")
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
    assert "ttf_eur_mwh" in data
    assert "note" in data
