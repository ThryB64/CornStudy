"""Tests VN-A2 — session timing PROVISIONAL/FINAL/SETTLING (DSP 18:30 CET Paris)."""
from __future__ import annotations

from datetime import datetime, timezone

import mais.premium.session_timing as st


def _utc(y, m, d, hh, mm):
    return datetime(y, m, d, hh, mm, tzinfo=timezone.utc)


def test_provisional_before_cutoff():
    # 08:00 UTC en juin = 10:00 Paris (CEST) -> avant 18:30 -> PROVISIONAL
    assert st.classify_record_status(_utc(2026, 6, 2, 8, 0)) == "PROVISIONAL"


def test_final_after_cutoff():
    # 17:00 UTC en juin = 19:00 Paris -> FINAL
    assert st.classify_record_status(_utc(2026, 6, 2, 17, 0)) == "FINAL"


def test_settling_buffer():
    # 16:32 UTC = 18:32 Paris -> entre 18:30 et 18:35 -> SETTLING
    assert st.classify_record_status(_utc(2026, 6, 2, 16, 32)) == "SETTLING"


def test_stamp_timing_fields():
    rec = {"price_date": "2026-06-02", "signal_tier": "SHORT_PREMIUM_STRONG"}
    out = st.stamp_timing(rec, collected_at_utc=_utc(2026, 6, 2, 17, 0))
    assert out["record_status"] == "FINAL"
    assert out["effective_session_date"] == "2026-06-02"
    assert out["provisional_warning"] is False
    assert "collected_at_paris" in out
    out2 = st.stamp_timing(rec, collected_at_utc=_utc(2026, 6, 2, 5, 0))
    assert out2["record_status"] == "PROVISIONAL"
    assert out2["provisional_warning"] is True


def test_invariants_ok_and_violation():
    rec = st.stamp_timing({"price_date": "2026-06-02"}, collected_at_utc=_utc(2026, 6, 2, 17, 0))
    assert st.session_invariants(rec) == []
    bad = dict(rec)
    bad["record_status"] = "FINAL"
    bad["collected_at_paris"] = "2026-06-02 10:00:00 CEST"  # FINAL mais 10:00 < 18:35
    assert any("FINAL" in v for v in st.session_invariants(bad))
