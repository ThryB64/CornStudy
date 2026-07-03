"""Features stationnaires P2 (étape 5) : WASDE état de bilan + Crop Condition.

Les niveaux bruts WASDE avaient dégradé le RMSE (étape 4) car non-stationnaires.
Ici on n'expose QUE des encodages stationnaires, tous train-only (z/percentile/
seuils expandants). Crop Condition : anomalies par semaine de campagne, variations,
écarts à la moyenne passée. Anti-fuite : WASDE via vintage EXT026 (publication+1BD) ;
crop condition disponible mardi (publication NASS lundi).
"""
from __future__ import annotations

import pandas as pd
import series_utils as S
import wasde_utils as WU
from ext_harness import DATA


def wasde_stationary() -> tuple[pd.DataFrame, dict]:
    w = WU.load_vintage().sort_values("available_from").reset_index(drop=True)
    s2u = w["stocks_to_use_ratio"]
    ev = pd.DataFrame(index=pd.to_datetime(w["available_from"]))
    ev["s2u"] = s2u.to_numpy()
    ev["s2u_z"] = S.expanding_z(s2u, min_periods=12).to_numpy()
    pct = S.expanding_pctile(s2u, min_periods=12)
    ev["s2u_pctile"] = pct.to_numpy()
    ev["s2u_slow_chg"] = s2u.diff(3).to_numpy()        # variation lente (3 rapports)
    ev["s2u_yoy"] = s2u.diff(12).to_numpy()            # variation annuelle (~12 rapports)
    ev["s2u_dev_hist"] = (s2u - s2u.expanding(min_periods=12).mean().shift(1)).to_numpy()
    ev["bilan_tight"] = (pct < 0.33).astype(float).to_numpy()   # stocks bas = tendu
    ev["bilan_loose"] = (pct > 0.66).astype(float).to_numpy()
    feats = S.daily_ffill(ev[~ev.index.duplicated(keep="last")])
    fdict = {
        "s2u": "Stocks-to-use ratio WASDE (ratio ~stationnaire)",
        "s2u_z": "z-score expandant du stocks-to-use",
        "s2u_pctile": "Percentile expandant du stocks-to-use",
        "s2u_slow_chg": "Variation lente du bilan (3 rapports)",
        "s2u_yoy": "Variation annuelle du bilan (~12 rapports)",
        "s2u_dev_hist": "Écart du stocks-to-use à sa moyenne passée",
        "bilan_tight": "Bilan tendu (percentile s2u < 0.33) = haussier",
        "bilan_loose": "Bilan large (percentile s2u > 0.66) = baissier",
    }
    return feats, fdict


def crop_stationary() -> tuple[pd.DataFrame, dict]:
    cp = pd.read_parquet(DATA / "raw" / "usda_nass_crop_condition" / "crop_progress.parquet")
    cp["Date"] = pd.to_datetime(cp["Date"])
    cp = cp.sort_values("Date").set_index("Date")
    cp = cp[cp.index.year >= 1995]
    f = pd.DataFrame(index=cp.index)
    f["cond_gd_ex"] = cp["condition_gd_ex_pct"]
    f["cond_poor_vp"] = cp["condition_poor_vp_pct"]
    f["cond_gd_ex_chg"] = cp["condition_gd_ex_pct"].diff()
    f["cond_gd_ex_anom"] = S.weekofyear_anom(cp["condition_gd_ex_pct"])
    f["cond_dev5y"] = cp["condition_gd_ex_pct"] - \
        cp["condition_gd_ex_pct"].rolling(52 * 5, min_periods=52).mean().shift(1)
    f["progress_gap_5y"] = cp["progress_gap_5y"]
    f["silking_pct"] = cp["silking_pct"]
    f["harvested_pct"] = cp["harvested_pct"]
    f.index = f.index + pd.Timedelta(days=2)   # publication lundi -> dispo mardi
    feats = S.daily_ffill(f)
    fdict = {
        "cond_gd_ex": "Condition good+excellent (%)",
        "cond_poor_vp": "Condition poor+very poor (%)",
        "cond_gd_ex_chg": "Variation hebdo good+excellent",
        "cond_gd_ex_anom": "Anomalie z good+excellent vs climatologie par semaine",
        "cond_dev5y": "Écart good+excellent vs moyenne 5 ans (passé)",
        "progress_gap_5y": "Écart d'avancement vs moyenne 5 ans",
        "silking_pct": "Avancement floraison", "harvested_pct": "Avancement récolte",
    }
    return feats, fdict


def build_p2_dataset() -> tuple[pd.DataFrame, dict, dict, dict]:
    """Retourne (df_features_quotidiennes, wasde_cols, crop_cols, feature_dict).
    NB : df indexé daily complet ; le harnais le reindexe sur le calendrier marché."""
    wf, wd = wasde_stationary()
    cf, cd = crop_stationary()
    df = wf.join(cf, how="outer").sort_index().ffill()
    fdict = {**wd, **cd}
    return df, list(wf.columns), list(cf.columns), fdict
