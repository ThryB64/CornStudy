"""V149 — Visuel multi-vues de l'indicateur : sur EMA, sur CBOT, et multi-seuils.

Trois sorties :
  1) docs/INDICATEUR_EMA_CBOT.png : les prix EMA (Euronext, €/t) et CBOT (€/t) dans le temps ; l'écart vertical
     = la prime/basis ; les entrées de signal (z>1) marquées sur la courbe EMA, colorées par tier.
  2) docs/INDICATEUR_MULTISEUIL.png : le basis_z avec PLUSIEURS seuils (0.5/0.75/1.0/1.25/1.5/2.0) et un panneau
     de répartition : combien de points par seuil et quel taux de compression. But : voir comment se
     répartissent les points au-delà du seuil officiel z>1 (on n'a que 42 trades), SANS changer la baseline.
  3) régénère le visuel V83 (épisodes) à jour.

DESCRIPTIF/EXPLORATOIRE : les seuils <1 sont montrés pour comprendre la distribution, ils NE deviennent PAS
la règle. Baseline figée z>1. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT
from mais.registry.holdout_lock import assert_no_holdout

VIS_DIR = ARTEFACTS_DIR / "visual"
VIS_DIR.mkdir(parents=True, exist_ok=True)
OUT_EMACBOT = ROOT / "docs" / "INDICATEUR_EMA_CBOT.png"
OUT_MULTI = ROOT / "docs" / "INDICATEUR_MULTISEUIL.png"
THRESHOLDS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
NON_OVERLAP_DAYS = 40
FWD_HORIZON = 90


def _tier(z: float) -> str:
    if z >= 2.0:
        return "EXTREME"
    if z >= 1.5:
        return "STRONG"
    if z >= 1.0:
        return "MODERATE"
    return "SUB"


def _nonoverlap_entries(bz: pd.Series, thr: float) -> list[int]:
    """Positions (iloc) des entrées z>=thr, non-chevauchantes (>=40 j calendaires)."""
    dates = bz.index
    cand = np.where(bz.to_numpy() >= thr)[0]
    kept, last = [], None
    for i in cand:
        if last is None or (dates[i] - dates[last]).days >= NON_OVERLAP_DAYS:
            kept.append(i)
            last = i
    return kept


def threshold_distribution(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Pour chaque seuil : n signaux non-chevauchants + taux de compression (z→≤0.5 sous 90 j) + €/t."""
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce").dropna()
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce").reindex(bz.index)
    rows = []
    vals = bz.to_numpy()
    bvals = basis.to_numpy()
    n = len(vals)
    for thr in THRESHOLDS:
        entries = _nonoverlap_entries(bz, thr)
        comp_ok, comp_z, comp_eur = [], [], []
        for i in entries:
            j = min(i + 1 + FWD_HORIZON, n)
            if i + 1 >= n:
                continue
            seg = vals[i + 1:j]
            min_z = np.nanmin(seg)
            comp_ok.append(1 if min_z <= 0.5 else 0)
            comp_z.append(float(vals[i] - min_z))
            if not np.isnan(bvals[i]):
                bseg = bvals[i + 1:j]
                if np.isfinite(bseg).any():
                    comp_eur.append(float(bvals[i] - np.nanmin(bseg)))
        rows.append({
            "threshold": thr,
            "n_signals": len(entries),
            "compression_rate_to_z05": round(float(np.mean(comp_ok)), 3) if comp_ok else None,
            "mean_compression_z": round(float(np.mean(comp_z)), 3) if comp_z else None,
            "mean_compression_eur_t": round(float(np.mean(comp_eur)), 1) if comp_eur else None,
        })
    return rows


