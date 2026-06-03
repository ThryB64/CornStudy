"""Tests V143 (enrichment) / V145 (lifecycle) / V146 (dashboard v4)."""
from __future__ import annotations

import json

import pandas as pd

import mais.premium.dashboard_v4 as dash
import mais.premium.lifecycle_report as lc
import mais.research.v143_event_catalyst_enrichment as v143


def test_v143_enrichment(tmp_path, monkeypatch):
    v129 = tmp_path / "v129.parquet"
    pd.DataFrame({"peak_date": ["2021-05-10", "2021-08-12"], "catalyst": ["CBOT_WEATHER", "CBOT_RALLY_UNATTRIBUTED"],
                  "f_cot_net_change_norm": [0.1, 0.4]}).to_parquet(v129, index=False)
    v137 = tmp_path / "v137.parquet"
    pd.DataFrame({"peak_date": ["2021-05-10", "2021-08-12"],
                  "report_label": ["CBOT_WASDE", "NO_REPORT"]}).to_parquet(v137, index=False)
    monkeypatch.setattr(v143, "V129_LIB", v129)
    monkeypatch.setattr(v143, "V137_LIB", v137)
    monkeypatch.setattr(v143, "ENRICHED", tmp_path / "enriched.parquet")
    monkeypatch.setattr(v143, "V_DIR", tmp_path)
    out = v143.run_v143_enrichment()
    assert out["verdict"] == "EVENT_ENRICHMENT_BUILT"
    cc = out["catalyst_final_counts"]
    # episode 1: report exact CBOT_WASDE (cot 0.1 < seuil) ; episode 2: COT_SHORT_COVERING (cot 0.4>=0.25, CBOT)
    assert cc.get("CBOT_WASDE") == 1
    assert cc.get("COT_SHORT_COVERING") == 1


def test_v143_no_lib(tmp_path, monkeypatch):
    monkeypatch.setattr(v143, "V129_LIB", tmp_path / "absent.parquet")
    assert v143.run_v143_enrichment()["verdict"] == "NO_V129_LIBRARY"


def test_v145_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setattr(lc, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(lc, "V_DIR", tmp_path)
    monkeypatch.setattr("mais.research.v124_active_monitoring_v2.monitor_active_signal_v2",
                        lambda: {"verdict": "ACTIVE_MONITORING_READY", "current_date": "2026-06-02",
                                 "days_since_entry": 4, "compression_realized_eur_t": 1.12, "mfe_eur_t": 1.12,
                                 "mae_eur_t": 0.0, "distance_to_z05": 1.47, "distance_to_z0": 1.97,
                                 "status": "HEALTHY"})
    monkeypatch.setattr("mais.premium.state_machine.run_v139_state_machine",
                        lambda: {"headline_state": "COMPRESSION_HEALTHY", "prime_nature": "PRIME_PHYSICALLY_JUSTIFIED",
                                 "lifecycle_state": "COMPRESSION_HEALTHY"})
    out = lc.run_v145_lifecycle()
    assert out["verdict"] == "LIFECYCLE_REPORT_BUILT"
    assert (tmp_path / "lifecycle.md").exists()


def test_v146_dashboard(tmp_path, monkeypatch):
    monkeypatch.setattr(dash, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr("mais.premium.head.build_premium_head",
                        lambda: {"verdict": "PREMIUM_HEAD_BUILT", "as_of": "2026-06-02",
                                 "PREMIUM_STATE": "SHORT_PREMIUM_STRONG", "basis_eur_t": 75.03, "basis_z": 1.969,
                                 "official_proxy_status": "proxy_implied", "HEADLINE_STATE": "COMPRESSION_HEALTHY",
                                 "PRIME_NATURE": "PRIME_PHYSICALLY_JUSTIFIED", "LIFECYCLE_STATE": "COMPRESSION_HEALTHY",
                                 "TARGET_RECOMMENDATION": "z->0.5", "HORIZON_ESTIMATE": {"median_horizon_days_seasonal": 23},
                                 "diagnostics": {"ADVERSE_RISK": {"value": "MEDIUM", "fresh": True}},
                                 "consistency": {"verdict": "LIVE_SIGNAL_CONSISTENT"},
                                 "freshness": {"verdict": "CONTEXT_COHERENT"}, "scope_clean": True, "warnings": []})
    monkeypatch.setattr("mais.premium.forward_milestones.run_v147_milestones",
                        lambda: {"n_official_days": 3, "next_milestone": 10, "next_meaning": "vérif technique",
                                 "rolling_official_z_available": False})
    out = dash.run_v146_dashboard()
    assert out["verdict"] == "DASHBOARD_V4_BUILT"
    assert (tmp_path / "dashboard_v4.md").exists()
