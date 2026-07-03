"""EXT015 — Sélection de variables / importances train-only (walk-forward).

Question : les variables WASDE/Crop sortent-elles VRAIMENT, de façon STABLE, ou
le gain de l'étape 4 était-il fragile ? Importance calculée DANS chaque fenêtre
d'entraînement uniquement (anti-fuite n10), jamais sur tout le dataset.

Modèle d'importance : permutation importance sur le TRAIN (RandomForest régularisé).
Comparaison : DA(toutes variables) vs DA(top-k sélectionné train-only) vs marché seul.
SHAP installé mais non utilisé en boucle (coût) ; l'importance par permutation est
suffisante et plus robuste pour ce diagnostic.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_common"))
import ext_harness as H  # noqa: E402
import ext_harness_dir as D  # noqa: E402
import features_p2 as F  # noqa: E402

EXP, DIRN = "EXT015", "EXT015_shap_feature_selection"
OUT = H.RESULTS / DIRN
TOPK = 6


def rf():
    return RandomForestClassifier(n_estimators=200, max_depth=4,
                                  min_samples_leaf=50, random_state=0, n_jobs=-1)


def walk_forward_select(X, r, cols, h):
    df = X[cols].copy()
    df["__r"] = r
    df["__tgt"] = H.target_dates_from_index(X.index, h)  # vraie date i+h (5bis)
    df = df.dropna(subset=cols + ["__r"])
    df = df[(df.index < H.HOLDOUT_START) & (df["__tgt"] < H.HOLDOUT_START)]
    df["__y"] = (df["__r"] > 0).astype(int)

    imp_rows, sel_rows = [], []
    da_all, da_top, y_all, p_all, y_top, p_top, dts = [], [], [], [], [], [], []
    for yr in range(2008, H.HOLDOUT_START.year):
        bound = pd.Timestamp(f"{yr}-01-01"); nxt = pd.Timestamp(f"{yr+1}-01-01")
        tr = df[df["__tgt"] < bound]
        te = df[(df.index >= bound) & (df.index < nxt)]
        if len(tr) < D.MIN_TRAIN or len(te) == 0 or tr["__y"].nunique() < 2:
            continue
        Xtr = tr[cols].to_numpy(float); med = np.nanmedian(Xtr, 0)
        Xtr = np.where(np.isfinite(Xtr), Xtr, med)
        m, sd = Xtr.mean(0), Xtr.std(0); sd[sd == 0] = 1
        Xtr_s = (Xtr - m) / sd; ytr = tr["__y"].to_numpy(int)
        Xte = te[cols].to_numpy(float); Xte = np.where(np.isfinite(Xte), Xte, med)
        Xte_s = (Xte - m) / sd

        model = rf(); model.fit(Xtr_s, ytr)
        pi = permutation_importance(model, Xtr_s, ytr, n_repeats=8,
                                    random_state=0, scoring="balanced_accuracy")
        imp = pi.importances_mean
        for c, v in zip(cols, imp, strict=False):
            imp_rows.append(dict(horizon=h, year=yr, feature=c, perm_importance=v))
        order = np.argsort(imp)[::-1][:TOPK]
        top = [cols[i] for i in order]
        sel_rows.append(dict(horizon=h, year=yr, selected=";".join(top)))

        p_all.extend(model.predict_proba(Xte_s)[:, 1]); y_all.extend(te["__y"])
        # refit logit sur top-k
        idx = [cols.index(c) for c in top]
        lg = LogisticRegression(C=1.0, max_iter=1000)
        lg.fit(Xtr_s[:, idx], ytr)
        p_top.extend(lg.predict_proba(Xte_s[:, idx])[:, 1]); y_top.extend(te["__y"])
        dts.extend(te.index)
    return (np.array(y_all), np.array(p_all), np.array(y_top), np.array(p_top),
            pd.DataFrame(imp_rows), pd.DataFrame(sel_rows))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mkt = H.load_market()
    df, wcols, ccols, _ = F.build_p2_dataset()
    fam = df.reindex(mkt.index).ffill()
    X = mkt.join(fam[wcols + ccols])
    cols = D.BASE_COLS + ["s2u_z", "s2u_pctile", "bilan_tight", "bilan_loose",
                          "s2u_slow_chg", "cond_gd_ex_anom", "cond_dev5y",
                          "cond_gd_ex_chg", "cond_poor_vp"]

    all_imp, all_sel, met = [], [], []
    for h in [20, 40, 90]:
        r = D.logret_target(mkt["corn_close"], h)
        ya, pa, yt, pt, imp, sel = walk_forward_select(X, r, cols, h)
        all_imp.append(imp); all_sel.append(sel)
        ma = D.dir_metrics(ya, pa); mt = D.dir_metrics(yt, pt)
        # marché seul reference
        base = D.walk_forward_clf(X, r, D.BASE_COLS, h)
        mb = D.dir_metrics(base["y_true"], base["prob_up"])
        met.append(dict(horizon=h, model="rf_all_features", **ma))
        met.append(dict(horizon=h, model=f"logit_top{TOPK}_trainonly", **mt))
        met.append(dict(horizon=h, model="market_only_logit", **mb))

    imp = pd.concat(all_imp, ignore_index=True)
    sel = pd.concat(all_sel, ignore_index=True)
    # importance moyenne par horizon
    by_h = imp.groupby(["horizon", "feature"])["perm_importance"].agg(
        ["mean", "std", "min", "max"]).reset_index()
    by_h.to_csv(OUT / "feature_importance_by_horizon.csv", index=False)
    # stabilité : fréquence d'apparition dans le top-k + signe de l'importance
    rows = []
    for (h, feat), g in imp.groupby(["horizon", "feature"]):
        n_years = g["year"].nunique()
        in_top = sel[sel.horizon == h]["selected"].str.contains(rf"\b{feat}\b").mean()
        pos = (g["perm_importance"] > 0).mean()
        rows.append(dict(horizon=h, feature=feat, mean_imp=g["perm_importance"].mean(),
                         frac_positive=pos, frac_in_topk=in_top, n_years=n_years))
    stab = pd.DataFrame(rows).sort_values(["horizon", "mean_imp"], ascending=[True, False])
    stab.to_csv(OUT / "feature_stability.csv", index=False)
    sel.to_csv(OUT / "selected_features_walkforward.csv", index=False)
    pd.DataFrame(met).to_csv(OUT / "metrics_EXT015.csv", index=False)

    print(stab.to_string(index=False))
    print()
    print(pd.DataFrame(met)[["horizon", "model", "da", "da_vs_majority", "roc_auc", "brier"]].to_string(index=False))


if __name__ == "__main__":
    main()
