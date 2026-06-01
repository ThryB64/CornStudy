import numpy as np
import pandas as pd

from mais.collect.drought_monitor_collector import build_drought_features
from mais.research.new_sources import NEW_SOURCE_GROUPS, run_ablation


def _make_drought_weekly(n: int = 100) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.date_range("2010-01-05", periods=n, freq="W-TUE")
    return pd.DataFrame({
        "Date": dates,
        "corn_area_d0": rng.uniform(0, 20, n),
        "corn_area_d1": rng.uniform(0, 15, n),
        "corn_area_d2": rng.uniform(0, 10, n),
        "corn_area_d3": rng.uniform(0, 8, n),
        "corn_area_d4": rng.uniform(0, 5, n),
    })


def _make_features_df(n: int = 600) -> pd.DataFrame:
    rng = np.random.default_rng(99)
    dates = pd.bdate_range("2010-01-04", periods=n)
    df = pd.DataFrame({"Date": dates})
    for col in ["corn_ret_1d", "corn_vol_20d", "cot_mm_net", "fedfunds"]:
        df[col] = rng.normal(0, 1, n)
    for col in NEW_SOURCE_GROUPS["drought_extended"]:
        df[col] = rng.uniform(0, 30, n)
    for col in NEW_SOURCE_GROUPS["cot_changes"]:
        df[col] = rng.normal(0, 500, n)
    for col in NEW_SOURCE_GROUPS["spreads"]:
        df[col] = rng.normal(0, 0.2, n)
    df["y_up_h40"] = (rng.normal(0, 1, n) > 0).astype(float)
    return df


def test_build_drought_features_columns():
    df = _make_drought_weekly()
    result = build_drought_features(df)
    assert "drought_d2plus" in result.columns
    assert "drought_change_4w" in result.columns
    assert "drought_extreme_flag" in result.columns
    assert result["drought_d2plus"].notna().any()


def test_build_drought_features_extreme_flag():
    raw = pd.DataFrame({
        "Date": [pd.Timestamp("2012-07-01")],
        "corn_area_d2": [5.0],
        "corn_area_d3": [8.0],
        "corn_area_d4": [5.0],
    })
    result = build_drought_features(raw)
    assert result["drought_extreme_flag"].iloc[0] == 1.0


def test_ablation_returns_dataframe(tmp_path):
    df = _make_features_df()
    results = run_ablation(df, output_dir=tmp_path)
    assert not results.empty
    assert "source" in results.columns
    assert "delta_auc" in results.columns


def test_ablation_produces_artefacts(tmp_path):
    df = _make_features_df()
    run_ablation(df, output_dir=tmp_path)
    assert (tmp_path / "new_sources_ablation.parquet").exists()
    assert (tmp_path / "new_sources_report.txt").exists()
    assert (tmp_path / "futures_m2m3_diagnostic.txt").exists()


def test_cot_changes_anti_leakage():
    """cot_mm_long_chg must be computed with shift(1) — value at t uses t-1 diff."""
    from mais.features import _add_cot_changes
    df = pd.DataFrame({
        "Date": pd.bdate_range("2015-01-01", periods=20),
        "cot_mm_long": list(range(100, 120)),
        "cot_mm_short": list(range(50, 70)),
        "cot_pm_long": list(range(200, 220)),
        "cot_pm_short": list(range(150, 170)),
    })
    _add_cot_changes(df)
    assert "cot_mm_long_chg" in df.columns
    assert pd.isna(df["cot_mm_long_chg"].iloc[0])
    assert pd.isna(df["cot_mm_long_chg"].iloc[1])
    assert not pd.isna(df["cot_mm_long_chg"].iloc[2])
    assert df["cot_mm_long_chg"].iloc[2] == 1.0
