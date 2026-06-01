import json

import numpy as np
import pandas as pd

from mais.features import build_multi_horizon_targets
from mais.research.canonical_benchmark import (
    CropYearWalkForward,
    add_benjamini_hochberg,
    analyze_sweep_zoo_contradiction,
    bootstrap_ci,
    run_canonical_benchmark,
    run_model_oof,
    summarize_oof,
    weekly_oof,
)


def _canonical_fixture(n=3400):
    dates = pd.bdate_range("2010-01-04", periods=n)
    cycle = np.sin(np.arange(n) / 18.0)
    price = 400.0 + np.cumsum(0.15 * cycle + np.random.default_rng(123).normal(0, 1.2, n))
    prices = pd.DataFrame({"Date": dates, "corn_close": price})
    features = pd.DataFrame(
        {
            "Date": dates,
            "factor_cycle": pd.Series(cycle).shift(1).fillna(0).to_numpy(),
            "factor_momentum": pd.Series(price).diff().shift(1).fillna(0).to_numpy(),
            "macro_noise": np.random.default_rng(456).normal(0, 1, n),
        }
    )
    targets = build_multi_horizon_targets(prices, [5, 10, 40])
    return features, targets


def test_crop_year_walk_forward_uses_2015_2022_when_complete():
    dates = pd.bdate_range("2010-01-04", "2022-08-31")
    splits = CropYearWalkForward(min_train_years=5).split(pd.Series(dates))
    years = [fold_label for _, _, fold_label in splits]
    assert years == list(range(2015, 2023))


def test_canonical_features_identical():
    features, targets = _canonical_fixture()
    oof_ridge, n_features_ridge = run_model_oof(
        features,
        targets,
        horizon=5,
        model_name="ridge",
        split_name="crop_year_walk_forward",
    )
    oof_logistic, n_features_logistic = run_model_oof(
        features,
        targets,
        horizon=5,
        model_name="logistic",
        split_name="crop_year_walk_forward",
    )
    assert not oof_ridge.empty
    assert not oof_logistic.empty
    assert n_features_ridge == n_features_logistic == 3


def test_metric_confidence_intervals_present():
    features, targets = _canonical_fixture()
    oof, n_features = run_model_oof(
        features,
        targets,
        horizon=5,
        model_name="ridge",
        split_name="crop_year_walk_forward",
    )
    row = summarize_oof(
        oof,
        horizon=5,
        model_name="ridge",
        split_name="crop_year_walk_forward",
        n_features=n_features,
        n_bootstrap=50,
    )
    assert 0 <= row["da_ci95_low"] <= row["da_ci95_high"] <= 1
    assert "auc_ci95_low" in row
    assert row["verdict"] in {"CONFIRMÉ", "PROMETTEUR", "NEUTRE", "REJETÉ", "INCONCLU"}


def test_annual_da_documented():
    features, targets = _canonical_fixture()
    oof, n_features = run_model_oof(
        features,
        targets,
        horizon=5,
        model_name="ridge",
        split_name="crop_year_walk_forward",
    )
    row = summarize_oof(
        oof,
        horizon=5,
        model_name="ridge",
        split_name="crop_year_walk_forward",
        n_features=n_features,
        n_bootstrap=20,
    )
    assert set(range(2015, 2023)).issubset(set(row["annual_da"]))


def test_no_single_year_dominance():
    features, targets = _canonical_fixture()
    oof, n_features = run_model_oof(
        features,
        targets,
        horizon=5,
        model_name="ridge",
        split_name="crop_year_walk_forward",
    )
    full = summarize_oof(
        oof,
        horizon=5,
        model_name="ridge",
        split_name="crop_year_walk_forward",
        n_features=n_features,
        n_bootstrap=20,
    )["da"]
    oof = oof.copy()
    dates = pd.to_datetime(oof["Date"])
    oof["crop_year"] = np.where(dates.dt.month >= 9, dates.dt.year + 1, dates.dt.year)
    drops = []
    for year in [2016, 2020]:
        sub = oof[oof["crop_year"] != year].drop(columns=["crop_year"])
        row = summarize_oof(
            sub,
            horizon=5,
            model_name="ridge",
            split_name="crop_year_walk_forward",
            n_features=n_features,
            n_bootstrap=20,
        )
        drops.append(full - row["da"])
    assert max(drops) < 0.07


def test_weekly_da_computed():
    features, targets = _canonical_fixture()
    oof, n_features = run_model_oof(
        features,
        targets,
        horizon=5,
        model_name="ridge",
        split_name="crop_year_walk_forward",
    )
    row = summarize_oof(
        oof,
        horizon=5,
        model_name="ridge",
        split_name="crop_year_walk_forward",
        n_features=n_features,
        n_bootstrap=20,
    )
    assert not weekly_oof(oof).empty
    assert 0 <= row["da_weekly"] <= 1


def test_canonical_results_saved(tmp_path):
    features, targets = _canonical_fixture()
    run_canonical_benchmark(
        features,
        targets,
        tmp_path,
        horizons=[5],
        models=["ridge", "logistic"],
        n_bootstrap=20,
        report_path=tmp_path / "BENCHMARK_CANONICAL.md",
        protocol_path=tmp_path / "PROTOCOL_FREEZE.md",
    )
    payload = json.loads((tmp_path / "benchmark_results.json").read_text(encoding="utf-8"))
    assert len(payload["results"]) == 4
    assert (tmp_path / "contradiction_analysis.json").exists()
    assert all("da_ci95_low" in row and "auc_ci95_low" in row for row in payload["results"])


def test_contradiction_decomposed(tmp_path):
    features, targets = _canonical_fixture()
    payload = analyze_sweep_zoo_contradiction(features, targets, output_dir=tmp_path, horizon=40)
    assert "identified_primary_cause" in payload
    assert "delta_explained_abs" in payload
    assert payload["sweep_features_count"] <= payload["zoo_features_count"]


def test_benjamini_hochberg_monotone():
    df = pd.DataFrame({"da_p_value": [0.01, 0.03, 0.02, 0.5]})
    out = add_benjamini_hochberg(df, p_col="da_p_value", out_col="da_q_value")
    assert out["da_q_value"].between(0, 1).all()


def test_bootstrap_ci_bounds():
    ci = bootstrap_ci(
        np.array([0, 1, 1, 0]),
        np.array([0, 1, 0, 0]),
        metric="da",
        n_bootstrap=20,
    )
    assert 0 <= ci[0] <= ci[1] <= 1
