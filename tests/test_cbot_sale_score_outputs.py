"""Tests des sorties du score de vente CBOT (étape 7)."""
from __future__ import annotations

import pytest

from mais.indicator import cbot_sale_score as sale
from mais.indicator import cbot_sale_score_features as feats


@pytest.fixture(scope="module")
def scored():
    cfg = sale.load_config()
    df, _ = feats.build_frame()
    frame = sale.score_timeseries(df, sale.build_models(df, cfg))
    return cfg, frame


def test_recommendations_are_in_allowed_set(scored):
    _cfg, frame = scored
    assert set(frame["recommendation"].unique()) <= set(sale.RECOMMENDATIONS)
    assert "BUY" not in set(frame["recommendation"].unique())   # jamais de BUY


def test_probabilities_in_unit_interval(scored):
    _cfg, frame = scored
    for c in ["prob_up_h40", "prob_up_h90", "p_down_h90", "confidence"]:
        v = frame[c].dropna()
        assert (v >= 0).all() and (v <= 1).all()


def test_risk_high_only_when_vol_high(scored):
    _cfg, frame = scored
    rh = frame[frame["recommendation"] == "RISK_HIGH"]
    assert (rh["vol_filter_high_decile"] == 1).all()


def test_no_signal_when_features_missing(scored):
    _cfg, frame = scored
    ns = frame[frame["recommendation"] == "NO_SIGNAL"]
    if len(ns):
        assert ns["prob_up_h90"].isna().all()


def test_latest_record_shape(scored):
    cfg, frame = scored
    rec = sale.latest_record(frame, cfg)
    assert rec["recommendation"] in sale.RECOMMENDATIONS
    assert rec["price_forecast_enabled"] is not True   # jamais de prévision de prix
    assert "note" in rec and "bot" in rec["note"].lower()
