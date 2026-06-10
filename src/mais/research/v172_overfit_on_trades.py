"""V172-REAL — Application du pack anti-overfitting aux VRAIS trades short basis-haut.

On chiffre la déflation effective : (a) Deflated Sharpe sur les rendements par trade de la baseline
(z>1), corrigé par la variance des Sharpe de la FAMILLE de seuils (0.5..2.0) = essais multiples ;
(b) PBO-CSCV sur la matrice (années × seuils) de PnL net = robustesse de la sélection de seuil.

Réutilise la simulation V17 (1 trade à la fois, sortie z0 max90, stop -20, coût dynamique). Le Sharpe
est PAR TRADE (non annualisé). RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.audit.overfitting import deflated_sharpe_ratio, pbo_cscv, sharpe_stats
from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout
from mais.research.v17_research_indicator import (
    MAX_HOLD,
    STOP_LOSS,
    _dynamic_cost,
    _sim_detail,
)

V172_DIR = ARTEFACTS_DIR / "v172"
V172_DIR.mkdir(parents=True, exist_ok=True)

THRESHOLDS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
BASELINE_THR = 1.0
# nombre d'essais déclarés pour la déflation (sensibilité reportée) : la famille de seuils est un
# minorant ; l'historique réel (seuils × sorties × stops × features) est plus large.
N_TRIALS_GRID = [1, len(THRESHOLDS), 50, 100]


def _trades_for_threshold(df: pd.DataFrame, thr: float) -> list[tuple[int, float]]:
    ema = df["ema_close"].to_numpy()
    cbot = df["cbot_eur_t"].to_numpy()
    bz = df["ema_cbot_basis_zscore_52w"].to_numpy()
    vol = df.get("corn_realized_vol_20", pd.Series(np.nan, index=df.index)).to_numpy()
    oi = df.get("ema_oi_total", pd.Series(np.nan, index=df.index)).to_numpy()
    oi_med = np.nanmedian(oi[oi > 0]) if np.isfinite(oi).any() else 0.0
    vol_med = np.nanmedian(vol) if np.isfinite(vol).any() else np.nan
    dates = df.index
    cand = np.where(bz > thr)[0]
    out: list[tuple[int, float]] = []
    busy_until = -1
    for i in cand:
        if i <= busy_until:
            continue
        res = _sim_detail(ema, cbot, bz, i, 0.0, MAX_HOLD, stop_loss=STOP_LOSS)
        if res is None:
            continue
        cost = _dynamic_cost(oi[i], oi_med, vol[i], vol_med, dates[i].month)
        out.append((int(dates[i].year), float(res["pnl"] - 2 * cost)))
        busy_until = res["exit_pos"]
    return out


def run_v172_on_real_trades(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    if "ema_close" not in df.columns:
        return {"version": "V172-REAL", "verdict": "MISSING_DATA"}

    families = {thr: _trades_for_threshold(df, thr) for thr in THRESHOLDS}
    nets = {thr: np.array([n for _, n in fam], dtype=float) for thr, fam in families.items()}

    # Sharpe par trade de chaque variante de seuil (essais multiples)
    trial = {thr: sharpe_stats(nets[thr]) for thr in THRESHOLDS if len(nets[thr]) >= 5}
    trial_sharpes = np.array([v["sharpe"] for v in trial.values()])

    base = nets[BASELINE_THR]
    base_stats = sharpe_stats(base)

    # Deflated Sharpe à plusieurs n_trials (sensibilité)
    dsr_by_trials = {}
    for nt in N_TRIALS_GRID:
        d = deflated_sharpe_ratio(base, n_trials=max(nt, len(trial_sharpes) or 1),
                                  trial_sharpes=trial_sharpes if len(trial_sharpes) >= 2 else None)
        dsr_by_trials[str(nt)] = {"deflated_sharpe_ratio": d["deflated_sharpe_ratio"],
                                  "expected_max_sharpe": d["expected_max_sharpe"],
                                  "survives": d["survives"]}

    # PBO sur (années × seuils) de PnL net
    years = sorted({y for fam in families.values() for y, _ in fam})
    mat = np.zeros((len(years), len(THRESHOLDS)))
    for c, thr in enumerate(THRESHOLDS):
        per_year: dict[int, float] = {}
        for y, n in families[thr]:
            per_year[y] = per_year.get(y, 0.0) + n
        for r, y in enumerate(years):
            mat[r, c] = per_year.get(y, 0.0)
    n_splits = max(2, min(10, (len(years) // 2) * 2))
    pbo = pbo_cscv(mat, n_splits=n_splits) if len(years) >= 4 else {"verdict": "SKIP", "reason": "trop peu d'années"}

    # verdict : l'edge "survit" s'il bat la déflation à n_trials réaliste (>=50) ET PBO<0.5
    dsr50 = dsr_by_trials.get("50", {})
    survives = bool(dsr50.get("deflated_sharpe_ratio", 0) > 0.5 and pbo.get("pbo", 1.0) < 0.5)

    out = {
        "version": "V172-REAL",
        "verdict": "SURVIVES_MULTIPLICITY" if survives else "FRAGILE_UNDER_MULTIPLICITY",
        "baseline_threshold": BASELINE_THR,
        "baseline_n_trades": base_stats["n"],
        "baseline_sharpe_per_trade": round(base_stats["sharpe"], 4),
        "baseline_mean_net_eur_t": round(float(base.mean()), 3) if len(base) else None,
        "family_thresholds": THRESHOLDS,
        "family_n_trades": {str(t): int(len(nets[t])) for t in THRESHOLDS},
        "family_sharpe_per_trade": {str(t): round(trial[t]["sharpe"], 4) for t in trial},
        "var_sr_across_thresholds": round(float(np.var(trial_sharpes, ddof=1)), 5)
        if len(trial_sharpes) >= 2 else None,
        "deflated_sharpe_by_n_trials": dsr_by_trials,
        "pbo": pbo,
        "interpretation": (
            f"Baseline z>{BASELINE_THR} : {base_stats['n']} trades, Sharpe/trade "
            f"{round(base_stats['sharpe'],3)}, net moyen {round(float(base.mean()),2)} €/t. "
            f"Deflated Sharpe à 50 essais = {dsr50.get('deflated_sharpe_ratio')} "
            f"(survit={dsr50.get('survives')}). PBO (sélection de seuil) = {pbo.get('pbo')} "
            f"({pbo.get('verdict')}). "
            + ("L'edge SURVIT à la correction pour essais multiples."
               if survives else
               "PRUDENCE : l'edge ne survit pas clairement à la déflation -> requalifier EXPLORATOIRE "
               "tant que le recensement complet des variantes + placebos (T-PLACEBO) n'est pas fait.")),
        "note": "Sharpe par trade (non annualisé). Spread proxy, sortie z0 optimiste. Family = minorant "
                "de la multiplicité réelle.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V172_DIR / "v172_overfit_on_trades.json").write_text(json.dumps(out, indent=2, default=str),
                                                          encoding="utf-8")
    return out
