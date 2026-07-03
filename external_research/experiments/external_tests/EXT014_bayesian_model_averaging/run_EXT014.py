"""EXT014 — Combinaison de modèles (BMA-like) pondérée par performance passée.

Pas de librairie BMA : version simple et anti-fuite. Poids de chaque membre =
performance walk-forward PASSÉE (accuracy annuelle expandante, laguée), normalisée.
Combinaison = moyenne pondérée des probabilités. Aucune optimisation sur tout
l'historique. Membres : market_only, market+wasde, market+crop, rw_baserate.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_common"))
import ensemble_members as EM  # noqa: E402
import ext_harness as H  # noqa: E402
import ext_harness_dir as D  # noqa: E402

EXP, DIRN = "EXT014", "EXT014_bayesian_model_averaging"
OUT = H.RESULTS / DIRN
MEMBERS = ["market_only", "market_wasde", "market_crop", "rw_baserate"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    met, wrows, preds = [], [], []
    for h in [40, 90]:
        mp = EM.member_predictions(h)
        y = mp["y_true"]
        mp["year"] = mp.index.year
        # accuracy annuelle par membre
        yearly = {}
        for m in MEMBERS:
            pred = (mp[m] >= 0.5).astype(int)
            yearly[m] = (pred == y).groupby(mp["year"]).mean()
        yearly = pd.DataFrame(yearly)
        # poids pour l'année Y = accuracy moyenne expandante des années < Y (laguée)
        w_by_year = yearly.expanding().mean().shift(1)
        w_by_year = w_by_year.sub(0.5).clip(lower=0)        # skill au-dessus du hasard
        w_by_year = w_by_year.div(w_by_year.sum(axis=1).replace(0, np.nan), axis=0)
        w_by_year = w_by_year.fillna(1.0 / len(MEMBERS))

        comb = np.zeros(len(mp))
        for m in MEMBERS:
            wm = mp["year"].map(w_by_year[m]).to_numpy()
            comb += wm * mp[m].to_numpy()
        mp["bma"] = comb
        for yr in w_by_year.index:
            wrows.append(dict(horizon=h, year=int(yr),
                              **{m: float(w_by_year.loc[yr, m]) for m in MEMBERS}))

        # métriques : chaque membre + BMA
        for m in MEMBERS + ["bma"]:
            mm = D.dir_metrics(y.to_numpy(), mp[m].to_numpy())
            sub_mid = mp.index[len(mp) // 2]
            pr = (mp[m] >= 0.5).astype(int)
            da1 = (pr[mp.index < sub_mid] == y[mp.index < sub_mid]).mean()
            da2 = (pr[mp.index >= sub_mid] == y[mp.index >= sub_mid]).mean()
            met.append(dict(horizon=h, model=m, da=mm["da"], balanced_acc=mm["balanced_acc"],
                            roc_auc=mm["roc_auc"], brier=mm["brier"],
                            da_first=float(da1), da_second=float(da2), n=mm["n"]))
        preds.append(mp.assign(horizon=h)[["horizon", "y_true", "bma"]].reset_index())

    pd.DataFrame(met).to_csv(OUT / "metrics_EXT014.csv", index=False)
    pd.DataFrame(wrows).to_csv(OUT / "model_weights_over_time.csv", index=False)
    pd.concat(preds, ignore_index=True).to_csv(OUT / "bma_predictions.csv", index=False)
    print(pd.DataFrame(met)[["horizon", "model", "da", "balanced_acc", "roc_auc", "brier",
                             "da_first", "da_second"]].to_string(index=False))


if __name__ == "__main__":
    main()
