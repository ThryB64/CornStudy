"""V17 — Indicateur research de prime EMA/CBOT : paliers, rapport, walk-forward, fiches trades.

Consolidation de V13-V16. AUCUN nouveau modèle. On transforme la règle validée (short basis-haut,
sortie au retour du basis, stop large) en indicateur research quotidien explicable, on le valide une
dernière fois proprement, et on documente chaque trade.

- compute_indicator_v17 : signal à paliers (MODERATE/STRONG/EXTREME) + UNCERTAIN (data/roll/vol).
- build_trades_detailed : fiche complète de chaque trade (entrée/sortie/PnL/MAE/contexte).
- run_walk_forward_final : validation ultra-propre, un trade à la fois, par année, coût dynamique + stop.
- run_failure_analysis : analyse qualitative des échecs / censures -> warnings.
- generate_daily_report : rapport Markdown quotidien.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V17_DIR = ARTEFACTS_DIR / "v17"
V17_DIR.mkdir(parents=True, exist_ok=True)

HORIZON = 40
MAX_HOLD = 90
STOP_LOSS = -20.0
CRISIS_YEARS = (2020, 2021, 2022)
# Médianes de reversion par saison (V14 survival)
SEASON_MEDIAN_DAYS = {1: 53, 2: 53, 3: 53, 4: 23, 5: 23, 6: 23,
                      7: 47, 8: 47, 9: 51, 10: 51, 11: 51, 12: 47}


def _tier(z: float) -> str:
    if z < 1.0:
        return "NO_SIGNAL"
    if z < 1.5:
        return "SHORT_PREMIUM_MODERATE"
    if z < 2.0:
        return "SHORT_PREMIUM_STRONG"
    return "SHORT_PREMIUM_EXTREME"


def _non_reversion_risk(z: float) -> str:
    # V15 : z>2 plus souvent censuré (haut rendement + risque de non-reversion)
    if z >= 2.0:
        return "high"
    if z >= 1.5:
        return "medium"
    return "low"


def _dynamic_cost(oi, oi_med, vol, vol_med, month) -> float:
    c = 1.0
    if not np.isnan(oi) and oi < oi_med:
        c += 2.0
    if not np.isnan(vol) and vol > vol_med:
        c += 2.0
    if month in (2, 5, 7, 10):
        c += 2.0
    return c


# ---------------------------------------------------------------------------
# V17-01 — Indicateur à paliers
# ---------------------------------------------------------------------------

def compute_indicator_v17(df: pd.DataFrame) -> pd.DataFrame:
    """Signal research par date : palier short basis-haut + warnings UNCERTAIN + objectifs/risque."""
    idx = df.index
    bz = df.get("ema_cbot_basis_zscore_52w", pd.Series(np.nan, index=idx))
    basis = df.get("ema_cbot_basis", pd.Series(np.nan, index=idx))
    dq = df.get("ema_data_availability_score", pd.Series(np.nan, index=idx))
    oi = df.get("ema_oi_total", pd.Series(np.nan, index=idx))
    vol = df.get("corn_realized_vol_20", pd.Series(np.nan, index=idx))
    trend = df.get("curve_backwardation_proxy", pd.Series(np.nan, index=idx))
    oi_med = oi[oi > 0].median() if (oi > 0).any() else 0.0
    vol_med = vol.median()
    vol_p90 = vol.quantile(0.90)

    rows = []
    for i, d in enumerate(idx):
        z = bz.iloc[i]
        if pd.isna(z):
            rows.append((d, "NO_SIGNAL", np.nan, np.nan, "", "", np.nan, np.nan, "", "", np.nan, np.nan))
            continue
        base_tier = _tier(float(z))
        warnings_list = []
        if not pd.isna(dq.iloc[i]) and dq.iloc[i] < 0.4:
            warnings_list.append("UNCERTAIN_DATA")
        if d.month in (2, 5, 7, 10):
            warnings_list.append("UNCERTAIN_ROLL")
        if not pd.isna(vol.iloc[i]) and vol.iloc[i] > vol_p90:
            warnings_list.append("UNCERTAIN_VOL")

        signal = base_tier
        # warnings rétrogradent un signal actif vers UNCERTAIN (pas un veto dur)
        if base_tier != "NO_SIGNAL" and warnings_list:
            signal = warnings_list[0]

        cbot_ctx = ("above_trend" if (not pd.isna(trend.iloc[i]) and trend.iloc[i] > 0)
                    else "below_trend" if not pd.isna(trend.iloc[i]) else "unknown")
        cost = _dynamic_cost(oi.iloc[i], oi_med, vol.iloc[i], vol_med, d.month)
        rows.append((
            d, signal, float(z), float(basis.iloc[i]) if not pd.isna(basis.iloc[i]) else np.nan,
            "z->0.5", "z->0",
            float(STOP_LOSS), float(SEASON_MEDIAN_DAYS.get(d.month, 47)),
            _non_reversion_risk(float(z)) if base_tier != "NO_SIGNAL" else "",
            cbot_ctx, round(cost, 1),
            round(float(dq.iloc[i]), 3) if not pd.isna(dq.iloc[i]) else np.nan,
        ))
    out = pd.DataFrame(rows, columns=[
        "date", "signal", "basis_z", "basis", "objective_prudent", "objective_full",
        "stop_eur_t", "median_horizon_days", "non_reversion_risk", "cbot_context",
        "est_cost_per_leg", "data_quality"]).set_index("date")
    out["statut"] = "RESEARCH_ONLY_NOT_TRADING"
    return out


# ---------------------------------------------------------------------------
# Fiches trades détaillées (partagé V17-04/05/06)
# ---------------------------------------------------------------------------

def _sim_detail(ema, cbot, bz, i, z_exit, max_hold, stop_loss=None):
    n = len(ema)
    e0, c0, z0 = ema[i], cbot[i], bz[i]
    if np.isnan(e0) or np.isnan(c0) or np.isnan(z0):
        return None
    sgn = np.sign(z0)
    mae = 0.0
    last = None
    for t in range(1, max_hold + 1):
        j = i + t
        if j >= n or np.isnan(ema[j]) or np.isnan(cbot[j]):
            continue
        pnl = -1.0 * ((ema[j] / e0 - 1) - (cbot[j] / c0 - 1)) * e0
        mae = min(mae, pnl)
        last = (pnl, t, bz[j], j)
        if stop_loss is not None and pnl <= stop_loss:
            return {"pnl": pnl, "days": t, "exit_z": bz[j], "exit_pos": j, "mae": mae, "reverted": 0, "stopped": 1}
        zt = bz[j]
        if not np.isnan(zt) and zt * sgn <= z_exit:
            return {"pnl": pnl, "days": t, "exit_z": bz[j], "exit_pos": j, "mae": mae,
                    "reverted": int(z_exit == 0.0), "stopped": 0}
    if last is None:
        return None
    return {"pnl": last[0], "days": last[1], "exit_z": last[2], "exit_pos": last[3],
            "mae": mae, "reverted": 0, "stopped": 0}


def build_trades_detailed(df: pd.DataFrame) -> pd.DataFrame:
    """Fiche détaillée de chaque trade short basis-haut (entrée z>1, non-overlap)."""
    ema = df["ema_close"].values
    cbot = df["cbot_eur_t"].values
    bz = df["ema_cbot_basis_zscore_52w"].values
    vol = df.get("corn_realized_vol_20", pd.Series(np.nan, index=df.index)).values
    oi = df.get("ema_oi_total", pd.Series(np.nan, index=df.index)).values
    trend = df.get("curve_backwardation_proxy", pd.Series(np.nan, index=df.index)).values
    oi_med = np.nanmedian(oi[oi > 0]) if np.isfinite(oi).any() else 0.0
    vol_med = np.nanmedian(vol)
    dates = df.index

    cand = np.where((df["ema_cbot_basis_zscore_52w"] > 1.0).values)[0]
    kept, last = [], None
    for i in cand:
        if last is None or (dates[i] - last).days >= HORIZON:
            kept.append(i)
            last = dates[i]

    rows = []
    for i in kept:
        z0_res = _sim_detail(ema, cbot, bz, i, 0.0, MAX_HOLD, stop_loss=STOP_LOSS)
        z05_res = _sim_detail(ema, cbot, bz, i, 0.5, 160)
        if z0_res is None:
            continue
        rows.append({
            "entry_date": str(dates[i].date()),
            "exit_date": str(dates[z0_res["exit_pos"]].date()),
            "season": ("jan_mar" if dates[i].month <= 3 else "apr_jun" if dates[i].month <= 6
                       else "jul_aug" if dates[i].month <= 8 else "sep_nov" if dates[i].month <= 11 else "dec"),
            "tier": _tier(float(bz[i])),
            "entry_z": round(float(bz[i]), 3),
            "exit_z": round(float(z0_res["exit_z"]), 3) if not np.isnan(z0_res["exit_z"]) else None,
            "pnl_z0_max90_sl20": round(float(z0_res["pnl"]), 2),
            "pnl_z0.5": round(float(z05_res["pnl"]), 2) if z05_res else None,
            "mae": round(float(z0_res["mae"]), 2),
            "duration_days": int(z0_res["days"]),
            "reverted": int(z0_res["reverted"]),
            "stopped": int(z0_res["stopped"]),
            "cbot_context": ("above_trend" if (not np.isnan(trend[i]) and trend[i] > 0) else "below_trend"),
            "high_vol": int(vol[i] > vol_med) if not np.isnan(vol[i]) else 0,
            "low_liquidity": int(oi[i] < oi_med) if not np.isnan(oi[i]) else 0,
            "roll_month": int(dates[i].month in (2, 5, 7, 10)),
            "crisis": int(dates[i].year in CRISIS_YEARS),
            "dyn_cost_per_leg": _dynamic_cost(oi[i], oi_med, vol[i], vol_med, dates[i].month),
            "win": int(z0_res["pnl"] > 0),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# V17-04 — Walk-forward final ultra propre
# ---------------------------------------------------------------------------

def run_walk_forward_final(df: pd.DataFrame) -> dict[str, Any]:
    """Validation finale : un trade à la fois, sortie z0 max90 + stop -20 + coût dynamique, par année."""
    assert_no_holdout(df)
    if "ema_close" not in df.columns:
        return {"version": "V17-04-WALKFORWARD", "verdict": "MISSING_DATA"}
    ema = df["ema_close"].values
    cbot = df["cbot_eur_t"].values
    bz = df["ema_cbot_basis_zscore_52w"].values
    vol = df.get("corn_realized_vol_20", pd.Series(np.nan, index=df.index)).values
    oi = df.get("ema_oi_total", pd.Series(np.nan, index=df.index)).values
    oi_med = np.nanmedian(oi[oi > 0]) if np.isfinite(oi).any() else 0.0
    vol_med = np.nanmedian(vol)
    dates = df.index

    cand = np.where((df["ema_cbot_basis_zscore_52w"] > 1.0).values)[0]
    trades = []
    busy_until = -1
    for i in cand:
        if i <= busy_until:
            continue
        res = _sim_detail(ema, cbot, bz, i, 0.0, MAX_HOLD, stop_loss=STOP_LOSS)
        if res is None:
            continue
        cost = _dynamic_cost(oi[i], oi_med, vol[i], vol_med, dates[i].month)
        trades.append({"year": dates[i].year, "pnl": res["pnl"], "net": res["pnl"] - 2 * cost,
                       "days": res["days"]})
        busy_until = res["exit_pos"]
    tdf = pd.DataFrame(trades)
    if len(tdf) < 10:
        return {"version": "V17-04-WALKFORWARD", "verdict": "TOO_FEW", "n": int(len(tdf))}

    g = tdf["net"].values
    eq = np.cumsum(g)
    peak = np.maximum.accumulate(eq)
    by_year = {}
    for y in sorted(tdf["year"].unique()):
        sub = tdf[tdf["year"] == y]["net"].values
        by_year[str(y)] = {"n": int(len(sub)), "net_pnl_dyncost": round(float(sub.sum()), 1),
                           "hit": round(float((sub > 0).mean()), 4)}
    years_pos = sum(1 for v in by_year.values() if v["net_pnl_dyncost"] > 0)
    out = {
        "version": "V17-04-WALKFORWARD",
        "setup": "1 trade à la fois, entrée z>1, sortie z0 max90, stop -20, coût dynamique",
        "n_trades": int(len(tdf)),
        "hit_rate": round(float((g > 0).mean()), 4),
        "net_pnl_dyncost_total": round(float(g.sum()), 1),
        "mean_net_per_trade": round(float(g.mean()), 2),
        "max_drawdown": round(float(np.min(eq - peak)), 1),
        "by_year": by_year,
        "years_positive": years_pos,
        "years_total": len(by_year),
        "verdict": ("WALKFORWARD_ROBUST" if (g.sum() > 0 and years_pos / len(by_year) >= 0.6)
                    else "WALKFORWARD_PARTIAL"),
        "note": "Spread proxy, sortie z0 optimiste, n limité. Research-only.",
    }
    (V17_DIR / "walk_forward_final.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V17-05 — Fiches des trades (export)
# ---------------------------------------------------------------------------

def run_trade_fiches(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    tdf = build_trades_detailed(df)
    if len(tdf) == 0:
        return {"version": "V17-05-TRADE-FICHES", "verdict": "NO_TRADES"}
    tdf.to_parquet(V17_DIR / "trade_fiches.parquet", index=False)
    summary = {
        "version": "V17-05-TRADE-FICHES",
        "n_trades": int(len(tdf)),
        "n_wins": int(tdf["win"].sum()),
        "n_losses": int((tdf["win"] == 0).sum()),
        "win_rate": round(float(tdf["win"].mean()), 4),
        "by_tier": {t: {"n": int((tdf["tier"] == t).sum()),
                        "win_rate": round(float(tdf[tdf["tier"] == t]["win"].mean()), 4),
                        "mean_pnl": round(float(tdf[tdf["tier"] == t]["pnl_z0_max90_sl20"].mean()), 2)}
                    for t in tdf["tier"].unique()},
        "n_stopped": int(tdf["stopped"].sum()),
        "n_reverted": int(tdf["reverted"].sum()),
        "trades_sample": tdf.head(8).to_dict(orient="records"),
        "losing_trades": tdf[tdf["win"] == 0].to_dict(orient="records"),
        "verdict": "TRADE_FICHES_DONE",
    }
    (V17_DIR / "trade_fiches_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary


# ---------------------------------------------------------------------------
# V17-06 — Analyse des échecs
# ---------------------------------------------------------------------------

def run_failure_analysis(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    tdf = build_trades_detailed(df)
    if len(tdf) == 0:
        return {"version": "V17-06-FAILURE", "verdict": "NO_TRADES"}
    losers = tdf[tdf["win"] == 0]
    winners = tdf[tdf["win"] == 1]

    def _prof(sub):
        if len(sub) == 0:
            return {"n": 0}
        return {"n": int(len(sub)),
                "mean_entry_z": round(float(sub["entry_z"].mean()), 3),
                "share_extreme_z_gt_2": round(float((sub["entry_z"] > 2).mean()), 3),
                "share_high_vol": round(float(sub["high_vol"].mean()), 3),
                "share_roll_month": round(float(sub["roll_month"].mean()), 3),
                "share_crisis": round(float(sub["crisis"].mean()), 3),
                "share_above_trend": round(float((sub["cbot_context"] == "above_trend").mean()), 3),
                "share_stopped": round(float(sub["stopped"].mean()), 3)}

    lp, wp = _prof(losers), _prof(winners)
    warnings_out = []
    if lp.get("n", 0) >= 3:
        if lp["share_extreme_z_gt_2"] > wp["share_extreme_z_gt_2"] + 0.15:
            warnings_out.append("WARNING : les pertes ont plus souvent un z d'entrée extrême (>2)")
        if lp["share_high_vol"] > wp["share_high_vol"] + 0.15:
            warnings_out.append("WARNING : les pertes arrivent plus en haute volatilité")
        if lp["share_crisis"] > wp["share_crisis"] + 0.15:
            warnings_out.append("WARNING : les pertes sont concentrées en années de crise")
        if lp["share_above_trend"] < wp["share_above_trend"] - 0.15:
            warnings_out.append("WARNING : les pertes arrivent plus quand le CBOT est sous sa tendance")
    out = {
        "version": "V17-06-FAILURE",
        "n_trades": int(len(tdf)), "n_losers": int(len(losers)), "n_winners": int(len(winners)),
        "profile_losers": lp,
        "profile_winners": wp,
        "warnings": warnings_out or ["aucun pattern d'échec net : ne pas sur-filtrer (cf. V15)"],
        "verdict": "FAILURE_ANALYSIS_DONE",
    }
    (V17_DIR / "failure_analysis.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V17-02 — Rapport quotidien
# ---------------------------------------------------------------------------

def generate_daily_report(df: pd.DataFrame) -> str:
    """Rapport Markdown du dernier signal exploitable de l'indicateur."""
    assert_no_holdout(df)
    ind = compute_indicator_v17(df)
    actionable = ind[~ind["signal"].isin(["NO_SIGNAL"])]
    if len(actionable) == 0:
        return "# Rapport maïs EMA/CBOT\n\nAucun signal de prime actif récemment.\n"
    from mais.research.data_freshness import compute_freshness
    last = actionable.iloc[-1]
    d = actionable.index[-1]
    cbot_eur = df["cbot_eur_t"].reindex([d]).iloc[0]
    ema_price = df["ema_close"].reindex([d]).iloc[0] if "ema_close" in df.columns else np.nan
    fresh = compute_freshness(df)
    # GATE DE FRAÎCHEUR : données périmées -> on n'émet pas de signal actionnable.
    signal_display = last["signal"] if fresh["signal_allowed"] else "UNCERTAIN_DATA_STALE"
    lines = [
        f"# Rapport maïs EMA/CBOT — dernière donnée {d.date()} (généré pour {fresh['as_of']})",
        "",
        f"**Statut** : {last['statut']}",
        f"**Fraîcheur** : {fresh['freshness_verdict']} | retard {fresh['staleness_days']} j ouvrés "
        f"(dernier basis {fresh['last_basis_date']}, CBOT {fresh['last_cbot_date']}, EMA {fresh['last_ema_date']})",
        "",
        f"1. Prix CBOT converti : {round(float(cbot_eur), 2) if not pd.isna(cbot_eur) else 'NA'} EUR/t",
        f"2. Prix EMA (proxy) : {round(float(ema_price), 2) if not pd.isna(ema_price) else 'NA'} EUR/t",
        f"3. Basis EMA/CBOT : {round(float(last['basis']), 2) if not pd.isna(last['basis']) else 'NA'} EUR/t",
        f"4. Z-score du basis : {round(float(last['basis_z']), 3)}",
        f"5. **Signal premium : {signal_display}**"
        + ("" if fresh["signal_allowed"] else f" (brut {last['signal']} — GATÉ : données périmées)"),
        f"6. Objectif de reversion : prudent {last['objective_prudent']} / complet {last['objective_full']}",
        f"7. Stop indicatif : {last['stop_eur_t']} EUR/t | horizon médian : {int(last['median_horizon_days'])} j",
        f"8. Risque de non-reversion : {last['non_reversion_risk']} | contexte CBOT : {last['cbot_context']}",
        f"9. Coût estimé/leg : {last['est_cost_per_leg']} EUR/t | qualité data : {last['data_quality']}",
        "10. Réserve : prix EMA proxy exploratoire, recherche uniquement, aucune exécution réelle.",
        "",
        "_Interprétation : un basis élevé tend à se compresser (la prime européenne se normalise). "
        "Signal = sous-performance probable d'EMA vs CBOT sur ~40-90 j._",
    ]
    # V101 : ÉTAT LIVE OFFICIEL en priorité (journal forward), avant les diagnostics master (qui peuvent être en retard)
    try:
        from mais.research.v101_official_synthesis_fix import official_live_report_block
        block = official_live_report_block(df)
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v132_indicator_synthesis_v3 import synthesis_v3_report_block
        block = synthesis_v3_report_block()
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v122_journal_consistency import consistency_report_block
        block = consistency_report_block()
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v123_freshness_gate import freshness_report_block
        block = freshness_report_block()
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v107_live_context_refresh import live_context_report_block
        block = live_context_report_block(try_network=False)
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v108_live_basis_reconstruction import live_basis_report_block
        block = live_basis_report_block()
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v109_ema_curve_live_tension import curve_tension_report_block
        block = curve_tension_report_block()
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v125_curve_accumulation import curve_accumulation_report_block
        block = curve_accumulation_report_block()
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v126_matif_substitution_v2 import substitution_v2_report_block
        block = substitution_v2_report_block()
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v127_weather_forecast_extremes import weather_warning_report_block
        block = weather_warning_report_block()
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v129_event_catalyst_library import event_library_report_block
        block = event_library_report_block()
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v131_target_recommendation_v3 import target_v3_report_block
        block = target_v3_report_block()
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v130_basis_regime_econometrics import regime_econometrics_report_block
        block = regime_econometrics_report_block()
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v102_active_signal_monitoring import active_signal_report_block
        block = active_signal_report_block()
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v124_active_monitoring_v2 import active_monitoring_v2_report_block
        block = active_monitoring_v2_report_block()
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v106_compression_trigger import compression_trigger_report_block
        block = compression_trigger_report_block(df)
        if block:
            lines += ["", block]
    except Exception:
        pass
    # V38/V41 : contextes ADVERSE_RISK + CBOT_SUPPORT additifs (jamais un veto, n'altèrent pas le signal)
    try:
        from mais.research.v38_adverse_risk import adverse_risk_report_block
        block = adverse_risk_report_block(df)
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v41_cbot_support import cbot_support_report_block
        block = cbot_support_report_block(df)
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v43_signal_quality_matrix import signal_quality_report_block
        block = signal_quality_report_block(df)
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v54_physical_tension import physical_tension_report_block
        block = physical_tension_report_block(df)
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v56_target_recommendation import target_recommendation_report_block
        block = target_recommendation_report_block(df)
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v64_adverse_risk_v2 import adverse_risk_v2_report_block
        block = adverse_risk_v2_report_block(df)
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v86_cbot_support_v2 import cbot_support_v2_report_block
        block = cbot_support_v2_report_block(df)
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v99_indicator_synthesis_v2 import synthesis_v2_report_block
        block = synthesis_v2_report_block(df, with_network=False)
        if block:
            lines += ["", block]
    except Exception:
        try:
            from mais.research.v77_indicator_synthesis import synthesis_report_block
            block = synthesis_report_block(df)
            if block:
                lines += ["", block]
        except Exception:
            pass
    try:
        from mais.research.v133_monthly_forward_report_v2 import monthly_v2_report_block
        block = monthly_v2_report_block()
        if block:
            lines += ["", block]
    except Exception:
        pass
    try:
        from mais.research.v135_decision_checkpoint import checkpoint_report_block
        block = checkpoint_report_block()
        if block:
            lines += ["", block]
    except Exception:
        pass
    report = "\n".join(lines)
    (V17_DIR / "daily_report.md").write_text(report, encoding="utf-8")
    return report
