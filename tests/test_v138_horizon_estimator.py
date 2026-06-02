"""Tests V138 — estimateur d'horizon par demi-vie."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v138_horizon_estimator as v138


def test_days_to_target():
    # z0=2, target=0.5, HL=4 -> 4*log2(4)=8
    assert v138.days_to_target(2.0, 0.5, 4.0) == 8.0
    assert v138.days_to_target(0.5, 0.5, 4.0) is None  # déjà à la cible
    assert v138.days_to_target(2.0, 0.0, 4.0) is None  # cible 0 impossible


def test_tier_from_z():
    assert v138._tier_from_z(1.2) == "MODERATE"
    assert v138._tier_from_z(2.5) == "EXTREME"


def test_live_estimate(tmp_path, monkeypatch):
    jp = tmp_path / "journal.parquet"
    pd.DataFrame([{"price_date": "2026-06-02", "signal_tier": "SHORT_PREMIUM_STRONG",
                   "basis_z_used": 1.969}]).to_parquet(jp, index=False)
    monkeypatch.setattr(v138, "V138_DIR", tmp_path)
    monkeypatch.setattr(v138, "OFFICIAL_JOURNAL", jp)
    monkeypatch.setattr(v138, "V130_ARTEFACT", tmp_path / "v130.json")
    (tmp_path / "v130.json").write_text('{"half_life_by_tier": {"STRONG": 4.9}}', encoding="utf-8")
    out = v138.run_v138_horizon(df=None)
    assert out["live_estimate"]["tier"] == "STRONG"
    assert out["live_estimate"]["half_life_days"] == 4.9
    assert out["live_estimate"]["analytic_days_to_z05"] > 0
    assert out["verdict"] == "LIVE_ONLY"


def test_validation(tmp_path, monkeypatch):
    monkeypatch.setattr(v138, "V138_DIR", tmp_path)
    monkeypatch.setattr(v138, "OFFICIAL_JOURNAL", tmp_path / "absent.parquet")
    monkeypatch.setattr(v138, "V130_ARTEFACT", tmp_path / "v130.json")
    (tmp_path / "v130.json").write_text('{"half_life_by_tier": {"MODERATE": 8.3, "STRONG": 4.9, "EXTREME": 3.3}}',
                                        encoding="utf-8")
    monkeypatch.setattr(v138, "assert_no_holdout", lambda d: None)
    rng = np.random.default_rng(0)
    n = 40
    z = rng.uniform(1.1, 2.5, n)
    fake = pd.DataFrame({"entry_z": z.round(3),
                         "days_z05": (4.9 * np.log2(z / 0.5) + rng.normal(0, 3, n)).clip(1, 90).round()})
    monkeypatch.setattr("mais.research.v47_objective_choice._paired_objectives", lambda df: fake)
    out = v138.run_v138_horizon(df=pd.DataFrame({"x": [1]}))
    assert out["validation"]["verdict"] == "VALIDATED"
    assert out["validation"]["corr_pred_real"] is not None
    assert out["verdict"] in ("ADD_TO_HORIZON", "WATCHLIST")


def test_report_block(tmp_path, monkeypatch):
    jp = tmp_path / "journal.parquet"
    pd.DataFrame([{"price_date": "2026-06-02", "signal_tier": "SHORT_PREMIUM_STRONG",
                   "basis_z_used": 1.969}]).to_parquet(jp, index=False)
    monkeypatch.setattr(v138, "V138_DIR", tmp_path)
    monkeypatch.setattr(v138, "OFFICIAL_JOURNAL", jp)
    monkeypatch.setattr(v138, "V130_ARTEFACT", tmp_path / "v130.json")
    (tmp_path / "v130.json").write_text('{"half_life_by_tier": {"STRONG": 4.9}}', encoding="utf-8")
    v138.run_v138_horizon(df=None)
    block = v138.horizon_estimator_report_block()
    assert "V138" in block and "z→0.5" in block
