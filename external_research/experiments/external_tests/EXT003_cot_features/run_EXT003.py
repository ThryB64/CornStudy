"""EXT003 — Features CFTC COT (Disaggregated Managed Money / Producer / Swap).

Source : data/interim/cftc_cot.parquet (hebdo, Date = MARDI = date des positions).
Anti-fuite majeure : positions du mardi PUBLIEES le vendredi -> disponible le
lundi suivant (available = Date + 6 jours, conservateur). Eval 2016+. Compare
explicitement au constat V18 (seul le net total avait ete falsifie).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_common"))
import ext_harness as H  # noqa: E402
import series_utils as S  # noqa: E402

EXP, DIRN = "EXT003", "EXT003_cot_features"
EVAL_START = pd.Timestamp("2016-01-01")


def build_features():
    c = pd.read_parquet(H.DATA / "interim" / "cftc_cot.parquet")
    c["Date"] = pd.to_datetime(c["Date"])
    c = c.sort_values("Date").set_index("Date")

    f = pd.DataFrame(index=c.index)
    f["mm_net_pct_oi"] = c["cot_mm_net_pct_oi"]
    f["pm_net_pct_oi"] = c["cot_pm_net_pct_oi"]
    f["mm_net_z"] = S.expanding_z(c["cot_mm_net"])
    f["mm_net_pctile"] = S.expanding_pctile(c["cot_mm_net"])
    f["mm_net_chg"] = c["cot_mm_net"].diff()
    f["oi_z"] = S.expanding_z(c["cot_open_interest"])
    f["mm_long_pct"] = c["cot_mm_long_pct"]
    f["mm_short_pct"] = c["cot_mm_short_pct"]
    # ratio speculateurs / commerciaux (PM = producer/merchant = commercial)
    with np.errstate(divide="ignore", invalid="ignore"):
        f["spec_comm_ratio"] = (c["cot_mm_long"] + c["cot_mm_short"]) / \
                               (c["cot_pm_long"] + c["cot_pm_short"]).replace(0, np.nan)

    fdict = {
        "mm_net_pct_oi": "Managed Money net / open interest",
        "pm_net_pct_oi": "Producer/Merchant net / open interest",
        "mm_net_z": "z-score expandant du MM net",
        "mm_net_pctile": "Percentile expandant du MM net (extremes)",
        "mm_net_chg": "Flux hebdo du MM net",
        "oi_z": "z-score expandant de l'open interest",
        "mm_long_pct": "MM long / OI", "mm_short_pct": "MM short / OI",
        "spec_comm_ratio": "Ratio positions speculateurs (MM) / commerciaux (PM)",
    }
    # disponibilite lundi = Date(mardi) + 6 jours (vendredi publication + marge)
    f.index = f.index + pd.Timedelta(days=6)
    feats = S.daily_ffill(f, end="2026-04-30")
    return feats, list(feats.columns), fdict


def main():
    feats, cols, fdict = build_features()
    out = H.RESULTS / DIRN
    out.mkdir(parents=True, exist_ok=True)
    feats.dropna(how="all").to_csv(out / "cot_features.csv")
    pd.DataFrame([{"feature": k, "description": v} for k, v in fdict.items()]).to_csv(
        out / "cot_feature_dictionary.csv", index=False)
    met = H.evaluate_family(EXP, DIRN, feats, cols, eval_start=EVAL_START,
                            feature_dictionary=fdict)
    print(met[met.model == "DELTA"][["horizon", "rmse_pct", "da", "dm_pvalue", "n"]].to_string())
    print("verdict:", H.verdict_from_delta(met))


if __name__ == "__main__":
    main()
