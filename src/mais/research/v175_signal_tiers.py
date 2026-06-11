"""V175 — Signal tiers & watchlist : étudier les phases AVANT le signal sans toucher la baseline.

La baseline reste figée (z>1 SHORT_PREMIUM, 1.5 STRONG, 2 EXTREME, objectifs z->0.5 / z->0). On ajoute
des CATÉGORIES D'ÉTUDE sous le seuil : WATCHLIST (0.5<=z<0.75) et PRE_SIGNAL (0.75<=z<1.0), pour
répondre à : les pré-signaux deviennent-ils des signaux ? en combien de jours ? qu'est-ce qui distingue
ceux qui escaladent de ceux qui retombent ?

Méthode purement DESCRIPTIVE : événements d'upcross (entrée dans un palier par le bas, lockout
anti-rebond), suivi forward H jours, comparaison escaladeurs vs retombés (Mann-Whitney). AUCUN modèle
ajusté, aucune règle ajoutée à l'indicateur ici. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROCESSED_DIR, PROJECT_ROOT

V175_DIR = ARTEFACTS_DIR / "v175"
V175_DIR.mkdir(parents=True, exist_ok=True)
TIERS_PARQUET = PROJECT_ROOT / "data" / "research" / "signal_tiers.parquet"

Z_COL = "ema_cbot_basis_zscore_52w"
HORIZON = 20      # jours de bourse pour juger l'escalade
LOCKOUT = 10      # anti-rebond entre deux upcross du même palier
FIZZLE_FLOOR = 0.5  # retombe sous ce niveau avant d'atteindre la cible = fizzle

TIER_BOUNDS = [
    ("EXTREME", 2.0), ("STRONG", 1.5), ("BASELINE_SIGNAL", 1.0),
    ("PRE_SIGNAL", 0.75), ("WATCHLIST", 0.5),
]


def assign_tier(z: float) -> str:
    if pd.isna(z):
        return "NO_DATA"
    if z <= -0.5:
        return "BELOW_NORMAL"
    for name, lo in TIER_BOUNDS:
        if z >= lo:
            return name
    return "NORMAL"


def build_tier_series(df: pd.DataFrame) -> pd.DataFrame:
    out = df[["Date", Z_COL]].copy()
    out["signal_tier_study"] = out[Z_COL].map(assign_tier)
    return out


def _upcross_indices(z: np.ndarray, level: float, lockout: int = LOCKOUT) -> list[int]:
    """Jours où z entre dans [level, +inf) par le bas, avec anti-rebond."""
    idx, last = [], -10**9
    for i in range(1, len(z)):
        if np.isnan(z[i]) or np.isnan(z[i - 1]):
            continue
        if z[i] >= level and z[i - 1] < level and (i - last) > lockout:
            idx.append(i)
            last = i
    return idx


def escalation_episodes(df: pd.DataFrame, entry_level: float, target_level: float,
                        horizon: int = HORIZON) -> pd.DataFrame:
    """Pour chaque upcross du palier d'entrée : atteint la cible dans `horizon` jours ou retombe ?"""
    z = pd.to_numeric(df[Z_COL], errors="coerce").to_numpy()
    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce").to_numpy()
    rel = pd.to_numeric(df.get("ema_cbot_rel_strength_20d"), errors="coerce").to_numpy()
    dates = pd.to_datetime(df["Date"]).to_numpy()
    rows = []
    for i in _upcross_indices(z, entry_level):
        if z[i] >= target_level:
            continue  # gap-jump : le jour d'entrée est déjà au-dessus de la cible -> pas un vrai pré-signal
        fut = z[i + 1:i + 1 + horizon]
        reached = np.where(fut >= target_level)[0]
        fizzled = np.where(fut < FIZZLE_FLOOR)[0]
        days_to_target = int(reached[0]) + 1 if len(reached) else None
        days_to_fizzle = int(fizzled[0]) + 1 if len(fizzled) else None
        if days_to_target is not None and (days_to_fizzle is None or days_to_target < days_to_fizzle):
            outcome = "ESCALATED"
        elif days_to_fizzle is not None:
            outcome = "FIZZLED"
        else:
            outcome = "STALLED"
        slope5 = float(z[i] - z[i - 5]) if i >= 5 and not np.isnan(z[i - 5]) else np.nan
        mom20 = (float(np.log(cbot[i] / cbot[i - 20]))
                 if i >= 20 and cbot[i] > 0 and cbot[i - 20] > 0 else np.nan)
        rows.append({
            "entry_date": str(pd.Timestamp(dates[i]).date()), "entry_z": round(float(z[i]), 3),
            "outcome": outcome, "days_to_target": days_to_target, "days_to_fizzle": days_to_fizzle,
            "z_slope_5d": slope5, "cbot_mom_20d": mom20,
            "ema_rel_strength_20d": float(rel[i]) if not np.isnan(rel[i]) else np.nan,
            "month": int(pd.Timestamp(dates[i]).month),
        })
    return pd.DataFrame(rows)


