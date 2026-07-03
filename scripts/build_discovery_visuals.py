"""Génère, pour chaque découverte et chaque modèle performant de l'étude, deux images :
1. un visuel de la découverte (ce qu'elle fait, le mécanisme, les chiffres réels) ;
2. la découverte reportée sur les vraies courbes CBOT et Euronext, avec le résultat par marché.
Sortie : artefacts/decouvertes/*.png + galerie.html + INDEX.md.
(L'index.html canonique, enrichi et avec l'indicateur final, est ecrit par build_discovery_synthese.)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artefacts" / "decouvertes"
OUT.mkdir(parents=True, exist_ok=True)

BLUE, GREEN, RED, ORANGE, GREY = "#1f77b4", "#2ca02c", "#d62728", "#e8943a", "#888888"
plt.rcParams.update({"figure.dpi": 110, "font.size": 11, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.axisbelow": True})


def load() -> pd.DataFrame:
    f = pd.read_parquet(ROOT / "data/processed/features.parquet")
    f["Date"] = pd.to_datetime(f["Date"])
    keep = {"cbot_eur_t": "cbot", "ema_liquid_price": "ema",
            "ema_cbot_basis": "basis", "ema_cbot_basis_zscore_52w": "basisz",
            "crop_ge_zscore_seasonal": "cropz", "wasde_stocks_to_use_ratio": "s2u",
            "corn_realized_vol_60": "vol60", "corn_wheat_ratio": "wcr",
            "is_harvest_season": "harvest"}
    df = f[["Date", *keep]].rename(columns=keep).set_index("Date").sort_index()
    return df


DF = load()
try:
    EP = pd.read_parquet(ROOT / "data/research/high_basis_episodes.parquet")
    EP["entry_date"] = pd.to_datetime(EP["entry_date"])
except Exception:
    EP = pd.DataFrame()


# --------------------------------------------------------------------------- #
# helpers courbes (image 2) : 2 panneaux CBOT + Euronext, avec note par marché #
# --------------------------------------------------------------------------- #
def _note(ax, txt, color):
    ax.text(0.012, 0.97, txt, transform=ax.transAxes, va="top", ha="left",
            fontsize=9.5, color="#111", bbox={"boxstyle": "round,pad=0.45",
            "fc": "white", "ec": color, "lw": 1.6, "alpha": 0.92})


def base_curves(title, cbot_res, ema_res):
    fig, (axc, axe) = plt.subplots(2, 1, figsize=(12.4, 8.2), sharex=True)
    c = DF["cbot"].dropna()
    e = DF["ema"].dropna()
    axc.plot(c.index, c.values, color=BLUE, lw=1.0)
    axe.plot(e.index, e.values, color=GREEN, lw=1.0)
    axc.set_ylabel("CBOT mais (EUR/t)")
    axe.set_ylabel("Euronext EMA (EUR/t)")
    axc.set_title("CBOT (Chicago)", fontsize=11, loc="left", color=BLUE)
    axe.set_title("Euronext (EMA, Europe)", fontsize=11, loc="left", color=GREEN)
    _note(axc, "CBOT : " + cbot_res, BLUE)
    _note(axe, "Euronext : " + ema_res, GREEN)
    axe.xaxis.set_major_locator(mdates.YearLocator(2))
    axe.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.suptitle(title, fontsize=14, fontweight="bold", y=0.985)
    return fig, axc, axe


def shade_high(axc, axe):
    bz = DF["basisz"]
    mask = bz > 2
    grp = (mask != mask.shift()).cumsum()
    for _, seg in DF[mask].groupby(grp[mask]):
        for ax in (axc, axe):
            ax.axvspan(seg.index[0], seg.index[-1], color=RED, alpha=0.16, lw=0)


def shade_season(axc, axe):
    h = DF["harvest"].fillna(0) > 0
    grp = (h != h.shift()).cumsum()
    for _, seg in DF[h].groupby(grp[h]):
        for ax in (axc, axe):
            ax.axvspan(seg.index[0], seg.index[-1], color=ORANGE, alpha=0.12, lw=0)


def shade_drawdown(axc, axe):
    c = DF["cbot"].dropna()
    dd = c / c.rolling(252, min_periods=60).max() - 1
    mask = dd < -0.18
    mask = mask.reindex(DF.index, fill_value=False)
    grp = (mask != mask.shift()).cumsum()
    for _, seg in DF[mask].groupby(grp[mask]):
        for ax in (axc, axe):
            ax.axvspan(seg.index[0], seg.index[-1], color=RED, alpha=0.14, lw=0)


def twin_series(ax, s, label, color):
    t = ax.twinx()
    t.plot(s.dropna().index, s.dropna().values, color=color, lw=0.9, alpha=0.85)
    t.set_ylabel(label, color=color)
    t.tick_params(axis="y", labelcolor=color)
    t.grid(False)


def shade_s2u(axc, axe):
    s = DF["s2u"].dropna()
    lo = s.quantile(0.33)
    tight = (DF["s2u"] < lo)  # stocks bas -> marche tendu
    grp = (tight != tight.shift()).cumsum()
    for _, seg in DF[tight.fillna(False)].groupby(grp[tight.fillna(False)]):
        for ax in (axc, axe):
            ax.axvspan(seg.index[0], seg.index[-1], color=GREEN, alpha=0.12, lw=0)


def mark_episodes(axc, axe):
    if EP.empty:
        return
    fam_color = {"ADVERSE": RED, "CBOT": BLUE, "EMA": GREEN}
    for _, r in EP.iterrows():
        if r.get("adverse", 0) == 1:
            fam = "ADVERSE"
        elif str(r.get("cbot_support", "")).upper() in ("HIGH", "MEDIUM", "1", "TRUE") \
                or r.get("cbot_support", 0) in (1, True):
            fam = "CBOT"
        else:
            fam = "EMA"
        d = r["entry_date"]
        for ax, col in ((axc, "cbot"), (axe, "ema")):
            s = DF[col]
            near = s.reindex([d]).dropna()
            if near.empty:
                near = s.loc[:d].dropna().tail(1)
            if not near.empty:
                ax.scatter([near.index[-1]], [near.values[-1]], s=42,
                           color=fam_color[fam], edgecolor="k", lw=0.5, zorder=5)


def curves(kind, title, cbot_res, ema_res):
    fig, axc, axe = base_curves(title, cbot_res, ema_res)
    if kind == "shade_high":
        shade_high(axc, axe)
    elif kind == "season":
        shade_season(axc, axe)
    elif kind == "drawdown":
        shade_drawdown(axc, axe)
    elif kind == "s2u":
        shade_s2u(axc, axe)
    elif kind == "crop":
        twin_series(axc, DF["cropz"], "Crop condition (z saison.)", "#7a4fb5")
    elif kind == "vol":
        twin_series(axc, DF["vol60"], "Vol realisee 60j", "#9467bd")
        twin_series(axe, DF["vol60"], "Vol realisee 60j", "#9467bd")
    elif kind == "wheatcorn":
        twin_series(axc, DF["wcr"], "Ratio mais/ble", "#8c564b")
        twin_series(axe, DF["wcr"], "Ratio mais/ble", "#8c564b")
    elif kind == "basis":
        twin_series(axe, DF["basis"], "Basis EMA-CBOT (EUR/t)", RED)
    elif kind == "basisz":
        twin_series(axe, DF["basisz"], "Basis z-score", RED)
        shade_high(axc, axe)
    elif kind == "episodes":
        mark_episodes(axc, axe)
    # kind == "plain" : courbes seules + notes
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    return fig


# --------------------------------------------------------------------------- #
# helpers concept (image 1)                                                    #
# --------------------------------------------------------------------------- #
def fig1(title, w=8.6, h=5.2):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.suptitle(title, fontsize=13, fontweight="bold")
    return fig, ax


def c_metric(p):
    fig, ax = fig1(p["title"])
    labels = [a for a, _ in p["bars"]]
    vals = [b for _, b in p["bars"]]
    ref = p.get("ref", 0.5)
    cols = [GREEN if v > ref else (RED if v < ref else GREY) for v in vals]
    y = np.arange(len(labels))
    ax.barh(y, vals, color=cols)
    ax.axvline(ref, ls="--", color="k", lw=1)
    ax.text(ref, len(labels) - 0.4, p.get("refnote", f"hasard {ref}"), fontsize=9, ha="left")
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel(p.get("xlabel", "AUC (1 = parfait, 0.5 = hasard)"))
    for yi, v in zip(y, vals, strict=False):
        ax.text(v, yi, f" {v:.3f}", va="center", fontsize=9.5)
    ax.invert_yaxis()
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def c_bars(p):
    fig, ax = fig1(p["title"])
    labels = [a for a, _ in p["bars"]]
    vals = [b for _, b in p["bars"]]
    cols = p.get("colors") or [BLUE] * len(labels)
    x = np.arange(len(labels))
    ax.bar(x, vals, color=cols)
    if "ref" in p:
        ax.axhline(p["ref"], ls="--", color="k", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel(p.get("ylabel", ""))
    for xi, v in zip(x, vals, strict=False):
        ax.text(xi, v, f"{v:g}", ha="center",
                va="bottom" if v >= 0 else "top", fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def c_reversion(p):
    fig, ax = fig1(p["title"])
    bz = DF["basisz"].dropna()
    trig = (bz.shift(1) <= 2) & (bz > 2)
    idx = np.where(trig.values)[0]
    arr = bz.values
    horizon = 90
    paths = [arr[i:i + horizon + 1] for i in idx if i + horizon < len(arr)]
    if paths:
        m = np.nanmean(np.array(paths), axis=0)
        ax.plot(range(len(m)), m, color=RED, lw=2)
        ax.axhline(0, color="k", lw=0.8)
        ax.axhline(0.5, color=GREEN, ls="--", lw=1)
        ax.text(len(m) - 1, 0.5, " cible z=0.5", color=GREEN, fontsize=9, va="bottom")
        ax.fill_between(range(len(m)), m, 0, color=RED, alpha=0.12)
    ax.set_xlabel("jours apres un basis tres haut (z>2)")
    ax.set_ylabel("basis z-score moyen")
    ax.text(0.98, 0.95, f"{len(paths)} episodes\ndemi-vie ~17 a 47 j",
            transform=ax.transAxes, ha="right", va="top", fontsize=9.5,
            bbox={"boxstyle": "round", "fc": "white", "ec": RED})
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def c_volfit(p):
    fig, ax = fig1(p["title"])
    v = DF["vol60"].dropna() * 100
    pred = v.shift(1)  # la vol d'hier predit tres bien celle d'aujourd'hui (persistance)
    ax.plot(v.index, v.values, color="#9467bd", lw=1, label="vol realisee 60j")
    ax.plot(pred.index, pred.values, color="k", lw=0.7, alpha=0.6, label="modele (HAR/EGARCH, schematique)")
    ax.set_ylabel("volatilite annualisee (%)")
    ax.legend(fontsize=9, loc="upper right")
    ax.text(0.02, 0.95, "HAR / EGARCH : -23 a -24 % de RMSE vs random walk",
            transform=ax.transAxes, va="top", fontsize=9.5,
            bbox={"boxstyle": "round", "fc": "white", "ec": "#9467bd"})
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def c_cost(p):
    fig, ax = fig1(p["title"])
    cost = np.linspace(0, 10, 100)
    net = 115 - 23 * cost  # PnL net decroit avec le cout par jambe (schematique, base +115)
    ax.plot(cost, net, color=BLUE, lw=2)
    ax.axhline(0, color="k", lw=1)
    cross = cost[np.argmin(np.abs(net))]
    ax.axvline(cross, color=RED, ls="--")
    ax.fill_between(cost, net, 0, where=net > 0, color=GREEN, alpha=0.15)
    ax.fill_between(cost, net, 0, where=net < 0, color=RED, alpha=0.15)
    ax.set_xlabel("cout par jambe (EUR/t)")
    ax.set_ylabel("PnL net cumule")
    ax.text(0.02, 0.06, "edge concentre sur les signaux extremes (z>2) ;\nsurvit ~5 EUR/t hors crise, s'efface au-dela",
            transform=ax.transAxes, va="bottom", fontsize=9,
            bbox={"boxstyle": "round", "fc": "white", "ec": RED})
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def c_text(p):
    fig, ax = fig1(p["title"])
    ax.axis("off")
    ax.text(0.5, 0.62, p["big"], ha="center", va="center", fontsize=22,
            fontweight="bold", color=p.get("bigcolor", RED), transform=ax.transAxes)
    ax.text(0.5, 0.30, p["sub"], ha="center", va="center", fontsize=11,
            color="#222", transform=ax.transAxes, wrap=True)
    fig.tight_layout()
    return fig


def concept(spec):
    t = spec["type"]
    if t == "metric":
        return c_metric(spec)
    if t == "bars":
        return c_bars(spec)
    if t == "reversion":
        return c_reversion(spec)
    if t == "volfit":
        return c_volfit(spec)
    if t == "cost":
        return c_cost(spec)
    return c_text(spec)


# --------------------------------------------------------------------------- #
# table des decouvertes / modeles                                             #
# --------------------------------------------------------------------------- #
D = []


def add(num, idx, cat, title, what, concept_spec, curves_kind, cbot_res, ema_res):
    D.append({"num": num, "id": idx, "cat": cat, "title": title, "what": what,
              "concept": concept_spec, "curves": curves_kind,
              "cbot": cbot_res, "ema": ema_res})


# ---- modeles performants & resultats exploitables ----
add(1, "random_walk", "Modele / resultat",
    "Le prix exact n'est pas previsible (random walk imbattable)",
    "Aucun des 36 couples (modele x horizon) ne bat 'le prix de demain = celui d'aujourd'hui'.",
    {"type": "text", "title": "Random walk imbattable en RMSE",
     "big": "0 / 36", "bigcolor": RED,
     "sub": "modeles testes qui battent la marche aleatoire (test de Diebold-Mariano, p<0.10).\n"
            "Le prix exact est imprevisible : il faut viser la DIRECTION, pas le niveau."},
    "plain", "prix exact non previsible (RMSE) : aucun modele ne bat la random walk.",
    "prix exact non previsible (RMSE) : meme conclusion sur l'Euronext.")

add(2, "indicateur_v9", "Modele / resultat",
    "Indicateur structurel de vente (basis + saison) - AUC 0.656",
    "Un indicateur a paliers fonde sur le basis et la saison atteint AUC 0.656.",
    {"type": "metric", "title": "Indicateur structurel V9 (basis + saison)",
     "bars": [("hasard", 0.5), ("indicateur V9", 0.656)]},
    "basisz", "le basis nourrit l'indicateur via la transmission CBOT->EMA.",
    "indicateur de vente de prime AUC 0.656 (basis_z + saison).")

add(3, "modele_2vars", "Modele / resultat",
    "Modele a 2 variables (basis_z + saison) - AUC 0.694",
    "Deux variables suffisent : la parcimonie bat les modeles complexes.",
    {"type": "metric", "title": "Modele 2 variables : basis_z + saison",
     "bars": [("hasard", 0.5), ("modele 2 vars", 0.694), ("indicateur V9", 0.656)]},
    "basisz", "appuie sur le basis CBOT-EMA, pas sur des dizaines de variables.",
    "AUC 0.694 avec seulement basis_z + saison : la simplicite gagne.")

add(4, "crop_h90", "Modele / resultat",
    "Crop Condition US -> direction a 90 jours - AUC 0.816 (holdout)",
    "La notation d'etat des cultures US donne la direction a 90 jours.",
    {"type": "metric", "title": "Crop Condition US -> direction H90",
     "bars": [("hasard", 0.5), ("crop H90 (recherche)", 0.724), ("crop H90 (holdout 2024+)", 0.816)]},
    "crop", "Crop Condition US : AUC 0.816 sur le holdout 2024+ (grosse recolte = baisse).",
    "se transmet a l'Euronext qui suit le CBOT (direction baissiere en 2024).")

add(5, "wasde_h40", "Modele / resultat",
    "WASDE stocks-sur-usage -> direction a 40 jours - DA 0.705",
    "Le ratio stocks-sur-usage du WASDE oriente la direction a 40 jours.",
    {"type": "metric", "title": "WASDE stocks/usage -> direction H40",
     "xlabel": "DA (taux de bonne direction ; 0.5 = hasard)",
     "bars": [("hasard", 0.5), ("WASDE s/u H40 (holdout)", 0.705)]},
    "s2u", "stocks US bas = marche tendu ; DA 0.705 a H40 sur le holdout.",
    "l'Euronext herite de la direction US via la cointegration.")

add(6, "volatilite", "Modele / resultat",
    "La volatilite est previsible (HAR / EGARCH, -24 % de RMSE)",
    "Les modeles HAR et EGARCH battent nettement la random walk sur la volatilite.",
    {"type": "volfit", "title": "Volatilite : HAR / EGARCH battent la random walk"},
    "vol", "vol previsible : HAR -23 %, EGARCH -23.7 % de RMSE (resultat le plus solide).",
    "meme persistance de volatilite sur l'Euronext (gate de risque).")

add(7, "drawdown_cbot", "Modele / resultat",
    "Le risque de drawdown CBOT est previsible - AUC 0.74",
    "On sait dire a l'avance quand le risque de forte baisse du CBOT monte.",
    {"type": "metric", "title": "Risque de drawdown CBOT (pas la direction)",
     "bars": [("hasard", 0.5), ("risque drawdown CBOT", 0.74)]},
    "drawdown", "risque de drawdown previsible AUC 0.74 (zones grisees = forts replis).",
    "un repli CBOT entraine l'Euronext : utile comme filtre de risque.")

add(8, "adverse_predictable", "Modele / resultat",
    "L'issue ADVERSE d'une vente de prime est previsible - AUC 0.72",
    "On ne sait pas COMMENT ca tourne mal, mais on estime le RISQUE a l'entree.",
    {"type": "metric", "title": "Issue ADVERSE previsible a l'entree (LOO)",
     "bars": [("hasard", 0.5), ("mecanisme (comment)", 0.48), ("issue ADVERSE (oui/non)", 0.72)]},
    "shade_high", "le risque d'echec se lit a l'entree (niveau + basis bas), AUC 0.72.",
    "permet de filtrer les ventes de prime risquees sur l'Euronext.")

add(9, "basis_reversion", "Modele / resultat",
    "Le basis revient a la moyenne (demi-vie 17 a 47 jours)",
    "Apres un basis tres haut, l'ecart EMA-CBOT redescend : signal de vente.",
    {"type": "reversion", "title": "Reversion du basis apres un pic (event study reel)"},
    "basisz", "le CBOT est l'ancre vers laquelle l'ecart revient.",
    "le basis EMA-CBOT revient a la moyenne : vendre la prime quand elle est haute.")

add(10, "sell_high_cost", "Modele / resultat",
    "Vendre quand le basis est haut survit aux couts (+115 hors crise)",
    "La regle 'vendre la prime haute' reste gagnante apres couts, hors crise.",
    {"type": "cost", "title": "Vendre le basis haut : PnL net vs cout par jambe"},
    "basisz", "le pari = hausse relative du CBOT pendant la compression.",
    "vendre une prime z>2 sur l'Euronext : +115 hors crise apres couts (~5 EUR/t).")

# ---- decouvertes (mecanisme) ----
add(11, "compression_cbot", "Decouverte",
    "La prime se compresse surtout quand le CBOT MONTE (6x)",
    "Vendre la prime revient a parier sur une hausse relative du CBOT.",
    {"type": "bars", "title": "Decomposition de la compression de prime",
     "bars": [("jambe CBOT", 6), ("jambe Euronext", 1)], "ylabel": "poids relatif",
     "colors": [BLUE, GREEN]},
    "shade_high", "la compression vient a ~69 % de la hausse CBOT (6x la jambe EMA).",
    "la prime EMA se reduit surtout par le haut (CBOT), peu par l'Euronext lui-meme.")

add(12, "asymmetry", "Decouverte",
    "Avantage asymetrique : vendre la prime haute bien plus que l'inverse",
    "Le short de prime haute est robuste ; le pari inverse ne l'est pas.",
    {"type": "bars", "title": "Asymetrie short (prime haute) vs long (prime basse)",
     "bars": [("short prime haute", 115), ("long prime basse", -10)],
     "ylabel": "PnL net (schematique)", "colors": [GREEN, RED], "ref": 0},
    "shade_high", "parier sur la baisse du CBOT (long prime) n'est pas robuste.",
    "vendre une prime haute marche ; acheter une prime basse, non.")

add(13, "cbot_support", "Decouverte",
    "Le support CBOT divise par 2 le risque ADVERSE et double le PnL",
    "Un CBOT qui soutient rend la compression plus sure et plus rapide.",
    {"type": "bars", "title": "Effet du support CBOT (risque ADVERSE et PnL)",
     "bars": [("risque ADVERSE\nsans support", 1.0), ("risque ADVERSE\navec support", 0.5),
              ("PnL\nsans support", 1.0), ("PnL\navec support", 2.0)],
     "ylabel": "multiple (sans support = 1)",
     "colors": [RED, GREEN, BLUE, BLUE]},
    "episodes", "un CBOT haussier : risque ADVERSE /2, PnL x2, reversion ~29 j vers z0 (87.5 %).",
    "les ventes de prime EMA reussissent surtout quand le CBOT soutient.")

add(14, "episodes", "Decouverte",
    "Trois familles d'episodes : CBOT_DRIVEN, EMA_DRIVEN, ADVERSE",
    "Les episodes tires par le CBOT gagnent presque toujours ; les ADVERSE jamais vraiment.",
    {"type": "bars", "title": "Episodes de prime haute : gain moyen par famille",
     "bars": [("CBOT_DRIVEN", 22.7), ("EMA_DRIVEN", 14.0), ("ADVERSE", 5.7)],
     "ylabel": "gain / excursion favorable", "colors": [BLUE, GREEN, RED]},
    "episodes", "CBOT_DRIVEN : gain ~100 % du temps ; ADVERSE distinguables tot.",
    "42 episodes EMA : familles nettement separees des l'entree.")

add(15, "exit_z05", "Decouverte",
    "La sortie partielle (revenir vers z=0.5) sauve des pertes",
    "Sortir a mi-chemin plutot qu'au retour complet evite les pertes en queue.",
    {"type": "bars", "title": "Objectif de sortie : z=0 (complet) vs z=0.5 (partiel)",
     "bars": [("2010 z->0", -1), ("2010 z->0.5", 23), ("2013 z->0", -5), ("2013 z->0.5", 30)],
     "ylabel": "PnL de l'episode", "colors": [RED, GREEN, RED, GREEN], "ref": 0},
    "basisz", "sortir tot evite d'attendre un retour complet qui n'arrive pas toujours.",
    "exit partiel z=0.5 : defaut prudent sur les ventes de prime EMA.")

add(16, "prime_locale", "Decouverte",
    "La prime europeenne est LOCALE : la macro ne l'explique pas (R2 -0.25)",
    "Les variables macro n'expliquent pas le basis hors echantillon.",
    {"type": "bars", "title": "La macro explique-t-elle le basis ? (R2 hors echantillon)",
     "bars": [("modele macro", -0.25), ("nul (moyenne)", 0.0)],
     "ylabel": "R2 hors echantillon", "colors": [RED, GREY], "ref": 0},
    "basis", "le CBOT n'explique pas non plus la prime locale europeenne.",
    "la prime EMA est une prime locale, pas un produit des fondamentaux mondiaux.")

add(17, "specificity", "Decouverte",
    "Specificite EU : la prime suit le basis (+0.59), pas le CBOT (-0.46)",
    "La prime correle avec le basis local et non avec le niveau du CBOT.",
    {"type": "bars", "title": "Avec quoi la prime correle-t-elle ?",
     "bars": [("corr(prime, basis)", 0.59), ("corr(prime, CBOT)", -0.46)],
     "ylabel": "correlation", "colors": [GREEN, RED], "ref": 0},
    "basis", "la prime n'est pas un artefact du niveau CBOT (corr -0.46).",
    "prime locale confirmee : elle vit avec le basis EMA-CBOT (+0.59).")

add(18, "halflife_extreme", "Decouverte",
    "La demi-vie du basis retrecit quand l'ecart est extreme",
    "Plus le basis est tendu, plus il revient vite a la moyenne.",
    {"type": "bars", "title": "Demi-vie de reversion du basis par regime",
     "bars": [("modere", 8.3), ("fort", 4.9), ("extreme", 3.3)],
     "ylabel": "demi-vie (jours)", "colors": [BLUE, ORANGE, RED]},
    "basisz", "le CBOT ramene l'ecart d'autant plus vite qu'il est extreme.",
    "un basis EMA tres haut se resorbe en ~3 jours (vs ~8 en regime modere).")

add(19, "marginal", "Decouverte",
    "Les signaux marginaux (z<1.2) sous-performent les signaux forts",
    "Un faible ecart rapporte bien moins qu'un ecart franc.",
    {"type": "bars", "title": "Gain selon la force du signal",
     "bars": [("marginal (z<1.2)", 6.1), ("fort (z eleve)", 14.1)],
     "ylabel": "gain moyen", "colors": [GREY, GREEN]},
    "shade_high", "ne vendre la prime que sur des ecarts francs (z eleve).",
    "les signaux EMA faibles rapportent ~2x moins : exiger un z eleve.")

add(20, "cbot_drops", "Decouverte",
    "Le CBOT predit mieux ses BAISSES que ses HAUSSES",
    "La predictabilite directionnelle est asymetrique du cote baissier.",
    {"type": "bars", "title": "Predictabilite directionnelle du CBOT",
     "bars": [("baisses", 0.62), ("hausses", 0.50)],
     "ylabel": "qualite de prediction", "colors": [GREEN, GREY], "ref": 0.5},
    "drawdown", "le signal d'offre US detecte surtout les baisses (recoltes).",
    "utile pour la VENTE : on detecte mieux quand vendre que quand attendre.")

add(21, "weather_extreme", "Decouverte",
    "Le signal meteo est dans les EXTREMES prevus, pas dans la moyenne",
    "Un dome de chaleur prevu en pollinisation deplace le prix ; la meteo moyenne non.",
    {"type": "bars", "title": "Effet d'un pic de chaleur prevu (pollinisation)",
     "bars": [("extreme prevu", 1.6), ("reste du temps", -2.3)],
     "ylabel": "rendement CBOT moyen (%)", "colors": [RED, BLUE], "ref": 0},
    "season", "pic de chaleur prevu : corr +0.31 avec le rendement CBOT.",
    "un ete de stress rend la prime EMA moins compressible (contexte).")

add(22, "wheat_corn", "Decouverte",
    "Le meilleur flag ADVERSE est l'ecart de prix ble/mais",
    "Le ratio ble/mais signale les ventes de prime qui vont mal tourner.",
    {"type": "metric", "title": "wheat_corn_z comme flag de risque ADVERSE",
     "bars": [("hasard", 0.5), ("wheat_corn_z", 0.653)]},
    "wheatcorn", "le ratio ble/mais est un contexte (corr 0.60), pas un predicteur direct.",
    "il aide a ecarter les ventes de prime EMA a risque (AUC 0.653).")

# ---- falsifications ----
add(23, "halflife_horizon", "Falsification",
    "La demi-vie du NIVEAU n'est PAS l'horizon de decision (x3)",
    "L'horizon analytique sous-estime trois fois l'horizon reel des trades.",
    {"type": "bars", "title": "Horizon : demi-vie analytique vs horizon reel des trades",
     "bars": [("analytique (demi-vie)", 9.5), ("reel (trades)", 28.6)],
     "ylabel": "jours", "colors": [GREY, RED]},
    "plain", "caler l'horizon sur le reel (28.6 j), pas sur la demi-vie (9.5 j).",
    "sur l'Euronext aussi : le retour prend ~3x plus longtemps que prevu.")

add(24, "weather_priced_in", "Falsification",
    "La meteo realisee est deja 'price-in' (AUC 0.508)",
    "Quand on observe la meteo, le marche l'a deja integree.",
    {"type": "metric", "title": "Meteo realisee comme predicteur (deja price-in)",
     "bars": [("hasard", 0.5), ("meteo realisee", 0.508)]},
    "plain", "la meteo moyenne realisee n'apporte aucun edge directionnel.",
    "meme constat cote Euronext : pas de signal exploitable de la meteo realisee.")

add(25, "granger", "Falsification",
    "L'explication 'fair-value' du basis est rejetee (Granger)",
    "La causalite de Granger est rejetee hors echantillon.",
    {"type": "text", "title": "Fair-value du basis : causalite de Granger rejetee",
     "big": "Granger : REJETE", "bigcolor": RED,
     "sub": "les fondamentaux ne 'causent' pas le basis hors echantillon (R2 -0.25).\n"
            "Le basis se suffit a lui-meme : on ne sur-interprete pas."},
    "plain", "pas de relation fair-value stable cote CBOT.",
    "le basis EMA n'est pas reconstituable par une juste valeur : prime locale.")

add(26, "complex_models", "Falsification",
    "Trend-following, stacking et deep learning echouent",
    "Le mais ne tend pas ; les modeles complexes sur-apprennent.",
    {"type": "text", "title": "Modeles complexes : aucun ne bat la reference",
     "big": "complexite = 0 gain", "bigcolor": RED,
     "sub": "trend-following (le mais ne tend pas), stacking et deep learning\n"
            "sur-apprennent et ne battent pas la random walk. La parcimonie gagne."},
    "plain", "aucun modele complexe ne bat la random walk sur le CBOT.",
    "idem sur l'Euronext : 2 variables suffisent, le reste sur-apprend.")

add(27, "placebo", "Falsification",
    "L'avantage du basis EMA n'est pas si specifique (placebo)",
    "Le test placebo retrouve une partie de l'effet sur des spreads temoins.",
    {"type": "text", "title": "Test placebo : specificite limitee de l'edge",
     "big": "placebo : effet partiel", "bigcolor": ORANGE,
     "sub": "une partie de l'avantage apparait aussi sur des spreads temoins\n"
            "sans lien attendu : prudence, l'edge n'est pas aussi unique qu'espere."},
    "plain", "controle negatif : une partie de l'effet n'est pas specifique.",
    "l'edge basis EMA doit etre pris avec prudence (pas 100 % specifique).")

add(28, "overfit", "Falsification",
    "Les strategies actives sont a risque de sur-ajustement (PSR/DSR/PBO)",
    "Les mesures dediees signalent un risque eleve de sur-ajustement.",
    {"type": "text", "title": "Anti-sur-ajustement : PSR / DSR / PBO",
     "big": "risque de sur-ajustement", "bigcolor": RED,
     "sub": "les backtests flatteurs ne survivent pas aux mesures PSR / DSR / PBO.\n"
            "On prefere assumer le simple plutot que d'optimiser le bruit."},
    "plain", "les performances actives sur le CBOT peuvent venir du hasard.",
    "meme garde-fou cote Euronext : ne pas sur-interpreter les backtests.")

add(29, "seasonal_inversion", "Falsification",
    "L'inversion saisonniere supposee du basis n'a pas resiste",
    "Une saisonnalite inverse attendue a ete falsifiee en forward.",
    {"type": "text", "title": "Inversion saisonniere du basis : falsifiee",
     "big": "saisonnalite inverse : NON", "bigcolor": RED,
     "sub": "l'hypothese d'une inversion saisonniere du basis ne s'est pas\n"
            "confirmee en forward : on garde la saisonnalite simple validee."},
    "season", "pas d'inversion saisonniere exploitable cote CBOT.",
    "sur l'Euronext non plus : la saisonnalite reste celle, simple, deja validee.")

# ---- limites ----
add(30, "cost_wall", "Limite",
    "Le mur des couts : l'avantage net est mince et conditionnel",
    "L'edge se concentre sur les extremes et s'efface vite avec les couts.",
    {"type": "cost", "title": "Mur des couts : PnL net vs cout par jambe"},
    "shade_high", "edge concentre sur z>2 ; au-dela de ~5 EUR/t, il disparait.",
    "vendre la prime EMA n'est rentable que sur des signaux francs, hors crise.")

add(31, "fragile", "Limite",
    "Le score de vente final est FRAGILE",
    "Il bat la random walk sur le holdout mais pas une simple saisonnalite.",
    {"type": "bars", "title": "Score de vente sur le holdout 2024+ (DA)",
     "bars": [("random walk", 0.5), ("score de vente", 0.686), ("saisonnalite simple", 0.752)],
     "ylabel": "DA (bonne direction)", "colors": [GREY, ORANGE, GREEN], "ref": 0.5},
    "crop", "DA 0.686 > random walk mais < saisonnalite (0.752) : a reconfirmer.",
    "sur l'Euronext : un repere utile, pas une preuve de robustesse.")

add(32, "euronext_ro", "Limite",
    "L'indicateur Euronext est RESEARCH_ONLY",
    "Il ordonne bien les retours mais discrimine mal hors echantillon (proxy 97 %).",
    {"type": "bars", "title": "Indicateur Euronext : retours futurs a 90 j par recommandation",
     "bars": [("SELL_PARTIAL", -5.8), ("WAIT", 5.1)],
     "ylabel": "retour moyen a 90 j (%)", "colors": [RED, GREEN], "ref": 0},
    "basisz", "le score vient du CBOT (basis et EUR/USD non integres).",
    "ordonne les retours (vendre -5.8 %, attendre +5.1 %) mais AUC 0.561, prix 97 % proxy.")

add(33, "direction_fusion", "Modele / resultat",
    "La fusion des fondamentaux d'offre est le meilleur modele directionnel (H90)",
    "Crop Condition + niveaux WASDE + ratio ble/mais combines battent chaque bloc isole "
    "pour predire la direction CBOT a 90 jours ; le marche seul ne predit rien.",
    {"type": "metric", "title": "Direction CBOT a 90 j : AUC walk-forward 2014-2026 par bloc",
     "bars": [("FUSION crop+WASDE+ble", 0.626), ("Crop condition", 0.604),
              ("Ratio ble/mais", 0.602), ("Niveaux WASDE", 0.570), ("Marche seul", 0.511)],
     "ref": 0.5},
    "crop", "fusion fondamentaux AUC 0.626 IC95 [0.607;0.646], placebo 0.489 ; echecs = "
    "chocs demande (2021, 2022) ; DA 0.63 -> 0.78 avec abstention.",
    "meme lecture cote Euronext : signal d'offre moyen terme, pas un signal de prime.")


# --------------------------------------------------------------------------- #
def main() -> None:
    rows = []
    for d in D:
        base = f"{d['num']:02d}_{d['id']}"
        f1 = concept(d["concept"])
        p1 = OUT / f"{base}_1_decouverte.png"
        f1.savefig(p1, bbox_inches="tight")
        plt.close(f1)

        f2 = curves(d["curves"], d["title"], d["cbot"], d["ema"])
        p2 = OUT / f"{base}_2_courbes.png"
        f2.savefig(p2, bbox_inches="tight")
        plt.close(f2)

        rows.append((d, p1.name, p2.name))

    # index markdown
    md = ["# Decouvertes de l'etude mais - visuels (CBOT & Euronext)", "",
          f"{len(D)} decouvertes / modeles, chacune avec 2 images : "
          "(1) ce que la decouverte fait, (2) report sur les vraies courbes CBOT et Euronext "
          "avec le resultat par marche.", ""]
    cats = []
    for d, a, b in rows:
        if d["cat"] not in cats:
            cats.append(d["cat"])
            md += [f"## {d['cat']}", ""]
        md += [f"### {d['num']:02d}. {d['title']}", "",
               d["what"], "",
               f"- CBOT : {d['cbot']}", f"- Euronext : {d['ema']}", "",
               f"![decouverte]({a})", "", f"![courbes]({b})", ""]
    (OUT / "INDEX.md").write_text("\n".join(md), encoding="utf-8")

    # index html autonome
    cards = []
    cur = None
    for d, a, b in rows:
        if d["cat"] != cur:
            cur = d["cat"]
            cards.append(f"<h2>{cur}</h2>")
        cards.append(
            f"<div class='card'><h3>{d['num']:02d}. {d['title']}</h3>"
            f"<p class='what'>{d['what']}</p>"
            f"<div class='imgs'><figure><figcaption>Ce que la decouverte fait</figcaption>"
            f"<img src='{a}'></figure>"
            f"<figure><figcaption>Sur les courbes CBOT &amp; Euronext</figcaption>"
            f"<img src='{b}'></figure></div>"
            f"<ul><li><b>CBOT :</b> {d['cbot']}</li>"
            f"<li><b>Euronext :</b> {d['ema']}</li></ul></div>")
    html = (
        "<!doctype html><html lang='fr'><head><meta charset='utf-8'>"
        "<title>Decouvertes - visuels CBOT & Euronext</title><style>"
        "body{font-family:system-ui,Arial,sans-serif;max-width:1180px;margin:24px auto;"
        "padding:0 16px;color:#1a1a1a}h1{margin-bottom:4px}h2{margin-top:34px;color:#333;"
        "border-bottom:2px solid #ddd;padding-bottom:4px}.card{border:1px solid #e2e2e2;"
        "border-radius:10px;padding:14px 16px;margin:16px 0;background:#fafafa}"
        ".what{color:#444;margin:.2em 0 .8em}.imgs{display:flex;gap:14px;flex-wrap:wrap}"
        "figure{margin:0;flex:1 1 360px}figcaption{font-size:.85em;color:#666;margin-bottom:4px}"
        "img{width:100%;border:1px solid #ddd;border-radius:6px;background:#fff}"
        "ul{margin:.6em 0 0;font-size:.95em}</style></head><body>"
        "<h1>Decouvertes de l'etude mais</h1>"
        "<p>Pour chaque decouverte et chaque modele performant : a gauche ce que la decouverte "
        "fait, a droite son report sur les vraies courbes CBOT et Euronext, avec le resultat "
        "par marche.</p>" + "".join(cards) + "</body></html>")
    (OUT / "galerie.html").write_text(html, encoding="utf-8")

    print(f"{len(D)} decouvertes -> {2 * len(D)} images dans {OUT}")
    print("galerie.html + INDEX.md ecrits")


if __name__ == "__main__":
    main()
