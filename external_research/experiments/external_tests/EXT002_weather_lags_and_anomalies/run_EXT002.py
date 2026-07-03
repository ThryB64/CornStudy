"""EXT002 — Lags et anomalies meteo sur fenetres glissantes.

Rolling 7/14/30/60/90 jours sur temperature et precipitations nationales
ponderees production, converti en anomalies standardisees (climatologie
expandante par day-of-year, annees passees seulement). Stress thermique et
deficit/exces de pluie inclus. Toutes les fenetres n'utilisent que le passe
(rolling) + decalage J+1 (wx_utils).
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_common"))
import ext_harness as H  # noqa: E402
import wx_utils as W  # noqa: E402

EXP = "EXT002"
DIRN = "EXT002_weather_lags_and_anomalies"
WINS = [7, 14, 30, 60, 90]


def build_features():
    wx = W.national_weather()
    tavg = wx["tavg_c"]
    prcp = wx["prcp_mm"]
    heat = (wx["tmax_c"] > 32).astype(float)

    feats, fdict = {}, {}
    for w in WINS:
        t_roll = tavg.rolling(w, min_periods=max(3, w // 2)).mean()
        p_roll = prcp.rolling(w, min_periods=max(3, w // 2)).sum()
        feats[f"tavg_anom_{w}"] = W.doy_anomaly_z(t_roll)
        feats[f"prcp_anom_{w}"] = W.doy_anomaly_z(p_roll)
        fdict[f"tavg_anom_{w}"] = f"Anomalie z de la temperature moyenne glissante {w}j"
        fdict[f"prcp_anom_{w}"] = f"Anomalie z du cumul de pluie glissant {w}j (deficit<0 / exces>0)"
    h30 = heat.rolling(30, min_periods=15).sum()
    feats["heat30_anom"] = W.doy_anomaly_z(h30)
    fdict["heat30_anom"] = "Anomalie z du nombre de jours tmax>32C sur 30j (stress thermique)"

    df = pd.DataFrame(feats)
    return df, list(df.columns), fdict


def main():
    feats, cols, fdict = build_features()
    # sorties additionnelles demandees par le ticket
    out = H.RESULTS / DIRN
    out.mkdir(parents=True, exist_ok=True)
    lag_cols = [c for c in cols if c.startswith("tavg") or c.startswith("prcp")]
    feats[lag_cols].dropna(how="all").to_csv(out / "weather_lags_features.csv")
    feats[[c for c in cols if "anom" in c]].dropna(how="all").to_csv(
        out / "weather_anomalies_features.csv")
    met = H.evaluate_family(EXP, DIRN, feats, cols, feature_dictionary=fdict)
    print(met[met.model == "DELTA"][["horizon", "rmse_pct", "da", "dm_pvalue", "n"]].to_string())
    print("verdict harness:", H.verdict_from_delta(met))


if __name__ == "__main__":
    main()
