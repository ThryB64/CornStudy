"""EXT050 — Stacking ensemble (méta-modèle simple).

Renommé EXT028 -> EXT050 à l'étape 5 bis : EXT028 ET EXT029 sont déjà réservés
dans ideas_matrix (satellite_usda_report_proxy, corn_crush_location_basis).
EXT050 est hors de la plage catalogue (EXT001-EXT045) = ID interne étape 5.

Méta-modèle = régression logistique sur les probabilités OOS des membres
directionnels, entraîné walk-forward sur le PASSÉ seulement (membres déjà OOS,
donc empilables sans fuite). Comparé à la moyenne simple et au meilleur membre.
Interdits respectés : pas d'optimisation sur tout l'historique, pas de holdout.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_common"))
import ensemble_members as EM  # noqa: E402
import ext_harness as H  # noqa: E402
import ext_harness_dir as D  # noqa: E402

EXP, DIRN = "EXT050", "EXT050_model_stacking_ensemble"
OUT = H.RESULTS / DIRN
MEMBERS = ["market_only", "market_wasde", "market_crop"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    met, wrows, preds = [], [], []
    for h in [40, 90]:
        mp = EM.member_predictions(h)
        y = mp["y_true"].to_numpy()
        idx = mp.index
        Z = mp[MEMBERS].to_numpy()

        stack_prob = np.full(len(mp), np.nan)
        avg_prob = mp[MEMBERS].mean(axis=1).to_numpy()
        for yr in range(idx.year.min() + 1, H.HOLDOUT_START.year):
            b = pd.Timestamp(f"{yr}-01-01"); n = pd.Timestamp(f"{yr+1}-01-01")
            tr = (idx < b); te = (idx >= b) & (idx < n)
            if tr.sum() < 200 or te.sum() == 0 or len(np.unique(y[tr])) < 2:
                continue
            meta = LogisticRegression(C=1.0, max_iter=1000)
            meta.fit(Z[tr], y[tr])
            stack_prob[te] = meta.predict_proba(Z[te])[:, 1]
            wrows.append(dict(horizon=h, year=yr,
                              **{m: float(c) for m, c in zip(MEMBERS, meta.coef_.ravel(), strict=False)},
                              intercept=float(meta.intercept_[0])))
        ok = ~np.isnan(stack_prob)
        for name, p in [("stack", stack_prob), ("simple_avg", avg_prob)] + \
                       [(m, mp[m].to_numpy()) for m in MEMBERS]:
            pp = p[ok]; yy = y[ok]
            mm = D.dir_metrics(yy, pp)
            pr = (pp >= 0.5).astype(int)
            mid = len(yy) // 2
            da1 = (pr[:mid] == yy[:mid]).mean(); da2 = (pr[mid:] == yy[mid:]).mean()
            met.append(dict(horizon=h, model=name, da=mm["da"], balanced_acc=mm["balanced_acc"],
                            roc_auc=mm["roc_auc"], brier=mm["brier"],
                            da_first=float(da1), da_second=float(da2), n=mm["n"]))
        preds.append(pd.DataFrame(dict(date=idx[ok], horizon=h, y_true=y[ok],
                                       stack_prob=stack_prob[ok])))
    pd.DataFrame(met).to_csv(OUT / "metrics_EXT050.csv", index=False)
    pd.DataFrame(wrows).to_csv(OUT / "ensemble_weights.csv", index=False)
    pd.concat(preds, ignore_index=True).to_csv(OUT / "ensemble_predictions.csv", index=False)
    print(pd.DataFrame(met)[["horizon", "model", "da", "balanced_acc", "roc_auc",
                             "brier", "da_first", "da_second"]].to_string(index=False))


if __name__ == "__main__":
    main()
