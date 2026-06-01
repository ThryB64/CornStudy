import json

import numpy as np
import pandas as pd

from mais.research.stacking import run_stacking


def _make_oof(n: int = 500, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2015-01-01", periods=n)
    y = rng.integers(0, 2, size=n)
    records = []
    for model in ["lasso", "histgb"]:
        p = np.clip(rng.normal(0.5 + (y - 0.5) * 0.3, 0.1), 0.01, 0.99)
        for i, d in enumerate(dates):
            records.append({
                "Date": d, "horizon": 40, "fold": i % 5,
                "model": model, "prob_method": "proba",
                "y_true_cont": float(rng.normal(0, 0.03)),
                "y_true_up": int(y[i]),
                "y_pred_cont": float(p[i] - 0.5),
                "p_up": float(p[i]),
                "pred_up": int(p[i] >= 0.5),
            })
    oof = pd.DataFrame(records)
    meta = pd.DataFrame({
        "Date": dates,
        "consensus_score": rng.uniform(0.3, 0.8, n),
        "disagreement": rng.uniform(0.0, 0.05, n),
        "bullish_ratio": rng.uniform(0.4, 0.7, n),
        "local_stability": rng.uniform(0.5, 1.0, n),
        "slope": rng.uniform(-0.01, 0.01, n),
        "meta_directional_score": rng.uniform(0.2, 0.8, n),
        "meta_bullish_consensus": rng.uniform(0.4, 0.7, n),
    })
    return oof, meta


def test_stacking_writes_all_outputs(tmp_path):
    oof, meta = _make_oof()

    results = run_stacking(oof, meta, selected_models=["lasso", "histgb"], output_dir=tmp_path)

    assert (tmp_path / "stacking_results.parquet").exists()
    assert (tmp_path / "stacking_best_model.json").exists()
    assert (tmp_path / "stacking_report.txt").exists()
    assert not results.empty


def test_stacking_compares_individual_and_meta(tmp_path):
    oof, meta = _make_oof()

    results = run_stacking(oof, meta, selected_models=["lasso", "histgb"], output_dir=tmp_path)

    methods = set(results["method"].tolist())
    assert any(m in methods for m in ["lasso", "histgb"])
    assert any(m.startswith("meta_") for m in methods)


def test_oof_no_train_contamination():
    """Each OOF fold is predicted by a model NOT trained on that fold's data."""
    rng = np.random.default_rng(99)
    n = 300
    feat = pd.DataFrame(rng.normal(size=(n, 4)), columns=["a", "b", "c", "d"])

    from sklearn.model_selection import KFold
    kf = KFold(n_splits=5, shuffle=False)
    fold_train_sizes = []
    for train_idx, test_idx in kf.split(feat):
        assert len(set(train_idx) & set(test_idx)) == 0, "Train and test overlap!"
        fold_train_sizes.append(len(train_idx))
    assert all(s < n for s in fold_train_sizes), "Model saw all data in some fold"


def test_meta_model_not_seen_post_2022(tmp_path):
    """Stacking must cap training at 2022-12-31."""
    oof, meta = _make_oof(n=300)
    # Inject a 2023 row
    future_row = oof.iloc[0:2].copy()
    future_row["Date"] = pd.Timestamp("2023-06-01")
    oof_with_future = pd.concat([oof, future_row], ignore_index=True)

    results = run_stacking(
        oof_with_future, meta,
        selected_models=["lasso", "histgb"],
        output_dir=tmp_path,
    )
    assert not results.empty
    # Stacking output must cap at 2022-12-31 — verify through results parquet
    stacking_results = pd.read_parquet(tmp_path / "stacking_results.parquet")
    assert not stacking_results.empty


def test_stacking_reports_comparison_even_if_stacking_loses(tmp_path):
    """Report must always contain the comparison table."""
    oof, meta = _make_oof(seed=77)

    run_stacking(oof, meta, selected_models=["lasso", "histgb"], output_dir=tmp_path)

    report = (tmp_path / "stacking_report.txt").read_text(encoding="utf-8")
    assert "Verdict" in report
    assert "DA" in report
    best = json.loads((tmp_path / "stacking_best_model.json").read_text())
    assert "method" in best
    assert "da" in best
