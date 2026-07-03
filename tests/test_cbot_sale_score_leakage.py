"""Tests anti-fuite du score de vente CBOT (étape 7)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.indicator import cbot_sale_score as sale
from mais.indicator import cbot_sale_score_features as feats
from mais.indicator import cbot_sale_score_model as mdl


def test_target_dates_use_market_rows_not_calendar_days():
    """La cible H40/H90 doit utiliser la vraie ligne i+h, pas date + h jours calendaires."""
    idx = pd.bdate_range("2010-01-04", periods=300)  # ~252 séances/an
    h = 90
    tgt = feats.target_dates_from_index(idx, h)
    # ligne de marché : exactement index[i+h]
    assert tgt.iloc[0] == idx[h]
    # et c'est BIEN différent de l'approximation calendaire (qui sous-estime)
    cal = idx[0] + pd.to_timedelta(h, "D")
    assert tgt.iloc[0] > cal           # h séances >> h jours calendaires
    # les h dernières lignes n'ont pas de cible
    assert tgt.iloc[-1] is pd.NaT or pd.isna(tgt.iloc[-1])


def test_direction_target_is_forward_sign():
    px = pd.Series([100, 101, 102, 103, 104.0],
                   index=pd.bdate_range("2020-01-01", periods=5))
    y = feats.direction_target(px, 1)
    assert y.iloc[0] == 1.0            # hausse
    assert pd.isna(y.iloc[-1])         # pas de futur


def test_holdout_2024_not_in_training():
    """Aucune ligne de décision OU de cible >= 2024-01-01 dans le train du modèle final."""
    df, _ = feats.build_frame()
    cfg = sale.load_config()
    hs = pd.Timestamp(cfg["holdout_start"])
    cols = cfg["features"]["h90"]
    mask = mdl._train_mask(df, 90, hs, cols)
    train_idx = df.index[mask]
    assert (train_idx < hs).all()                       # décision < holdout
    tgt = feats.target_dates_from_index(df.index, 90)[mask]
    assert (tgt < hs).all()                             # cible < holdout (purge)


def test_har_vol_training_excludes_2024_targets():
    """Aucune cible de volatilité future utilisée en train HAR ne tombe en 2024+ (purge)."""
    df, _ = feats.build_frame()
    cfg = sale.load_config()
    hs = pd.Timestamp(cfg["holdout_start"])
    for h in (40, 90):
        mask = mdl.har_train_mask(df, h, hs)
        tgt = feats.target_dates_from_index(df.index, h)[mask]
        assert (df.index[mask] < hs).all()          # décision < holdout
        assert (tgt < hs).all()                      # vraie date de la vol future < holdout


def test_expanding_transforms_use_past_only():
    """z-score expandant : la 1re valeur est NaN (shift(1)), aucune fuite du présent."""
    s = pd.Series(np.arange(50.0))
    z = feats._expanding_z(s, min_periods=12)
    assert pd.isna(z.iloc[0])
    # la valeur en i n'utilise que <= i-1
    assert pd.isna(z.iloc[:12]).all()


def test_only_allowed_features_in_score_models():
    """Les modèles directionnels du score n'utilisent que les variables autorisées."""
    cfg = sale.load_config()
    allowed = set(sum(cfg["features"].values(), []))
    df, _ = feats.build_frame()
    models = sale.build_models(df, cfg)
    assert set(models.h40.cols) <= allowed
    assert set(models.h90.cols) <= allowed
    # aucune famille rejetée
    forbidden = {"cot", "ethanol", "weather", "trend", "stack", "basis", "egarch_implied"}
    for c in models.h40.cols + models.h90.cols:
        assert not any(f in c.lower() for f in forbidden)
