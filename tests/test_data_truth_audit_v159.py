"""V159 — pack d'audit de la vérité des données."""
from __future__ import annotations

import pytest

from mais.audit import data_truth as dt
from mais.research import v27_official_forward as v27

_NO_JOURNAL = not v27.JOURNAL_JSONL.exists()


@pytest.mark.skipif(_NO_JOURNAL, reason="journal officiel absent")
def test_session_alignment_no_orphan():
    r = dt.session_alignment_audit()
    assert r["verdict"] == "PASS"
    assert r["n_orphans"] == 0


@pytest.mark.skipif(_NO_JOURNAL, reason="journal officiel absent")
def test_cbot_eur_roundtrip_within_tolerance():
    r = dt.cbot_eur_conversion_audit()
    assert r["verdict"] in ("PASS", "SKIP")
    if r["verdict"] == "PASS":
        assert r["max_abs_err_eur_t"] <= dt.CBOT_EUR_TOL


@pytest.mark.skipif(_NO_JOURNAL, reason="journal officiel absent")
def test_finality_gate_view_is_final_only():
    r = dt.finality_gate_audit()
    assert r["verdict"] in ("PASS", "SKIP")


@pytest.mark.skipif(_NO_JOURNAL, reason="journal officiel absent")
def test_overall_audit_runs():
    r = dt.run_data_truth_audit()
    assert r["overall"] in ("PASS", "WARN")
    assert "session_alignment" in r["verdicts"]
