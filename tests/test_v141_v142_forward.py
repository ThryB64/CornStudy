"""V141/V142 — validation forward gatée (offline via monkeypatch du journal)."""
from __future__ import annotations

import pandas as pd

from mais.research import v141_v142_forward_validation as fv
from mais.research import v27_official_forward as v27


def _fake_journal(n_days: int) -> pd.DataFrame:
    dates = pd.date_range("2026-06-01", periods=n_days, freq="B").strftime("%Y-%m-%d")
    return pd.DataFrame({
        "price_date": dates,
        "basis_official_eur_t": [70.0 + i * 0.5 for i in range(n_days)],
        "basis_z_used": [1.8] * n_days,
        "record_status": ["REVISED"] * n_days,
    })


def test_gate_blocks_small_n(monkeypatch, tmp_path):
    monkeypatch.setattr(v27, "load_forward_journal", lambda final_only=True: _fake_journal(5))
    monkeypatch.setattr(fv, "CURVE_PATH", tmp_path / "absent.parquet")
    monkeypatch.setattr(fv, "MATIF_PATH", tmp_path / "absent2.parquet")
    monkeypatch.setattr(fv, "V_DIR", tmp_path)
    out = fv.run_v141_v142_forward()
    assert out["verdict"] == "ACCUMULATING_5_DAYS"


def test_gate_opens_at_min_days(monkeypatch, tmp_path):
    monkeypatch.setattr(v27, "load_forward_journal", lambda final_only=True: _fake_journal(45))
    monkeypatch.setattr(fv, "CURVE_PATH", tmp_path / "absent.parquet")
    monkeypatch.setattr(fv, "MATIF_PATH", tmp_path / "absent2.parquet")
    monkeypatch.setattr(fv, "V_DIR", tmp_path)
    out = fv.run_v141_v142_forward()
    assert out["verdict"] == "SAMPLE_OK_SEE_TESTS"
    assert out["n_official_days_aligned"] == 45
