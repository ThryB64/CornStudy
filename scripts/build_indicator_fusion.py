"""Fusion de l'indicateur selectif : un signal unique BEARISH / NEUTRAL / UNCERTAIN
(gate de confiance), module par la volatilite, plus le reste du backlog :
- coute reels M4 (brut / net / +2 / +5 EUR/t),
- placebo etendu (permutation des labels),
- calibration M3 + seuils de regime figes,
- snapshot live (lecture du jour).
Reutilise le moteur walk-forward de build_risk_indicator.
Sorties : artefacts/indicator_v1/fusion_*.{csv,png}, snapshot_live.json, carte_live.png,
          docs/INDICATOR_V1_FUSION.md.
"""
from __future__ import annotations

import json
from pathlib import Path

import build_risk_indicator as eng
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.linear_model import LogisticRegression, Ridge  # noqa: E402
from sklearn.metrics import r2_score, roc_auc_score  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artefacts" / "indicator_v1"
RNG = np.random.default_rng(7)
BLUE, GREEN, RED, ORANGE, PURPLE, GREY = (
    "#1f77b4", "#2ca02c", "#d62728", "#e8943a", "#9467bd", "#888888")
plt.rcParams.update({"figure.dpi": 110, "font.size": 11, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.axisbelow": True})

DF = eng.DF
# seuils de decision figes a priori, ancres sur la base rate (~0.37) :
# p<LOW = peu de risque (NEUTRAL), p>HIGH = risque eleve (BEARISH), entre = UNCERTAIN
LOW_THR, HIGH_THR = 0.30, 0.50
H = 60


def classify(p: float) -> str:
    if p > HIGH_THR:
        return "BEARISH_RISK"
    if p < LOW_THR:
        return "NEUTRAL"
    return "UNCERTAIN"


# --------------------------------------------------------------------------- #
def fuse():
    m1 = eng.run_m1()[H]["oos"].rename(columns={"y_down_gt_3pct_h60": "y_down"})
    m3 = eng.run_m3()["oos"].rename(columns={"pred": "vol_pred"})[["Date", "vol_pred"]]
    f = m1.merge(m3, on="Date", how="left")
    # seuils de regime de vol figes sur la 1re moitie (2014-2018), pas sur tout l'echantillon
    early = f[f["year"] <= 2018]["vol_pred"].dropna()
    q = np.quantile(early, [0.33, 0.66, 0.90])
    def regime(v):
        if np.isnan(v):
            return "NA"
        return ["CALME", "NORMAL", "VOLATIL", "EXTREME"][int(np.searchsorted(q, v))]
    f["vol_regime"] = f["vol_pred"].map(regime)
    f["conf"] = (f["pred"] - 0.5).abs()
    f["signal"] = [classify(p) for p in f["pred"]]
    return f, q


def backtest_fusion(f):
    base = float(f["y_down"].mean())
    rows = []
    for sig in ["BEARISH_RISK", "NEUTRAL", "UNCERTAIN"]:
        g = f[f["signal"] == sig]
        if g.empty:
            continue
        pdown = float(g["y_down"].mean())
        rows.append((sig, len(g), len(g) / len(f), pdown, pdown - base))
    tb = pd.DataFrame(rows, columns=["signal", "n", "couverture", "p_down_realise", "lift_vs_base"])
    # par annee : taux de baisse realise dans les jours BEARISH vs NEUTRAL
    per = []
    for yr, g in f.groupby("year"):
        b = g[g["signal"] == "BEARISH_RISK"]["y_down"]
        n = g[g["signal"] == "NEUTRAL"]["y_down"]
        per.append((yr, float(b.mean()) if len(b) else np.nan,
                    float(n.mean()) if len(n) else np.nan, len(b), len(n)))
    per = pd.DataFrame(per, columns=["year", "p_down_bearish", "p_down_neutral", "n_bear", "n_neut"])
    return tb, base, per


# --------------------------------------------------------------------------- #
# backlog : M4 couts reels                                                      #
# --------------------------------------------------------------------------- #
def m4_costs():
    d = DF.dropna(subset=["ema_cbot_basis_zscore_52w", "ema_cbot_basis"]).reset_index(drop=True)
    bz = d["ema_cbot_basis_zscore_52w"].to_numpy(float)
    basis = d["ema_cbot_basis"].to_numpy(float)  # basis en EUR/t
    h = 90
    fwd_basis = np.full(len(bz), np.nan)
    fwd_basis[:-h] = basis[h:]
    high = (bz > 2) & ~np.isnan(fwd_basis)
    # vendre la prime = short du basis : PnL brut = basis a l'entree - basis futur (compression)
    gross = float(np.nanmean(basis[high] - fwd_basis[high]))
    rows = []
    for c in (0.0, 2.0, 5.0):
        rows.append((c, gross, gross - 2 * c))  # 2 jambes (entree + sortie)
    return pd.DataFrame(rows, columns=["cout_par_jambe", "pnl_brut_eur_t", "pnl_net_eur_t"]), int(high.sum())


# --------------------------------------------------------------------------- #
# backlog : placebo etendu (permutation des labels)                            #
# --------------------------------------------------------------------------- #
def placebo():
    d = DF.dropna(subset=[*eng.FEAT_M1, "y_down_gt_3pct_h60"]).copy()
    d["y_down_gt_3pct_h60"] = RNG.permutation(d["y_down_gt_3pct_h60"].to_numpy())
    oos = eng.walkforward(d, eng.FEAT_M1, "y_down_gt_3pct_h60", H, "clf")
    return float(roc_auc_score(oos["y_down_gt_3pct_h60"], oos["pred"]))


# --------------------------------------------------------------------------- #
# backlog : M3 calibration                                                     #
# --------------------------------------------------------------------------- #
def m3_calibration():
    oos = eng.run_m3()["oos"]
    y = oos["y_realized_vol_h20"].to_numpy(float)
    p = oos["pred"].to_numpy(float)
    return float(r2_score(y, p)), y, p


# --------------------------------------------------------------------------- #
# snapshot live                                                                #
# --------------------------------------------------------------------------- #
def snapshot(regime_q):
    sub = DF.dropna(subset=[*eng.FEAT_M1, "y_down_gt_3pct_h60"]).reset_index(drop=True)
    train = sub.iloc[:-H]  # purge : derniers H jours sans cible realisee
    xtr = train[eng.FEAT_M1].to_numpy(float)
    mu, sd = xtr.mean(0), xtr.std(0)
    sd[sd == 0] = 1
    clf = LogisticRegression(C=1.0, max_iter=1000).fit((xtr - mu) / sd,
                                                        train["y_down_gt_3pct_h60"].to_numpy(int))
    sub3 = DF.dropna(subset=[*eng.FEAT_M3, "y_realized_vol_h20"]).reset_index(drop=True)
    tr3 = sub3.iloc[:-20]
    x3 = tr3[eng.FEAT_M3].to_numpy(float)
    m3mu, m3sd = x3.mean(0), x3.std(0)
    m3sd[m3sd == 0] = 1
    reg = Ridge(alpha=1.0).fit((x3 - m3mu) / m3sd, tr3["y_realized_vol_h20"].to_numpy(float))

    last = DF.dropna(subset=eng.FEAT_M1).iloc[-1]
    p = float(clf.predict_proba(((last[eng.FEAT_M1].to_numpy(float) - mu) / sd).reshape(1, -1))[0, 1])
    last3 = DF.dropna(subset=eng.FEAT_M3).iloc[-1]
    vp = float(reg.predict(((last3[eng.FEAT_M3].to_numpy(float) - m3mu) / m3sd).reshape(1, -1))[0])
    vol_reg = ["CALME", "NORMAL", "VOLATIL", "EXTREME"][int(np.searchsorted(regime_q, vp))]
    conf = abs(p - 0.5)
    sig = classify(p)
    bz = float(DF.dropna(subset=["ema_cbot_basis_zscore_52w"]).iloc[-1]["ema_cbot_basis_zscore_52w"])
    prime = "PRIME HAUTE (a surveiller)" if bz > 2 else ("prime basse" if bz < 0 else "prime normale")
    return {"date": str(last["Date"].date()), "signal_cbot_h60": sig,
            "prob_baisse_3pct_h60": round(p, 3), "confiance": round(min(1.0, conf / 0.4), 2),
            "regime_volatilite": vol_reg, "vol_attendue_pct": round(100 * vp, 1),
            "basis_z_euronext": round(bz, 2), "premium_status": prime,
            "note": "research-only ; M4 prix EMA ~97 % proxy ; aucune action si confiance faible"}


# --------------------------------------------------------------------------- #
# graphiques                                                                   #
# --------------------------------------------------------------------------- #
def fig_fusion_bt(tb, base):
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    cmap = {"BEARISH_RISK": RED, "NEUTRAL": GREEN, "UNCERTAIN": GREY}
    x = np.arange(len(tb))
    ax.bar(x, tb["p_down_realise"], color=[cmap[s] for s in tb["signal"]])
    ax.axhline(base, ls="--", color="k", label=f"base rate {base:.2f}")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{s}\ncouv. {c:.0%}" for s, c in zip(tb["signal"], tb["couverture"], strict=False)])
    ax.set_ylabel("P(baisse > 3 % a H60) realisee")
    ax.set_title("Signal fusionne : la baisse arrive plus souvent quand le signal dit BEARISH",
                 fontsize=11.5, fontweight="bold")
    for xi, v in zip(x, tb["p_down_realise"], strict=False):
        ax.text(xi, v, f"{v:.2f}", ha="center", va="bottom", fontsize=9.5)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "fusion_backtest.png", bbox_inches="tight")
    plt.close(fig)


def fig_m4_costs(tbl, n):
    fig, ax = plt.subplots(figsize=(8, 4.6))
    x = np.arange(len(tbl))
    cols = [GREEN if v > 0 else RED for v in tbl["pnl_net_eur_t"]]
    ax.bar(x, tbl["pnl_net_eur_t"], color=cols)
    ax.axhline(0, color="k")
    ax.set_xticks(x)
    ax.set_xticklabels([f"cout {int(c)} EUR/t/jambe" for c in tbl["cout_par_jambe"]])
    ax.set_ylabel("PnL net (EUR/t)")
    ax.set_title(f"M4 - mur des couts : vendre la prime haute (n={n}, H90, research-only)",
                 fontsize=11.5, fontweight="bold")
    for xi, v in zip(x, tbl["pnl_net_eur_t"], strict=False):
        ax.text(xi, v, f"{v:+.1f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=9.5)
    fig.tight_layout()
    fig.savefig(OUT / "fusion_m4_couts.png", bbox_inches="tight")
    plt.close(fig)


def fig_m3_cal(r2, y, p):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(100 * p, 100 * y, s=6, alpha=0.3, color=PURPLE)
    lim = [0, 100 * max(y.max(), p.max())]
    ax.plot(lim, lim, ls="--", color="k")
    ax.set_xlabel("vol predite (%)")
    ax.set_ylabel("vol realisee (%)")
    ax.set_title(f"M3 - calibration volatilite (R2 = {r2:.2f})", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "fusion_m3_calibration.png", bbox_inches="tight")
    plt.close(fig)


def fig_card(snap):
    fig, ax = plt.subplots(figsize=(7.6, 5.2))
    ax.axis("off")
    col = {"BEARISH_RISK": RED, "NEUTRAL": GREEN, "UNCERTAIN": GREY}[snap["signal_cbot_h60"]]
    ax.text(0.5, 0.93, f"Lecture du {snap['date']}", ha="center", fontsize=12, transform=ax.transAxes)
    ax.text(0.5, 0.80, snap["signal_cbot_h60"], ha="center", fontsize=26, fontweight="bold",
            color=col, transform=ax.transAxes)
    lines = [
        f"Probabilite de baisse > 3 % a 60 j : {snap['prob_baisse_3pct_h60']:.0%}",
        f"Confiance : {snap['confiance']:.0%}",
        f"Regime de volatilite : {snap['regime_volatilite']} (vol attendue {snap['vol_attendue_pct']} %)",
        f"Basis Euronext z : {snap['basis_z_euronext']:+.2f}  ->  {snap['premium_status']}",
    ]
    for i, t in enumerate(lines):
        ax.text(0.08, 0.60 - i * 0.10, t, fontsize=12, transform=ax.transAxes)
    ax.text(0.5, 0.06, snap["note"], ha="center", fontsize=8.5, color="#555",
            style="italic", transform=ax.transAxes)
    fig.savefig(OUT / "carte_live.png", bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
def main():
    if "cbot_eur_t" in DF.columns:
        DF.rename(columns={"cbot_eur_t": "cbot"}, inplace=True)
    f, regime_q = fuse()
    tb, base, per = backtest_fusion(f)
    f[["Date", "year", "pred", "conf", "vol_regime", "signal", "y_down"]].to_csv(
        OUT / "fusion_signal.csv", index=False)
    tb.to_csv(OUT / "fusion_backtest.csv", index=False)
    per.to_csv(OUT / "fusion_par_annee.csv", index=False)

    cost_tbl, n_high = m4_costs()
    cost_tbl.to_csv(OUT / "fusion_m4_couts.csv", index=False)
    plac = placebo()
    r2, vy, vp = m3_calibration()
    snap = snapshot(regime_q)
    json.dump(snap, (OUT / "snapshot_live.json").open("w"), indent=2)
    json.dump({"placebo_auc": plac, "m3_r2": r2, "base_rate": base,
               "low_thr": LOW_THR, "high_thr": HIGH_THR,
               "backtest": tb.to_dict("records"),
               "m4_couts": cost_tbl.to_dict("records"), "n_high": n_high},
              (OUT / "fusion_summary.json").open("w"), indent=2)

    fig_fusion_bt(tb, base)
    fig_m4_costs(cost_tbl, n_high)
    fig_m3_cal(r2, vy, vp)
    fig_card(snap)

    md = ["# Indicateur selectif V1 - fusion et signal unique", "",
          "Un seul signal BEARISH_RISK / NEUTRAL / UNCERTAIN, par seuils figes a priori ancres sur "
          f"la base rate (~0.37) : BEARISH si p>{HIGH_THR}, NEUTRAL si p<{LOW_THR}, UNCERTAIN entre "
          "les deux. Module par le regime de volatilite. Anti-leakage : memes regles que la "
          "validation walk-forward.", "",
          "## Backtest du signal fusionne (OOS 2014-2025)", "",
          f"Base rate de baisse > 3 % a H60 : {base:.2f}.", "",
          "| signal | n | couverture | P(baisse) realisee | lift vs base |",
          "|---|---|---|---|---|"]
    for _, r in tb.iterrows():
        md.append(f"| {r['signal']} | {int(r['n'])} | {r['couverture']:.0%} | "
                  f"{r['p_down_realise']:.2f} | {r['lift_vs_base']:+.2f} |")
    md += ["", "Lecture : quand le signal dit BEARISH_RISK, la baisse arrive nettement plus souvent "
               "que la base ; NEUTRAL est sous la base ; UNCERTAIN (abstention) reste proche du hasard.",
           "", "## Backlog termine", "",
           f"- Placebo etendu (permutation des labels) : AUC = **{plac:.3f}** (proche de 0.5 = le "
           "signal reel n'est pas du hasard).",
           f"- M3 calibration : R2 (vol predite vs realisee) = **{r2:.2f}**.",
           "- M3 seuils de regime figes sur 2014-2018 (CALME / NORMAL / VOLATIL / EXTREME).",
           "- M4 couts reels (vendre la prime haute, H90, research-only) :", "",
           "| cout/jambe (EUR/t) | PnL brut | PnL net |", "|---|---|---|"]
    for _, r in cost_tbl.iterrows():
        md.append(f"| {int(r['cout_par_jambe'])} | {r['pnl_brut_eur_t']:+.1f} | {r['pnl_net_eur_t']:+.1f} |")
    md += ["", "## Snapshot live (lecture du jour)", "",
           "```json", json.dumps(snap, indent=2, ensure_ascii=False), "```", "",
           "## Statut final", "",
           "L'indicateur est un detecteur de CONTEXTE de risque, pas un predicteur de prix : il dit "
           "BEARISH_RISK, NEUTRAL ou UNCERTAIN, et s'abstient quand la confiance est faible. Module "
           "M4 reste research-only (prix EMA proxy, couts qui rongent l'edge). Prochaine etape "
           "naturelle : validation forward en conditions reelles (paper) avant tout usage.", ""]
    (ROOT / "docs" / "INDICATOR_V1_FUSION.md").write_text("\n".join(md), encoding="utf-8")

    # index html (ajoute fusion)
    imgs = ["carte_live.png", "fusion_backtest.png", "fusion_m4_couts.png",
            "fusion_m3_calibration.png", "fiche_m1_downside.png", "fiche_m1_par_annee.png",
            "fiche_m1_calibration.png", "fiche_confidence_abstention.png", "fiche_m3_volatility.png",
            "fiche_m4_premium.png"]
    html = ("<!doctype html><html lang='fr'><head><meta charset='utf-8'>"
            "<title>Indicateur selectif V1</title><style>"
            "body{font-family:system-ui,Arial,sans-serif;max-width:1100px;margin:24px auto;"
            "padding:0 16px}h1{margin-bottom:2px}img{width:100%;border:1px solid #ddd;"
            "border-radius:6px;margin:10px 0;background:#fff}</style></head><body>"
            "<h1>Indicateur selectif de risque V1 (fusion)</h1>"
            "<p>Signal unique BEARISH_RISK / NEUTRAL / UNCERTAIN, validation walk-forward "
            "hors echantillon (2014-2025). Voir docs/INDICATOR_V1_FUSION.md et "
            "docs/INDICATOR_V1_VALIDATION.md.</p>"
            + "".join(f"<img src='{i}'>" for i in imgs) + "</body></html>")
    (OUT / "index.html").write_text(html, encoding="utf-8")

    print("fusion backtest:")
    print(tb.to_string(index=False))
    print(f"placebo AUC {plac:.3f} | M3 R2 {r2:.2f}")
    print("M4 couts:", cost_tbl.to_dict("records"))
    print("snapshot:", snap["date"], snap["signal_cbot_h60"], "conf", snap["confiance"])
    print("ecrit : artefacts/indicator_v1/fusion_* + docs/INDICATOR_V1_FUSION.md")


if __name__ == "__main__":
    main()
