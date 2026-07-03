"""EXT017 — Détection de régimes de marché.

Les signaux IMPROVE (WASDE@H40, Crop@H90) ne marchent-ils que dans certains
régimes ? Régimes définis SUR INFO PASSÉE uniquement (vol, tendance, bilan,
condition, saison, proximité WASDE). On mesure la DA du meilleur modèle
directionnel par régime, et on teste un filtre de régime.

Garde-fou overfitting : on ne fitte PAS un modèle par régime (échantillons trop
petits) — on slice les prédictions d'un modèle global et on documente n par régime.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_common"))
import ext_harness as H  # noqa: E402
import ext_harness_dir as D  # noqa: E402
import features_p2 as F  # noqa: E402

EXP, DIRN = "EXT017", "EXT017_market_regime_detection"
OUT = H.RESULTS / DIRN


def build_regimes(mkt):
    logp = np.log(mkt["corn_close"])
    r = logp.diff()
    reg = pd.DataFrame(index=mkt.index)
    rv20 = r.rolling(20).std()
    reg["vol_regime"] = np.where(rv20 > rv20.expanding(252).median().shift(1),
                                 "high_vol", "low_vol")
    mom = logp.diff(120)
    reg["trend_regime"] = np.where(mom > 0.02, "uptrend",
                          np.where(mom < -0.02, "downtrend", "neutral_trend"))
    reg["season_regime"] = np.where(mkt.index.month.isin([5, 6, 7, 8, 9]),
                                    "growing", "off_season")
    df, wcols, ccols, _ = F.build_p2_dataset()
    fam = df.reindex(mkt.index).ffill()
    s2up = fam["s2u_pctile"]
    reg["stocks_regime"] = np.where(s2up < 0.33, "tight",
                           np.where(s2up > 0.66, "loose", "normal_stocks"))
    anom = fam["cond_gd_ex_anom"]
    reg["crop_regime"] = np.where(anom > 0.5, "good_crop",
                         np.where(anom < -0.5, "bad_crop", "normal_crop"))
    cal = pd.read_parquet(H.DATA / "interim" / "usda_calendar.parquet")
    cal["Date"] = pd.to_datetime(cal["Date"])
    cal = cal.set_index("Date")
    reg["wasde_regime"] = np.where(
        cal["days_since_last_wasde"].reindex(mkt.index) <= 10, "near_wasde", "far_wasde")
    return reg, fam, wcols, ccols


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mkt = H.load_market()
    reg, fam, wcols, ccols = build_regimes(mkt)
    reg.to_csv(OUT / "market_regimes.csv")
    X = mkt.join(fam[wcols + ccols])

    specs = {40: D.BASE_COLS + ["s2u_z", "s2u_pctile", "bilan_tight", "bilan_loose", "s2u_slow_chg"],
             90: D.BASE_COLS + ["cond_gd_ex_anom", "cond_dev5y", "cond_gd_ex_chg", "cond_poor_vp"]}

    rows = []
    for h, cols in specs.items():
        r = D.logret_target(mkt["corn_close"], h)
        res = D.walk_forward_clf(X, r, cols, h)
        pred = pd.Series((res["prob_up"] >= 0.5).astype(int), index=pd.DatetimeIndex(res["dates"]))
        ytrue = pd.Series(res["y_true"], index=pd.DatetimeIndex(res["dates"]))
        prob = pd.Series(res["prob_up"], index=pd.DatetimeIndex(res["dates"]))
        rsl = reg.reindex(pred.index)
        # global
        m = D.dir_metrics(ytrue.to_numpy(), prob.to_numpy())
        rows.append(dict(horizon=h, regime_dim="ALL", regime="all", n=m["n"],
                         da=m["da"], balanced_acc=m["balanced_acc"], brier=m["brier"]))
        for dim in ["vol_regime", "trend_regime", "season_regime", "stocks_regime",
                    "crop_regime", "wasde_regime"]:
            for val, idx in rsl.groupby(rsl[dim]).groups.items():
                idx = pd.DatetimeIndex(idx)
                if len(idx) < 40:
                    continue
                mm = D.dir_metrics(ytrue.reindex(idx).to_numpy(), prob.reindex(idx).to_numpy())
                rows.append(dict(horizon=h, regime_dim=dim, regime=val, n=mm["n"],
                                 da=mm["da"], balanced_acc=mm["balanced_acc"], brier=mm["brier"]))
    mbr = pd.DataFrame(rows)
    mbr.to_csv(OUT / "metrics_by_regime.csv", index=False)

    # règles de régime documentées
    pd.DataFrame([
        ("vol_regime", "rv20 vs médiane expandante (passé)", "high_vol / low_vol"),
        ("trend_regime", "momentum 120j, bande neutre ±0.02", "uptrend / downtrend / neutral_trend"),
        ("season_regime", "mois de croissance mai-sep", "growing / off_season"),
        ("stocks_regime", "percentile expandant stocks-to-use", "tight<0.33 / normal / loose>0.66"),
        ("crop_regime", "anomalie condition good/excellent", "good>0.5 / normal / bad<-0.5"),
        ("wasde_regime", "jours depuis dernier WASDE (calendrier ex ante)", "near<=10j / far"),
    ], columns=["regime_dim", "rule_past_only", "values"]).to_csv(
        OUT / "regime_rules.csv", index=False)

    # importance des régimes ajoutés au modèle (dummies) — test marginal
    imp_rows = []
    for h, cols in specs.items():
        r = D.logret_target(mkt["corn_close"], h)
        Xr = X.copy()
        for dim in ["vol_regime", "trend_regime", "stocks_regime", "crop_regime"]:
            dums = pd.get_dummies(reg[dim], prefix=dim).astype(float)
            Xr = Xr.join(dums)
        extra = [c for c in Xr.columns if any(c.startswith(p + "_") for p in
                 ["vol_regime", "trend_regime", "stocks_regime", "crop_regime"])]
        res = D.walk_forward_clf(Xr, r, cols + extra, h)
        for c, v in sorted(res["coef"].items(), key=lambda x: -x[1]):
            if c in extra:
                imp_rows.append(dict(horizon=h, regime_feature=c, abs_coef=v))
    pd.DataFrame(imp_rows).to_csv(OUT / "regime_feature_importance.csv", index=False)

    print(mbr.to_string(index=False))


if __name__ == "__main__":
    main()
