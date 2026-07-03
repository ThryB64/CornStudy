"""Tests du dashboard Euronext : HTML créé, autonome (pas d'image externe), graphiques présents."""
from __future__ import annotations

import json

from mais.indicator import euronext_indicator_dashboard as dash
from mais.paths import PROJECT_ROOT

OUT = PROJECT_ROOT / "artefacts" / "final_euronext_indicator"


def test_finalize_creates_artefacts():
    res = dash.finalize()
    assert res["verdict"] in ("VALIDATED", "FRAGILE", "RESEARCH_ONLY", "NOT_VALIDATED")
    for f in ("euronext_indicator_history.csv", "euronext_indicator_latest.json",
              "euronext_indicator_dashboard.html", "euronext_indicator_metrics.csv",
              "euronext_backtest_decisions.csv", "euronext_backtest_summary.csv",
              "euronext_backtest_by_campaign.csv",
              "euronext_indicator_feature_dictionary.csv"):
        assert (OUT / f).is_file(), f


def test_html_is_self_contained():
    html = (OUT / "euronext_indicator_dashboard.html").read_text(encoding="utf-8")
    low = html.lower()
    assert "<html" in low
    assert "plotly" in low                               # JS Plotly inline
    assert "<img" not in low                             # aucune balise image
    # pas de balise externe fetchée par le navigateur (script/link/img src http)
    assert "<script src=" not in low and "<link " not in low
    for title in ("Prix Euronext", "recommandations", "confusion", "backtest"):
        assert title.lower() in low


def test_latest_json_shape():
    rec = json.loads((OUT / "euronext_indicator_latest.json").read_text(encoding="utf-8"))
    assert rec["recommendation"] in ("SELL_PARTIAL", "WAIT", "WATCH", "RISK_HIGH", "NO_SIGNAL")
    assert rec["price_forecast_enabled"] is False
    assert "score_stale" in rec and "bot" in rec["note"].lower()
