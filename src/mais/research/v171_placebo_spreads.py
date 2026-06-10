"""V171 / T-PLACEBO — L'edge short basis-haut est-il spécifique au maïs EMA/CBOT ?

Test de falsification : on passe EXACTEMENT le même moteur de réversion (entrée z>1, sortie z<=0 ou
max90, 1 trade à la fois) sur le basis EMA/CBOT réel ET sur des spreads TÉMOINS sans lien direct avec
la prime EU (corn/wheat, corn/soy, corn/oil, corn/gas, corn/dxy). Si les témoins donnent un edge
similaire, l'edge n'est pas spécifique ; si le basis EMA domine, la spécificité est confirmée.

z-score causal : (s - mean_roll.shift(1)) / std_roll.shift(1). PnL par trade short = -(s[j]-s[i]) en
unités du spread ; le Sharpe (mean/std par trade) est scale-free donc comparable entre spreads.
RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.audit.overfitting import sharpe_stats
from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V171_DIR = ARTEFACTS_DIR / "v171"
V171_DIR.mkdir(parents=True, exist_ok=True)

REAL = "ema_cbot_basis"
PLACEBOS = ["corn_wheat_ratio", "corn_soy_ratio", "corn_oil_ratio", "corn_gas_ratio", "corn_dxy_ratio"]
ROLL = 252
MAX_HOLD = 90
ENTRY_Z = 1.0


def _zscore(s: pd.Series, roll: int = ROLL) -> pd.Series:
    m = s.rolling(roll, min_periods=roll // 2).mean().shift(1)
    sd = s.rolling(roll, min_periods=roll // 2).std().shift(1)
    return (s - m) / sd


def _reversion_trades(s: pd.Series, z: pd.Series, max_hold: int = MAX_HOLD,
                      entry_z: float = ENTRY_Z) -> np.ndarray:
    """PnL par trade short (profit si le spread baisse), 1 trade à la fois, sortie z<=0 ou max_hold."""
    sv = s.to_numpy(dtype=float)
    zv = z.to_numpy(dtype=float)
    n = len(sv)
    cand = np.where(zv > entry_z)[0]
    pnls: list[float] = []
    busy_until = -1
    for i in cand:
        if i <= busy_until or np.isnan(sv[i]):
            continue
        exit_pos = None
        for t in range(1, max_hold + 1):
            j = i + t
            if j >= n or np.isnan(sv[j]):
                continue
            exit_pos = j
            if not np.isnan(zv[j]) and zv[j] <= 0.0:
                break
        if exit_pos is None:
            continue
        pnls.append(-(sv[exit_pos] - sv[i]))  # short le spread
        busy_until = exit_pos
    return np.array(pnls, dtype=float)


def _run_one(df: pd.DataFrame, col: str) -> dict[str, Any] | None:
    if col not in df.columns:
        return None
    s = pd.to_numeric(df[col], errors="coerce")
    if s.notna().sum() < 300:
        return None
    z = _zscore(s)
    pnl = _reversion_trades(s, z)
    if len(pnl) < 5:
        return {"spread": col, "n_trades": int(len(pnl)), "insufficient": True}
    st = sharpe_stats(pnl)
    return {"spread": col, "n_trades": int(len(pnl)),
            "sharpe_per_trade": round(st["sharpe"], 4),
            "win_rate": round(float((pnl > 0).mean()), 4),
            "mean_pnl_units": round(float(pnl.mean()), 5)}


def run_v171_placebo(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    real = _run_one(df, REAL)
    if real is None or real.get("insufficient"):
        return {"version": "V171-PLACEBO", "verdict": "REAL_SPREAD_UNAVAILABLE"}
    placebos = [r for c in PLACEBOS if (r := _run_one(df, c)) is not None and not r.get("insufficient")]

    real_sr = real["sharpe_per_trade"]
    placebo_srs = [p["sharpe_per_trade"] for p in placebos]
    better_or_equal = sum(1 for x in placebo_srs if x >= real_sr)
    # spécificité : le réel domine si son Sharpe est > tous les témoins (ou quasi)
    dominates = better_or_equal == 0
    rank = 1 + better_or_equal  # 1 = meilleur

    out = {
        "version": "V171-PLACEBO",
        "verdict": "EDGE_SPECIFIC_TO_EMA_BASIS" if dominates else "EDGE_NOT_CLEARLY_SPECIFIC",
        "real": real,
        "placebos": sorted(placebos, key=lambda p: -p["sharpe_per_trade"]),
        "real_rank_among_all": rank,
        "n_placebos": len(placebos),
        "n_placebos_beating_real": better_or_equal,
        "interpretation": (
            f"Basis EMA/CBOT : Sharpe/trade {real_sr} ({real['n_trades']} trades, win "
            f"{real['win_rate']}). Témoins : {[(p['spread'], p['sharpe_per_trade']) for p in placebos]}. "
            f"Le basis EMA est rang {rank}/{1+len(placebos)}. "
            + ("Edge SPÉCIFIQUE au basis EMA (domine les témoins) — la prime locale n'est pas un "
               "artefact générique de réversion de spread."
               if dominates else
               f"{better_or_equal} témoin(s) font aussi bien/mieux -> l'edge n'est pas clairement "
               "spécifique ; prudence sur la narration « prime maïs unique ».")),
        "note": "Même moteur exact, z causal shift(1), Sharpe par trade scale-free. Témoins internes "
                "(faute de colza/canola ou blé MATIF/CBOT) -> falsification partielle.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V171_DIR / "v171_placebo.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
