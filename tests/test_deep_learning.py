import numpy as np
import pandas as pd

from mais.research.deep_learning import (
    SEEDS,
    _build_mlp,
    run_deep_learning,
    run_mlp_stability,
)


def _make_features(n: int = 300, seed: int = 42) -> tuple[pd.DataFrame, pd.Series]:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2012-01-02", periods=n)
    df = pd.DataFrame({"Date": dates})
    for i in range(10):
        df[f"feat_{i}"] = rng.normal(0, 1, n)
    y = pd.Series((rng.normal(0, 1, n) > 0).astype(int), name="y_up")
    return df, y


def test_mlp_returns_valid_metrics(tmp_path):
    df, y = _make_features()
    feat_cols = [c for c in df.columns if c != "Date"]
    feats = df[feat_cols]
    model = _build_mlp((32, 16), seed=42)
    from mais.research.deep_learning import _oof_eval
    metrics = _oof_eval(feats, y, model, n_splits=3)
    assert 0.0 <= metrics["da"] <= 1.0
    assert 0.0 <= metrics["auc"] <= 1.0 or np.isnan(metrics["auc"])


def test_mlp_stability_3_seeds(tmp_path):
    df, y = _make_features()
    feat_cols = [c for c in df.columns if c != "Date"]
    feats = df[feat_cols]
    res = run_mlp_stability(feats, y, n_splits=3, seeds=SEEDS)
    assert "da_mean" in res
    assert "da_std" in res
    assert len(res["seeds_results"]) == 3
    assert 0.0 <= res["da_mean"] <= 1.0


def test_run_deep_learning_produces_artefacts(tmp_path):
    df, y = _make_features()
    results = run_deep_learning(df, y, n_splits=3, output_dir=tmp_path)
    assert not results.empty
    assert (tmp_path / "dl_comparison_report.parquet").exists()
    assert (tmp_path / "dl_comparison_report.txt").exists()
    assert (tmp_path / "dl_best_model.json").exists()


def test_mlp_beats_baseline_documented(tmp_path):
    """Verdict must compare MLP to ridge baseline and be documented in JSON."""
    import json
    df, y = _make_features()
    run_deep_learning(df, y, n_splits=3, output_dir=tmp_path)
    best = json.loads((tmp_path / "dl_best_model.json").read_text())
    assert "verdict" in best
    assert "mlp_da_mean" in best
    assert "ridge_da" in best


def test_stability_criterion():
    """Stability flag: std ≤ 0.015."""
    df, y = _make_features(n=200, seed=5)
    feat_cols = [c for c in df.columns if c != "Date"]
    res = run_mlp_stability(df[feat_cols], y, n_splits=3, seeds=[42, 123])
    assert isinstance(res["stable"], bool)
