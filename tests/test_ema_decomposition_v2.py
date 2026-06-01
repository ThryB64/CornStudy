from __future__ import annotations

import json

from mais.research.ema_decomposition_v2 import build_decomposition_v2, save_decomposition_v2


def test_decomposition_v2_separates_blocks():
    data = build_decomposition_v2()
    assert data["descriptive_contemporaneous"]["label"] == "DESCRIPTIF_NON_PREDICTIF"
    assert data["predictive_shift1_oof"]["label"] == "PREDICTIF_SHIFT1_OOF"


def test_decomposition_v2_descriptive_r2_high():
    r2 = build_decomposition_v2()["key_findings"]["descriptive_r2_cbot_basis"]
    assert r2 > 0.80


def test_decomposition_v2_predictive_has_verdict():
    verdict = build_decomposition_v2()["key_findings"]["predictive_verdict"]
    assert verdict in {"PREDICTIVE_WEAK", "PREDICTIVE_NO_GO"}


def test_save_decomposition_v2(tmp_path):
    out = save_decomposition_v2(tmp_path / "decomposition_v2.json")
    assert out.exists()
    data = json.loads(out.read_text())
    assert "key_findings" in data
