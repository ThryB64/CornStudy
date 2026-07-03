"""EXT010 — HAR comme benchmark de volatilité réalisée.

HAR-RV (Corsi) : RV_h forward régressée sur RV passées 5/22/66 j, OLS expandant
(refit annuel). Comparé à la RW de vol (rv_h passé) et à rolling vol 20 j.
Cibles : vol H20/H40/H90. Métriques : RMSE/MAE/QLIKE/corr.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_common"))
import ext_harness as H  # noqa: E402
import vol_utils as V  # noqa: E402

EXP, DIRN = "EXT010", "EXT010_har_realized_volatility"
OUT = H.RESULTS / DIRN


def walk_har(r, h):
    feats = V.har_features(r)
    y = V.future_rv(r, h)
    df = feats.join(y.rename("y")).dropna()
    df = df[df.index < H.HOLDOUT_START]
    df["__tgt"] = H.target_dates_from_index(df.index, h)  # vraie date i+h (5bis)
    df = df[df["__tgt"] < H.HOLDOUT_START]
    cols = ["rv_w", "rv_m", "rv_q"]
    rows = []
    for yr in range(2008, H.HOLDOUT_START.year):
        b = pd.Timestamp(f"{yr}-01-01"); n = pd.Timestamp(f"{yr+1}-01-01")
        tr = df[df["__tgt"] < b]; te = df[(df.index >= b) & (df.index < n)]
        if len(tr) < 500 or len(te) == 0:
            continue
        Xtr = np.column_stack([np.ones(len(tr)), tr[cols].to_numpy()])
        beta, *_ = np.linalg.lstsq(Xtr, tr["y"].to_numpy(), rcond=None)
        Xte = np.column_stack([np.ones(len(te)), te[cols].to_numpy()])
        pred = np.clip(Xte @ beta, 1e-6, None)
        for dt, yt, pr, rvw in zip(te.index, te["y"], pred, te["rv_w"], strict=False):
            rows.append((dt, yt, pr))
    res = pd.DataFrame(rows, columns=["date", "y_true", "har"]).set_index("date")
    # benchmarks alignés
    res["rw_vol"] = V.past_rv(r, h).reindex(res.index)
    res["roll20"] = V.past_rv(r, 20).reindex(res.index) * np.sqrt(h / 20)
    return res.dropna()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    r = V.daily_logret()
    V.har_features(r).dropna().to_csv(OUT / "har_features.csv")
    allres, met = [], []
    for h in [20, 40, 90]:
        res = walk_har(r, h)
        res.insert(0, "horizon", h)
        allres.append(res.reset_index())
        for model in ["har", "rw_vol", "roll20"]:
            m = V.vol_metrics(res["y_true"].to_numpy(), res[model].to_numpy())
            met.append(dict(horizon=h, model=model, **m))
    pd.concat(allres, ignore_index=True).to_csv(OUT / "volatility_forecasts_EXT010.csv", index=False)
    mt = pd.DataFrame(met)
    mt.to_csv(OUT / "metrics_EXT010.csv", index=False)
    print(mt.to_string(index=False))


if __name__ == "__main__":
    main()
