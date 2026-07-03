"""EXT020 — Evenements meteo extremes (vs moyennes simples).

Indicateurs : jours de canicule (tmax>35C), sequences consecutives de chaleur,
sequences consecutives sans pluie, exces de pluie, stress canicule pendant
pollinisation (juillet) et remplissage (aout). National pondere production,
realise decale J+1, climatologie expandante.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_common"))
import ext_harness as H  # noqa: E402
import wx_utils as W  # noqa: E402

EXP = "EXT020"
DIRN = "EXT020_extreme_weather_events"


def run_length(flag: pd.Series) -> pd.Series:
    """Longueur de la sequence consecutive en cours (jusqu'a aujourd'hui)."""
    f = flag.fillna(0).to_numpy()
    out = np.zeros(len(f))
    run = 0
    for i, v in enumerate(f):
        run = run + 1 if v > 0 else 0
        out[i] = run
    return pd.Series(out, index=flag.index)


def build_features():
    wx = W.national_weather()
    tmax = wx["tmax_c"]
    prcp = wx["prcp_mm"]

    heatwave = (tmax > 35).astype(float)          # canicule
    hot = (tmax > 32).astype(float)
    dry = (prcp < 1.0).astype(float)
    wet = (prcp > 25).astype(float)

    feats, fdict = {}, {}
    # sequences consecutives en cours
    feats["heat_streak"] = run_length(hot)
    feats["dry_streak"] = run_length(dry)
    fdict["heat_streak"] = "Longueur de la sequence consecutive de jours tmax>32C en cours"
    fdict["dry_streak"] = "Longueur de la sequence consecutive de jours prcp<1mm en cours"

    # canicule saison-a-date (anomalie) globale et par stade
    hw_year = W.season_to_date_sum(heatwave, list(range(1, 13)))
    feats["heatwave_anom_ytd"] = W.doy_anomaly_z(hw_year)
    fdict["heatwave_anom_ytd"] = "Anomalie z des jours canicule (tmax>35C) cumules dans l'annee"

    hw_poll = W.season_to_date_sum(heatwave, [7])
    feats["heatwave_anom_pollination"] = W.doy_anomaly_z(hw_poll)
    fdict["heatwave_anom_pollination"] = "Anomalie z des jours canicule cumules en juillet (pollinisation)"

    hw_fill = W.season_to_date_sum(heatwave, [8])
    feats["heatwave_anom_fill"] = W.doy_anomaly_z(hw_fill)
    fdict["heatwave_anom_fill"] = "Anomalie z des jours canicule cumules en aout (remplissage)"

    dry_poll = W.season_to_date_sum(dry, [7])
    feats["dry_anom_pollination"] = W.doy_anomaly_z(dry_poll)
    fdict["dry_anom_pollination"] = "Anomalie z des jours secs cumules en juillet (stress hydrique pollinisation)"

    wet_year = W.season_to_date_sum(wet, list(range(4, 11)))
    feats["wet_excess_anom"] = W.doy_anomaly_z(wet_year)
    fdict["wet_excess_anom"] = "Anomalie z des jours d'exces de pluie (prcp>25mm) cumules avr-oct"

    df = pd.DataFrame(feats)
    return df, list(df.columns), fdict


def main():
    feats, cols, fdict = build_features()
    met = H.evaluate_family(EXP, DIRN, feats, cols, feature_dictionary=fdict)
    print(met[met.model == "DELTA"][["horizon", "rmse_pct", "da", "dm_pvalue", "n"]].to_string())
    print("verdict harness:", H.verdict_from_delta(met))


if __name__ == "__main__":
    main()
