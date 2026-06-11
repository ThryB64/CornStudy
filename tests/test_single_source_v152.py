"""V152-SYNC — cohérence de la source unique premium (head/dashboard/lifecycle/monthly/latest).

Complète tests/test_session_truth_v150.py (précédence REVISED>FINAL>PROVISIONAL, champs de session).
Les tests tournent sur l'état réel du repo et skippent si les artefacts live sont absents.
"""
from __future__ import annotations

import pytest

from mais.audit import single_source as ss

_NO_HEAD = not ss.HEAD_PATH.exists()


@pytest.mark.skipif(_NO_HEAD, reason="premium head absent")
def test_single_source_truth_consistency():
    r = ss.run_single_source_audit()
    assert r["overall"] in ("PASS", "WARN"), r
    assert r["checks"]["head_matches_v132"]["verdict"] == "PASS"


@pytest.mark.skipif(_NO_HEAD, reason="premium head absent")
def test_dashboard_reads_head_only():
    r = ss.run_single_source_audit()
    c = r["checks"]["dashboard_reads_head_only"]
    assert c["verdict"] == "PASS", c
    assert c["declares_head_source"] is True


@pytest.mark.skipif(_NO_HEAD, reason="premium head absent")
def test_monthly_reads_head_only():
    r = ss.run_single_source_audit()
    assert r["checks"]["monthly_in_sync"]["verdict"] in ("PASS", "WARN")


@pytest.mark.skipif(_NO_HEAD, reason="premium head absent")
def test_no_stale_artifact_used_in_live_report():
    r = ss.run_single_source_audit()
    assert r["checks"]["head_not_stale_vs_journal"]["verdict"] == "PASS"
    # FAIL ici signifierait : le head commité est plus vieux que le dernier run CI
    assert r["checks"]["latest_embeds_same_head"]["verdict"] != "FAIL"


@pytest.mark.skipif(_NO_HEAD, reason="premium head absent")
def test_head_exposes_session_truth():
    r = ss.run_single_source_audit()
    assert r["checks"]["head_has_session_truth"]["verdict"] == "PASS"
