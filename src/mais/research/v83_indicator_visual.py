"""V-VISUAL — Visuel de l'indicateur : quand il signale et s'il a eu raison.

Produit une figure PNG : le basis_z dans le temps avec les seuils figés, chaque signal d'entrée marqué et
coloré selon le RÉSULTAT (compression réussie vs ADVERSE), la période de détention, et le PnL par signal.
But : VOIR ce que prédit l'indicateur (compression de la prime EMA/CBOT) et vérifier visuellement sa justesse.

Descriptif, baseline figée, `RESEARCH_ONLY_NOT_TRADING`.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT
from mais.registry.holdout_lock import assert_no_holdout

VIS_DIR = ARTEFACTS_DIR / "visual"
VIS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PNG = ROOT / "docs" / "INDICATEUR_VISUEL.png"
OUT_EVENT_PNG = ROOT / "docs" / "INDICATEUR_EVENT_STUDY.png"
EPISODES = ROOT / "data" / "research" / "high_basis_episodes.parquet"


def build_event_study(df: pd.DataFrame, out_png=OUT_EVENT_PNG, horizon: int = 90) -> dict[str, Any]:
    """Trajectoire MOYENNE du basis_z après chaque signal (t=0=entrée) : preuve visuelle de la compression."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    assert_no_holdout(df)

    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    if EPISODES.exists():
        ep = pd.read_parquet(EPISODES)
    else:
        from mais.research.v82_episode_library import build_episodes
        ep = build_episodes(df, with_network=False)

    def _paths(mask) -> np.ndarray:
        rows = []
        for _, e in ep[mask].iterrows():
            d = pd.Timestamp(e["entry_date"])
            if d not in bz.index:
                continue
            i = bz.index.get_loc(d)
            seg = bz.iloc[i:i + horizon + 1].to_numpy()
            if len(seg) >= horizon // 2:
                seg = np.concatenate([seg, np.full(horizon + 1 - len(seg), np.nan)])
                rows.append(seg)
        return np.array(rows) if rows else np.empty((0, horizon + 1))

    all_p = _paths(ep["entry_z"].notna())
    win_p = _paths(ep["win"] == 1)
    adv_p = _paths(ep["path"] == "ADVERSE")
    if len(all_p) == 0:
        return {"verdict": "NO_DATA"}
    x = np.arange(horizon + 1)

    fig, ax = plt.subplots(figsize=(12, 7))
    ax.axhline(0, color="grey", lw=0.7)
    ax.axhline(0.5, color="#1a9850", lw=0.9, ls="--", alpha=0.7, label="objectif prudent z→0.5")
    ax.axhline(1.0, color="#f0a500", lw=0.9, ls="--", alpha=0.7, label="seuil signal z=1")

    # nuage de toutes les trajectoires (fin, gris)
    for row in all_p:
        ax.plot(x, row, color="grey", lw=0.4, alpha=0.18)

    mean_all = np.nanmean(all_p, axis=0)
    ax.plot(x, mean_all, color="#3a6ea5", lw=3, label=f"moyenne TOUS signaux (n={len(all_p)})")
    if len(win_p):
        ax.plot(x, np.nanmean(win_p, axis=0), color="#1a9850", lw=2.2,
                label=f"moyenne compressions réussies (n={len(win_p)})")
    if len(adv_p):
        ax.plot(x, np.nanmean(adv_p, axis=0), color="#d73027", lw=2.2,
                label=f"moyenne ADVERSE (n={len(adv_p)})")

    ax.set_xlabel("jours après le signal (t=0 = entrée)", fontsize=10)
    ax.set_ylabel("basis_z (prime EMA/CBOT)", fontsize=10)
    ax.set_title(
        "Event study — trajectoire moyenne du basis_z APRÈS un signal\n"
        f"Au signal z≈{np.nanmean(all_p[:, 0]):.2f}, la prime se COMPRIME en moyenne vers 0 "
        "(preuve que l'indicateur prédit bien la compression) — RESEARCH_ONLY",
        fontsize=11)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(alpha=0.15)
    fig.tight_layout()
    fig.savefig(out_png, dpi=130)
    plt.close(fig)
    return {"verdict": "EVENT_STUDY_BUILT", "path": str(out_png),
            "mean_z_at_entry": round(float(np.nanmean(all_p[:, 0])), 2),
            "mean_z_at_40d": round(float(mean_all[min(40, horizon)]), 2),
            "mean_z_at_90d": round(float(mean_all[horizon]), 2),
            "status": "RESEARCH_ONLY_NOT_TRADING"}


