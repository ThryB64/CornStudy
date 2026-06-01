"""V14 — Indicateur short-only assemblé, durée de reversion, robustesse proxy.

Point d'orgue de la lignée basis. On assemble tout ce qui a été validé V10-V13 en UN indicateur
discipliné, on modélise la durée de reversion, et on teste la robustesse aux erreurs du proxy EMA.

- assemble_short_indicator / run_short_indicator : entrée basis_z>1 + gate conforme α=0.10 +
  cost-aware + vetoes, sortie z->0 (max 90j). Backtest coûts + LOYO + leave-one-crisis-out.
- run_reversion_survival : Kaplan-Meier du temps de reversion (basis_z -> 0), médiane + P(revert<=T), par saison.
- run_proxy_robustness   : perturbe le prix EMA proxy, mesure la dégradation de l'edge short.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit

from mais.meta.cqr import _finite_sample_residual_quantile
from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout
from mais.research.v13_basis_reversion_indicator import _simulate_trade

V14_DIR = ARTEFACTS_DIR / "v14"
V14_DIR.mkdir(parents=True, exist_ok=True)

HORIZON = 40
CRISIS_YEARS = (2020, 2021, 2022)


def _basis_change_oof(df: pd.DataFrame, h: int = HORIZON, alpha: float = 0.10):
    """OOF point + demi-largeur conforme de basis_change_h. Retourne séries alignées sur df.index."""
    basis = df["ema_cbot_basis"]
    x = pd.DataFrame({
        "basis_z": df.get("ema_cbot_basis_zscore_52w"),
        "month_cos": np.cos(2 * np.pi * df.index.month / 12),
        "eurusd": df.get("eurusd"),
    }, index=df.index)
    target = basis.shift(-h) - basis
    keep = target.notna() & x.notna().all(axis=1)
    xk, yk = x.loc[keep], target.loc[keep]
    point = pd.Series(np.nan, index=df.index)
    hw = pd.Series(np.nan, index=df.index)
    if len(xk) < 300:
        return point, hw
    dates = xk.index
    means, stds = xk.mean(), xk.std().replace(0, 1)
    xs = (xk - means) / stds
    pv = np.full(len(xk), np.nan)
    hv = np.full(len(xk), np.nan)
    for tr, te in TimeSeriesSplit(n_splits=6).split(xs):
        train_end = dates[tr[-1]]
        te_p = np.array([i for i in te if dates[i] > train_end + pd.Timedelta(days=h)])
        if len(tr) < 120 or len(te_p) < 10:
            continue
        cut = int(len(tr) * 0.7)
        fit_idx, cal_idx = tr[:cut], tr[cut:]
        if len(cal_idx) < 30:
            continue
        reg = Ridge(alpha=1.0).fit(xs.iloc[fit_idx], yk.iloc[fit_idx])
        q = _finite_sample_residual_quantile(
            np.abs(yk.iloc[cal_idx].values - reg.predict(xs.iloc[cal_idx])), alpha)
        pv[te_p] = reg.predict(xs.iloc[te_p])
        hv[te_p] = q
    v = ~np.isnan(pv)
    point.loc[dates[v]] = pv[v]
    hw.loc[dates[v]] = hv[v]
    return point, hw


def _vetoes(df: pd.DataFrame) -> pd.Series:
    idx = df.index
    dq = df.get("ema_data_availability_score", pd.Series(np.nan, index=idx)).fillna(0.0) < 0.4
    oi = df.get("ema_oi_total", pd.Series(np.nan, index=idx))
    oi_floor = oi[oi > 0].quantile(0.10) if (oi > 0).any() else 0.0
    liq = oi.fillna(0.0) < oi_floor
    dtw = df.get("days_to_next_wasde", pd.Series(np.nan, index=idx)).fillna(99) <= 2
    roll = pd.Series(idx.month, index=idx).isin([2, 5, 7, 10]).values
    return (dq | liq | dtw | pd.Series(roll, index=idx))


# ---------------------------------------------------------------------------
# V14-01 — Indicateur short-only assemblé
# ---------------------------------------------------------------------------

def assemble_short_indicator(df: pd.DataFrame, alpha: float = 0.10, cost_per_leg: float = 3.0,
                             margin: float = 2.0, gate: str = "relaxed") -> pd.DataFrame:
    """Signal SHORT_PREMIUM / ABSTAIN par date.

    gate='strict'  : exige l'intervalle conforme ENTIÈREMENT sous 0 (compression certaine) -> très rare.
    gate='relaxed' : exige une compression attendue (point<0) couvrant les coûts (cost-aware) -> usuel.
    Dans les deux cas : entrée basis_z>1, vetoes appliqués.
    """
    idx = df.index
    bz = df.get("ema_cbot_basis_zscore_52w", pd.Series(np.nan, index=idx))
    point, hw = _basis_change_oof(df, HORIZON, alpha)
    vetoes = _vetoes(df)

    hi = point + hw  # borne haute de l'intervalle conforme sur basis_change
    expected_compression = -point  # pour un short, on profite si le basis baisse (point < 0)
    edge_threshold = 2 * cost_per_leg + margin

    out = pd.DataFrame(index=idx)
    signal = pd.Series("ABSTAIN", index=idx)

    entry = bz > 1.0
    cost_ok = expected_compression > edge_threshold
    gate_ok = (hi < 0) & cost_ok if gate == "strict" else (point < 0) & cost_ok
    ok = entry & gate_ok & (~vetoes) & point.notna()
    signal[ok.values] = "SHORT_PREMIUM"

    out["signal"] = signal
    out["basis_z"] = bz
    out["pred_basis_change"] = point
    out["conformal_hi"] = hi
    out["expected_compression"] = expected_compression
    out["veto"] = vetoes.values
    out["reason"] = np.where(ok.values, f"basis_high+{gate}_compression+cost_ok", "")
    conf = (expected_compression / (expected_compression + edge_threshold)).clip(0, 1)
    out["confidence"] = conf.where(signal == "SHORT_PREMIUM", 0.0).fillna(0.0)
    return out


def _backtest_short(df: pd.DataFrame, signals: pd.DataFrame, exit_rule="z0_max90"):
    ema = df["ema_close"].values
    cbot = df["cbot_eur_t"].values
    bzv = df["ema_cbot_basis_zscore_52w"].values
    sig = signals["signal"].reindex(df.index).fillna("ABSTAIN")
    cand = np.where((sig == "SHORT_PREMIUM").values)[0]
    dates = df.index
    kept, last = [], None
    for i in cand:
        d = dates[i]
        if last is None or (d - last).days >= HORIZON:
            kept.append(i)
            last = d
    trades = []
    for i in kept:
        p, t, mae = _simulate_trade(ema, cbot, bzv, i, -1.0, exit_rule)
        if not np.isnan(p):
            trades.append({"year": dates[i].year, "pnl": p, "days": t, "mae": mae})
    return pd.DataFrame(trades)


def _summary(tdf):
    if len(tdf) < 5:
        return {"n": int(len(tdf))}
    g = tdf["pnl"].values
    return {"n": int(len(tdf)), "hit_rate": round(float((g > 0).mean()), 4),
            "mean_pnl": round(float(g.mean()), 2),
            "mean_holding_days": round(float(tdf["days"].mean()), 1),
            "net_cost1": round(float((g - 2).sum()), 1),
            "net_cost3": round(float((g - 6).sum()), 1),
            "net_cost5": round(float((g - 10).sum()), 1)}


def run_short_indicator(df: pd.DataFrame, cost_per_leg: float = 3.0) -> dict[str, Any]:
    """V14-01 — assemble (strict + relaxed) + backtest + LOYO + leave-one-crisis-out."""
    assert_no_holdout(df)
    if "ema_close" not in df.columns or "ema_cbot_basis" not in df.columns:
        return {"version": "V14-01-SHORT-INDICATOR", "verdict": "MISSING_DATA"}

    strict_sig = assemble_short_indicator(df, cost_per_leg=cost_per_leg, gate="strict")
    relaxed_sig = assemble_short_indicator(df, cost_per_leg=cost_per_leg, gate="relaxed")
    strict_trades = _backtest_short(df, strict_sig)
    relaxed_trades = _backtest_short(df, relaxed_sig)

    base_sig = pd.DataFrame(index=df.index)
    base_sig["signal"] = np.where(df["ema_cbot_basis_zscore_52w"] > 1.0, "SHORT_PREMIUM", "ABSTAIN")
    base_trades = _backtest_short(df, base_sig)

    relaxed = _summary(relaxed_trades)
    baseline = _summary(base_trades)
    loyo = ({str(y): _summary(relaxed_trades[relaxed_trades["year"] == y])
             for y in sorted(relaxed_trades["year"].unique())} if len(relaxed_trades) else {})
    years_pos = sum(1 for v in loyo.values() if v.get("mean_pnl", -1) > 0 and v.get("n", 0) >= 3)
    years_eval = sum(1 for v in loyo.values() if v.get("n", 0) >= 3)
    crisis_out = _summary(relaxed_trades[~relaxed_trades["year"].isin(CRISIS_YEARS)]) if len(relaxed_trades) else {}

    relaxed_c5 = relaxed.get("net_cost5", -1)
    base_c5 = baseline.get("net_cost5", -1)
    survives = relaxed_c5 > 0 and crisis_out.get("net_cost5", -1) > 0
    out = {
        "version": "V14-01-SHORT-INDICATOR",
        "cost_per_leg_for_gate": cost_per_leg,
        "n_signals_strict": int((strict_sig["signal"] == "SHORT_PREMIUM").sum()),
        "n_signals_relaxed": int((relaxed_sig["signal"] == "SHORT_PREMIUM").sum()),
        "over_gating_finding": (
            "Le gate strict (intervalle conforme entièrement < 0) émet quasi 0 signal : la magnitude du "
            "basis_change est trop incertaine (R²<0) pour que l'intervalle exclue 0 en €/t. Empiler tous les "
            "gates à pleine sévérité vide l'ensemble -> on retient le gate relaxed (compression attendue + cost-aware)."
        ),
        "strict_indicator": _summary(strict_trades),
        "relaxed_indicator": relaxed,
        "baseline_short_no_gates": baseline,
        "loyo_years_positive": years_pos,
        "loyo_years_evaluable": years_eval,
        "leave_all_crises_out": crisis_out,
        "gate_reduces_trades_vs_baseline": bool(relaxed.get("n", 0) < baseline.get("n", 1)),
        "relaxed_cost5_per_trade": round(relaxed_c5 / max(relaxed.get("n", 1), 1), 2),
        "baseline_cost5_per_trade": round(base_c5 / max(baseline.get("n", 1), 1), 2),
        "verdict": "SHORT_INDICATOR_SURVIVES_COST5" if survives else "SHORT_INDICATOR_PARTIAL",
        "note": "Spread EMA proxy, sortie z0_max90 optimiste, trades clusterisés. Research-only.",
    }
    (V14_DIR / "short_indicator.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V14-02 — Durée de reversion (Kaplan-Meier)
# ---------------------------------------------------------------------------

def _km_survival(durations: np.ndarray, observed: np.ndarray):
    """Kaplan-Meier. Retourne (times, S(t)) et médiane de survie."""
    order = np.argsort(durations)
    d, o = durations[order], observed[order]
    n = len(d)
    times, surv = [], []
    s = 1.0
    at_risk = n
    for t in np.unique(d):
        mask = d == t
        events = int(o[mask].sum())
        if at_risk > 0 and events > 0:
            s *= (1 - events / at_risk)
        times.append(float(t))
        surv.append(s)
        at_risk -= int(mask.sum())
    times, surv = np.array(times), np.array(surv)
    med = float(times[surv <= 0.5][0]) if (surv <= 0.5).any() else None
    return times, surv, med


def run_reversion_survival(df: pd.DataFrame, z_entry: float = 1.0, max_h: int = 160) -> dict[str, Any]:
    """Kaplan-Meier du temps avant que basis_z (extrême) revienne croiser 0. Global + par saison."""
    assert_no_holdout(df)
    bz = df.get("ema_cbot_basis_zscore_52w")
    if bz is None:
        return {"version": "V14-02-REVERSION-SURVIVAL", "verdict": "MISSING_BASIS_Z"}
    bzv = bz.values
    n = len(bzv)
    rows = []
    last = None
    dates = df.index
    for i in range(n):
        if np.isnan(bzv[i]) or abs(bzv[i]) <= z_entry:
            continue
        d = dates[i]
        if last is not None and (d - last).days < HORIZON:
            continue
        last = d
        sgn = np.sign(bzv[i])
        dur, obs = max_h, 0
        for t in range(1, max_h + 1):
            if i + t >= n or np.isnan(bzv[i + t]):
                continue
            if bzv[i + t] * sgn <= 0:
                dur, obs = t, 1
                break
        rows.append({"month": d.month, "duration": dur, "observed": obs})
    if len(rows) < 15:
        return {"version": "V14-02-REVERSION-SURVIVAL", "verdict": "TOO_FEW", "n": len(rows)}
    rdf = pd.DataFrame(rows)
    dur = rdf["duration"].values.astype(float)
    obs = rdf["observed"].values.astype(float)
    _, surv, med = _km_survival(dur, obs)

    def _p_by(t_days):
        # P(reversion <= t_days) estimée KM
        ts, s, _ = _km_survival(dur, obs)
        idx = np.searchsorted(ts, t_days, side="right") - 1
        return round(float(1 - s[idx]), 4) if idx >= 0 else 0.0

    seasons = {"jan_mar": [1, 2, 3], "apr_jun": [4, 5, 6], "jul_aug": [7, 8],
               "sep_nov": [9, 10, 11], "dec": [12]}
    by_season = {}
    for sname, mm in seasons.items():
        sub = rdf[rdf["month"].isin(mm)]
        if len(sub) >= 8:
            _, _, m = _km_survival(sub["duration"].values.astype(float), sub["observed"].values.astype(float))
            by_season[sname] = {"n": int(len(sub)), "median_days_to_reversion": m}

    out = {
        "version": "V14-02-REVERSION-SURVIVAL",
        "z_entry": z_entry,
        "n_entries": int(len(rdf)),
        "n_reverted": int(obs.sum()),
        "n_censored": int((1 - obs).sum()),
        "median_days_to_reversion_km": med,
        "p_revert_by_40d": _p_by(40),
        "p_revert_by_60d": _p_by(60),
        "p_revert_by_90d": _p_by(90),
        "median_by_season": by_season,
        "interpretation": (
            "La médiane KM situe l'horizon naturel de sortie ; P(revert<=90d) justifie le plafond 90j. "
            "Une saison à reversion lente justifie un plafond plus long ou une abstention."
        ),
        "verdict": "REVERSION_SURVIVAL_DONE",
    }
    (V14_DIR / "reversion_survival.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V14-04 — Robustesse au bruit du proxy EMA
# ---------------------------------------------------------------------------

def run_proxy_robustness(df: pd.DataFrame, noise_levels=(0, 1, 2, 5, 10), n_seeds: int = 5) -> dict[str, Any]:
    """Perturbe le prix EMA proxy (bruit gaussien €/t) et mesure la dégradation de l'edge short basis-haut."""
    assert_no_holdout(df)
    if "ema_close" not in df.columns:
        return {"version": "V14-04-PROXY-ROBUSTNESS", "verdict": "MISSING_PRICES"}
    base_ema = df["ema_close"].copy()
    results = {}
    for noise in noise_levels:
        hits, pnls, ns = [], [], []
        for seed in range(n_seeds if noise > 0 else 1):
            rng = np.random.default_rng(1000 + seed)
            df2 = df.copy()
            if noise > 0:
                df2["ema_close"] = base_ema + rng.normal(0, noise, len(base_ema))
            # recalc basis + z approximatif sur prix perturbé n'est pas trivial ; on garde basis_z d'origine
            # (le z vient des fondamentaux laggés) et on mesure l'impact PnL via le prix de sortie perturbé.
            sig = pd.DataFrame(index=df2.index)
            sig["signal"] = np.where(df2["ema_cbot_basis_zscore_52w"] > 1.0, "SHORT_PREMIUM", "ABSTAIN")
            t = _backtest_short(df2, sig)
            if len(t) >= 5:
                g = t["pnl"].values
                hits.append(float((g > 0).mean()))
                pnls.append(float((g - 6).sum()))
                ns.append(len(t))
        if hits:
            results[f"noise_{noise}eur"] = {
                "mean_hit_rate": round(float(np.mean(hits)), 4),
                "mean_net_pnl_cost3": round(float(np.mean(pnls)), 1),
                "std_net_pnl_cost3": round(float(np.std(pnls)), 1),
                "mean_n_trades": round(float(np.mean(ns)), 1),
            }
    base = results.get("noise_0eur", {})
    n10 = results.get("noise_10eur", {})
    degr = (round(base.get("mean_net_pnl_cost3", 0) - n10.get("mean_net_pnl_cost3", 0), 1)
            if base and n10 else None)
    robust = bool(n10 and n10.get("mean_net_pnl_cost3", -1) > 0)
    out = {
        "version": "V14-04-PROXY-ROBUSTNESS",
        "results_by_noise": results,
        "pnl_degradation_0_to_10eur": degr,
        "edge_robust_to_10eur_noise": robust,
        "interpretation": (
            "On ajoute un bruit gaussien au prix EMA proxy (jusqu'à 10 €/t) et on mesure la perte d'edge. "
            "Si l'edge short survit à un bruit important -> conclusions peu sensibles à l'erreur de proxy."
        ),
        "verdict": "PROXY_ROBUST" if robust else "PROXY_SENSITIVE",
        "note": "Le basis_z (fondamental laggé) est conservé ; on perturbe le prix de sortie. Test indicatif.",
    }
    (V14_DIR / "proxy_robustness.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
