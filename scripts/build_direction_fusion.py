"""Etude fusion directionnelle H60/H90 : les blocs fondamentaux valides (crop, WASDE,
ble/mais) ajoutent-ils du signal directionnel au-dela du marche seul, et le signal
generalise-t-il sur l'annee frais (post 2025-07-25, jamais vue par le projet) ?

Protocole = validate_pistes : walk-forward refit annuel purge, AUC + IC bootstrap +
part d'annees positives + placebo permutation. Verdict ROBUSTE/LIMITE a priori.
Sorties : artefacts/direction_fusion/*.csv/json/png + docs/FINAL_DIRECTION_FUSION_STUDY.md.
"""
from __future__ import annotations

import json
from pathlib import Path

import build_risk_indicator as eng
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artefacts" / "direction_fusion"
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(7)
FRESH_START = pd.Timestamp("2025-07-26")  # 1er jour jamais vu par le developpement

BLUE, GREEN, RED, ORANGE, PURPLE, GREY = (
    "#1f77b4", "#2ca02c", "#d62728", "#e8943a", "#9467bd", "#888888")
plt.rcParams.update({"figure.dpi": 110, "font.size": 11, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.axisbelow": True})

FFILL = ["crop_ge_zscore_seasonal", "crop_ge_5y_avg_deviation", "crop_condition_momentum_2w",
         "wasde_stocks_to_use_ratio", "wasde_stocks_to_use_calc_z"]

BLOCKS = {
    "MARKET": ["corn_logret_20d", "corn_dist_to_52w_high", "corn_realized_vol_60"],
    "CROP": ["crop_ge_zscore_seasonal", "crop_ge_5y_avg_deviation", "crop_condition_momentum_2w"],
    "WASDE": ["wasde_stocks_to_use_ratio", "wasde_stocks_to_use_calc_z"],
    "WHEAT": ["corn_wheat_ratio", "spread_corn_wheat"],
}
BLOCKS["FOND"] = BLOCKS["CROP"] + BLOCKS["WASDE"] + BLOCKS["WHEAT"]
BLOCKS["FULL"] = BLOCKS["MARKET"] + BLOCKS["FOND"]

TARGETS = [("y_up_h60", 60), ("y_up_h90", 90), ("y_down_gt_3pct_h60", 60)]


def load() -> pd.DataFrame:
    df = eng.DF.copy()
    t = pd.read_parquet(ROOT / "data/processed/targets.parquet")
    t["Date"] = pd.to_datetime(t["Date"])
    extra = [c for c in ["y_up_h60", "y_up_h90"] if c not in df.columns]
    if extra:
        df = df.merge(t[["Date", *extra]], on="Date", how="left")
    for c in FFILL:
        if c in df:
            df[c] = df[c].ffill()
    return df


def validate(df, feats, target, horizon):
    oos = eng.walkforward(df, feats, target, horizon, "clf")
    if oos.empty:
        return None, oos
    y, p = oos[target].to_numpy(int), oos["pred"].to_numpy(float)
    auc = roc_auc_score(y, p)
    lo, hi = eng.boot_auc(y, p)
    years = oos.groupby("year").apply(
        lambda g: roc_auc_score(g[target], g["pred"]) if g[target].nunique() > 1 else np.nan,
        include_groups=False)
    share = float((years.dropna() > 0.5).mean())
    d2 = df.dropna(subset=[*feats, target]).copy()
    d2[target] = RNG.permutation(d2[target].to_numpy())
    op = eng.walkforward(d2, feats, target, horizon, "clf")
    plac = float(roc_auc_score(op[target], op["pred"]))
    fresh = oos[oos["Date"] >= FRESH_START]
    fresh_auc = (roc_auc_score(fresh[target], fresh["pred"])
                 if len(fresh) > 30 and fresh[target].nunique() > 1 else np.nan)
    r = {"auc": float(auc), "ci_low": lo, "ci_high": hi, "n": int(len(oos)),
         "year_share_pos": share, "placebo_auc": plac,
         "fresh_auc": float(fresh_auc) if np.isfinite(fresh_auc) else None,
         "fresh_n": int(len(fresh)),
         "per_year": {int(k): (round(float(v), 3) if np.isfinite(v) else None)
                      for k, v in years.items()}}
    ok = r["ci_low"] > 0.52 and r["year_share_pos"] >= 0.60 and 0.45 <= plac <= 0.55
    r["verdict"] = "Robuste" if ok else "Limite"
    return r, oos


def abstention(oos, target):
    rows = []
    y = oos[target].to_numpy(int)
    p = oos["pred"].to_numpy(float)
    for thr in [0.0, 0.05, 0.10, 0.15, 0.20]:
        m = np.abs(p - 0.5) >= thr
        if m.sum() < 50:
            continue
        da = float(((p[m] >= 0.5).astype(int) == y[m]).mean())
        rows.append({"threshold": thr, "coverage": float(m.mean()),
                     "n": int(m.sum()), "directional_accuracy": da})
    return rows


def plot_auc_ci(res):
    fig, ax = plt.subplots(figsize=(9.5, 6))
    labels, ys = [], []
    i = 0
    colors = {"y_up_h60": BLUE, "y_up_h90": GREEN, "y_down_gt_3pct_h60": RED}
    for tgt, _h in TARGETS:
        for blk in BLOCKS:
            r = res.get((tgt, blk))
            if not r:
                continue
            ax.errorbar(r["auc"], i, xerr=[[r["auc"] - r["ci_low"]], [r["ci_high"] - r["auc"]]],
                        fmt="o", color=colors[tgt], capsize=3, markersize=7)
            if r["fresh_auc"] is not None:
                ax.plot(r["fresh_auc"], i, marker="D", color=ORANGE, markersize=6,
                        linestyle="none")
            labels.append(f"{tgt} | {blk}")
            ys.append(i)
            i += 1
        i += 1
    ax.axvline(0.5, color=GREY, linestyle="--", linewidth=1)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("AUC walk-forward (rond = OOS 2014+, losange orange = annee frais 2025-07+)")
    ax.set_title("Fusion directionnelle : AUC par cible et bloc de features (IC95 bootstrap)")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(OUT / "fusion_auc_ci.png")
    plt.close(fig)


def plot_abstention(abst):
    fig, ax = plt.subplots(figsize=(8, 5))
    for (tgt, blk), rows in abst.items():
        if not rows:
            continue
        cov = [r["coverage"] for r in rows]
        da = [r["directional_accuracy"] for r in rows]
        ax.plot(cov, da, marker="o", label=f"{tgt} | {blk}")
    ax.axhline(0.5, color=GREY, linestyle="--", linewidth=1)
    ax.set_xlabel("Couverture (part des jours ou on tranche)")
    ax.set_ylabel("Directional accuracy")
    ax.set_title("Abstention : la DA monte-t-elle quand on ne tranche que les jours confiants ?")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fusion_abstention.png")
    plt.close(fig)


def main():
    df = load()
    last = df["Date"].max()
    print(f"donnees : {df['Date'].min().date()} -> {last.date()}  n={len(df)}")
    res, abst = {}, {}
    for tgt, h in TARGETS:
        for blk, feats in BLOCKS.items():
            miss = [f for f in feats if f not in df.columns]
            if miss:
                print(f"SKIP {tgt}|{blk} features absentes: {miss}")
                continue
            r, oos = validate(df, feats, tgt, h)
            if r is None:
                continue
            res[(tgt, blk)] = r
            fresh_txt = (f" frais {r['fresh_auc']:.3f} (n={r['fresh_n']})"
                         if r["fresh_auc"] is not None else "")
            print(f"{tgt:20s} {blk:7s} AUC {r['auc']:.3f} "
                  f"IC[{r['ci_low']:.3f};{r['ci_high']:.3f}] annees+ {r['year_share_pos']:.0%} "
                  f"placebo {r['placebo_auc']:.3f} -> {r['verdict']}{fresh_txt}")
            if blk in ("FULL", "FOND"):
                abst[(tgt, blk)] = abstention(oos, tgt)

    rows = [{"target": t, "block": b, **{k: v for k, v in r.items() if k != "per_year"}}
            for (t, b), r in res.items()]
    pd.DataFrame(rows).to_csv(OUT / "fusion_results.csv", index=False)
    json.dump({f"{t}|{b}": r for (t, b), r in res.items()},
              (OUT / "fusion_verdicts.json").open("w"), indent=2, ensure_ascii=False)
    json.dump({f"{t}|{b}": rows_ for (t, b), rows_ in abst.items()},
              (OUT / "fusion_abstention.json").open("w"), indent=2, ensure_ascii=False)
    plot_auc_ci(res)
    plot_abstention(abst)
    print(f"ecrit : {OUT}")
    return res, abst


if __name__ == "__main__":
    main()
