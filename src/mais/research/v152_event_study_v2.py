"""V152 — Compression Event Study 2.0 (aligné sur le START A, avec CI bootstrap + censure).

Aligne la trajectoire du basis (z et €/t) sur le jour de DÉBUT de compression (déf. A, V153.start_events,
restreint aux départs où la prime était élevée basis_z>=1). Pour chaque offset relatif [-pre,+post] :
moyenne, médiane, quantiles 25/75, n épisodes NON censurés, et IC bootstrap 95 % de la moyenne.

Remplace les visuels « illustratifs » par un visuel-preuve. FINAL-only ne s'applique pas (historique
proxy/research figé). Anti-leakage : alignement ex-post sur un label causal, aucune décision live.
RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.research.v153_start_vs_inprogress import start_events

V152_DIR = ARTEFACTS_DIR / "v152"
V152_DIR.mkdir(parents=True, exist_ok=True)

PRE, POST = 30, 90
MIN_PREMIUM_Z = 1.0


def _aligned_matrix(series: pd.Series, start_idx: list[int], pre: int, post: int) -> np.ndarray:
    """Matrice (épisodes x offsets) ; NaN = censuré (hors série)."""
    n = len(series)
    vals = series.to_numpy(dtype=float)
    offs = post + pre + 1
    mat = np.full((len(start_idx), offs), np.nan)
    for r, s in enumerate(start_idx):
        lo, hi = s - pre, s + post
        for j, k in enumerate(range(lo, hi + 1)):
            if 0 <= k < n:
                mat[r, j] = vals[k]
    return mat


def _bootstrap_ci(mat: np.ndarray, n_boot: int = 1000, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """IC 95 % de la moyenne par offset, par rééchantillonnage des épisodes (lignes)."""
    rng = np.random.default_rng(seed)
    n_ep = mat.shape[0]
    boot_means = np.full((n_boot, mat.shape[1]), np.nan)
    for b in range(n_boot):
        idx = rng.integers(0, n_ep, n_ep)
        boot_means[b] = np.nanmean(mat[idx], axis=0)
    lo = np.nanpercentile(boot_means, 2.5, axis=0)
    hi = np.nanpercentile(boot_means, 97.5, axis=0)
    return lo, hi


def build_event_study(df: pd.DataFrame, pre: int = PRE, post: int = POST,
                      n_boot: int = 1000, make_plot: bool = True) -> dict[str, Any]:
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    ev = start_events(df).to_numpy()
    # départ retenu si la prime était élevée juste avant (basis_z>=1 sur [t-5,t])
    bz_arr = bz.to_numpy()
    starts = [i for i in range(len(df)) if ev[i] == 1
              and np.nanmax(bz_arr[max(0, i - 5):i + 1]) >= MIN_PREMIUM_Z]
    if len(starts) < 5:
        return {"version": "V152-EVENT-STUDY-2", "verdict": "TOO_FEW_EPISODES", "n_episodes": len(starts)}

    offsets = list(range(-pre, post + 1))
    out: dict[str, Any] = {"version": "V152-EVENT-STUDY-2", "verdict": "EVENT_STUDY_BUILT",
                           "n_episodes": len(starts), "pre": pre, "post": post,
                           "min_premium_z": MIN_PREMIUM_Z, "offsets": offsets, "series": {}}

    for name, series in (("basis_z", bz), ("basis_eur_t", basis)):
        mat = _aligned_matrix(series, starts, pre, post)
        with np.errstate(all="ignore"):
            mean = np.nanmean(mat, axis=0)
            median = np.nanmedian(mat, axis=0)
            q25 = np.nanpercentile(mat, 25, axis=0)
            q75 = np.nanpercentile(mat, 75, axis=0)
            n_at = np.sum(~np.isnan(mat), axis=0)
        lo, hi = _bootstrap_ci(mat, n_boot=n_boot)
        out["series"][name] = {
            "mean": [round(float(x), 4) for x in mean],
            "median": [round(float(x), 4) for x in median],
            "q25": [round(float(x), 4) for x in q25],
            "q75": [round(float(x), 4) for x in q75],
            "ci95_lo": [round(float(x), 4) for x in lo],
            "ci95_hi": [round(float(x), 4) for x in hi],
            "n_at_offset": [int(x) for x in n_at],
        }
    # lecture synthétique au point start (offset 0) et à +post
    z0 = out["series"]["basis_z"]["median"][pre]
    z_post = out["series"]["basis_z"]["median"][-1]
    out["median_basis_z_at_start"] = z0
    out["median_basis_z_at_post"] = z_post
    out["median_compression_over_window"] = round(z0 - z_post, 4)
    n_at = out["series"]["basis_z"]["n_at_offset"]
    out["censoring_note"] = (f"n épisodes non censurés varie de {min(n_at)} à {max(n_at)} sur "
                             f"[-{pre},+{post}] (censure aux deux bords : début/fin de série).")
    out["status"] = "RESEARCH_ONLY_NOT_TRADING"

    if make_plot:
        out["plot"] = _plot(out, offsets, pre)
    (V152_DIR / "v152_event_study.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def _plot(out: dict[str, Any], offsets: list[int], pre: int) -> str | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    s = out["series"]["basis_z"]
    x = np.array(offsets)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(x, s["q25"], s["q75"], alpha=0.15, color="tab:blue", label="q25–q75")
    ax.fill_between(x, s["ci95_lo"], s["ci95_hi"], alpha=0.3, color="tab:blue", label="IC95 moyenne")
    ax.plot(x, s["mean"], color="tab:blue", lw=2, label="moyenne")
    ax.plot(x, s["median"], color="tab:orange", lw=1.5, ls="--", label="médiane")
    ax.axvline(0, color="k", lw=1, ls=":")
    ax.axhline(0.5, color="green", lw=0.8, ls=":", label="objectif z=0.5")
    ax.set_title(f"Event study compression (START A) — n={out['n_episodes']} épisodes")
    ax.set_xlabel("jours relatifs au début de compression")
    ax.set_ylabel("basis_z")
    ax.legend(fontsize=8)
    path = V152_DIR / "v152_event_study.png"
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return str(path)
