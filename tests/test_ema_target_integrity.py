from __future__ import annotations

import json

from mais.research.ema_target_integrity import (
    build_target_integrity_audit,
    save_target_integrity_audit,
)


def test_target_integrity_audit_passes():
    data = build_target_integrity_audit()
    assert data["verdict"] == "TARGET_INTEGRITY_PASS"


def test_target_integrity_checks_relative_targets():
    targets = {row["target"] for row in build_target_integrity_audit()["targets_checked"]}
    assert "y_ema_outperforms_cbot_h40" in targets


def test_target_integrity_tail_nan_counts():
    data = build_target_integrity_audit()
    for row in data["targets_checked"]:
        assert row["tail_non_null_count"] == 0


def test_save_target_integrity_audit(tmp_path):
    out = save_target_integrity_audit(tmp_path / "target_integrity.json")
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["verdict"] == "TARGET_INTEGRITY_PASS"
