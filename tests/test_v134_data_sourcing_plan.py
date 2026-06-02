"""Tests V134 — plan de sourcing (statique)."""
from __future__ import annotations

import mais.research.v134_data_sourcing_plan as v134


def test_run(tmp_path, monkeypatch):
    monkeypatch.setattr(v134, "V134_DIR", tmp_path)
    out = v134.run_v134_sourcing_plan()
    assert out["verdict"] == "DATA_SOURCE_PLAN_READY"
    assert out["n_sources"] == len(v134.SOURCES)
    assert "Eurostat COMEXT (DS-045409)" in out["blocked"]
    # toutes les entrées ont les champs requis
    for s in out["sources"]:
        for k in ("source", "use", "availability", "cost", "api", "constraints", "status", "unblocks"):
            assert k in s


def test_report_block(tmp_path, monkeypatch):
    monkeypatch.setattr(v134, "V134_DIR", tmp_path)
    block = v134.sourcing_plan_report_block()
    assert "V134" in block and "DATA_SOURCE_PLAN_READY" in block