def build_ema_cbot_visual(df: pd.DataFrame, out_png=OUT_EMACBOT) -> dict[str, Any]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    assert_no_holdout(df)

    sub = df[["ema_close", "cbot_eur_t", "ema_cbot_basis", "ema_cbot_basis_zscore_52w"]].copy()
    sub = sub.dropna(subset=["ema_close", "cbot_eur_t"])
    if len(sub) < 200:
        return {"verdict": "NO_DATA"}
    bz = pd.to_numeric(sub["ema_cbot_basis_zscore_52w"], errors="coerce")
    entries = _nonoverlap_entries(bz.dropna(), 1.0)
    edates = bz.dropna().index[entries]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 9), height_ratios=[3, 1.4], sharex=True,
                                   gridspec_kw={"hspace": 0.08})
    ax1.plot(sub.index, sub["ema_close"], color="#1f4e79", lw=1.0, label="EMA Euronext (€/t)")
    ax1.plot(sub.index, sub["cbot_eur_t"], color="#c55a11", lw=1.0, label="CBOT maïs (€/t éq.)")
    ax1.fill_between(sub.index, sub["cbot_eur_t"], sub["ema_close"],
                     where=(sub["ema_close"] >= sub["cbot_eur_t"]), color="#9bc2e6", alpha=0.35,
                     label="prime EMA/CBOT (basis)")
    # marqueurs d'entrée signal sur la courbe EMA
    ema_at = sub["ema_close"].reindex(edates)
    ax1.scatter(edates, ema_at, marker="v", s=55, c="#cc2936", edgecolors="black", linewidths=0.4,
                zorder=5, label=f"entrée signal z>1 (n={len(edates)})")
    ax1.set_ylabel("Prix (€/t)", fontsize=10)
    ax1.set_title("Indicateur de prime sur les COURBES EMA (Euronext) et CBOT\n"
                  "L'écart bleu = la prime ; ▼ rouge = l'indicateur signale (basis_z>1) une prime à comprimer "
                  "— RESEARCH_ONLY", fontsize=11)
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(alpha=0.15)

    ax2.plot(sub.index, sub["ema_cbot_basis"], color="#3a6ea5", lw=0.9, label="basis = EMA − CBOT (€/t)")
    ax2.axhline(float(pd.to_numeric(sub["ema_cbot_basis"], errors="coerce").mean()), color="grey", ls="--",
                lw=0.8, label="basis moyen")
    ax2.set_ylabel("basis (€/t)", fontsize=9)
    ax2.legend(loc="upper left", fontsize=8)
    ax2.grid(alpha=0.15)
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax2.set_xlabel("Date", fontsize=10)
    fig.tight_layout()
    fig.savefig(out_png, dpi=130)
    plt.close(fig)
    return {"verdict": "EMA_CBOT_VISUAL_BUILT", "path": str(out_png), "n_entries": int(len(edates)),
            "status": "RESEARCH_ONLY_NOT_TRADING"}


