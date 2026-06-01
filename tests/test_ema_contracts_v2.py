from __future__ import annotations

import json

from mais.research.ema_contracts_v2 import build_contracts_v2, save_contracts_v2


def test_contracts_v2_required_keys():
    data = build_contracts_v2()
    for key in [
        "base_contracts_rolls",
        "front_raw_vs_adjusted_returns",
        "harvest_nov_coverage",
        "recommendation",
        "key_findings",
    ]:
        assert key in data


def test_contracts_v2_roll_windows_are_ordered():
    k = build_contracts_v2()["key_findings"]
    assert k["pct_H20_windows_with_roll"] < k["pct_H40_windows_with_roll"] < k["pct_H60_windows_with_roll"]


def test_contracts_v2_recommends_adjusted_for_returns():
    rec = build_contracts_v2()["recommendation"]
    assert "rendements" in rec["adjusted"]


def test_save_contracts_v2(tmp_path):
    out = save_contracts_v2(tmp_path / "contracts_v2.json")
    assert out.exists()
    data = json.loads(out.read_text())
    assert "key_findings" in data
