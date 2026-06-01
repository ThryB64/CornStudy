import numpy as np
import pandas as pd

from mais.research.model_zoo import (
    compute_error_correlation,
    model_specs,
    run_model_zoo,
    select_diverse_models,
)


def test_model_specs_cover_required_models():
    specs = model_specs()

    required = {
        "ridge",
        "lasso",
        "elasticnet",
        "bayesian_ridge",
        "logistic",
        "rf",
        "extratrees",
        "histgb",
        "linear_svm",
        "mlp",
    }
    assert required.issubset(specs)
    assert len(specs) >= 10


def test_compute_error_correlation_shape():
    corr = compute_error_correlation(
        {
            "a": np.array([0, 1, 0, 1]),
            "b": np.array([0, 1, 1, 1]),
            "c": np.array([1, 0, 1, 0]),
        }
    )

    assert corr.shape == (3, 3)
    assert list(corr.index) == ["a", "b", "c"]


def test_select_diverse_models_filters_high_correlation():
    results = pd.DataFrame(
        {
            "model": ["a", "b", "c"],
            "da": [0.64, 0.63, 0.61],
            "auc": [0.66, 0.65, 0.62],
            "da_std": [0.01, 0.01, 0.02],
        }
    )
    corr = pd.DataFrame(
        [[1.0, 0.9, 0.2], [0.9, 1.0, 0.1], [0.2, 0.1, 1.0]],
        index=["a", "b", "c"],
        columns=["a", "b", "c"],
    )

    selected = select_diverse_models(results, corr, top_n=3, min_auc=0.55)

    assert selected == ["a", "c"]


def test_run_model_zoo_writes_oof_and_ensembles(synthetic_features, synthetic_prices, tmp_path):
    specs = {name: model_specs()[name] for name in ["ridge", "logistic", "rf"]}
    targets = pd.DataFrame({"Date": synthetic_prices["Date"]})
    ret = np.log(synthetic_prices["corn_close"].shift(-5) / synthetic_prices["corn_close"])
    targets["y_cont_h5"] = ret
    targets["y_up_h5"] = (ret > 0).astype(float)
    targets.loc[ret.isna(), "y_up_h5"] = np.nan

    results = run_model_zoo(
        synthetic_features,
        targets,
        horizons=[5],
        specs=specs,
        output_dir=tmp_path,
    )

    assert {"vote_majority", "avg_proba"}.issubset(set(results["model"]))
    assert (tmp_path / "model_zoo_results.parquet").exists()
    assert (tmp_path / "model_zoo_oof_predictions.parquet").exists()
    assert (tmp_path / "model_zoo_error_correlation.parquet").exists()
    assert (tmp_path / "model_zoo_selected_models.json").exists()
    assert (tmp_path / "model_zoo_report.txt").exists()
