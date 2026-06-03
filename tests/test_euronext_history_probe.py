"""Tests VN-C1 — probe historique endpoint Euronext (offline + mock)."""
from __future__ import annotations

import mais.premium.euronext_history_probe as hp


def test_offline():
    assert hp.probe_history(try_network=False)["verdict"] == "OFFLINE_SKIP"


def test_no_public_range(tmp_path, monkeypatch):
    monkeypatch.setattr(hp, "V_DIR", tmp_path)
    # snapshot live = une seule date
    out = hp.probe_history(try_network=True, fetch=lambda url: "<td>02/06/2026</td><td>224.25</td>")
    assert out["verdict"] == "NO_PUBLIC_RANGE"
    assert out["max_distinct_dates_seen"] == 1


def test_has_public_range(tmp_path, monkeypatch):
    monkeypatch.setattr(hp, "V_DIR", tmp_path)
    html = "29/05/2026 ... 01/06/2026 ... 02/06/2026 ... 03/06/2026"
    out = hp.probe_history(try_network=True, fetch=lambda url: html)
    assert out["verdict"] == "HAS_PUBLIC_RANGE"
    assert out["max_distinct_dates_seen"] >= 3


def test_distinct_dates():
    assert hp._distinct_dates("02/06/2026 02/06/2026 2026-05-29") == {"02/06/2026", "2026-05-29"}
