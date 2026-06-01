import json

import numpy as np
import pandas as pd

from mais.collect.futures_curve import (
    build_cbot_symbol,
    check_no_outliers,
    check_price_continuity_around_expiry,
    diagnose_futures_curve_quality,
)
from mais.features.curve_spreads import build_curve_spread_features, evaluate_curve_spreads


def _curve_frame(n: int = 260) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2020-01-02", periods=n)
    zcz = 420 + np.cumsum(rng.normal(0, 1, n))
    return pd.DataFrame(
        {
            "Date": dates,
            "zcz_close": zcz,
            "zch_close": zcz + 8 + rng.normal(0, 0.5, n),
            "zck_close": zcz + 12 + rng.normal(0, 0.5, n),
            "zcn_close": zcz + 18 + rng.normal(0, 0.5, n),
        }
    )


def test_phase1_diagnostic_runs():
    report = diagnose_futures_curve_quality(start_year=2020, end_year=2020, provider="yfinance")
    assert "status" in report
    assert "contracts" in report


def test_provider_symbol_mapping():
    assert build_cbot_symbol("Z", 2024, "yfinance") == "ZCZ24.CBT"
    assert build_cbot_symbol("H", 2025, "generic") == "ZCH25"
    assert build_cbot_symbol("N", 2026, "quandl") == "CHRIS/CME_CN26"


def test_curve_spreads_anti_leakage():
    raw = _curve_frame(40)
    out = build_curve_spread_features(raw, spot=raw["zcz_close"])
    expected = raw["zch_close"].iloc[0] - raw["zcz_close"].iloc[0]
    assert pd.isna(out["curve_zh_spread"].iloc[0])
    assert np.isclose(out["curve_zh_spread"].iloc[1], expected)


def test_curve_spreads_delta_auc_documented(tmp_path):
    raw = _curve_frame(900)
    curve = build_curve_spread_features(raw, spot=raw["zcz_close"])
    df = raw[["Date"]].merge(curve, on="Date")
    rng = np.random.default_rng(8)
    df["baseline_signal"] = rng.normal(0, 1, len(df))
    score = df["baseline_signal"] + df["curve_nz_spread"].fillna(0) * 0.03
    df["y_up_h40"] = (score > score.median()).astype(int)
    out_path = tmp_path / "curve_spreads_eval.json"
    payload = evaluate_curve_spreads(df, output_path=out_path)
    loaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["verdict"] in {"CONFIRMÉ", "PROMETTEUR", "NEUTRE", "REJETÉ", "INCONCLU"}
    assert "delta_auc" in loaded


def test_contango_seasonal_coherence():
    raw = _curve_frame(120)
    out = build_curve_spread_features(raw, spot=raw["zcz_close"])
    assert out["curve_contango_flag"].dropna().mean() > out["curve_backwardation_flag"].dropna().mean()


def test_price_quality_checks():
    ok = pd.Series(np.linspace(400, 450, 60))
    bad = ok.copy()
    bad.iloc[20] = -1
    jump = ok.copy()
    jump.iloc[30] = 1000
    assert check_no_outliers(ok)
    assert not check_no_outliers(bad)
    assert check_price_continuity_around_expiry(ok)
    assert not check_price_continuity_around_expiry(jump)
