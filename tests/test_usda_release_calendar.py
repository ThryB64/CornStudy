"""Tests VN-C5 — calendrier de publication USDA (fallback approximation honnête)."""
from __future__ import annotations

import mais.collect.usda_release_calendar as cal


def test_fallback_approx(monkeypatch):
    monkeypatch.setattr(cal, "_try_fetch_exact", lambda year, timeout=20: None)
    out = cal.wasde_release_dates(2026, try_network=True)
    assert out["is_exact"] is False
    assert out["source"] == "approximation_~10th"
    assert out["n"] == 12


def test_offline_is_approx():
    out = cal.wasde_release_dates(2026, try_network=False)
    assert out["is_exact"] is False
    assert len(out["dates"]) == 12


def test_exact_when_fetched(monkeypatch):
    import pandas as pd
    monkeypatch.setattr(cal, "_try_fetch_exact",
                        lambda year, timeout=20: [pd.Timestamp("2026-01-12"), pd.Timestamp("2026-02-11")])
    out = cal.wasde_release_dates(2026, try_network=True)
    assert out["is_exact"] is True
    assert out["source"] == "usda_live"
    assert out["n"] == 2
