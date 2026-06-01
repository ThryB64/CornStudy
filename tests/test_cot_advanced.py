import json

import numpy as np
import pandas as pd

from mais.features.cot_advanced import (
    ADVANCED_COT_COLUMNS,
    build_cot_advanced_features,
    evaluate_cot_advanced_stability,
    expanding_percentile,
)


def _cot_frame(n: int = 260) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2010-01-04", periods=n)
    oi = rng.uniform(300_000, 600_000, n)
    mm_net = rng.normal(0, 70_000, n)
    comm_net = -mm_net + rng.normal(0, 20_000, n)
    return pd.DataFrame(
        {
            "Date": dates,
            "cot_open_interest": oi,
            "cot_mm_net": mm_net,
            "cot_comm_net": comm_net,
        }
    )


def test_cot_pct_oi_bounded():
    df = build_cot_advanced_features(_cot_frame())
    ratio = df["cot_mm_net_pct_oi"].dropna()
    assert set(ADVANCED_COT_COLUMNS).issubset(df.columns)
    assert ratio.between(-1.5, 1.5).all()


def test_cot_percentile_expanding():
    values = pd.Series([1, 2, 3, 4, 5, 6], dtype=float)
    pct = expanding_percentile(values, min_periods=3)
    assert pct.iloc[:2].isna().all()
    assert pct.iloc[2] == 1.0
    assert pct.iloc[5] == 1.0


def test_cot_extreme_flags_rare():
    df = build_cot_advanced_features(_cot_frame(1200))
    long_freq = df["cot_mm_extreme_long_flag"].dropna().mean()
    short_freq = df["cot_mm_extreme_short_flag"].dropna().mean()
    assert 0.06 <= long_freq <= 0.16
    assert 0.06 <= short_freq <= 0.16


def test_cot_temporal_stability_documented(tmp_path):
    base = _cot_frame(1800)
    adv = build_cot_advanced_features(base)
    df = base.merge(adv, on="Date")
    rng = np.random.default_rng(7)
    df["baseline_signal"] = rng.normal(0, 1, len(df))
    score = df["baseline_signal"].fillna(0) + df["cot_crowding_score"].fillna(0) * 0.2
    df["y_up_h40"] = (score > score.median()).astype(int)
    out_path = tmp_path / "cot_advanced_stability.json"
    payload = evaluate_cot_advanced_stability(df, output_path=out_path)
    loaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["verdict"] in {"CONFIRMÉ", "PROMETTEUR", "NEUTRE", "REJETÉ", "INCONCLU"}
    assert "auc_2010_2015" in loaded
    assert "auc_2016_2022" in loaded
