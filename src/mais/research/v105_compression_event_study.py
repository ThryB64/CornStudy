"""CT-02 (v105) — Event study AUTOUR du début de compression (t=0 = compression_start_date).

On aligne les épisodes sur le début de compression (def A, V104) et on regarde ce qui bouge AVANT (t-10..t=0) :
rendement CBOT, rendement EMA, variation basis_z, ratio blé/maïs, distance CBOT/SMA20, volatilité. But :
identifier le(s) précurseur(s) — le CBOT rattrape-t-il avant ? l'EMA s'essouffle-t-il ? le blé/maïs se
retourne-t-il ? Descriptif (le start est daté a posteriori) ; sert à concevoir le trigger causal (CT-10).

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout verrouillé. Baseline figée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT
from mais.registry.holdout_lock import assert_no_holdout

V105_DIR = ARTEFACTS_DIR / "v105"
V105_DIR.mkdir(parents=True, exist_ok=True)
TP_PARQUET = ROOT / "data" / "research" / "high_basis_episodes_with_turning_point.parquet"
EVENT_PNG = ROOT / "docs" / "COMPRESSION_TRIGGER_EVENT_STUDY.png"
PRE, POST = 20, 10


def _series(df: pd.DataFrame) -> dict[str, pd.Series]:
    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce")
    ema = pd.to_numeric(df.get("ema_close"), errors="coerce")
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    wheat = pd.to_numeric(df.get("wheat_close"), errors="coerce")
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    wc = corn / wheat
    return {"cbot": cbot, "ema": ema, "bz": bz, "wc": wc,
            "cbot_sma20": corn / corn.rolling(20, min_periods=10).mean() - 1.0}


def run_v105_event_study(df: pd.DataFrame, make_png: bool = True) -> dict[str, Any]:
    assert_no_holdout(df)
    if TP_PARQUET.exists():
        tp = pd.read_parquet(TP_PARQUET)
    else:
        from mais.research.v104_compression_start import build_turning_points
        tp = build_turning_points(df)
    tp = tp.dropna(subset=["compression_start_date"])
    if len(tp) < 15:
        return {"version": "V105-EVENT-STUDY", "verdict": "TOO_FEW", "n": int(len(tp))}

    s = _series(df)
    idx = df.index
    bz_paths, cbot_paths, ema_paths = [], [], []
    pre = {"cbot_ret_pre10": [], "ema_ret_pre10": [], "bz_change_pre5": [],
           "wc_change_pre10": [], "cbot_vs_sma20": []}
    pre_by_path: dict[str, list[float]] = {}
    for _, e in tp.iterrows():
        d0 = pd.Timestamp(e["compression_start_date"])
        if d0 not in df.index:
            continue
        i = idx.get_loc(d0)
        if i - PRE < 0 or i + POST >= len(idx):
            continue
        bzv = s["bz"].to_numpy()
        cb = s["cbot"].to_numpy()
        em = s["ema"].to_numpy()
        wc = s["wc"].to_numpy()
        sma = s["cbot_sma20"].to_numpy()
        bz_paths.append(bzv[i - PRE:i + POST + 1])
        cbot_paths.append(cb[i - PRE:i + POST + 1] / cb[i] - 1.0)
        ema_paths.append(em[i - PRE:i + POST + 1] / em[i] - 1.0)
        # mouvements AVANT le start (fenêtre [t-10, t-1] -> connue à t-1)
        if not np.isnan(cb[i - 10]) and cb[i - 10]:
            pre["cbot_ret_pre10"].append(float(cb[i - 1] / cb[i - 10] - 1))
        if not np.isnan(em[i - 10]) and em[i - 10]:
            pre["ema_ret_pre10"].append(float(em[i - 1] / em[i - 10] - 1))
        if not np.isnan(bzv[i - 5]):
            pre["bz_change_pre5"].append(float(bzv[i - 1] - bzv[i - 5]))
        if not np.isnan(wc[i - 10]) and wc[i - 10]:
            pre["wc_change_pre10"].append(float(wc[i - 1] / wc[i - 10] - 1))
        if not np.isnan(sma[i - 1]):
            pre["cbot_vs_sma20"].append(float(sma[i - 1]))
        p = e.get("path")
        if p in ("CBOT_DRIVEN", "EMA_DRIVEN") and not np.isnan(cb[i - 10]) and cb[i - 10]:
            pre_by_path.setdefault(p, []).append(float(cb[i - 1] / cb[i - 10] - 1))

    if len(bz_paths) < 10:
        return {"version": "V105-EVENT-STUDY", "verdict": "TOO_FEW_ALIGNED", "n": int(len(bz_paths))}

    pre_means = {k: round(float(np.nanmean(v)), 4) for k, v in pre.items() if v}
    cbot_pre_by_path = {k: round(float(np.nanmean(v)), 4) for k, v in pre_by_path.items() if v}
    bz_mean = np.nanmean(np.array(bz_paths), axis=0)
    cbot_mean = np.nanmean(np.array(cbot_paths), axis=0)
    ema_mean = np.nanmean(np.array(ema_paths), axis=0)

    # précurseur dominant : CBOT monte AVANT (>+0.5%) et/ou EMA s'essouffle (<= ~0)
    cbot_precursor = bool(pre_means.get("cbot_ret_pre10", 0) > 0.005)
    ema_exhaustion = bool(pre_means.get("ema_ret_pre10", 1) < pre_means.get("cbot_ret_pre10", 0))
    if cbot_precursor and ema_exhaustion:
        verdict = "CBOT_REBOUND_PRECEDES_COMPRESSION"
    elif ema_exhaustion:
        verdict = "EMA_EXHAUSTION_PRECEDES_COMPRESSION"
    elif cbot_precursor:
        verdict = "CBOT_REBOUND_PRECEDES_COMPRESSION"
    else:
        verdict = "NO_CLEAR_SINGLE_PRECURSOR"

    if make_png:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            x = np.arange(-PRE, POST + 1)
            fig, (axz, axr) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
            axz.axvline(0, color="grey", ls="--", lw=1)
            axz.plot(x, bz_mean, color="#3a6ea5", lw=2.5, label="basis_z moyen")
            axz.axhline(0.5, color="#1a9850", ls=":", lw=0.8)
            axz.set_ylabel("basis_z")
            axz.set_title("Event study autour du DÉBUT de compression (t=0)\n"
                          f"n={len(bz_paths)} épisodes — que se passe-t-il AVANT le retournement ? RESEARCH_ONLY")
            axz.legend(fontsize=8)
            axz.grid(alpha=0.15)
            axr.axvline(0, color="grey", ls="--", lw=1)
            axr.axhline(0, color="black", lw=0.6)
            axr.plot(x, cbot_mean * 100, color="#cc7a00", lw=2, label="CBOT cum. ret % (vs t0)")
            axr.plot(x, ema_mean * 100, color="#762a83", lw=2, label="EMA cum. ret % (vs t0)")
            axr.set_ylabel("rendement cumulé %")
            axr.set_xlabel("jours autour du début de compression")
            axr.legend(fontsize=8)
            axr.grid(alpha=0.15)
            fig.tight_layout()
            fig.savefig(EVENT_PNG, dpi=120)
            plt.close(fig)
        except Exception:  # noqa: BLE001
            pass

    out = {
        "version": "V105-EVENT-STUDY",
        "n_aligned": int(len(bz_paths)),
        "pre_start_means_t_minus10_to_t_minus1": pre_means,
        "cbot_pre_return_by_path": cbot_pre_by_path,
        "bz_at_tminus10": round(float(bz_mean[PRE - 10]), 3),
        "bz_at_t0": round(float(bz_mean[PRE]), 3),
        "bz_at_tplus10": round(float(bz_mean[PRE + POST]), 3),
        "cbot_cumret_tminus10_to_t0_pct": round(float((cbot_mean[PRE] - cbot_mean[PRE - 10]) * 100), 2),
        "verdict": verdict,
        "interpretation": (
            f"Avant le début de compression (t-10→t-1) : CBOT {pre_means.get('cbot_ret_pre10')}, EMA "
            f"{pre_means.get('ema_ret_pre10')}, Δbasis_z {pre_means.get('bz_change_pre5')}, Δwheat/corn "
            f"{pre_means.get('wc_change_pre10')}. Par canal, rendement CBOT pré-start : {cbot_pre_by_path}. "
            "Si le CBOT monte (et plus pour les CBOT_DRIVEN) avant que le basis baisse, c'est le précurseur "
            "central -> base du COMPRESSION_TRIGGER (CT-10). Figure : docs/COMPRESSION_TRIGGER_EVENT_STUDY.png."),
        "note": "Descriptif (start daté a posteriori). Les features du trigger seront strictement causales (CT-10).",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V105_DIR / "v105_event_study.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
