"""Score de vente / direction / risque CBOT (étape 7 — orchestrateur).

Compose les briques validées en un score d'**aide à la décision de commercialisation**
H40-H90. **Ne prédit pas le prix.** Sorties possibles : SELL_PARTIAL, WAIT, WATCH,
RISK_HIGH, NO_SIGNAL (jamais BUY, jamais de short). Tout est entraîné sur ≤2023 ; le score
s'applique ensuite à toute la chronologie (y compris le holdout 2024+, évalué une seule fois
ailleurs). Logique simple, explicable, documentée.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from mais.indicator import cbot_sale_score_features as feats
from mais.indicator import cbot_sale_score_model as mdl
from mais.paths import PROJECT_ROOT
from mais.utils import get_logger, load_yaml

log = get_logger("mais.indicator.cbot_sale_score")

CONFIG_PATH = PROJECT_ROOT / "config" / "cbot_sale_score.yaml"
RECOMMENDATIONS = ("SELL_PARTIAL", "WAIT", "WATCH", "RISK_HIGH", "NO_SIGNAL")

MARKET_BASELINE_COLS = ["base_ret_5d", "base_ret_20d", "base_vol_20", "base_sin", "base_cos"]


def load_config() -> dict:
    return load_yaml(CONFIG_PATH)


@dataclass
class SaleScoreModels:
    cfg: dict
    h40: mdl.FittedLogit
    h90: mdl.FittedLogit
    pred_vol: pd.Series
    vol_gate: float
    baselines: dict          # name -> (FittedLogit | "base_rate", horizon)


def build_models(df: pd.DataFrame, cfg: dict) -> SaleScoreModels:
    hs = pd.Timestamp(cfg["holdout_start"])
    c = float(cfg.get("logit_C", 1.0))
    h40, h90 = cfg["horizons"]["direction_h40"], cfg["horizons"]["direction_h90"]
    m40 = mdl.fit_logit(df, cfg["features"]["h40"], h40, hs, c)
    m90 = mdl.fit_logit(df, cfg["features"]["h90"], h90, hs, c)
    pred_vol = mdl.har_vol_forecast(df, h90, hs)
    gate = mdl.frozen_vol_gate(pred_vol, hs, cfg["rules"]["risk_high_vol_decile"])
    baselines = {
        "season_only_h90": (mdl.fit_logit(df, feats.BASE_COLS, h90, hs, c), h90),
        "crop_only_h90": (mdl.fit_logit(df, [x for x in cfg["features"]["h90"]
                                            if x not in feats.BASE_COLS], h90, hs, c), h90),
        "wasde_only_h40": (mdl.fit_logit(df, [x for x in cfg["features"]["h40"]
                                             if x not in feats.BASE_COLS], h40, hs, c), h40),
        "market_only_h90": (mdl.fit_logit(df, MARKET_BASELINE_COLS, h90, hs, c), h90),
        "random_walk_h90": ("base_rate", h90),
    }
    return SaleScoreModels(cfg, m40, m90, pred_vol, gate, baselines)


def _confidence(row: pd.Series, cfg: dict) -> float:
    """Confiance 0-1 : cohérence H40/H90, régime favorable, vol non extrême.

    Les régimes (post-hoc) ne modulent QUE la confiance, jamais la direction.
    """
    conf = 0.5
    pd40, pd90 = row["p_down_h40"], row["p_down_h90"]
    if np.isfinite(pd40) and np.isfinite(pd90):
        conf += 0.15 if (pd40 - 0.5) * (pd90 - 0.5) > 0 else -0.15   # cohérence
    if row.get("regime_low_vol", 0) == 1:
        conf += 0.10
    if row.get("regime_bilan_extreme", 0) == 1:
        conf += 0.10
    if row.get("regime_uptrend", 0) == 1:
        conf += 0.05
    if row.get("vol_filter_high_decile", 0) == 1:
        conf -= 0.20
    return float(np.clip(conf, 0.0, 1.0))


def _recommend(row: pd.Series, cfg: dict) -> str:
    r = cfg["rules"]
    if not np.isfinite(row["p_down_h90"]):
        return "NO_SIGNAL"
    if row.get("vol_filter_high_decile", 0) == 1:
        return "RISK_HIGH"
    if row["p_down_h90"] >= r["sell_partial_threshold"] and \
            row["confidence"] >= r["min_confidence"]:
        return "SELL_PARTIAL"
    if (1.0 - row["p_down_h90"]) >= r["wait_threshold"]:
        return "WAIT"
    return "WATCH"


def score_timeseries(df: pd.DataFrame, models: SaleScoreModels) -> pd.DataFrame:
    cfg = models.cfg
    out = pd.DataFrame(index=df.index)
    out["corn_close"] = df["corn_close"]
    out["prob_up_h40"] = models.h40.predict_proba_up(df)
    out["prob_up_h90"] = models.h90.predict_proba_up(df)
    # features manquantes => pas de signal (NaN propagé)
    miss40 = df[models.h40.cols].isna().any(axis=1)
    miss90 = df[models.h90.cols].isna().any(axis=1)
    out.loc[miss40, "prob_up_h40"] = np.nan
    out.loc[miss90, "prob_up_h90"] = np.nan
    out["p_down_h40"] = 1.0 - out["prob_up_h40"]
    out["p_down_h90"] = 1.0 - out["prob_up_h90"]
    out["pred_vol_h90"] = models.pred_vol
    out["vol_gate"] = models.vol_gate
    out["vol_filter_high_decile"] = (models.pred_vol >= models.vol_gate).astype(float)
    for rc in cfg["features"]["regimes"]:
        out[rc] = df[rc]
    out["confidence"] = out.apply(lambda r: _confidence(r, cfg), axis=1)
    out["recommendation"] = out.apply(lambda r: _recommend(r, cfg), axis=1)
    return out


def latest_record(frame: pd.DataFrame, cfg: dict) -> dict:
    row = frame.dropna(subset=["prob_up_h90"]).iloc[-1]
    return {
        "version": cfg["version"],
        "price_forecast_enabled": bool(cfg.get("price_forecast_enabled", False)),
        "as_of": str(frame.index[-1].date()),
        "signal_date": str(row.name.date()),
        "corn_close": float(row["corn_close"]),
        "recommendation": row["recommendation"],
        "prob_up_h40": round(float(row["prob_up_h40"]), 4),
        "prob_up_h90": round(float(row["prob_up_h90"]), 4),
        "p_down_h90": round(float(row["p_down_h90"]), 4),
        "pred_vol_h90": round(float(row["pred_vol_h90"]), 6),
        "vol_high_decile": bool(row["vol_filter_high_decile"]),
        "confidence": round(float(row["confidence"]), 3),
        "note": "Aide a la decision de vente. PAS une prevision de prix ni un bot de trading.",
    }