def _mann_whitney(a: pd.Series, b: pd.Series) -> dict[str, Any]:
    a, b = a.dropna(), b.dropna()
    if len(a) < 5 or len(b) < 5:
        return {"n_a": int(len(a)), "n_b": int(len(b)), "p": None}
    try:
        from scipy.stats import mannwhitneyu
        _, p = mannwhitneyu(a, b, alternative="two-sided")
        return {"n_a": int(len(a)), "n_b": int(len(b)),
                "median_a": round(float(a.median()), 4), "median_b": round(float(b.median()), 4),
                "p": round(float(p), 4)}
    except ImportError:
        return {"n_a": int(len(a)), "n_b": int(len(b)), "p": None}


def run_v175_signal_tiers(df: pd.DataFrame | None = None) -> dict[str, Any]:
    if df is None:
        df = pd.read_parquet(PROCESSED_DIR / "features.parquet",
                             columns=["Date", Z_COL, "cbot_eur_t", "ema_cbot_rel_strength_20d"])
    df = df[df[Z_COL].notna()].reset_index(drop=True)
    if df.empty:
        return {"version": "V175-SIGNAL-TIERS", "verdict": "WAITING_DATA"}

    tiers = build_tier_series(df)
    TIERS_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    tiers.to_parquet(TIERS_PARQUET, index=False)
    tier_counts = tiers["signal_tier_study"].value_counts().to_dict()

    analyses: dict[str, Any] = {}
    for label, entry, target in (("pre_signal_to_baseline", 0.75, 1.0),
                                 ("watchlist_to_baseline", 0.5, 1.0),
                                 ("watchlist_to_pre_signal", 0.5, 0.75)):
        ep = escalation_episodes(df, entry, target)
        if ep.empty:
            analyses[label] = {"n": 0}
            continue
        esc = ep[ep["outcome"] == "ESCALATED"]
        fiz = ep[ep["outcome"] == "FIZZLED"]
        discr = {c: _mann_whitney(esc[c], fiz[c])
                 for c in ("z_slope_5d", "cbot_mom_20d", "ema_rel_strength_20d")}
        analyses[label] = {
            "n_episodes": int(len(ep)),
            "escalation_rate": round(float((ep["outcome"] == "ESCALATED").mean()), 3),
            "fizzle_rate": round(float((ep["outcome"] == "FIZZLED").mean()), 3),
            "stall_rate": round(float((ep["outcome"] == "STALLED").mean()), 3),
            "median_days_to_target": (float(esc["days_to_target"].median())
                                      if len(esc) else None),
            "months_escalated": esc["month"].value_counts().to_dict() if len(esc) else {},
            "discriminants_escalated_vs_fizzled": discr,
        }
        ep.to_json(V175_DIR / f"v175_episodes_{label}.json", orient="records", indent=1)

    out = {
        "version": "V175-SIGNAL-TIERS",
        "verdict": "TIERS_BUILT_DESCRIPTIVE_ONLY",
        "baseline_untouched": True,
        "horizon_days": HORIZON, "lockout_days": LOCKOUT, "fizzle_floor": FIZZLE_FLOOR,
        "tier_counts": tier_counts,
        "analyses": analyses,
        "guardrails": [
            "catégories d'ÉTUDE uniquement : la baseline z>1 reste le seul signal",
            "aucun modèle ajusté ; stats descriptives + Mann-Whitney",
            "fenêtre proxy 2010-2025 (proxy_implied) ; à revalider sur l'officiel accumulé",
        ],
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V175_DIR / "v175_signal_tiers_results.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
