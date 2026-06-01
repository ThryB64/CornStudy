"""CT-01 (v104) — Définir le DÉBUT DE COMPRESSION pour chaque épisode de basis haut.

Avant de chercher les causes, on date proprement le moment où la compression commence. On teste 5 définitions
et on garde une primaire (A). DESCRIPTIF (utilise le futur relatif à l'entrée) -> JAMAIS une feature.

Définitions (à partir de l'entrée, fenêtre <=120 j) :
  A : 1er jour où basis_z a baissé de >=0.3 depuis son pic courant
  B : 1er jour où le basis (€/t) a baissé de >=5 depuis son pic courant
  C : 1er jour où basis_z passe sous sa moyenne mobile 5 j
  D : 1er jour avec 3 baisses de basis_z sur les 5 derniers jours
  E : 1er jour où la compression cumulée atteint 25 % du chemin du pic vers z=0.5

Livrable : data/research/high_basis_episodes_with_turning_point.parquet.
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

V104_DIR = ARTEFACTS_DIR / "v104"
V104_DIR.mkdir(parents=True, exist_ok=True)
OUT_PARQUET = ROOT / "data" / "research" / "high_basis_episodes_with_turning_point.parquet"
EPISODES = ROOT / "data" / "research" / "high_basis_episodes.parquet"
MAX_HOLD = 120


def _turning_points(bz: np.ndarray, basis: np.ndarray, i: int) -> dict[str, Any]:
    n = len(bz)
    end = min(i + MAX_HOLD, n - 1)
    seg_z = bz[i:end + 1]
    seg_b = basis[i:end + 1]
    if len(seg_z) < 5 or np.isnan(seg_z[0]):
        return {}
    z0 = seg_z[0]
    run_peak_z, run_peak_b = z0, seg_b[0]
    a = b = c = d = e = None
    z_target = 0.5
    ma5 = pd.Series(seg_z).rolling(5, min_periods=3).mean().to_numpy()
    for t in range(1, len(seg_z)):
        z, bval = seg_z[t], seg_b[t]
        if np.isnan(z):
            continue
        run_peak_z = max(run_peak_z, z)
        if not np.isnan(bval):
            run_peak_b = max(run_peak_b, bval)
        if a is None and (run_peak_z - z) >= 0.3:
            a = t
        if b is None and not np.isnan(bval) and (run_peak_b - bval) >= 5.0:
            b = t
        if c is None and not np.isnan(ma5[t]) and z < ma5[t]:
            c = t
        if d is None and t >= 5:
            downs = sum(1 for k in range(t - 4, t + 1)
                        if not np.isnan(seg_z[k]) and not np.isnan(seg_z[k - 1]) and seg_z[k] < seg_z[k - 1])
            if downs >= 3:
                d = t
        if e is None and (run_peak_z - z) >= 0.25 * (run_peak_z - z_target) and run_peak_z > z_target:
            e = t
    return {"start_A_z_drop03": a, "start_B_basis_drop5": b, "start_C_below_ma5": c,
            "start_D_3downs5": d, "start_E_25pct_path": e}


def build_turning_points(df: pd.DataFrame) -> pd.DataFrame:
    if EPISODES.exists():
        ep = pd.read_parquet(EPISODES)
    else:
        from mais.research.v82_episode_library import build_episodes
        ep = build_episodes(df, with_network=False)
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce").to_numpy()
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce").to_numpy()
    dates = df.index
    rows = []
    for _, e in ep.iterrows():
        d0 = pd.Timestamp(e["entry_date"])
        if d0 not in df.index:
            continue
        i = df.index.get_loc(d0)
        tp = _turning_points(bz, basis, i)
        if not tp:
            continue
        # primaire = A ; date = entrée + offset
        a = tp.get("start_A_z_drop03")
        start_date = str(dates[i + a].date()) if a is not None and i + a < len(dates) else None
        rows.append({
            "entry_date": e["entry_date"], "peak_basis_date": e.get("peak_basis_date"),
            "path": e.get("path"), "adverse": e.get("adverse"), "win": e.get("win"),
            "entry_z": e.get("entry_z"), "duration_days": e.get("duration_days"), "mfe": e.get("mfe"),
            "compression_start_date": start_date,
            "days_entry_to_start": int(a) if a is not None else None,
            **{k: (int(v) if v is not None else None) for k, v in tp.items()},
        })
    return pd.DataFrame(rows)


def run_v104_compression_start(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    tp = build_turning_points(df)
    if len(tp) < 15:
        return {"version": "V104-COMPRESSION-START", "verdict": "TOO_FEW", "n": int(len(tp))}
    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    tp.to_parquet(OUT_PARQUET, index=False)

    defs = ["start_A_z_drop03", "start_B_basis_drop5", "start_C_below_ma5",
            "start_D_3downs5", "start_E_25pct_path"]
    coverage = {dcol: int(tp[dcol].notna().sum()) for dcol in defs}
    median_offset = {dcol: (round(float(tp[dcol].median()), 1) if tp[dcol].notna().any() else None)
                     for dcol in defs}
    # cohérence entre définitions : corrélation des offsets (là où toutes définies)
    common = tp[defs].dropna()
    agreement = round(float(common.std(axis=1).median()), 1) if len(common) >= 5 else None
    non_adverse = tp[tp["path"] != "ADVERSE"]
    median_entry_to_start = (round(float(non_adverse["days_entry_to_start"].median()), 1)
                             if non_adverse["days_entry_to_start"].notna().any() else None)

    out = {
        "version": "V104-COMPRESSION-START",
        "n_episodes": int(len(tp)),
        "coverage_by_definition": coverage,
        "median_offset_days_by_definition": median_offset,
        "definitions_agreement_std_days": agreement,
        "median_days_entry_to_start_non_adverse": median_entry_to_start,
        "primary_definition": "A (basis_z -0.3 depuis le pic)",
        "parquet": (str(OUT_PARQUET.relative_to(ROOT)) if OUT_PARQUET.is_relative_to(ROOT)
                    else str(OUT_PARQUET)),
        "verdict": "COMPRESSION_START_DEFINED",
        "interpretation": (
            f"Début de compression daté sur {len(tp)} épisodes (primaire = def A). Offset médian entrée→start "
            f"(hors ADVERSE) ≈ {median_entry_to_start} j. Les 5 définitions sont comparées (couverture + offset "
            "médian) ; A/C/D donnent un timing technique, B un seuil €/t, E un % de chemin. Base de la phase "
            "trigger (event study + cible imminente). DESCRIPTIF, jamais une feature."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V104_DIR / "v104_compression_start.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
