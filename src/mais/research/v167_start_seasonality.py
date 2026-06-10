"""V167 / T-SEASON — Saisonnalité des départs de compression & survie hors-saison.

Les 42 épisodes ne sont pas forcément i.i.d. dans le temps : ils peuvent se concentrer à certaines
saisons (tension de soudure l'été, détente à la récolte). On cartographie QUAND tombent les départs
(mois, saison), la vitesse de compression (jours à z<=0.5, censuré à 90), et la magnitude (Δz sur 90j),
puis on teste si l'edge survit hors de sa saison forte.

Descriptif, sur label causal (V153.start_events). Ne touche pas la baseline. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.research.v153_start_vs_inprogress import start_events

V167_DIR = ARTEFACTS_DIR / "v167"
V167_DIR.mkdir(parents=True, exist_ok=True)

SEASONS = {"DJF": (12, 1, 2), "MAM": (3, 4, 5), "JJA": (6, 7, 8), "SON": (9, 10, 11)}
POST = 90
MIN_PREMIUM_Z = 1.0


def _season(month: int) -> str:
    for name, months in SEASONS.items():
        if month in months:
            return name
    return "?"


def _episodes(df: pd.DataFrame) -> pd.DataFrame:
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce").to_numpy()
    ev = start_events(df).to_numpy()
    idx = df.index
    rows = []
    n = len(df)
    for i in range(n):
        if ev[i] != 1 or np.nanmax(bz[max(0, i - 5):i + 1]) < MIN_PREMIUM_Z:
            continue
        z0 = bz[i]
        fwd = bz[i + 1:min(n, i + 1 + POST)]
        z_end = fwd[-1] if len(fwd) else np.nan
        # jours à z<=0.5 (censuré si jamais atteint dans la fenêtre)
        hit = np.where(fwd <= 0.5)[0]
        days_to_z05 = int(hit[0] + 1) if len(hit) else None
        month = idx[i].month if hasattr(idx[i], "month") else pd.Timestamp(idx[i]).month
        rows.append({"date": str(idx[i].date()) if hasattr(idx[i], "date") else str(idx[i]),
                     "month": int(month), "season": _season(int(month)),
                     "z_start": float(z0), "z_end_90": float(z_end) if not np.isnan(z_end) else None,
                     "compression_90": float(z0 - z_end) if not np.isnan(z_end) else None,
                     "days_to_z05": days_to_z05,
                     "censored": days_to_z05 is None})
    return pd.DataFrame(rows)


def run_v167(df: pd.DataFrame) -> dict[str, Any]:
    ep = _episodes(df)
    if len(ep) < 8:
        return {"version": "V167-SEASONALITY", "verdict": "TOO_FEW_EPISODES", "n": int(len(ep))}

    by_month = ep.groupby("month").size().reindex(range(1, 13), fill_value=0)
    def _agg(g: pd.DataFrame) -> dict[str, Any]:
        comp = g["compression_90"].dropna()
        reached = g[~g["censored"]]["days_to_z05"].dropna()
        return {"n": int(len(g)),
                "median_compression_90": round(float(comp.median()), 3) if len(comp) else None,
                "median_days_to_z05": round(float(reached.median()), 1) if len(reached) else None,
                "reach_rate_90": round(float((~g["censored"]).mean()), 3)}
    by_season = {s: _agg(g) for s, g in ep.groupby("season")}

    # saison forte = celle au plus d'épisodes ; survie hors-saison = compression médiane ailleurs
    strong_season = by_month.idxmax()  # mois
    strong_seas = _season(int(strong_season))
    in_seas = ep[ep["season"] == strong_seas]["compression_90"].dropna()
    out_seas = ep[ep["season"] != strong_seas]["compression_90"].dropna()
    edge_survives_offseason = bool(len(out_seas) and out_seas.median() > 0.3)

    out = {
        "version": "V167-SEASONALITY",
        "verdict": "SEASONALITY_MAPPED",
        "n_episodes": int(len(ep)),
        "starts_by_month": {int(m): int(v) for m, v in by_month.items()},
        "by_season": by_season,
        "peak_start_month": int(strong_season),
        "peak_start_season": strong_seas,
        "compression_in_peak_season_median": round(float(in_seas.median()), 3) if len(in_seas) else None,
        "compression_offseason_median": round(float(out_seas.median()), 3) if len(out_seas) else None,
        "edge_survives_offseason": edge_survives_offseason,
        "interpretation": (
            f"{len(ep)} départs de prime élevée. Pic de départs en mois {int(strong_season)} "
            f"({strong_seas}). Compression médiane à 90j en saison forte "
            f"{round(float(in_seas.median()),3) if len(in_seas) else None} vs hors-saison "
            f"{round(float(out_seas.median()),3) if len(out_seas) else None}. "
            + ("L'edge SURVIT hors-saison (ne pas le restreindre)."
               if edge_survives_offseason else
               "L'edge est concentré en saison -> envisager un filtre saison explicite.")
            + " À rapprocher des horizons saisonniers V27 (avr-juin ~23j rapide / jan-mars ~53j lent)."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V167_DIR / "v167_seasonality.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
