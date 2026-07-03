"""EXT009 — GARCH / EGARCH / GJR-GARCH pour la volatilité (outil de RISQUE).

Pas un prédicteur de prix : sert au risque, à l'incertitude, aux gates et à un
score de vente plus prudent. Refit mensuel expandant (passé only), prévision
h-jours, comparé à la RW de vol et à rolling 20. Test aussi un filtre : ne pas
vendre quand la vol prévue est dans le décile haut (réduction de drawdown).
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_common"))
import ext_harness as H  # noqa: E402
import vol_utils as V  # noqa: E402

warnings.filterwarnings("ignore")
EXP, DIRN = "EXT009", "EXT009_garch_egarch_volatility"
OUT = H.RESULTS / DIRN
REFIT_EVERY = 21  # ~ mensuel


def garch_forecasts(r_pct: pd.Series, h: int, spec: str, eval_dates):
    """Refit mensuel, prévision h-jours de vol (en unités de r_pct)."""
    from arch import arch_model
    preds = {}
    eval_set = set(eval_dates)
    idx = r_pct.index
    last_fit = -10 ** 9
    res = None
    for i, dt in enumerate(idx):
        if dt not in eval_set:
            continue
        if i - last_fit >= REFIT_EVERY or res is None:
            train = r_pct.iloc[:i + 1]
            if len(train) < 500:
                continue
            try:
                if spec == "garch":
                    am = arch_model(train, vol="Garch", p=1, q=1, mean="Zero", dist="t")
                elif spec == "egarch":
                    am = arch_model(train, vol="EGARCH", p=1, o=1, q=1, mean="Zero", dist="t")
                elif spec == "gjr":
                    am = arch_model(train, vol="Garch", p=1, o=1, q=1, mean="Zero", dist="t")
                res = am.fit(disp="off", show_warning=False)
                last_fit = i
            except Exception:
                continue
        if res is None:
            continue
        try:
            method = "analytic" if spec in ("garch", "gjr") else "simulation"
            fc = res.forecast(horizon=h, reindex=False, method=method,
                              simulations=300 if method == "simulation" else 0)
            var_path = fc.variance.values[-1]            # variance par pas (en r_pct^2)
            hvar = np.nansum(var_path)                    # variance h-jours
            preds[dt] = np.sqrt(hvar)
        except Exception:
            continue
    return pd.Series(preds)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    r = V.daily_logret()
    r_pct = r * 100.0
    feat_rows = []
    metrics, fc_store = [], {}
    for h in [20, 40, 90]:
        ed = V.eval_index(r, h)
        yfut = (V.future_rv(r, h) * 100.0).reindex(ed)        # vol réalisée en r_pct
        benchmarks = {
            "rw_vol": (V.past_rv(r, h) * 100.0).reindex(ed),
            "roll20": (V.past_rv(r, 20) * 100.0).reindex(ed) * np.sqrt(h / 20),
        }
        series = dict(benchmarks)
        for spec in ["garch", "egarch", "gjr"]:
            series[spec] = garch_forecasts(r_pct, h, spec, ed)
        for name, pred in series.items():
            common = yfut.dropna().index.intersection(pred.dropna().index)
            if len(common) < 50:
                continue
            m = V.vol_metrics(yfut.reindex(common).to_numpy(),
                              pred.reindex(common).to_numpy())
            metrics.append(dict(horizon=h, model=name, **m))
            for dt in common:
                fc_store.setdefault(dt, {}).setdefault(h, {})[name] = pred[dt]
        # features GARCH(1,1) 1-pas pour usage gate (vol conditionnelle)
    mt = pd.DataFrame(metrics)
    mt.to_csv(OUT / "metrics_EXT009.csv", index=False)

    # ---- filtre de vol : backtest d'un score directionnel simple sous gate ----
    import ext_harness_dir as D
    mkt = H.load_market()
    import features_p2 as F
    df, wcols, ccols, _ = F.build_p2_dataset()
    fam = df.reindex(mkt.index).ffill()
    X = mkt.join(fam[wcols + ccols])
    rr = D.logret_target(mkt["corn_close"], 90)
    base = D.walk_forward_clf(X, rr, D.BASE_COLS + ["cond_gd_ex_anom", "cond_dev5y",
                              "cond_gd_ex_chg", "cond_poor_vp"], 90)
    # vol prévue GARCH H90 alignée
    gpred = garch_forecasts(r_pct, 90, "garch", pd.DatetimeIndex(base["dates"]))
    g = gpred.reindex(pd.DatetimeIndex(base["dates"]))
    thr = g.quantile(0.90)
    pred_dir = (base["prob_up"] >= 0.5).astype(int)
    correct = (pred_dir == base["y_true"]).astype(float)
    fwd = rr.reindex(pd.DatetimeIndex(base["dates"])).to_numpy()
    pnl_signed = np.where(pred_dir == 1, fwd, -fwd)   # PnL d'un pari directionnel
    hi = (g.to_numpy() >= thr)
    bt = pd.DataFrame({
        "regime": ["all", "low_vol(<p90)", "high_vol(>=p90)"],
        "n": [len(correct), int((~hi).sum()), int(hi.sum())],
        "da": [correct.mean(), correct[~hi].mean() if (~hi).any() else np.nan,
               correct[hi].mean() if hi.any() else np.nan],
        "mean_pnl": [np.nanmean(pnl_signed), np.nanmean(pnl_signed[~hi]) if (~hi).any() else np.nan,
                     np.nanmean(pnl_signed[hi]) if hi.any() else np.nan],
    })
    bt.to_csv(OUT / "volatility_filter_backtest.csv", index=False)

    # store forecasts
    rows = []
    for dt, hd in fc_store.items():
        for h, md in hd.items():
            for name, val in md.items():
                rows.append(dict(date=dt, horizon=h, model=name, pred_vol_pct=val))
    pd.DataFrame(rows).to_csv(OUT / "volatility_forecasts_EXT009.csv", index=False)

    print(mt.to_string(index=False))
    print("\n-- filtre vol sur score directionnel H90 (crop) --")
    print(bt.to_string(index=False))


if __name__ == "__main__":
    main()
