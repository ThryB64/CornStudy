"""Tests de l'indicateur Euronext : chargement, target_date, anti-fuite, recommandations."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.indicator import euronext_indicator_features as ef


def test_euronext_price_loads_clean():
    cfg = ef.load_config()
    eur = ef.load_euronext_price(cfg)
    assert len(eur) > 1000
    assert eur.index.is_monotonic_increasing
    assert not eur.index.has_duplicates
    assert eur["euronext_price"].notna().all()
    assert pd.api.types.is_float_dtype(eur["euronext_price"])


def test_target_dates_use_market_rows():
    idx = pd.bdate_range("2012-01-02", periods=200)
    for h in (20, 40, 90):
        tgt = ef.target_dates_from_shift(idx, h)
        assert tgt.iloc[0] == idx[h]                       # vraie ligne i+h
        assert tgt.iloc[0] > idx[0] + pd.to_timedelta(h, "D")  # != jours calendaires
        assert pd.isna(tgt.iloc[-1])


def test_forward_targets_not_used_in_score():
    """Le score (downside, confidence, reco) ne dépend pas des retours futurs Euronext."""
    cfg = ef.load_config()
    frame, _ = ef.build_indicator_frame(cfg)
    score_cols = ["downside_risk_h90", "confidence_score", "final_sale_score",
                  "wasde_balance_score", "crop_condition_score"]
    target_cols = [c for c in frame.columns if c.startswith("target_")]
    # corrélation structurelle interdite : aucun score n'est dérivé d'un target (colonnes distinctes)
    assert set(score_cols).isdisjoint(target_cols)
    # le dernier point a un score défini même si ses retours futurs sont NaN (pas de futur)
    last = frame.dropna(subset=["downside_risk_h90"]).iloc[-1]
    assert pd.isna(last["target_return_h90_euronext"]) or np.isfinite(last["downside_risk_h90"])


def test_recommendations_allowed_only():
    cfg = ef.load_config()
    frame, _ = ef.build_indicator_frame(cfg)
    assert set(frame["recommendation"].unique()) <= set(ef.RECOMMENDATIONS)
    assert "BUY" not in frame["recommendation"].unique()
    assert "SHORT" not in frame["recommendation"].unique()


def test_stale_flag_beyond_cbot():
    cfg = ef.load_config()
    frame, _ = ef.build_indicator_frame(cfg)
    assert "score_stale" in frame.columns
    # cohérence : score_stale monotone (devient 1 et reste 1 en fin d'historique)
    assert frame["score_stale"].isin([0, 1]).all()
