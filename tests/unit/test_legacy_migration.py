"""Verify the legacy migration fixes the two known bugs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from mais.clean.legacy_migration import (
    _MACRO_FRED_HEADERS,
    _read_macro_fred_with_correct_header,
    migrate_legacy,
)
from mais.utils import dedupe_columns


def test_macro_fred_header_fix(tmp_path):
    """Reproducing the bug: a CSV without header should read with the
    correct names from _MACRO_FRED_HEADERS, not with '5.98', '175.1' etc.
    """
    headerless = tmp_path / "macro_fred_completed.csv"
    headerless.write_text(
        "2001-01-01,5.98,175.1,0.63,3.73,1.51,-0.42,-0.53,6.30,-0.66,2.25\n"
        "2001-01-02,5.98,175.1,0.63,3.73,1.51,-0.42,-0.53,6.30,-0.66,2.25\n"
        "2001-01-03,5.50,176.0,0.50,4.00,2.00,-0.10,-0.20,5.00,-0.30,3.00\n",
        encoding="utf-8",
    )
    df = _read_macro_fred_with_correct_header(headerless)
    assert list(df.columns) == list(_MACRO_FRED_HEADERS)
    # No "5.98" or "175.1" as columns
    assert all(not str(c).replace(".", "").lstrip("-").isdigit() for c in df.columns)
    assert pd.api.types.is_datetime64_any_dtype(df["Date"])
    assert df["fedfunds"].iloc[0] == pytest.approx(5.98)
    assert df["cpiaucns"].iloc[0] == pytest.approx(175.1)


def test_dedupe_drops_dot_one_columns():
    df = pd.DataFrame({
        "Date": pd.bdate_range("2020-01-01", periods=5),
        "corn_close": [100.0] * 5,
        "corn_close.1": [99.0] * 5,            # should be dropped
        "corn_ret_1d.1": [0.01] * 5,           # should be dropped
        "5.98": [1.0] * 5,                     # should be dropped (numeric header)
        "175.1": [1.0] * 5,                    # should be dropped (numeric header)
    })
    cleaned = dedupe_columns(df)
    assert "corn_close" in cleaned.columns
    assert "corn_close.1" not in cleaned.columns
    assert "corn_ret_1d.1" not in cleaned.columns
    assert "5.98" not in cleaned.columns
    assert "175.1" not in cleaned.columns


@pytest.mark.integration
def test_migration_runs_against_real_legacy_data(tmp_path, project_root):
    legacy_dir = Path(project_root) / "csv" / "corrige"
    if not legacy_dir.is_dir():
        pytest.skip("No legacy csv/corrige/ directory.")
    written = migrate_legacy(legacy_dir=legacy_dir, interim_dir=tmp_path)
    assert written, "Migration produced no files."
    if "combined" in written:
        df = pd.read_parquet(written["combined"])
        # The famous bug
        assert "5.98" not in df.columns
        assert "175.1" not in df.columns
        assert not any(str(c).endswith(".1") for c in df.columns)
        # The fix should bring the proper macro_fred columns
        for c in ["fedfunds", "cpiaucns", "cpi_yoy_pct"]:
            # may be prefixed in combined; accept either
            assert c in df.columns or any(str(col).endswith(c) for col in df.columns)
