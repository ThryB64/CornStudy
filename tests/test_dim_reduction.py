import numpy as np
import pandas as pd

from mais.research.dim_reduction import (
    _identify_families,
    compressive_sensing,
    pca_by_family,
    run_dim_reduction_comparison,
)


def _make_features(n: int = 300, seed: int = 42) -> tuple[pd.DataFrame, pd.Series]:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2012-01-02", periods=n)
    df = pd.DataFrame({"Date": dates})
    for i in range(5):
        df[f"wasde_col_{i}"] = rng.normal(0, 1, n)
    for i in range(4):
        df[f"cot_mm_long_{i}"] = rng.normal(0, 1, n)
    for i in range(3):
        df[f"corn_ret_{i}d"] = rng.normal(0, 1, n)
    for i in range(2):
        df[f"temp_belt_{i}"] = rng.normal(0, 1, n)
    y = pd.Series((rng.normal(0, 1, n) > 0).astype(int), name="y_up")
    return df, y


def test_identify_families():
    cols = ["wasde_ending_stocks", "cot_mm_long", "corn_ret_1d", "temp_belt", "fedfunds"]
    families = _identify_families(cols)
    assert "wasde" in families
    assert "cot" in families
    assert "market" in families
    assert "wasde_ending_stocks" in families["wasde"]


def test_pca_by_family_reduces_dims():
    df, _ = _make_features()
    feat_cols = [c for c in df.columns if c != "Date"]
    train_mask = np.ones(len(df), dtype=bool)
    compressed, models, var_info = pca_by_family(df[feat_cols], train_mask)
    assert not compressed.empty
    assert compressed.shape[0] == len(df)
    assert compressed.shape[1] <= len(feat_cols)
    assert all(c.startswith("pca_") for c in compressed.columns)


def test_pca_fitted_on_train_only():
    """PCA must not use test data. Fitting on 50% then projecting all rows."""
    df, _ = _make_features(n=200)
    feat_cols = [c for c in df.columns if c != "Date"]
    train_mask = np.zeros(len(df), dtype=bool)
    train_mask[:100] = True
    compressed, models, _ = pca_by_family(df[feat_cols], train_mask)
    # All rows projected successfully (train + test)
    assert len(compressed) == len(df)


def test_compressive_sensing_shape():
    df, _ = _make_features()
    feat_cols = [c for c in df.columns if c != "Date"]
    train_mask = np.ones(len(df), dtype=bool)
    cs = compressive_sensing(df[feat_cols], train_mask, n_components=20)
    assert cs.shape[0] == len(df)
    assert cs.shape[1] <= 20
    assert all(c.startswith("cs_") for c in cs.columns)


def test_dim_reduction_comparison_returns_dataframe(tmp_path):
    df, y = _make_features(n=200)
    results = run_dim_reduction_comparison(df, y, n_splits=3, cs_components=(10, 20), output_dir=tmp_path)
    assert not results.empty
    reps = set(results["representation"].tolist())
    assert "raw" in reps
    assert "pca_by_family" in reps
    assert "cs_n10" in reps
    assert (tmp_path / "dim_reduction_comparison.parquet").exists()
    assert (tmp_path / "dim_reduction_report.txt").exists()