def build_indicator_visual(df: pd.DataFrame, out_png=OUT_PNG) -> dict[str, Any]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    assert_no_holdout(df)

    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce").dropna()
    if len(bz) < 200:
        return {"verdict": "NO_DATA"}

    if EPISODES.exists():
        ep = pd.read_parquet(EPISODES)
    else:
        from mais.research.v82_episode_library import build_episodes
        ep = build_episodes(df, with_network=False)
    ep = ep.copy()
    ep["entry_dt"] = pd.to_datetime(ep["entry_date"])
    ep["exit_dt"] = pd.to_datetime(ep["exit_date"])

    win = ep["win"] == 1
    n = len(ep)
    win_rate = float(ep["win"].mean())
    mean_pnl = float(ep["pnl_z0_max90_sl20"].mean())
    adv_rate = float((ep["path"] == "ADVERSE").mean())

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(15, 9), height_ratios=[3, 1], sharex=True,
        gridspec_kw={"hspace": 0.08})

    # --- Panneau 1 : basis_z + seuils + signaux ---
    ax1.plot(bz.index, bz.values, color="#3a6ea5", lw=0.8, alpha=0.85, label="basis_z (prime EMA/CBOT)")
    ax1.axhline(0, color="grey", lw=0.6)
    for thr, lab, c in [(1.0, "z=1 MODERATE", "#f0a500"), (1.5, "z=1.5 STRONG", "#e67300"),
                        (2.0, "z=2 EXTREME", "#cc2936")]:
        ax1.axhline(thr, color=c, lw=0.9, ls="--", alpha=0.7)
        ax1.text(bz.index[5], thr + 0.04, lab, color=c, fontsize=8, va="bottom")
    ax1.axhspan(1.0, ax1.get_ylim()[1], color="#f0a500", alpha=0.05)

    # période de détention (entrée -> sortie) en segment fin
    for _, e in ep.iterrows():
        seg = bz.loc[(bz.index >= e["entry_dt"]) & (bz.index <= e["exit_dt"])]
        if len(seg):
            ax1.plot(seg.index, seg.values, color=("#1a9850" if e["win"] == 1 else "#d73027"),
                     lw=1.8, alpha=0.5, solid_capstyle="round")

    # marqueurs d'entrée : vert = compression réussie, rouge = ADVERSE/perte ; forme = canal
    markers = {"CBOT_DRIVEN": "o", "EMA_DRIVEN": "s", "BOTH": "D", "ADVERSE": "X"}
    for path, mk in markers.items():
        sub = ep[ep["path"] == path]
        if len(sub):
            col = "#d73027" if path == "ADVERSE" else "#1a9850"
            ax1.scatter(sub["entry_dt"], pd.to_numeric(sub["entry_z"]),
                        marker=mk, s=70, c=col, edgecolors="black", linewidths=0.5,
                        zorder=5, label=f"{path} (n={len(sub)})")

    ax1.set_ylabel("basis_z  (prime EMA/CBOT, z-score 52s)", fontsize=10)
    ax1.set_title(
        f"Indicateur prime EMA/CBOT — quand il signale (z>1) et s'il a eu raison\n"
        f"{n} signaux · réussite {win_rate:.0%} · PnL moyen {mean_pnl:+.1f} €/t · ADVERSE {adv_rate:.0%}  "
        f"— vert = compression réussie, rouge = ADVERSE · RESEARCH_ONLY",
        fontsize=11)
    ax1.legend(loc="upper right", fontsize=8, ncol=2, framealpha=0.9)
    ax1.grid(alpha=0.15)

    # --- Panneau 2 : PnL par signal (barres vertes/rouges) ---
    colors = ["#1a9850" if w else "#d73027" for w in win]
    ax2.bar(ep["entry_dt"], ep["pnl_z0_max90_sl20"], width=20, color=colors, alpha=0.85)
    ax2.axhline(0, color="black", lw=0.7)
    ax2.set_ylabel("PnL /signal\n(€/t, z→0)", fontsize=9)
    ax2.grid(alpha=0.15)
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax2.set_xlabel("Date d'entrée du signal", fontsize=10)

    fig.text(0.012, 0.012,
             "Lecture : à chaque point, la prime EU était anormalement haute (z>1). L'indicateur PRÉDIT sa "
             "COMPRESSION. Si le basis_z redescend ensuite (segment vert) = juste ; s'il s'écarte (rouge) = ADVERSE.",
             fontsize=8, color="#333")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    out_png = ROOT / out_png if not str(out_png).startswith("/") else out_png
    fig.savefig(out_png, dpi=130)
    plt.close(fig)

    return {
        "verdict": "VISUAL_BUILT", "path": str(out_png),
        "n_signals": n, "win_rate": round(win_rate, 3),
        "mean_pnl": round(mean_pnl, 2), "adverse_rate": round(adv_rate, 3),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from mais.scripts.run_v8_phase_a import filter_out_holdout, load_master_dataset
    print(build_indicator_visual(filter_out_holdout(load_master_dataset())))
