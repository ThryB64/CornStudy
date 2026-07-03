"""EXT018 — Prime de risque meteo new-crop (PARTIAL_DATA).

Contrats decembre CBOT absents -> approximation par la serie continue +
saisonnalite, conditionnee par les stocks (WASDE) et le stress meteo d'ete.
Volet 1 (descriptif, type Janzen) : trajectoire du retour pre-recolte par mois,
annees de stress vs normales (classement ex ante). Volet 2 (conditionnel) :
features prime passees au harnais commun.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_common"))
import ext_harness as H  # noqa: E402
import series_utils as S  # noqa: E402
import wasde_utils as WU  # noqa: E402
import wx_utils as W  # noqa: E402

EXP, DIRN = "EXT018", "EXT018_weather_risk_premium_new_crop"


def build_features():
    mkt = H.load_market()
    idx = mkt.index
    month = idx.month.to_numpy()
    # phase pre-recolte (avr-aout) : la prime meteo est censee se dissiper vers la recolte
    preharvest = ((month >= 4) & (month <= 8)).astype(float)

    # stress meteo d'ete : anomalie de jours canicule cumules en juillet (pollinisation)
    wx = W.national_weather()
    heatwave = (wx["tmax_c"] > 35).astype(float)
    july_stress = W.doy_anomaly_z(W.season_to_date_sum(heatwave, [7])).reindex(idx)

    # stocks-to-use (WASDE vintage, available_from) : faible = marche tendu = prime forte
    wfeats, _ = WU.release_features()
    s2u = wfeats["wasde_stocks_to_use_ratio"].reindex(idx).ffill()
    s2u_tight = -S.expanding_z(s2u.dropna()).reindex(idx)  # tension = -z(stocks)

    f = pd.DataFrame(index=idx)
    f["preharvest_flag"] = preharvest
    f["july_heat_stress"] = july_stress
    f["stocks_tightness"] = s2u_tight
    f["premium_pressure"] = preharvest * july_stress.fillna(0) * s2u_tight.fillna(0)
    fdict = {
        "preharvest_flag": "Phase pre-recolte (avr-aout) ou la prime meteo se dissipe",
        "july_heat_stress": "Anomalie z des jours canicule de juillet (stress pollinisation)",
        "stocks_tightness": "Tension de bilan = -z(stocks-to-use) WASDE",
        "premium_pressure": "Interaction pre-recolte x stress x tension (proxy prime new-crop)",
    }
    return f, list(f.columns), fdict


def descriptive_premium(out: Path):
    """Volet Janzen : retour forward 90j moyen par mois, stress vs normal."""
    mkt = H.load_market()
    logp = np.log(mkt["corn_close"])
    fwd90 = logp.shift(-90) - logp
    df = pd.DataFrame({"fwd90": fwd90})
    df["month"] = df.index.month
    df["year"] = df.index.year

    # classement ex ante des annees de stress : anomalie canicule juillet (info de l'ete meme)
    wx = W.national_weather()
    hw = (wx["tmax_c"] > 35).astype(float)
    jul = hw[hw.index.month == 7].groupby(hw[hw.index.month == 7].index.year).sum()
    stress_years = set(jul[jul > jul.median()].index)
    df["stress"] = df["year"].isin(stress_years)

    pre = df[(df.month >= 4) & (df.month <= 9) & (df.index.year < 2024)]
    g = pre.groupby(["month", "stress"])["fwd90"].mean().unstack()
    g.columns = ["normal_year", "stress_year"]
    g.to_csv(out / "premium_seasonal_descriptive.csv")
    return g


def main():
    out = H.RESULTS / DIRN
    out.mkdir(parents=True, exist_ok=True)
    feats, cols, fdict = build_features()
    feats.dropna(how="all").to_csv(out / "weather_risk_premium_features.csv")
    desc = descriptive_premium(out)
    print("Retour forward 90j moyen par mois (pre-recolte), stress vs normal:")
    print(desc.to_string())
    met = H.evaluate_family(EXP, DIRN, feats, cols, feature_dictionary=fdict)
    print(met[met.model == "DELTA"][["horizon", "rmse_pct", "da", "dm_pvalue", "n"]].to_string())
    print("verdict harness:", H.verdict_from_delta(met))


if __name__ == "__main__":
    main()
