import json

import numpy as np
import pandas as pd

from mais.research.consensus_v2 import build_consensus_v2
from mais.research.multi_horizon_oof import align_multi_horizon_oof


def _oof_fixture(n: int = 240) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2018-01-02", periods=n)
    rows = []
    for horizon, phase in [(28, 0.0), (35, 0.5), (40, 1.0), (45, 1.5), (60, 2.0)]:
        signal = 0.5 + 0.18 * np.sin(np.arange(n) / 13.0 + phase)
        truth = (signal + rng.normal(0, 0.12, n) >= 0.5).astype(int)
        for model in ["ridge", "histgb"]:
            p = np.clip(signal + rng.normal(0, 0.03, n), 0.01, 0.99)
            rows.append(
                pd.DataFrame(
                    {
                        "Date": dates,
                        "horizon": horizon,
                        "model": model,
                        "split": "crop_year_walk_forward",
                        "fold": 0,
                        "fold_label": "synthetic",
                        "y_true_up": truth,
                        "p_up": p,
                        "pred_up": (p >= 0.5).astype(int),
                    }
                )
            )
    return pd.concat(rows, ignore_index=True)


def test_disagreement_not_degenerate():
    oof = _oof_fixture()
    consensus, metrics = build_consensus_v2(oof, horizons=[28, 35, 40, 45, 60])
    assert consensus["disagreement"].std() > 0.005
    assert metrics["disagreement_unique_values"] > 10


def test_multi_horizon_oof_aligned():
    aligned = align_multi_horizon_oof(_oof_fixture(), horizons=[28, 35, 40, 45, 60])
    counts = aligned.groupby("Date")["horizon"].nunique()
    assert counts.min() == 5
    assert aligned["p_up"].notna().all()


def test_consensus_verdict_documented(tmp_path):
    out = tmp_path / "consensus_results.json"
    _, metrics = build_consensus_v2(_oof_fixture(), horizons=[28, 35, 40, 45, 60], output_path=out)
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert metrics["verdict"] in {"ALPHA", "FILTRE", "PRUDENCE", "REJETÉ"}
    assert loaded["verdict"] == metrics["verdict"]


def test_uncertain_proportion_usable():
    _, metrics = build_consensus_v2(_oof_fixture(), horizons=[28, 35, 40, 45, 60])
    assert 0.0 <= metrics["proportion_uncertain"] <= 1.0
    assert any(0.05 <= row["proportion_uncertain"] <= 0.60 for row in metrics["threshold_curve"])


def test_threshold_calibrated_on_oof():
    _, metrics = build_consensus_v2(_oof_fixture(), horizons=[28, 35, 40, 45, 60])
    thresholds = {row["threshold"] for row in metrics["threshold_curve"]}
    assert metrics["threshold_calibrated"] in thresholds
    assert len(thresholds) > 5
