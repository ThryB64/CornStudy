"""Tests config + reproductibilité du score de vente CBOT (étape 7)."""
from __future__ import annotations

import pandas as pd

from mais.indicator import cbot_sale_score as sale
from mais.indicator import cbot_sale_score_features as feats
from mais.paths import CONFIG_DIR


def test_config_exists_and_has_required_keys():
    cfg = sale.load_config()
    assert (CONFIG_DIR / "cbot_sale_score.yaml").is_file()
    assert cfg["price_forecast_enabled"] is False
    for key in ("version", "horizons", "features", "rules", "outputs", "holdout_start"):
        assert key in cfg
    assert cfg["horizons"]["direction_h40"] == 40
    assert cfg["horizons"]["direction_h90"] == 90
    for block in ("h40", "h90", "volatility", "regimes"):
        assert block in cfg["features"] and cfg["features"][block]
    for thr in ("sell_partial_threshold", "wait_threshold", "risk_high_vol_decile",
                "min_confidence"):
        assert thr in cfg["rules"]


def test_score_is_reproducible():
    """Deux exécutions sur les mêmes données donnent exactement les mêmes sorties."""
    cfg = sale.load_config()
    df, _ = feats.build_frame()
    f1 = sale.score_timeseries(df, sale.build_models(df, cfg))
    f2 = sale.score_timeseries(df, sale.build_models(df, cfg))
    pd.testing.assert_series_equal(f1["recommendation"], f2["recommendation"])
    pd.testing.assert_series_equal(f1["prob_up_h90"], f2["prob_up_h90"])
    pd.testing.assert_series_equal(f1["confidence"], f2["confidence"])


def test_model_is_parsimonious():
    """3 à 6 variables principales par horizon (parcimonie)."""
    cfg = sale.load_config()
    assert 3 <= len(cfg["features"]["h40"]) <= 6
    assert 3 <= len(cfg["features"]["h90"]) <= 6
