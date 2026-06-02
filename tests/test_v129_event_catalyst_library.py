"""Tests V129 — catalogue de catalyseurs (détection d'épisodes + classification, données synthétiques)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v129_event_catalyst_library as v129


def _synthetic():
    # construit un basis_z avec un pic à 2.0 puis chute à 0.5, CBOT qui rallie + chaleur
    n = 400
    idx = pd.date_range("2021-01-01", periods=n, freq="B")
    z = np.full(n, 0.0)
    z[100:115] = np.linspace(0.5, 2.0, 15)   # montée vers le pic
    z[115:150] = np.linspace(2.0, 0.3, 35)   # compression
    cbot = np.linspace(400, 420, n)
    cbot[115:150] = np.linspace(420, 470, 35)  # CBOT rallie pendant la compression
    heat = np.zeros(n)
    heat[115:150] = 1.5
    df = pd.DataFrame({
        "ema_cbot_basis_zscore_52w": z,
        "ema_cbot_basis": 80 - z * 5,
        "cbot_close": cbot,
        "wx_belt_tmax_c_anom_z": heat,
        "cot_mm_net": np.linspace(1000, 1100, n),
        "corn_logret_1d": np.r_[0.0, np.diff(np.log(cbot))],
    }, index=idx)
    df.index.name = "Date"
    return df


def test_detect_events():
    ev = v129.detect_compression_events(_synthetic())
    assert len(ev) >= 1
    assert ev["peak_z"].iloc[0] >= 1.5


def test_classify_cbot_weather(monkeypatch, tmp_path):
    df = _synthetic()
    monkeypatch.setattr(v129, "V129_DIR", tmp_path)
    monkeypatch.setattr(v129, "EVENT_STORE", tmp_path / "lib.parquet")
    monkeypatch.setattr(v129, "assert_no_holdout", lambda d: None)
    out = v129.run_v129_event_library(df)
    assert out["verdict"] == "EVENT_LIBRARY_READY"
    assert "CBOT_WEATHER" in out["catalyst_counts"]


def test_no_events(monkeypatch, tmp_path):
    df = pd.DataFrame({"ema_cbot_basis_zscore_52w": np.zeros(300)},
                      index=pd.date_range("2021-01-01", periods=300, freq="B"))
    df.index.name = "Date"
    monkeypatch.setattr(v129, "assert_no_holdout", lambda d: None)
    assert v129.run_v129_event_library(df)["verdict"] == "NO_EVENTS"


def test_report_block(monkeypatch, tmp_path):
    df = _synthetic()
    monkeypatch.setattr(v129, "V129_DIR", tmp_path)
    monkeypatch.setattr(v129, "EVENT_STORE", tmp_path / "lib.parquet")
    monkeypatch.setattr(v129, "assert_no_holdout", lambda d: None)
    v129.run_v129_event_library(df)
    block = v129.event_library_report_block()
    assert "V129" in block
