"""Indicateur Euronext — construction du dataset aligné (étape de visualisation).

On applique le **score de vente CBOT** (étude finale, verdict FRAGILE) à l'historique de prix
**Euronext** (EMA, série continue back-adjusted ; cf. `docs/EURONEXT_DATA_AUDIT.md`, ~97 %
proxy). Le score (direction/risque/confiance) vient des fondamentaux US (Crop Condition, WASDE
stocks-to-use, saison, volatilité, régimes) ; on l'aligne sur le calendrier Euronext par
`merge_asof` **backward** (chaque date Euronext n'utilise que l'info CBOT ≤ cette date) et on
évalue contre les **retours futurs Euronext**. Anti-fuite : les `target_return_*` Euronext ne
servent QU'À l'évaluation, jamais au calcul du score ; `target_date[i] = index[i+h]` (vraie
ligne de marché, jamais `date + h jours`).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.indicator import cbot_sale_score as sale
from mais.indicator import cbot_sale_score_features as cfeat
from mais.indicator import cbot_sale_score_model as cmodel
from mais.paths import PROJECT_ROOT
from mais.utils import load_yaml

CONFIG_PATH = PROJECT_ROOT / "config" / "euronext_indicator.yaml"
RECOMMENDATIONS = ("SELL_PARTIAL", "WAIT", "WATCH", "RISK_HIGH", "NO_SIGNAL")


def load_config() -> dict:
    return load_yaml(CONFIG_PATH)


def target_dates_from_shift(index: pd.DatetimeIndex, h: int) -> pd.Series:
    """Vraie date de la cible : index[i+h] (lignes de marché), PAS date + h jours calendaires."""
    return pd.Series(index, index=index).shift(-h)


def load_euronext_price(cfg: dict) -> pd.DataFrame:
    df = pd.read_parquet(PROJECT_ROOT / cfg["euronext_price_parquet"])
    dcol, pcol = cfg["euronext_date_col"], cfg["euronext_price_col"]
    out = pd.DataFrame({"euronext_price": df[pcol].astype(float).to_numpy()},
                       index=pd.to_datetime(df[dcol]))
    if "source_quality" in df.columns:
        out["source_quality"] = df["source_quality"].to_numpy()
    out = out[~out.index.duplicated(keep="last")].sort_index()
    return out


def forward_logret(price: pd.Series, h: int) -> pd.Series:
    logp = np.log(price)
    return logp.shift(-h) - logp


def forward_direction(price: pd.Series, h: int) -> pd.Series:
    fwd = forward_logret(price, h)
    return (fwd > 0).astype(float).where(fwd.notna())


def _vol_risk_score(pred_vol: pd.Series, holdout_start: pd.Timestamp) -> pd.Series:
    """Percentile de la vol prévue vs distribution ≤2023 (gelée, anti-fuite). 0-1."""
    pre = np.sort(pred_vol[pred_vol.index < holdout_start].dropna().to_numpy())
    rank = np.searchsorted(pre, pred_vol.to_numpy(), side="right") / max(len(pre), 1)
    return pd.Series(np.clip(rank, 0, 1), index=pred_vol.index)


def build_cbot_scores() -> tuple[pd.DataFrame, dict]:
    """Score CBOT + sous-scores composants, sur le calendrier marché CBOT."""
    cfg_c = sale.load_config()
    df, _fd = cfeat.build_frame()
    models = sale.build_models(df, cfg_c)
    frame = sale.score_timeseries(df, models)
    hs = pd.Timestamp(cfg_c["holdout_start"])

    wasde_only = models.baselines["wasde_only_h40"][0].predict_proba_up(df)
    crop_only = models.baselines["crop_only_h90"][0].predict_proba_up(df)

    out = pd.DataFrame(index=frame.index)
    out["cbot_price"] = frame["corn_close"]
    out["direction_score_h40"] = 2 * frame["prob_up_h40"] - 1
    out["direction_score_h90"] = 2 * frame["prob_up_h90"] - 1
    out["downside_risk_h90"] = frame["p_down_h90"]
    out["wasde_balance_score"] = wasde_only
    out["crop_condition_score"] = crop_only
    out["volatility_risk_score"] = _vol_risk_score(frame["pred_vol_h90"], hs)
    out["vol_high_decile"] = frame["vol_filter_high_decile"]
    out["market_regime_score"] = frame[["regime_low_vol", "regime_bilan_extreme",
                                        "regime_uptrend"]].mean(axis=1)
    out["confidence_score"] = frame["confidence"]
    out["final_sale_score"] = frame["p_down_h90"]    # pression de vente = P(baisse) H90
    return out, _coef_doc(models)


def _coef_doc(models) -> dict:
    d = {}
    for tag, fit in (("h90_crop", models.h90), ("h40_wasde", models.h40)):
        d[tag] = dict(zip(fit.cols, np.round(fit.coef, 4), strict=False))
    return d


def _recommend_row(p_down90: float, conf: float, vol_high: float, th: dict) -> str:
    if not np.isfinite(p_down90):
        return "NO_SIGNAL"
    if vol_high == 1:
        return "RISK_HIGH"
    if p_down90 >= th["sell_partial_downside_h90"] and conf >= th["min_confidence"]:
        return "SELL_PARTIAL"
    if (1.0 - p_down90) >= th["wait_upside_h90"]:
        return "WAIT"
    return "WATCH"


def build_indicator_frame(cfg: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """Historique aligné : prix Euronext + scores CBOT + retours/directions futurs Euronext."""
    cfg = cfg or load_config()
    th = cfg["thresholds"]
    eur = load_euronext_price(cfg)
    cbot, coefs = build_cbot_scores()

    # alignement anti-fuite : pour chaque date Euronext, dernier score CBOT <= cette date
    cbot_last = cbot.index.max()
    e = eur.copy()
    e.index.name = "date"
    e = e.reset_index()
    c = cbot.copy()
    c.index.name = "date"
    c = c.reset_index()
    c["cbot_score_date"] = c["date"]
    out = pd.merge_asof(e, c, on="date", direction="backward").set_index("date")
    # le score CBOT n'est plus mis à jour au-delà de la fin des données CBOT : on le signale
    out["score_stale"] = (out.index > cbot_last).astype(int)

    # recommandation (seuils Euronext, sur les scores CBOT)
    out["recommendation"] = [
        _recommend_row(p, c, v, th)
        for p, c, v in zip(out["downside_risk_h90"], out["confidence_score"],
                           out["vol_high_decile"].fillna(0), strict=False)]

    # retours/directions FUTURS Euronext (évaluation seulement) + vraies target_date
    px = out["euronext_price"]
    for h in (cfg["horizons"]["h20"], cfg["horizons"]["h40"], cfg["horizons"]["h90"]):
        out[f"target_return_h{h}_euronext"] = forward_logret(px, h)
        out[f"target_direction_h{h}_euronext"] = forward_direction(px, h)
        out[f"target_date_h{h}"] = target_dates_from_shift(out.index, h).to_numpy()
    return out, coefs


FEATURE_DICTIONARY = {
    "euronext_price": "Prix Euronext EMA continu back-adjusted (€/t ; ~97% proxy)",
    "cbot_price": "Prix CBOT continu (¢/bu) ayant servi au score",
    "source_quality": "Qualité de la source Euronext (exploratory=proxy / official_or_manual)",
    "direction_score_h40": "2*P(hausse H40)-1 ; >0 hausse plus probable (WASDE)",
    "direction_score_h90": "2*P(hausse H90)-1 ; >0 hausse plus probable (Crop)",
    "downside_risk_h90": "P(baisse) du CBOT à H90 (cœur du signal de vente)",
    "wasde_balance_score": "P(hausse) d'un modèle WASDE stocks-to-use seul (H40)",
    "crop_condition_score": "P(hausse) d'un modèle Crop Condition seul (H90)",
    "volatility_risk_score": "Percentile (gelé ≤2023) de la vol prévue HAR ; haut = risque",
    "vol_high_decile": "Vol prévue dans le décile haut (gate de risque)",
    "market_regime_score": "Moyenne des régimes favorables (low_vol/bilan extrême/uptrend)",
    "confidence_score": "Confiance 0-1 (cohérence H40/H90, régime, vol)",
    "final_sale_score": "Score global de pression de vente = P(baisse) H90",
    "recommendation": "SELL_PARTIAL / WAIT / WATCH / RISK_HIGH / NO_SIGNAL (jamais BUY/SHORT)",
    "cbot_score_date": "Date du score CBOT aligné (≤ date Euronext, anti-fuite)",
    "score_stale": "1 si la date Euronext dépasse la fin des données CBOT (score figé, non à jour)",
    "target_return_h20_euronext": "Log-retour Euronext futur H20 (évaluation seulement)",
    "target_return_h40_euronext": "Log-retour Euronext futur H40 (évaluation seulement)",
    "target_return_h90_euronext": "Log-retour Euronext futur H90 (évaluation seulement)",
    "target_direction_h20_euronext": "Signe du retour Euronext H20 (1=hausse)",
    "target_direction_h40_euronext": "Signe du retour Euronext H40 (1=hausse)",
    "target_direction_h90_euronext": "Signe du retour Euronext H90 (1=hausse)",
    "target_date_h20": "Vraie date de marché à i+20 (Euronext)",
    "target_date_h40": "Vraie date de marché à i+40 (Euronext)",
    "target_date_h90": "Vraie date de marché à i+90 (Euronext)",
}


def dir_metrics(y_true, prob_up, thr: float = 0.5) -> dict:
    return cmodel.dir_metrics(np.asarray(y_true, float), np.asarray(prob_up, float), thr)
