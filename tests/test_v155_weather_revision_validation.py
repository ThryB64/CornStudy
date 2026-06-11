"""V155 — validation exploratoire des révisions météo (offline, données synthétiques)."""
from __future__ import annotations

import pandas as pd

from mais.research import v155_weather_revision_validation as v155


def _mock_long():
    rows = []
    for valid, base in (("2026-06-08", 30.0), ("2026-06-09", 31.0), ("2026-06-10", 29.0)):
        for lead in range(0, 4):
            rows.append({"issue_date": str(pd.Timestamp(valid).date() - pd.Timedelta(days=lead)),
                         "valid_date": valid, "lead_day": lead, "zone": "iowa",
                         "variable": "tmax", "value": base + lead})  # plus vieux = plus chaud -> rev_hot<0
            rows.append({"issue_date": str(pd.Timestamp(valid).date() - pd.Timedelta(days=lead)),
                         "valid_date": valid, "lead_day": lead, "zone": "france",
                         "variable": "precip", "value": 2.0 + lead})
    return pd.DataFrame(rows)


def test_build_revision_features_regions_and_signs():
    feats = v155.build_revision_features(_mock_long())
    assert set(feats["region"]) == {"us", "eu"}
    us = feats[feats["region"] == "us"]
    # tmax baisse en se rapprochant (value = base + lead) : révision vers MOINS chaud -> rev_hot négatif
    assert (us["rev_hot"].dropna() < 0).all()
    eu = feats[feats["region"] == "eu"]
    # precip baisse en se rapprochant -> révision precip négative -> rev_dry = -rev > 0 (vers plus sec)
    assert (eu["rev_dry"].dropna() > 0).all()


def test_features_indexed_at_issue_date():
    feats = v155.build_revision_features(_mock_long())
    # une révision from_lead=1 pour valid 2026-06-10 est émise le 2026-06-10 (jamais après)
    assert "2026-06-10" in set(feats["issue_date"])
    assert feats["issue_date"].max() <= "2026-06-10"


def test_validation_with_synthetic_cbot_stays_honest():
    feats_src = _mock_long()
    # monkey-free : on passe une série CBOT synthétique courte -> verdict petit n obligatoire
    closes = pd.Series([400.0, 401.0, 402.0, 401.5, 403.0],
                       index=["2026-06-06", "2026-06-07", "2026-06-08", "2026-06-09", "2026-06-10"])
    import mais.collect.openmeteo_previous_runs as pr
    orig = pr.load_revisions
    pr.load_revisions = lambda: feats_src
    v155.load_revisions = lambda: feats_src
    try:
        out = v155.run_v155_validation(cbot_close=closes)
    finally:
        pr.load_revisions = orig
        v155.load_revisions = orig
    assert out["verdict"] in ("PRELIMINARY_N_SMALL", "WAITING_DATA")
    assert out.get("status", "RESEARCH_ONLY_NOT_TRADING") == "RESEARCH_ONLY_NOT_TRADING"
