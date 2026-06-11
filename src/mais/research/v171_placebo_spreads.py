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


# ---------------------------------------------------------------------------
# V171-EXT (P8 consolidation 2026-06-11) : univers de témoins élargi + placebos structurels
# ---------------------------------------------------------------------------

# paires SANS maïs construites depuis les clôtures brutes : si la réversion de spread « marche
# partout », l'edge EMA n'a rien de spécial.
EXTRA_PAIRS = [("wheat_close", "soy_close"), ("wheat_close", "oil_close"), ("soy_close", "oil_close"),
               ("wheat_close", "oats_close"), ("soy_close", "gas_close"),
               ("wheat_close", "usd_index_close"), ("soy_close", "usd_index_close"),
               ("oats_close", "soy_close"), ("oats_close", "oil_close")]
N_RANDOM_DRAWS = 500
SHIFT_DAYS = 30


def build_extra_pair_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for a, b in EXTRA_PAIRS:
        if a in df.columns and b in df.columns:
            num = pd.to_numeric(df[a], errors="coerce")
            den = pd.to_numeric(df[b], errors="coerce")
            out[f"placebo_{a.split('_')[0]}_{b.split('_')[0]}"] = num / den
    return out


def _random_entry_sharpes(s: pd.Series, n_trades: int, draws: int = N_RANDOM_DRAWS,
                          seed: int = 0) -> np.ndarray:
    """Distribution de Sharpe/trade sous entrées ALÉATOIRES (même n, même moteur de sortie max_hold)."""
    sv = s.to_numpy(dtype=float)
    valid = np.where(~np.isnan(sv[:-MAX_HOLD]))[0]
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(draws):
        picks = np.sort(rng.choice(valid, size=min(n_trades, len(valid)), replace=False))
        pnls, busy = [], -1
        for i in picks:
            if i <= busy:
                continue
            j = min(i + MAX_HOLD, len(sv) - 1)
            if np.isnan(sv[j]):
                continue
            pnls.append(-(sv[j] - sv[i]))
            busy = j
        if len(pnls) >= 5:
            st = sharpe_stats(np.array(pnls))
            out.append(st["sharpe"])
    return np.array(out, dtype=float)


def run_v171_extended(df: pd.DataFrame) -> dict[str, Any]:
    """Falsification élargie : ~14 spreads témoins + signal décalé + sens inversé + entrées aléatoires."""
    assert_no_holdout(df)
    dfx = build_extra_pair_columns(df)
    real = _run_one(dfx, REAL)
    if real is None or real.get("insufficient"):
        return {"version": "V171-EXT", "verdict": "REAL_SPREAD_UNAVAILABLE"}

    extra_cols = [c for c in dfx.columns if c.startswith("placebo_")]
    all_placebo_cols = PLACEBOS + extra_cols
    placebos = [r for c in all_placebo_cols
                if (r := _run_one(dfx, c)) is not None and not r.get("insufficient")]
    real_sr = real["sharpe_per_trade"]
    beating = sum(1 for p in placebos if p["sharpe_per_trade"] >= real_sr)
    rank = 1 + beating

    s = pd.to_numeric(dfx[REAL], errors="coerce")
    z = _zscore(s)
    # placebo structurel 1 : signal DÉCALÉ de 30 j (le timing ne devrait plus rien valoir)
    shifted_pnl = _reversion_trades(s, z.shift(SHIFT_DAYS))
    shifted = (sharpe_stats(shifted_pnl)["sharpe"] if len(shifted_pnl) >= 5 else None)
    # placebo structurel 2 : sens INVERSÉ (long le spread sur z>1 — devrait être négatif)
    flipped_pnl = -_reversion_trades(s, z)
    flipped = (sharpe_stats(flipped_pnl)["sharpe"] if len(flipped_pnl) >= 5 else None)
    # placebo structurel 3 : entrées ALÉATOIRES (même n, distribution de Sharpe)
    rnd = _random_entry_sharpes(s, real["n_trades"])
    p_random = (round(float((rnd >= real_sr).mean()), 4) if len(rnd) else None)

    specific = (beating <= 1) and (p_random is not None and p_random <= 0.10)
    out = {
        "version": "V171-EXT",
        "verdict": "EDGE_SPECIFIC_CONFIRMED_EXTENDED" if specific else "EDGE_SPECIFICITY_WEAKENED",
        "real": real,
        "n_placebo_spreads": len(placebos),
        "real_rank_among_spreads": rank,
        "n_spreads_beating_real": beating,
        "placebos_sorted": sorted(placebos, key=lambda p: -p["sharpe_per_trade"]),
        "structural": {
            "shifted_signal_30d_sharpe": (round(shifted, 4) if shifted is not None else None),
            "flipped_direction_sharpe": (round(flipped, 4) if flipped is not None else None),
            "random_entries": {"n_draws": int(len(rnd)),
                               "mean_sharpe": round(float(rnd.mean()), 4) if len(rnd) else None,
                               "p_value_real_vs_random": p_random},
        },
        "interpretation": (
            f"Basis EMA Sharpe/trade {real_sr} : rang {rank}/{1+len(placebos)} dans l'univers élargi ; "
            f"{beating} témoin(s) >= réel. Signal décalé 30 j : {shifted} ; sens inversé : {flipped} ; "
            f"p(random >= réel) = {p_random}. "
            + ("Spécificité CONFIRMÉE sur l'univers élargi." if specific
               else "Spécificité AFFAIBLIE sur l'univers élargi — à dire honnêtement.")),
        "note": "Même moteur exact que V171 (z causal shift(1), 1 trade à la fois, max90). Témoins en "
                "unités hétérogènes -> Sharpe scale-free seul comparé.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V171_DIR / "v171_extended.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
