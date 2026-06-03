"""Tests VN-D2 — transitions d'état."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v_state_transitions as stt


def test_classify_states():
    assert stt.classify_state(0.5, 0, 0, "LOW") == "NO_SIGNAL"
    assert stt.classify_state(1.1, 0, 0, "LOW") == "WAIT_CONFIRMATION"
    assert stt.classify_state(1.7, 0.3, 0, "LOW") == "STILL_WIDENING"      # s'écarte encore (pré-pic)
    assert stt.classify_state(2.1, -0.3, 0, "LOW") == "EXTREME_EARLY_RELAXATION"
    assert stt.classify_state(2.1, 0.0, 0, "LOW") == "EXTREME_STATIC"
    assert stt.classify_state(1.7, 0.0, 0, "HIGH") == "STRONG_PHYSICAL_JUSTIFIED"
    assert stt.classify_state(1.7, 0.0, 0.05, "LOW") == "STRONG_CBOT_CATCHUP"


def _master():
    n = 400
    idx = pd.date_range("2018-01-01", periods=n, freq="B")
    z = np.r_[np.full(200, 0.3), np.linspace(2.2, 0.4, 100), np.full(100, 1.7)]
    cbot = np.linspace(380, 470, n)
    df = pd.DataFrame({"ema_cbot_basis_zscore_52w": z, "ema_cbot_basis": 80 - z * 5,
                       "cbot_close": cbot}, index=idx)
    df.index.name = "Date"
    return df


def test_run(tmp_path, monkeypatch):
    df = _master()
    monkeypatch.setattr(stt, "V_DIR", tmp_path)
    monkeypatch.setattr(stt, "assert_no_holdout", lambda d: None)
    out = stt.run_v_state_transitions(df)
    assert out["verdict"] == "STATE_TRANSITIONS_BUILT"
    assert out["n_active_days"] > 0
    assert "current_state" in out


def test_report_block(tmp_path, monkeypatch):
    df = _master()
    monkeypatch.setattr(stt, "V_DIR", tmp_path)
    monkeypatch.setattr(stt, "assert_no_holdout", lambda d: None)
    stt.run_v_state_transitions(df)
    block = stt.state_transitions_report_block()
    assert "VN-D2" in block
