"""EXT019 — Features USDA Crop Progress / Crop Condition.

Source : data/raw/usda_nass_crop_condition/crop_progress.parquet (hebdo, dimanche
= semaine finissante). Publication NASS lundi ~16h ET -> disponible mardi
(available = Date + 2 jours). Climatologie par semaine de l'annee, annees passees
seulement. Cible : log-retour CBOT t->t+h.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_common"))
import ext_harness as H  # noqa: E402
import series_utils as S  # noqa: E402

EXP, DIRN = "EXT019", "EXT019_crop_condition_report_features"


def build_features():
    cp = pd.read_parquet(H.DATA / "raw" / "usda_nass_crop_condition" / "crop_progress.parquet")
    cp["Date"] = pd.to_datetime(cp["Date"])
    cp = cp.sort_values("Date").set_index("Date")
    cp = cp[cp.index.year >= 1995]  # historique suffisant pour climatologie

    f = pd.DataFrame(index=cp.index)
    f["cond_gd_ex"] = cp["condition_gd_ex_pct"]
    f["cond_poor_vp"] = cp["condition_poor_vp_pct"]
    f["cond_gd_ex_chg"] = cp["condition_gd_ex_pct"].diff()
    f["cond_gd_ex_anom"] = S.weekofyear_anom(cp["condition_gd_ex_pct"])
    # surprise = variation hebdo - variation hebdo attendue (climatologie expandante)
    exp_chg = S.weekofyear_anom(cp["condition_gd_ex_pct"].diff())
    f["cond_surprise"] = exp_chg
    f["progress_gap_5y"] = cp["progress_gap_5y"]
    f["silking_pct"] = cp["silking_pct"]
    f["harvested_pct"] = cp["harvested_pct"]

    fdict = {
        "cond_gd_ex": "Niveau condition good+excellent (%)",
        "cond_poor_vp": "Niveau condition poor+very poor (%)",
        "cond_gd_ex_chg": "Variation hebdo de good+excellent",
        "cond_gd_ex_anom": "Anomalie z de good+excellent vs climatologie par semaine",
        "cond_surprise": "Surprise = variation hebdo vs variation attendue (climatologie)",
        "progress_gap_5y": "Ecart d'avancement vs moyenne 5 ans",
        "silking_pct": "Pourcentage en floraison (silking)",
        "harvested_pct": "Pourcentage recolte",
    }
    # disponibilite mardi = Date(dimanche) + 2 jours
    f.index = f.index + pd.Timedelta(days=2)
    feats = S.daily_ffill(f)
    return feats, list(feats.columns), fdict


def main():
    feats, cols, fdict = build_features()
    out = H.RESULTS / DIRN
    out.mkdir(parents=True, exist_ok=True)
    feats.dropna(how="all").to_csv(out / "crop_condition_features.csv")
    met = H.evaluate_family(EXP, DIRN, feats, cols, feature_dictionary=fdict)
    print(met[met.model == "DELTA"][["horizon", "rmse_pct", "da", "dm_pvalue", "n"]].to_string())
    print("verdict:", H.verdict_from_delta(met))


if __name__ == "__main__":
    main()
