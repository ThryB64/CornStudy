"""Tests V147/V148 — milestones forward + checkpoint gated."""
from __future__ import annotations

import pandas as pd

import mais.premium.forward_milestones as fm


def _journal(tmp_path, n_days):
    jp = tmp_path / "journal.parquet"
    dates = pd.bdate_range("2026-05-29", periods=n_days)
    pd.DataFrame({"price_date": [str(d.date()) for d in dates],
                  "basis_official_eur_t": [75.0] * n_days}).to_parquet(jp, index=False)
    return jp


def test_milestones_early(tmp_path, monkeypatch):
    monkeypatch.setattr(fm, "OFFICIAL_JOURNAL", _journal(tmp_path, 3))
    monkeypatch.setattr(fm, "V_DIR", tmp_path)
    out = fm.run_v147_milestones()
    assert out["n_official_days"] == 3
    assert out["milestones_reached"] == []
    assert out["next_milestone"] == 10
    assert out["rolling_official_z_available"] is False


def test_milestones_reached(tmp_path, monkeypatch):
    monkeypatch.setattr(fm, "OFFICIAL_JOURNAL", _journal(tmp_path, 45))
    monkeypatch.setattr(fm, "V_DIR", tmp_path)
    out = fm.run_v147_milestones()
    assert 10 in out["milestones_reached"] and 40 in out["milestones_reached"]
    assert out["next_milestone"] == 90
    assert out["rolling_official_z_available"] is True


def test_checkpoint_not_yet(tmp_path, monkeypatch):
    monkeypatch.setattr(fm, "OFFICIAL_JOURNAL", _journal(tmp_path, 5))
    out = fm.run_v148_checkpoint_40d()
    assert out["verdict"] == "NOT_YET"
    assert out["days_to_checkpoint"] == 35


def test_report_block(tmp_path, monkeypatch):
    monkeypatch.setattr(fm, "OFFICIAL_JOURNAL", _journal(tmp_path, 3))
    monkeypatch.setattr(fm, "V_DIR", tmp_path)
    assert "V147" in fm.milestones_report_block()
