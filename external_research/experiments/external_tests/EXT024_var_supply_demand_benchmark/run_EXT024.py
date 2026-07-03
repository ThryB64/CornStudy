"""EXT024 — Benchmark supply-demand directionnel (parcimonieux, interprétable).

Question : les deux signaux IMPROVE de l'étape 4 (WASDE état de bilan, Crop
Condition), encodés de façon STATIONNAIRE, améliorent-ils la DIRECTION H40/H90
au-delà d'un modèle de marché minimal ? RMSE = métrique secondaire seulement.

Modèles (parcimonieux) : marché seul (= AR directionnel), +WASDE, +Crop,
+WASDE+Crop, et WASDE+Crop sans marché. Classifieur : régression logistique L2
(walk-forward expandant, train-only). Robustesse : RidgeClassifier.
"""
import sys
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_common"))
import ext_harness as H  # noqa: E402
import ext_harness_dir as D  # noqa: E402
import features_p2 as F  # noqa: E402

EXP, DIRN = "EXT024", "EXT024_var_supply_demand_benchmark"
OUT = H.RESULTS / DIRN

WASDE_PARSI = ["s2u_z", "s2u_pctile", "bilan_tight", "bilan_loose", "s2u_slow_chg"]
CROP_PARSI = ["cond_gd_ex_anom", "cond_dev5y", "cond_gd_ex_chg", "cond_poor_vp"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mkt = H.load_market()
    df, wcols, ccols, fdict = F.build_p2_dataset()
    fam = df.reindex(mkt.index).ffill()
    X = mkt.join(fam[wcols + ccols])
    X[wcols + ccols].dropna(how="all").to_csv(OUT / "ext024_dataset.csv")

    specs = {
        "market_only": D.BASE_COLS,
        "market+wasde": D.BASE_COLS + WASDE_PARSI,
        "market+crop": D.BASE_COLS + CROP_PARSI,
        "market+wasde+crop": D.BASE_COLS + WASDE_PARSI + CROP_PARSI,
        "wasde+crop_only": WASDE_PARSI + CROP_PARSI,
    }
    models = {
        "logit_l2": lambda: LogisticRegression(C=1.0, max_iter=1000),
        "logit_l2_strong": lambda: LogisticRegression(C=0.25, max_iter=1000),
    }

    met_rows, calib_rows, coef_rows, pred_rows = [], [], [], []
    for h in [40, 90]:
        r = D.logret_target(mkt["corn_close"], h)
        for sname, cols in specs.items():
            for mname, mk in models.items():
                res = D.walk_forward_clf(X, r, cols, h, make_model=mk)
                if res is None:
                    continue
                m = D.dir_metrics(res["y_true"], res["prob_up"])
                sub = D.subperiod_da(res)
                pred = (res["prob_up"] >= 0.5).astype(int)
                lo, hi = D.block_bootstrap_da(res["y_true"], pred)
                met_rows.append(dict(experiment=EXP, horizon=h, spec=sname,
                    model=mname, **m, da_ci_lo=lo, da_ci_hi=hi,
                    da_first=sub.get("first_half"), da_second=sub.get("second_half")))
                if mname == "logit_l2" and sname in ("market+wasde+crop", "wasde+crop_only"):
                    cal = D.calibration_table(res["y_true"], res["prob_up"])
                    cal["horizon"] = h; cal["spec"] = sname
                    calib_rows.append(cal)
                    for c, v in res["coef"].items():
                        coef_rows.append(dict(horizon=h, spec=sname, feature=c, abs_coef=v))
                if mname == "logit_l2" and sname == "market+wasde+crop":
                    pred_rows.append(pd.DataFrame(dict(
                        date=res["dates"], horizon=h, y_true=res["y_true"],
                        prob_up=res["prob_up"])))

    met = pd.DataFrame(met_rows)
    met.to_csv(OUT / "metrics_EXT024.csv", index=False)
    if calib_rows:
        pd.concat(calib_rows).to_csv(OUT / "calibration_EXT024.csv", index=False)
    pd.DataFrame(coef_rows).to_csv(OUT / "coefficients_EXT024.csv", index=False)
    if pred_rows:
        pd.concat(pred_rows).to_csv(OUT / "ext024_predictions.csv", index=False)
    pd.DataFrame([{"feature": k, "description": v} for k, v in fdict.items()]).to_csv(
        OUT / "ext024_feature_dictionary.csv", index=False)

    show = met[met.model == "logit_l2"][["horizon", "spec", "da", "da_vs_majority",
        "balanced_acc", "roc_auc", "brier", "da_first", "da_second",
        "p_binom_vs_majority"]]
    print(show.to_string(index=False))


if __name__ == "__main__":
    main()
