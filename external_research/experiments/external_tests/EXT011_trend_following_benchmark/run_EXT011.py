"""EXT011 — Benchmark trend-following (technique, causal).

Règles figées ex ante (aucun tuning) sur le CBOT continu : momentum 20/60/120,
croisement MA 50/200, EWMAC(16,64). Évalué (a) comme signal directionnel H40/H90
(comparable à EXT024), (b) comme stratégie (Sharpe/maxDD/hit/turnover). Le signal
du jour t n'utilise que l'information ≤ t (position prise pour t+1).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_common"))
import ext_harness as H  # noqa: E402
import ext_harness_dir as D  # noqa: E402

EXP, DIRN = "EXT011", "EXT011_trend_following_benchmark"
OUT = H.RESULTS / DIRN
EVAL = pd.Timestamp("2008-01-01")


def signals(px):
    logp = np.log(px)
    s = pd.DataFrame(index=px.index)
    s["mom20"] = np.sign(logp.diff(20))
    s["mom60"] = np.sign(logp.diff(60))
    s["mom120"] = np.sign(logp.diff(120))
    s["ma_50_200"] = np.sign(px.rolling(50).mean() - px.rolling(200).mean())
    ema16 = px.ewm(span=16).mean(); ema64 = px.ewm(span=64).mean()
    vol = logp.diff().rolling(64).std()
    s["ewmac_16_64"] = np.sign((ema16 - ema64) / (px * vol))
    return s


def strat_metrics(pos, daily_ret):
    r = (pos.shift(1) * daily_ret).dropna()
    if r.std() == 0 or len(r) < 50:
        return dict(sharpe=np.nan, max_dd=np.nan, hit=np.nan, turnover=np.nan, n=len(r))
    sharpe = float(r.mean() / r.std() * np.sqrt(252))
    cum = (1 + r).cumprod()
    dd = float((cum / cum.cummax() - 1).min())
    nz = r[pos.shift(1).reindex(r.index).abs() > 0]
    hit = float((nz > 0).mean()) if len(nz) else np.nan
    turn = float(pos.diff().abs().mean())
    return dict(sharpe=sharpe, max_dd=dd, hit=hit, turnover=turn, n=len(r))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mkt = H.load_market()
    px = mkt["corn_close"].astype(float)
    sig = signals(px)
    sig_eval = sig[(sig.index >= EVAL) & (sig.index < H.HOLDOUT_START)]
    sig_eval.to_csv(OUT / "trend_signals.csv")
    daily_ret = np.log(px).diff()

    # (a) direction H40/H90 : DA du signe du signal vs signe du retour futur
    dir_rows = []
    for h in [40, 90]:
        r = D.logret_target(px, h)
        ytrue = (r > 0).astype(int)
        idx = sig_eval.index
        tgt = H.target_dates_from_index(idx, h)  # vraie date i+h (5bis)
        m = tgt.notna() & (tgt < H.HOLDOUT_START)
        idx = idx[m.to_numpy()]
        for col in sig.columns:
            pred = (sig.loc[idx, col] > 0).astype(int)
            yt = ytrue.reindex(idx)
            ok = pred.notna() & yt.notna()
            mm = D.dir_metrics(yt[ok].to_numpy(), pred[ok].to_numpy().astype(float))
            dir_rows.append(dict(horizon=h, signal=col, da=mm["da"],
                                 da_vs_majority=mm["da_vs_majority"],
                                 balanced_acc=mm["balanced_acc"], n=mm["n"]))
    pd.DataFrame(dir_rows).to_csv(OUT / "metrics_EXT011.csv", index=False)

    # (b) stratégie : par signal, global + 2 sous-périodes
    bt_rows = []
    sub = sig_eval.index[len(sig_eval) // 2]
    for col in sig.columns:
        pos = sig[col].reindex(sig_eval.index)
        for label, mask in (("all", slice(None)),):
            bt_rows.append(dict(signal=col, period="all",
                                **strat_metrics(pos, daily_ret.reindex(sig_eval.index))))
        for label, idx in (("first_half", sig_eval.index[sig_eval.index < sub]),
                           ("second_half", sig_eval.index[sig_eval.index >= sub])):
            bt_rows.append(dict(signal=col, period=label,
                                **strat_metrics(sig[col].reindex(idx), daily_ret.reindex(idx))))
    # buy & hold
    for label, idx in (("all", sig_eval.index),):
        r = daily_ret.reindex(idx).dropna()
        cum = (1 + r).cumprod()
        bt_rows.append(dict(signal="buy_and_hold", period="all",
            sharpe=float(r.mean()/r.std()*np.sqrt(252)),
            max_dd=float((cum/cum.cummax()-1).min()), hit=float((r>0).mean()),
            turnover=0.0, n=len(r)))
    pd.DataFrame(bt_rows).to_csv(OUT / "trend_backtest_metrics.csv", index=False)

    print("-- direction H40/H90 --")
    print(pd.DataFrame(dir_rows).to_string(index=False))
    print("\n-- stratégie (global) --")
    print(pd.DataFrame([b for b in bt_rows if b["period"] == "all"]).to_string(index=False))


if __name__ == "__main__":
    main()
