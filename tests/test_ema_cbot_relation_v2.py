from __future__ import annotations

import json

from mais.research.ema_cbot_relation_v2 import build_cbot_relation_v2, save_cbot_relation_v2


def test_cbot_relation_v2_required_keys():
    data = build_cbot_relation_v2()
    for key in ["static", "cointegration", "rolling_corr_price_260d", "lead_lag_returns", "granger"]:
        assert key in data


def test_cbot_relation_v2_wording_is_conservative():
    wording = build_cbot_relation_v2()["granger"]["mandatory_wording"]
    assert "NON CONFIRMÉ" in wording
    assert "contemporaine" in wording


def test_cbot_relation_v2_has_half_life():
    half_life = build_cbot_relation_v2()["key_findings"]["vecm_half_life_days"]
    assert half_life > 0


def test_save_cbot_relation_v2(tmp_path):
    out = save_cbot_relation_v2(tmp_path / "relation_v2.json")
    assert out.exists()
    data = json.loads(out.read_text())
    assert "key_findings" in data
