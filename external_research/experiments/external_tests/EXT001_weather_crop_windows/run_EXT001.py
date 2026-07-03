"""EXT001 — Meteo agregee par fenetres agronomiques du mais.

Hypothese : la meteo est plus informative agregee par stade phenologique
(semis, vegetatif, pollinisation, remplissage, recolte) qu'en brut.
Approximation conservatrice par mois (dates par Etat non disponibles) :
avril-mai=semis, juin=vegetatif, juillet=pollinisation (stress critique),
aout=remplissage, sept-oct=recolte.

Features = anomalies standardisees (climatologie expandante, annees passees
seulement) des cumuls saison-a-date ponderes production par fenetre.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_common"))
import ext_harness as H  # noqa: E402
import wx_utils as W  # noqa: E402

EXP = "EXT001"
DIRN = "EXT001_weather_crop_windows"

WINDOWS = {
    "planting": [4, 5],
    "vegetative": [6],
    "pollination": [7],
    "fill": [8],
    "harvest": [9, 10],
}


def build_features():
    wx = W.national_weather()
    gdd = wx["gdd_base10"]
    prcp = wx["prcp_mm"]
    heat = (wx["tmax_c"] > 32).astype(float)  # jour de chaleur agronomique

    feats = {}
    fdict = {}
    for name, months in WINDOWS.items():
        gdd_std = W.season_to_date_sum(gdd, months)
        prcp_std = W.season_to_date_sum(prcp, months)
        feats[f"gdd_anom_{name}"] = W.doy_anomaly_z(gdd_std)
        feats[f"prcp_anom_{name}"] = W.doy_anomaly_z(prcp_std)
        fdict[f"gdd_anom_{name}"] = f"Anomalie z du cumul GDD saison-a-date, fenetre {name} ({months})"
        fdict[f"prcp_anom_{name}"] = f"Anomalie z du cumul precip saison-a-date, fenetre {name} ({months})"
        if name == "pollination":
            heat_std = W.season_to_date_sum(heat, months)
            feats[f"heat_anom_{name}"] = W.doy_anomaly_z(heat_std)
            fdict[f"heat_anom_{name}"] = "Anomalie z des jours tmax>32C cumules en pollinisation (juillet)"
    import pandas as pd
    df = pd.DataFrame(feats)
    return df, list(df.columns), fdict


def main():
    feats, cols, fdict = build_features()
    met = H.evaluate_family(EXP, DIRN, feats, cols, feature_dictionary=fdict)
    print(met[met.model == "DELTA"][["horizon", "rmse_pct", "da", "dm_pvalue", "n"]].to_string())
    print("verdict harness:", H.verdict_from_delta(met))


if __name__ == "__main__":
    main()
