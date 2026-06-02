"""Tests V137 — attribution par dates de rapports USDA (synthétique)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import mais.research.v137_event_date_attribution as v137


def _synthetic():
    n = 400
    idx = pd.date_range("2021-01-01", periods=n, freq="B")
    z = np.zeros(n)
    z[100:115] = np.linspace(0.5, 2.0, 15)
    z[115:150] = np.linspace(2.0, 0.3, 35)
    cbot = np.linspace(400, 420, n)
    cbot[115:150] = np.linspace(420, 470, 35)
    df = pd.DataFrame({"ema_cbot_basis_zscore_52w": z, "ema_cbot_basis": 80 - z * 5,
                       "cbot_close": cbot, "corn_logret_1d": np.r_[0.0, np.diff(np.log(cbot))]}, index=idx)
    df.index.name = "Date"
    return df


def test_report_calendar():
    cal = v137.report_calendar(pd.Timestamp("2021-01-01"), pd.Timestamp("2021-12-31"))
    assert len(cal["WASDE"]) == 12  # un par mois
    assert len(cal["GRAIN_STOCKS"]) >= 3
    assert len(cal["ACREAGE"]) >= 1


def test_run(tmp_path, monkeypatch):
    df = _synthetic()
    monkeypatch.setattr(v137, "V137_DIR", tmp_path)
    monkeypatch.setattr(v137, "assert_no_holdout", lambda d: None)
    out = v137.run_v137_event_dates(df)
    assert out["verdict"] == "EVENT_DATES_READY"
    assert out["n_events"] >= 1
    # la fenêtre de compression couvre ~mai-juin -> contient au moins un WASDE mensuel
    assert out["n_episodes_overlap_report"] >= 1
    assert (tmp_path / "event_date_attribution.parquet").exists()


def test_no_events(tmp_path, monkeypatch):
    df = pd.DataFrame({"ema_cbot_basis_zscore_52w": np.zeros(300)},
                      index=pd.date_range("2021-01-01", periods=300, freq="B"))
    df.index.name = "Date"
    monkeypatch.setattr(v137, "assert_no_holdout", lambda d: None)
    assert v137.run_v137_event_dates(df)["verdict"] == "NO_EVENTS"


def test_report_block(tmp_path, monkeypatch):
    df = _synthetic()
    monkeypatch.setattr(v137, "V137_DIR", tmp_path)
    monkeypatch.setattr(v137, "assert_no_holdout", lambda d: None)
    v137.run_v137_event_dates(df)
    block = v137.event_dates_report_block()
    assert "V137" in block
