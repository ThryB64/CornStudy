from __future__ import annotations

import json

from mais.research.ema_volatility_v2 import _load_vol, build_volatility_v2, save_volatility_v2


def test_volatility_v2_required_keys():
    data = build_volatility_v2()
    for key in ["vol_descriptive", "vol_regimes", "har_models", "vol_regime_prediction_oof"]:
        assert key in data


def test_volatility_v2_regimes_present():
    regimes = build_volatility_v2()["vol_regimes"]
    assert "normal" in regimes
    assert "stress" in regimes


def test_volatility_v2_har_models():
    har = build_volatility_v2()["har_models"]
    assert "har_plus_basis" in har


def test_volatility_v2_future_vol_tail_is_unknown():
    df = _load_vol()
    future_vol = df["vol_20d"].shift(-20)
    assert future_vol.tail(20).isna().all()


def test_save_volatility_v2(tmp_path):
    out = save_volatility_v2(tmp_path / "vol_v2.json")
    assert out.exists()
    data = json.loads(out.read_text())
    assert "key_findings" in data