def build_multithreshold_visual(df: pd.DataFrame, out_png=OUT_MULTI) -> dict[str, Any]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    assert_no_holdout(df)

    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce").dropna()
    if len(bz) < 200:
        return {"verdict": "NO_DATA"}
    dist = threshold_distribution(df)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 9), height_ratios=[2.2, 1.4],
                                   gridspec_kw={"hspace": 0.22})
    # Panneau 1 : basis_z + seuils multiples + points par bande
    ax1.plot(bz.index, bz.values, color="#3a6ea5", lw=0.7, alpha=0.8, label="basis_z")
    ax1.axhline(0, color="grey", lw=0.6)
    band_colors = {0.5: "#9ecae1", 0.75: "#6baed6", 1.0: "#f0a500", 1.25: "#e6892b",
                   1.5: "#e3611c", 2.0: "#cc2936"}
    for thr in THRESHOLDS:
        c = band_colors[thr]
        ax1.axhline(thr, color=c, lw=0.9, ls="--", alpha=0.8)
        ax1.text(bz.index[5], thr + 0.02, f"z={thr}", color=c, fontsize=8, va="bottom")
        entries = _nonoverlap_entries(bz, thr)
        # ne marquer un point que dans sa bande la plus haute atteinte
        pts = [bz.index[i] for i in entries]
        ax1.scatter(pts, [bz.iloc[i] for i in entries], s=14, color=c, alpha=0.5, zorder=4)
    ax1.axhspan(1.0, max(2.6, float(bz.max())), color="#f0a500", alpha=0.05)
    ax1.set_ylabel("basis_z", fontsize=10)
    ax1.set_title("Indicateur multi-seuils — répartition des points au-delà de chaque seuil\n"
                  "Seuil officiel FIGÉ = z>1 ; les seuils 0.5/0.75 montrent les points 'marginaux' "
                  "(plus nombreux mais plus faibles) — DESCRIPTIF, baseline inchangée", fontsize=11)
    ax1.legend(loc="upper left", fontsize=8)
    ax1.grid(alpha=0.15)
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # Panneau 2 : n signaux (barres) + amplitude de compression (ligne) par seuil
    thrs = [d["threshold"] for d in dist]
    ns = [d["n_signals"] for d in dist]
    cz = [d["mean_compression_z"] for d in dist]
    x = np.arange(len(thrs))
    bars = ax2.bar(x, ns, width=0.55, color=[band_colors[t] for t in thrs], alpha=0.8)
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"z≥{t}" for t in thrs])
    ax2.set_ylabel("n signaux non-chevauchants", fontsize=9)
    for b, nval in zip(bars, ns, strict=False):
        ax2.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5, str(nval), ha="center", fontsize=8)
    ax2b = ax2.twinx()
    ax2b.plot(x, [c if c is not None else np.nan for c in cz], color="#1a9850", marker="o", lw=2,
              label="amplitude compression (Δz max sous 90j)")
    ax2b.set_ylabel("amplitude compression (z)", color="#1a9850", fontsize=9)
    ax2b.tick_params(axis="y", labelcolor="#1a9850")
    ax2.set_title("Baisser le seuil = PLUS de points (62 à z≥0.5 vs 18 à z≥2) ; le NIVEAU réverse partout "
                  "(taux z→≤0.5 ≈0.93-1.0, best-case) MAIS l'amplitude par signal ↓ et le PnL coût-aware "
                  "(stop/expo, V131) favorise les seuils élevés", fontsize=9)
    ax2.grid(alpha=0.15)
    fig.tight_layout()
    fig.savefig(out_png, dpi=130)
    plt.close(fig)
    return {"verdict": "MULTITHRESHOLD_VISUAL_BUILT", "path": str(out_png),
            "threshold_distribution": dist,
            "metric_caveat": ("taux de compression = z atteint ≤0.5 sous 90j = BEST-CASE (MFE-like), pas un PnL "
                              "réalisé : il flatte les seuils bas (cible plus proche). Le PnL coût-aware avec "
                              "stop/exposition (V131 : marginaux z<1.2 +6.09 vs confirmés +14.14 €/t) favorise "
                              "les seuils ÉLEVÉS. Baisser le seuil donne de la QUANTITÉ, pas de l'edge/trade."),
            "status": "RESEARCH_ONLY_NOT_TRADING"}


def run_v149_all(df: pd.DataFrame) -> dict[str, Any]:
    out = {"version": "V149-INDICATOR-MULTIVIEW",
           "ema_cbot": build_ema_cbot_visual(df),
           "multithreshold": build_multithreshold_visual(df)}
    # régénère aussi le visuel V83 (épisodes) à jour
    try:
        from mais.research.v83_indicator_visual import build_event_study, build_indicator_visual
        out["v83_visual"] = build_indicator_visual(df)
        out["v83_event_study"] = build_event_study(df)
    except Exception as exc:  # noqa: BLE001
        out["v83_visual"] = {"verdict": "SKIP", "reason": f"{type(exc).__name__}: {str(exc)[:60]}"}
    out["threshold_distribution"] = out["multithreshold"].get("threshold_distribution")
    out["status"] = "RESEARCH_ONLY_NOT_TRADING"
    import json
    (VIS_DIR / "v149_multiview.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    import json

    from mais.scripts.run_v8_phase_a import filter_out_holdout, load_master_dataset
    print(json.dumps(run_v149_all(filter_out_holdout(load_master_dataset())), indent=2, default=str))
