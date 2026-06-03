"""Tests VN-E2 — microstructure événementielle (offline, journal mocké)."""
from __future__ import annotations

import mais.collect.euronext_evening_snapshots as ev
import mais.research.v_event_microstructure as em


def _journal(slots):
    rows = []
    for slot, front, spread, cbot in slots:
        rows.append({"effective_session_date": "2026-06-11", "event_label": "WASDE", "slot_cet": slot,
                     "front_settle": front, "front_next_spread": spread, "curve_shape": "BACKWARDATION",
                     "cbot_last": cbot})
    return rows


def test_forward_only_empty(monkeypatch):
    monkeypatch.setattr(ev, "load_evening_journal", lambda: [])
    assert em.run_v_event_microstructure()["verdict"] == "FORWARD_ONLY_ACCUMULATING"


def test_watchlist_one_event(tmp_path, monkeypatch):
    monkeypatch.setattr(em, "V_DIR", tmp_path)
    monkeypatch.setattr(ev, "load_evening_journal",
                        lambda: _journal([("17:55", 224.0, 12.0, 441.0), ("19:00", 225.5, 13.5, 444.0)]))
    out = em.run_v_event_microstructure()
    assert out["verdict"] == "WATCHLIST_FEW_EVENTS"
    assert out["n_events"] == 1
    assert out["by_event"][0]["front_move"] == 1.5
    assert out["by_event"][0]["cbot_move"] == 3.0


def test_microstructure_ready(tmp_path, monkeypatch):
    monkeypatch.setattr(em, "V_DIR", tmp_path)
    rows = []
    for day in ("2026-06-11", "2026-07-11", "2026-08-12"):
        for slot, fr in (("17:55", 224.0), ("19:00", 225.0)):
            rows.append({"effective_session_date": day, "event_label": "WASDE", "slot_cet": slot,
                         "front_settle": fr, "front_next_spread": 12.0, "curve_shape": "BACKWARDATION",
                         "cbot_last": 441.0})
    monkeypatch.setattr(ev, "load_evening_journal", lambda: rows)
    out = em.run_v_event_microstructure()
    assert out["verdict"] == "MICROSTRUCTURE_READY"
    assert out["n_events"] == 3
