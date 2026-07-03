"""Indicateur selectif de risque - validation walk-forward stricte (anti-leakage).

Modules : M1 CBOT Downside Risk (classification), M3 Volatility regime (regression),
M4 Euronext Premium (reversion du basis, research-only) + Confidence Gate (abstention).
Anti-leakage : refit annuel, purge = horizon entre train et test, standardisation train-only.
Sorties : artefacts/indicator_v1/*.csv + *.png + index.html + snapshot.json,
          docs/INDICATOR_V1_VALIDATION.md.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artefacts" / "indicator_v1"
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(42)

BLUE, GREEN, RED, ORANGE, PURPLE, GREY = (
    "#1f77b4", "#2ca02c", "#d62728", "#e8943a", "#9467bd", "#888888")
plt.rcParams.update({"figure.dpi": 110, "font.size": 11, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.axisbelow": True})

FUND = ["crop_ge_zscore_seasonal", "wasde_stocks_to_use_ratio", "crop_ge_5y_avg_deviation"]
FEAT_M1 = ["crop_ge_zscore_seasonal", "wasde_stocks_to_use_ratio", "corn_logret_20d",
           "corn_realized_vol_60", "corn_wheat_ratio", "corn_dist_to_52w_high",
           "is_harvest_season"]
FEAT_M3 = ["corn_realized_vol_20", "corn_realized_vol_60", "corn_logret_20d"]


def load() -> pd.DataFrame:
    f = pd.read_parquet(ROOT / "data/processed/features.parquet")
    t = pd.read_parquet(ROOT / "data/processed/targets.parquet")
    f["Date"] = pd.to_datetime(f["Date"])
    t["Date"] = pd.to_datetime(t["Date"])
    cols_t = ["Date", "y_down_gt_3pct_h30", "y_down_gt_3pct_h60", "future_min_return_h60",
              "y_realized_vol_h20", "y_logret_h30", "y_logret_h60", "y_logret_h90"]
    df = f.merge(t[cols_t], on="Date", how="inner").sort_values("Date").reset_index(drop=True)
    for c in FUND:  # fondamentaux = paliers connus jusqu'a la prochaine publication : ffill anti-leakage
        if c in df:
            df[c] = df[c].ffill()
    df["year"] = df["Date"].dt.year
    return df


DF = load()


# --------------------------------------------------------------------------- #
# walk-forward generique : refit annuel, purge = horizon, standardisation train #
# --------------------------------------------------------------------------- #
def walkforward(df, feats, target, horizon, kind, start_year=2014):
    sub = df.dropna(subset=[*feats, target]).reset_index(drop=True)
    out = []
    for yr in range(start_year, int(sub["year"].max()) + 1):
        test = sub[sub["year"] == yr]
        if test.empty:
            continue
        test_start = test.index.min()
        train = sub.iloc[:max(0, test_start - horizon)]  # purge = horizon
        if len(train) < 250:
            continue
        xtr = train[feats].to_numpy(float)
        xte = test[feats].to_numpy(float)
        mu, sd = xtr.mean(0), xtr.std(0)
        sd[sd == 0] = 1
        xtr = (xtr - mu) / sd
        xte = (xte - mu) / sd
        if kind == "clf":
            m = LogisticRegression(C=1.0, max_iter=1000)
            m.fit(xtr, train[target].to_numpy(int))
            pred = m.predict_proba(xte)[:, 1]
        else:
            m = Ridge(alpha=1.0)
            m.fit(xtr, train[target].to_numpy(float))
            pred = m.predict(xte)
        o = test[["Date", "year", target]].copy()
        o["pred"] = pred
        out.append(o)
    return pd.concat(out).reset_index(drop=True) if out else pd.DataFrame()


def boot_auc(y, p, b=1000):
    y, p = np.asarray(y), np.asarray(p)
    n = len(y)
    vals = []
    for _ in range(b):
        idx = RNG.integers(0, n, n)
        if len(np.unique(y[idx])) < 2:
            continue
        vals.append(roc_auc_score(y[idx], p[idx]))
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(lo), float(hi)


# --------------------------------------------------------------------------- #
# M1 - CBOT Downside Risk                                                       #
# --------------------------------------------------------------------------- #
def run_m1():
    res = {}
    for h, tgt in [(30, "y_down_gt_3pct_h30"), (60, "y_down_gt_3pct_h60")]:
        oos = walkforward(DF, FEAT_M1, tgt, h, "clf")
        y, p = oos[tgt].to_numpy(int), oos["pred"].to_numpy(float)
        auc = roc_auc_score(y, p)
        lo, hi = boot_auc(y, p)
        base = float(y.mean())
        # par annee
        per = []
        for yr, g in oos.groupby("year"):
            yy, pp = g[tgt].to_numpy(int), g["pred"].to_numpy(float)
            a = roc_auc_score(yy, pp) if len(np.unique(yy)) > 1 else np.nan
            da = float(((pp > 0.5).astype(int) == yy).mean())
            per.append((yr, len(g), float(yy.mean()), a, da))
        per = pd.DataFrame(per, columns=["year", "n", "base_rate", "auc", "da"])
        # calibration
        bins = np.linspace(0, 1, 11)
        oos["bin"] = pd.cut(p, bins, include_lowest=True)
        cal = oos.groupby("bin", observed=True).agg(
            pred_mean=("pred", "mean"), obs_freq=(tgt, "mean"), n=("pred", "size")).reset_index()
        # abstention : confiance = |p - 0.5|
        conf = np.abs(p - 0.5)
        absten = []
        for thr in [0.0, 0.05, 0.10, 0.15, 0.20]:
            mask = conf >= thr
            if mask.sum() == 0:
                continue
            da = float(((p[mask] > 0.5).astype(int) == y[mask]).mean())
            absten.append((thr, int(mask.sum()), float(mask.mean()), da))
        absten = pd.DataFrame(absten, columns=["conf_min", "n", "couverture", "da"])
        res[h] = {"oos": oos, "auc": auc, "ci": (lo, hi), "base": base,
                  "per": per, "cal": cal, "absten": absten, "tgt": tgt}
    return res


# --------------------------------------------------------------------------- #
# M3 - Volatility regime                                                        #
# --------------------------------------------------------------------------- #
def run_m3():
    oos = walkforward(DF, FEAT_M3, "y_realized_vol_h20", 20, "reg")
    y = oos["y_realized_vol_h20"].to_numpy(float)
    p = oos["pred"].to_numpy(float)
    base = oos.merge(DF[["Date", "corn_realized_vol_20"]], on="Date")["corn_realized_vol_20"].to_numpy(float)
    rmse_m = float(np.sqrt(np.mean((y - p) ** 2)))
    rmse_b = float(np.sqrt(np.mean((y - base) ** 2)))
    gain = 100 * (rmse_m - rmse_b) / rmse_b
    per = []
    for yr, g in oos.groupby("year"):
        gg = g.merge(DF[["Date", "corn_realized_vol_20"]], on="Date")
        yy, pp, bb = (gg["y_realized_vol_h20"].to_numpy(float), gg["pred"].to_numpy(float),
                      gg["corn_realized_vol_20"].to_numpy(float))
        per.append((yr, len(gg), float(np.sqrt(np.mean((yy - pp) ** 2))),
                    float(np.sqrt(np.mean((yy - bb) ** 2)))))
    per = pd.DataFrame(per, columns=["year", "n", "rmse_model", "rmse_baseline"])
    q = np.quantile(p, [0.33, 0.66, 0.90])
    return {"oos": oos, "base": base, "rmse_m": rmse_m, "rmse_b": rmse_b, "gain": gain,
            "per": per, "regime_q": q}


# --------------------------------------------------------------------------- #
# M4 - Euronext Premium (reversion du basis, research-only)                     #
# --------------------------------------------------------------------------- #
def run_m4():
    d = DF.dropna(subset=["ema_cbot_basis_zscore_52w", "ema_liquid_price"]).reset_index(drop=True)
    bz = d["ema_cbot_basis_zscore_52w"].to_numpy(float)
    ema = d["ema_liquid_price"].to_numpy(float)
    rows = []
    for h in (60, 90):
        fwd_bz = np.full(len(bz), np.nan)
        fwd_ret = np.full(len(bz), np.nan)
        fwd_bz[:-h] = bz[h:] - bz[:-h]
        fwd_ret[:-h] = np.log(ema[h:] / ema[:-h])
        high = bz > 2
        low = bz < 0
        rows.append({
            "horizon": h,
            "delta_bz_high": float(np.nanmean(fwd_bz[high])),
            "ret_high_pct": float(100 * np.nanmean(fwd_ret[high])),
            "ret_low_pct": float(100 * np.nanmean(fwd_ret[low])),
            "n_high": int(np.sum(high & ~np.isnan(fwd_ret))),
        })
    return {"table": pd.DataFrame(rows)}


# --------------------------------------------------------------------------- #
# fiches graphiques (P2)                                                        #
# --------------------------------------------------------------------------- #
def _box(ax, txt, color):
    ax.text(0.012, 0.97, txt, transform=ax.transAxes, va="top", ha="left", fontsize=9,
            bbox={"boxstyle": "round,pad=0.45", "fc": "white", "ec": color, "lw": 1.5, "alpha": .93})


def fiche_m1(m1):
    r = m1[60]
    oos = r["oos"].merge(DF[["Date", "cbot"]] if "cbot" in DF
                         else DF[["Date", "cbot_eur_t"]].rename(columns={"cbot_eur_t": "cbot"}),
                         on="Date")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12.4, 8), sharex=True,
                                   gridspec_kw={"height_ratios": [2, 1]})
    ax1.plot(oos["Date"], oos["cbot"], color=BLUE, lw=1)
    hi = oos["pred"] > 0.5
    ax1.scatter(oos["Date"][hi], oos["cbot"][hi], s=8, color=RED, alpha=0.5,
                label="risque de baisse eleve (p>0.5)")
    ax1.set_ylabel("CBOT (EUR/t)")
    ax1.legend(loc="upper left", fontsize=9)
    lo, hi2 = r["ci"]
    _box(ax1, f"M1 CBOT Downside Risk H60 (baisse > 3 %)\nAUC {r['auc']:.3f}  IC95 "
              f"[{lo:.3f} ; {hi2:.3f}]  base {r['base']:.2f}  n={len(oos)}  (OOS 2014-2025)", RED)
    ax2.plot(oos["Date"], oos["pred"], color=RED, lw=0.7)
    ax2.axhline(r["base"], ls="--", color="k", lw=1)
    ax2.set_ylabel("prob. de baisse")
    ax2.xaxis.set_major_locator(mdates.YearLocator(2))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.suptitle("M1 - Risque de baisse CBOT previsible (walk-forward hors echantillon)",
                 fontsize=14, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUT / "fiche_m1_downside.png", bbox_inches="tight")
    plt.close(fig)


def fiche_peryear(m1):
    per = m1[60]["per"]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    x = np.arange(len(per))
    cols = [GREEN if a > 0.55 else (ORANGE if a > 0.5 else RED) for a in per["auc"]]
    ax.bar(x, per["auc"], color=cols)
    ax.axhline(0.5, ls="--", color="k")
    ax.set_xticks(x)
    ax.set_xticklabels(per["year"], rotation=0)
    ax.set_ylabel("AUC")
    ax.set_title("M1 - AUC PAR ANNEE (verifie que ce n'est pas qu'une seule annee)",
                 fontsize=12, fontweight="bold")
    for xi, a, n in zip(x, per["auc"], per["n"], strict=False):
        ax.text(xi, a, f"{a:.2f}\nn={n}", ha="center", va="bottom", fontsize=7.5)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(OUT / "fiche_m1_par_annee.png", bbox_inches="tight")
    plt.close(fig)


def fiche_calibration(m1):
    cal = m1[60]["cal"]
    fig, ax = plt.subplots(figsize=(6.2, 6))
    ax.plot([0, 1], [0, 1], ls="--", color="k", label="calibration parfaite")
    ax.plot(cal["pred_mean"], cal["obs_freq"], "o-", color=RED, label="modele M1")
    ax.set_xlabel("probabilite predite")
    ax.set_ylabel("frequence observee")
    ax.set_title("M1 - Calibration (fiabilite des probabilites)", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "fiche_m1_calibration.png", bbox_inches="tight")
    plt.close(fig)


def fiche_abstention(m1):
    ab = m1[60]["absten"]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    x = np.arange(len(ab))
    ax.bar(x, ab["da"], color=[GREY if c == 0 else GREEN for c in ab["conf_min"]])
    ax.axhline(0.5, ls="--", color="k")
    ax.set_xticks(x)
    ax.set_xticklabels([f"|p-0.5|>={c}\ncouv. {cov:.0%}"
                        for c, cov in zip(ab["conf_min"], ab["couverture"], strict=False)])
    ax.set_ylabel("DA (bonne direction)")
    ax.set_title("Confidence Gate - la DA monte quand on n'agit que sur les signaux confiants",
                 fontsize=11.5, fontweight="bold")
    for xi, da in zip(x, ab["da"], strict=False):
        ax.text(xi, da, f"{da:.3f}", ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, max(0.8, ab["da"].max() + 0.08))
    fig.tight_layout()
    fig.savefig(OUT / "fiche_confidence_abstention.png", bbox_inches="tight")
    plt.close(fig)


def fiche_m3(m3):
    oos = m3["oos"]
    fig, ax = plt.subplots(figsize=(12.4, 5))
    ax.plot(oos["Date"], 100 * oos["y_realized_vol_h20"], color=GREY, lw=1, label="vol realisee future (cible)")
    ax.plot(oos["Date"], 100 * oos["pred"], color=PURPLE, lw=0.9, label="M3 modele (walk-forward)")
    ax.set_ylabel("volatilite annualisee (%)")
    _box(ax, f"M3 Volatility H20  RMSE modele {m3['rmse_m']:.3f} vs baseline {m3['rmse_b']:.3f} "
             f"({m3['gain']:+.1f} %)  n={len(oos)}  (OOS 2014-2025)", PURPLE)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title("M3 - Regime de volatilite previsible (hors echantillon)",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "fiche_m3_volatility.png", bbox_inches="tight")
    plt.close(fig)


def fiche_m4(m4):
    t = m4["table"]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    h = t[t["horizon"] == 90].iloc[0]
    x = np.arange(2)
    ax.bar(x, [h["ret_high_pct"], h["ret_low_pct"]], color=[RED, GREEN])
    ax.axhline(0, color="k")
    ax.set_xticks(x)
    ax.set_xticklabels(["basis HAUT (z>2)\nvendre la prime", "basis BAS (z<0)\nattendre"])
    ax.set_ylabel("retour EMA moyen a 90 j (%)")
    ax.set_title("M4 - Euronext Premium (research-only) : ordonne bien les retours futurs",
                 fontsize=11.5, fontweight="bold")
    for xi, v in zip(x, [h["ret_high_pct"], h["ret_low_pct"]], strict=False):
        ax.text(xi, v, f"{v:+.1f} %", ha="center", va="bottom" if v >= 0 else "top", fontsize=10)
    _box(ax, f"n(basis haut)={int(h['n_high'])}  delta basis_z futur (haut)={h['delta_bz_high']:+.2f} "
             "(reversion)\nresearch-only : prix EMA ~97 % proxy, couts a integrer", RED)
    fig.tight_layout()
    fig.savefig(OUT / "fiche_m4_premium.png", bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
def main():
    DF.rename(columns={"cbot_eur_t": "cbot"}, inplace=True)
    m1, m3, m4 = run_m1(), run_m3(), run_m4()

    # exports CSV
    m1[60]["per"].to_csv(OUT / "m1_par_annee.csv", index=False)
    m1[60]["cal"].astype(str).to_csv(OUT / "m1_calibration.csv", index=False)
    m1[60]["absten"].to_csv(OUT / "m1_abstention.csv", index=False)
    m3["per"].to_csv(OUT / "m3_par_annee.csv", index=False)
    m4["table"].to_csv(OUT / "m4_premium.csv", index=False)

    # graphiques (P2)
    fiche_m1(m1)
    fiche_peryear(m1)
    fiche_calibration(m1)
    fiche_abstention(m1)
    fiche_m3(m3)
    fiche_m4(m4)

    # snapshot (dernier signal connu)
    last = DF.dropna(subset=FEAT_M1).iloc[-1]
    snap = {"date": str(last["Date"].date()),
            "note": "signal indicatif (modele plein historique), research-only"}
    json.dump(snap, (OUT / "snapshot.json").open("w"), indent=2)

    # resume machine-lisible (pour la synthese / index.html)
    summ = {"m1_h60": {"auc": m1[60]["auc"], "ci": list(m1[60]["ci"]),
                       "base": m1[60]["base"], "n": int(len(m1[60]["oos"]))},
            "m1_h30": {"auc": m1[30]["auc"]},
            "m3": {"rmse_model": m3["rmse_m"], "rmse_baseline": m3["rmse_b"],
                   "gain_pct": m3["gain"], "n": int(len(m3["oos"]))}}
    json.dump(summ, (OUT / "summary.json").open("w"), indent=2)

    # rapport markdown
    a60 = m1[60]
    lo, hi = a60["ci"]
    md = ["# Indicateur selectif de risque V1 - validation walk-forward", "",
          "Validation hors echantillon (OOS 2014-2025), anti-leakage : refit annuel, purge = "
          "horizon entre train et test, standardisation train-only.", "",
          "## M1 - CBOT Downside Risk (le module le plus credible)", "",
          f"- Cible : baisse de plus de 3 % a H60. AUC = **{a60['auc']:.3f}** "
          f"(IC95 bootstrap [{lo:.3f} ; {hi:.3f}]), base rate {a60['base']:.2f}, n={len(a60['oos'])}.",
          f"- A H30 : AUC = {m1[30]['auc']:.3f} (IC95 [{m1[30]['ci'][0]:.3f} ; {m1[30]['ci'][1]:.3f}]).",
          "- Performance PAR ANNEE (extrait) :", ""]
    md += ["| annee | n | base | AUC | DA |", "|---|---|---|---|---|"]
    for _, r in a60["per"].iterrows():
        md.append(f"| {int(r['year'])} | {int(r['n'])} | {r['base_rate']:.2f} | "
                  f"{r['auc']:.3f} | {r['da']:.3f} |")
    md += ["", "- Confidence Gate / abstention (DA selon la confiance |p-0.5|) :", "",
           "| confiance min | couverture | DA |", "|---|---|---|"]
    for _, r in a60["absten"].iterrows():
        md.append(f"| >= {r['conf_min']:.2f} | {r['couverture']:.0%} | {r['da']:.3f} |")
    md += ["", f"Lecture : agir seulement sur les signaux confiants augmente la DA "
               f"(de {a60['absten'].iloc[0]['da']:.3f} sur tous les jours a "
               f"{a60['absten'].iloc[-1]['da']:.3f} sur les plus confiants), au prix de la couverture.",
           "", "## M3 - Volatility regime", "",
           f"- Cible : volatilite realisee H20. RMSE modele **{m3['rmse_m']:.3f}** vs baseline "
           f"persistance {m3['rmse_b']:.3f} ({m3['gain']:+.1f} %), n={len(m3['oos'])}.",
           "", "## M4 - Euronext Premium (research-only)", ""]
    for _, r in m4["table"].iterrows():
        md.append(f"- H{int(r['horizon'])} : basis haut -> retour EMA {r['ret_high_pct']:+.1f} %, "
                  f"basis bas -> {r['ret_low_pct']:+.1f} % (n haut={int(r['n_high'])}, "
                  f"delta basis_z futur {r['delta_bz_high']:+.2f} = reversion).")
    md += ["", "RESEARCH_ONLY : prix Euronext ~97 % proxy, couts a integrer (brut/net/+2/+5 EUR/t).",
           "", "## Statut", "",
           "V1 valide la THESE : on ne predit pas le prix, mais le risque de baisse et la "
           "volatilite sont previsibles hors echantillon, et l'abstention ameliore la qualite. "
           "Modules a fusionner ensuite (gate de confiance unique) ; couts reels et placebo "
           "etendu restent au backlog.", ""]
    (ROOT / "docs" / "INDICATOR_V1_VALIDATION.md").write_text("\n".join(md), encoding="utf-8")

    # index html
    imgs = ["fiche_m1_downside.png", "fiche_m1_par_annee.png", "fiche_m1_calibration.png",
            "fiche_confidence_abstention.png", "fiche_m3_volatility.png", "fiche_m4_premium.png"]
    html = ("<!doctype html><html lang='fr'><head><meta charset='utf-8'>"
            "<title>Indicateur selectif V1 - validation</title><style>"
            "body{font-family:system-ui,Arial,sans-serif;max-width:1100px;margin:24px auto;"
            "padding:0 16px}h1{margin-bottom:2px}img{width:100%;border:1px solid #ddd;"
            "border-radius:6px;margin:10px 0;background:#fff}</style></head><body>"
            "<h1>Indicateur selectif de risque V1</h1><p>Validation walk-forward hors echantillon "
            "(2014-2025), anti-leakage strict. Voir docs/INDICATOR_V1_VALIDATION.md.</p>"
            + "".join(f"<img src='{i}'>" for i in imgs) + "</body></html>")
    (OUT / "index.html").write_text(html, encoding="utf-8")

    print(f"M1 H60 AUC {a60['auc']:.3f} IC95 [{lo:.3f};{hi:.3f}] base {a60['base']:.2f} n={len(a60['oos'])}")
    print(f"M1 H30 AUC {m1[30]['auc']:.3f}")
    print(f"M3 RMSE {m3['rmse_m']:.3f} vs base {m3['rmse_b']:.3f} ({m3['gain']:+.1f}%)")
    print("abstention DA:", a60["absten"][["conf_min", "couverture", "da"]].to_dict("records"))
    print("ecrit : artefacts/indicator_v1/ (csv+png+html) + docs/INDICATOR_V1_VALIDATION.md")


if __name__ == "__main__":
    main()
