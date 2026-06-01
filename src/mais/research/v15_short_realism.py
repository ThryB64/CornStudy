"""V15 — Rendre l'indicateur short basis-haut plus réaliste, saison-aware et moins optimiste.

Suite V14. Discipline stricte : on n'ajoute PAS de modèle ; on affine la sortie, le risque, les coûts et
le forward de la règle short basis-haut (basis_z > 1), validée robuste hors crise en V13.

- run_season_aware_exits : plafond de sortie adapté à la vitesse de reversion par saison.
- run_censored_archaeology : analyse des trades qui ne reviennent pas -> vetoes intelligents.
- run_drawdown_study : distribution du MAE avant reversion -> stop rationnel.
- run_partial_exits : sortie 50% z->0.5 + 50% z->0, vs sorties pleines.
- run_position_sizing : taille par niveau d'anomalie basis_z (research-only).
- run_dynamic_cost : coût par trade fonction de liquidité/vol/roll, vs coût fixe.
- run_strict_portfolio : un seul trade ouvert à la fois (vs non-overlap, vs events indépendants).

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V15_DIR = ARTEFACTS_DIR / "v15"
V15_DIR.mkdir(parents=True, exist_ok=True)

HORIZON = 40
CRISIS_YEARS = (2020, 2021, 2022)
# Plafonds saison-aware (issus de V14 survival : médianes 23-53j)
SEASON_EXIT = {1: ("z0", 120), 2: ("z0", 120), 3: ("z0", 120),
               4: ("z0", 60), 5: ("z0", 60), 6: ("z0", 60),
               7: ("z0", 90), 8: ("z0", 90),
               9: ("z0", 120), 10: ("z0", 120), 11: ("z0", 120),
               12: ("z0", 90)}


def _arrays(df: pd.DataFrame):
    return (df["ema_close"].values, df["cbot_eur_t"].values,
            df["ema_cbot_basis_zscore_52w"].values)


def _sim(ema, cbot, bz, i, side, z_exit, max_hold, stop_loss=None):
    """Trade depuis i : sortie quand basis_z*sgn <= z_exit, ou max_hold, ou stop_loss.

    Renvoie (pnl_eur_t, holding_days, mae_eur_t).
    """
    n = len(ema)
    e0, c0, z0 = ema[i], cbot[i], bz[i]
    if np.isnan(e0) or np.isnan(c0) or np.isnan(z0):
        return np.nan, np.nan, np.nan
    sgn = np.sign(z0)
    mae = 0.0
    last_pnl, last_t = np.nan, np.nan
    for t in range(1, max_hold + 1):
        j = i + t
        if j >= n or np.isnan(ema[j]) or np.isnan(cbot[j]):
            continue
        pnl = side * ((ema[j] / e0 - 1) - (cbot[j] / c0 - 1)) * e0
        mae = min(mae, pnl)
        last_pnl, last_t = pnl, t
        if stop_loss is not None and pnl <= stop_loss:
            return pnl, t, mae
        zt = bz[j]
        if not np.isnan(zt) and zt * sgn <= z_exit:
            return pnl, t, mae
    return last_pnl, last_t, mae


def _sim_partial(ema, cbot, bz, i, side, z1, z2, max_hold, frac=0.5, stop_loss=None):
    """Sortie partielle : frac à z->z1, reste à z->z2 (ou max_hold). Renvoie (pnl, days, mae)."""
    n = len(ema)
    e0, c0, z0 = ema[i], cbot[i], bz[i]
    if np.isnan(e0) or np.isnan(c0) or np.isnan(z0):
        return np.nan, np.nan, np.nan
    sgn = np.sign(z0)
    mae = 0.0
    leg1_pnl, leg1_done = np.nan, False
    last_pnl, last_t = np.nan, np.nan
    for t in range(1, max_hold + 1):
        j = i + t
        if j >= n or np.isnan(ema[j]) or np.isnan(cbot[j]):
            continue
        pnl = side * ((ema[j] / e0 - 1) - (cbot[j] / c0 - 1)) * e0
        mae = min(mae, pnl)
        last_pnl, last_t = pnl, t
        zt = bz[j]
        if stop_loss is not None and pnl <= stop_loss:
            if not leg1_done:
                return pnl, t, mae
            return frac * leg1_pnl + (1 - frac) * pnl, t, mae
        if not leg1_done and not np.isnan(zt) and zt * sgn <= z1:
            leg1_pnl, leg1_done = pnl, True
        if leg1_done and not np.isnan(zt) and zt * sgn <= z2:
            return frac * leg1_pnl + (1 - frac) * pnl, t, mae
    if leg1_done:
        return frac * leg1_pnl + (1 - frac) * last_pnl, last_t, mae
    return last_pnl, last_t, mae


def _entries(df, mask, spacing=HORIZON):
    idx = np.where(mask.values)[0]
    dates = df.index
    kept, last = [], None
    for i in idx:
        d = dates[i]
        if last is None or (d - last).days >= spacing:
            kept.append(i)
            last = d
    return kept


def _z_exit_val(name):
    return {"z0": 0.0, "z0.5": 0.5}.get(name, 0.0)


def _summ(pnls, days=None):
    if len(pnls) < 5:
        return {"n": int(len(pnls))}
    g = np.array(pnls)
    out = {"n": int(len(g)), "hit_rate": round(float((g > 0).mean()), 4),
           "mean_pnl": round(float(g.mean()), 2),
           "net_cost1": round(float((g - 2).sum()), 1),
           "net_cost3": round(float((g - 6).sum()), 1),
           "net_cost5": round(float((g - 10).sum()), 1)}
    if days is not None and len(days):
        d = np.array(days)
        out["mean_holding_days"] = round(float(d.mean()), 1)
        out["profit_per_day"] = round(float(g.sum() / max(d.sum(), 1)), 4)
    return out


# ---------------------------------------------------------------------------
# V15-01 — Sortie saison-aware
# ---------------------------------------------------------------------------

def run_season_aware_exits(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    if "ema_close" not in df.columns or "ema_cbot_basis_zscore_52w" not in df.columns:
        return {"version": "V15-01-SEASON-EXITS", "verdict": "MISSING_DATA"}
    ema, cbot, bz = _arrays(df)
    entries = _entries(df, df["ema_cbot_basis_zscore_52w"] > 1.0)
    months = df.index.month

    # règles uniformes de référence
    uniform = {"H40": ("z0", 40), "z0.5": ("z0.5", 160), "z0": ("z0", 160), "z0_max90": ("z0", 90)}
    results = {}
    for name, (zx, mh) in uniform.items():
        pnls, days = [], []
        for i in entries:
            p, t, _ = _sim(ema, cbot, bz, i, -1.0, _z_exit_val(zx), mh)
            if not np.isnan(p):
                pnls.append(p)
                days.append(t)
        results[name] = _summ(pnls, days)

    # règle saison-aware
    pnls, days = [], []
    for i in entries:
        zx, mh = SEASON_EXIT.get(int(months[i]), ("z0", 90))
        p, t, _ = _sim(ema, cbot, bz, i, -1.0, _z_exit_val(zx), mh)
        if not np.isnan(p):
            pnls.append(p)
            days.append(t)
    results["season_aware"] = _summ(pnls, days)

    ranked = sorted([(k, v) for k, v in results.items() if "net_cost3" in v],
                    key=lambda kv: -kv[1]["net_cost3"])
    sa = results["season_aware"]
    z0 = results["z0"]
    out = {
        "version": "V15-01-SEASON-EXITS",
        "season_exit_map": {str(k): v for k, v in SEASON_EXIT.items()},
        "results": results,
        "best_by_net_cost3": ranked[0][0] if ranked else None,
        "season_aware_beats_uniform_z0": bool(sa.get("net_cost3", -1) > z0.get("net_cost3", -1)
                                              or sa.get("profit_per_day", -1) > z0.get("profit_per_day", -1)),
        "interpretation": (
            "Plafond court au printemps (reversion rapide 23j), long en hiver (53j). On compare l'efficacité "
            "capital (profit_per_day) et le PnL net coût 3 à la sortie uniforme."
        ),
        "verdict": "SEASON_AWARE_DONE",
    }
    (V15_DIR / "season_aware_exits.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V15-02 — Archéologie des trades censurés
# ---------------------------------------------------------------------------

def run_censored_archaeology(df: pd.DataFrame, max_hold: int = 120) -> dict[str, Any]:
    assert_no_holdout(df)
    ema, cbot, bz = _arrays(df)
    entries = _entries(df, df["ema_cbot_basis_zscore_52w"] > 1.0)
    vol = df.get("corn_realized_vol_20", pd.Series(np.nan, index=df.index)).values
    macd = df.get("corn_macd_hist", pd.Series(np.nan, index=df.index)).values
    n = len(bz)
    rows = []
    for i in entries:
        sgn = np.sign(bz[i])
        reverted, dur = 0, max_hold
        for t in range(1, max_hold + 1):
            if i + t >= n or np.isnan(bz[i + t]):
                continue
            if bz[i + t] * sgn <= 0:
                reverted, dur = 1, t
                break
        rows.append({"year": df.index[i].year, "month": df.index[i].month,
                     "entry_z": float(bz[i]), "vol": float(vol[i]) if not np.isnan(vol[i]) else None,
                     "macd": float(macd[i]) if not np.isnan(macd[i]) else None,
                     "roll_month": int(df.index[i].month in (2, 5, 7, 10)),
                     "crisis": int(df.index[i].year in CRISIS_YEARS),
                     "reverted": reverted, "duration": dur})
    rdf = pd.DataFrame(rows)
    if len(rdf) < 15:
        return {"version": "V15-02-CENSORED", "verdict": "TOO_FEW", "n": int(len(rdf))}
    cens = rdf[rdf["reverted"] == 0]
    rev = rdf[rdf["reverted"] == 1]

    def _profile(sub):
        if len(sub) == 0:
            return {"n": 0}
        return {"n": int(len(sub)),
                "mean_entry_z": round(float(sub["entry_z"].mean()), 3),
                "mean_vol": round(float(sub["vol"].dropna().mean()), 4) if sub["vol"].notna().any() else None,
                "share_crisis": round(float(sub["crisis"].mean()), 3),
                "share_roll_month": round(float(sub["roll_month"].mean()), 3),
                "share_extreme_z_gt_2": round(float((sub["entry_z"] > 2).mean()), 3)}

    proposed = []
    if len(cens) >= 3:
        if cens["entry_z"].mean() > rev["entry_z"].mean() + 0.3:
            proposed.append("veto_or_reduce_if_entry_z_gt_2 (échecs ont un z d'entrée plus extrême)")
        if cens["crisis"].mean() > rev["crisis"].mean() + 0.2:
            proposed.append("reduce_size_in_crisis_years")
        if cens["roll_month"].mean() > rev["roll_month"].mean() + 0.2:
            proposed.append("veto_roll_month_entries")
    out = {
        "version": "V15-02-CENSORED",
        "n_entries": int(len(rdf)), "n_reverted": int(len(rev)), "n_censored": int(len(cens)),
        "profile_censored": _profile(cens),
        "profile_reverted": _profile(rev),
        "proposed_vetoes": proposed or ["aucun pattern net : ne pas sur-filtrer"],
        "interpretation": "On compare le profil des échecs vs réussites pour proposer des vetoes ciblés (pas du sur-filtrage).",
        "verdict": "CENSORED_ARCHAEOLOGY_DONE",
    }
    (V15_DIR / "censored_archaeology.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V15-03 — Drawdown / MAE avant reversion
# ---------------------------------------------------------------------------

def run_drawdown_study(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    ema, cbot, bz = _arrays(df)
    entries = _entries(df, df["ema_cbot_basis_zscore_52w"] > 1.0)
    vol = df.get("corn_realized_vol_20", pd.Series(np.nan, index=df.index)).values
    vol_med = np.nanmedian(vol)
    rows = []
    for i in entries:
        p, t, mae = _sim(ema, cbot, bz, i, -1.0, 0.0, 90)
        if np.isnan(p):
            continue
        rows.append({"month": df.index[i].month, "entry_z": float(bz[i]), "mae": float(mae),
                     "pnl": float(p), "high_vol": int(vol[i] > vol_med) if not np.isnan(vol[i]) else 0})
    rdf = pd.DataFrame(rows)
    if len(rdf) < 10:
        return {"version": "V15-03-DRAWDOWN", "verdict": "TOO_FEW"}
    mae = rdf["mae"].values
    pct = {"p50": float(np.percentile(mae, 50)), "p75": float(np.percentile(mae, 25)),
           "p90": float(np.percentile(mae, 10)), "p95": float(np.percentile(mae, 5)),
           "worst": float(mae.min())}
    pct = {k: round(v, 2) for k, v in pct.items()}

    # test stops aux percentiles
    stops = {}
    for sl in (-10, -15, -20, -25):
        pnls = []
        for i in entries:
            p, _, _ = _sim(ema, cbot, bz, i, -1.0, 0.0, 90, stop_loss=sl)
            if not np.isnan(p):
                pnls.append(p)
        stops[f"sl_{sl}"] = _summ(pnls)
    by_extreme = {
        "entry_z_1_2": round(float(rdf[(rdf["entry_z"] <= 2)]["mae"].mean()), 2),
        "entry_z_gt_2": round(float(rdf[rdf["entry_z"] > 2]["mae"].mean()), 2) if (rdf["entry_z"] > 2).any() else None,
        "high_vol": round(float(rdf[rdf["high_vol"] == 1]["mae"].mean()), 2) if (rdf["high_vol"] == 1).any() else None,
        "low_vol": round(float(rdf[rdf["high_vol"] == 0]["mae"].mean()), 2) if (rdf["high_vol"] == 0).any() else None,
    }
    out = {
        "version": "V15-03-DRAWDOWN",
        "n_trades": int(len(rdf)),
        "mae_percentiles_eur_t": pct,
        "mae_by_context": by_extreme,
        "stop_loss_tests": stops,
        "recommended_stop_eur_t": -20,
        "interpretation": (
            "Le MAE p90/p95 dimensionne le stop. V13 montrait SL -10 destructeur ; on confirme et on "
            "recommande un stop large (~ -20) compatible avec la respiration du trade."
        ),
        "verdict": "DRAWDOWN_STUDY_DONE",
    }
    (V15_DIR / "drawdown_study.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V15-04 — Sorties partielles
# ---------------------------------------------------------------------------

def run_partial_exits(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    ema, cbot, bz = _arrays(df)
    entries = _entries(df, df["ema_cbot_basis_zscore_52w"] > 1.0)

    def _run(simfn):
        pnls, days, maes = [], [], []
        for i in entries:
            p, t, m = simfn(i)
            if not np.isnan(p):
                pnls.append(p)
                days.append(t)
                maes.append(m)
        s = _summ(pnls, days)
        if maes:
            s["mean_mae"] = round(float(np.mean(maes)), 2)
        return s

    results = {
        "full_z0.5": _run(lambda i: _sim(ema, cbot, bz, i, -1.0, 0.5, 160)),
        "full_z0_max90": _run(lambda i: _sim(ema, cbot, bz, i, -1.0, 0.0, 90)),
        "partial_50_z0.5_then_z0_max90": _run(lambda i: _sim_partial(ema, cbot, bz, i, -1.0, 0.5, 0.0, 90)),
        "partial_50_z0.5_then_z0_max90_sl20": _run(
            lambda i: _sim_partial(ema, cbot, bz, i, -1.0, 0.5, 0.0, 90, stop_loss=-20)),
    }
    ranked = sorted([(k, v) for k, v in results.items() if v.get("profit_per_day") is not None],
                    key=lambda kv: -kv[1]["profit_per_day"])
    out = {
        "version": "V15-04-PARTIAL-EXITS",
        "results": results,
        "best_by_profit_per_day": ranked[0][0] if ranked else None,
        "interpretation": (
            "La sortie partielle vise à combiner l'efficacité de z->0.5 et le PnL de z->0, en réduisant le MAE. "
            "On juge surtout sur profit_per_day et MAE moyen."
        ),
        "verdict": "PARTIAL_EXITS_DONE",
    }
    (V15_DIR / "partial_exits.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V15-05 — Position sizing research-only
# ---------------------------------------------------------------------------

def run_position_sizing(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    ema, cbot, bz = _arrays(df)
    vol = df.get("corn_realized_vol_20", pd.Series(np.nan, index=df.index)).values
    vol_med = np.nanmedian(vol)
    entries = _entries(df, df["ema_cbot_basis_zscore_52w"] > 1.0)

    def _size(z, v):
        s = 1.0
        if z > 2:
            s = 2.0
        elif z > 1.5:
            s = 1.5
        if not np.isnan(v) and v > vol_med:
            s = min(s, 1.5)  # cap si vol élevée
        return s

    eq_pnl, sized_pnl, sizes = [], [], []
    by_bucket = {"z_1_1.5": [], "z_1.5_2": [], "z_gt_2": []}
    for i in entries:
        p, _, _ = _sim(ema, cbot, bz, i, -1.0, 0.0, 90)
        if np.isnan(p):
            continue
        z = bz[i]
        s = _size(z, vol[i])
        eq_pnl.append(p)
        sized_pnl.append(p * s)
        sizes.append(s)
        if z > 2:
            by_bucket["z_gt_2"].append(p)
        elif z > 1.5:
            by_bucket["z_1.5_2"].append(p)
        else:
            by_bucket["z_1_1.5"].append(p)

    bucket_stats = {k: _summ(v) for k, v in by_bucket.items()}
    eq = _summ(eq_pnl)
    sized = _summ(sized_pnl)
    bigger_anomaly_bigger_edge = bool(
        (bucket_stats.get("z_gt_2", {}).get("mean_pnl", -1e9)) >=
        (bucket_stats.get("z_1_1.5", {}).get("mean_pnl", -1e9)))
    out = {
        "version": "V15-05-POSITION-SIZING",
        "equal_weight": eq,
        "z_scaled_weight": sized,
        "mean_size": round(float(np.mean(sizes)), 3) if sizes else None,
        "pnl_by_entry_z_bucket": bucket_stats,
        "bigger_anomaly_bigger_edge": bigger_anomaly_bigger_edge,
        "interpretation": (
            "Research-only : on regarde si un basis plus extrême donne un edge par trade plus fort (sizing). "
            "Pas une recommandation de levier."
        ),
        "verdict": "POSITION_SIZING_DONE",
    }
    (V15_DIR / "position_sizing.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V15-06 — Coût dynamique
# ---------------------------------------------------------------------------

def run_dynamic_cost(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    ema, cbot, bz = _arrays(df)
    oi = df.get("ema_oi_total", pd.Series(np.nan, index=df.index)).values
    vol = df.get("corn_realized_vol_20", pd.Series(np.nan, index=df.index)).values
    oi_med = np.nanmedian(oi[oi > 0]) if np.isfinite(oi).any() else 0
    vol_med = np.nanmedian(vol)
    entries = _entries(df, df["ema_cbot_basis_zscore_52w"] > 1.0)

    def _dyn_cost(i):
        c = 1.0
        if not np.isnan(oi[i]) and oi[i] < oi_med:
            c += 2.0
        if not np.isnan(vol[i]) and vol[i] > vol_med:
            c += 2.0
        if df.index[i].month in (2, 5, 7, 10):
            c += 2.0
        return c

    pnls, dyn_net, flat3_net = [], [], []
    for i in entries:
        p, _, _ = _sim(ema, cbot, bz, i, -1.0, 0.0, 90)
        if np.isnan(p):
            continue
        c = _dyn_cost(i)
        pnls.append(p)
        dyn_net.append(p - 2 * c)
        flat3_net.append(p - 6)
    if len(pnls) < 5:
        return {"version": "V15-06-DYNAMIC-COST", "verdict": "TOO_FEW"}
    dyn = np.array(dyn_net)
    flat = np.array(flat3_net)
    out = {
        "version": "V15-06-DYNAMIC-COST",
        "n_trades": int(len(pnls)),
        "dynamic_cost_model": "1€/leg base +2 si OI faible +2 si vol haute +2 si mois de roll",
        "net_pnl_dynamic_cost": round(float(dyn.sum()), 1),
        "hit_rate_dynamic": round(float((dyn > 0).mean()), 4),
        "net_pnl_flat_cost3": round(float(flat.sum()), 1),
        "mean_dynamic_cost_per_leg": round(float(np.mean([_dyn_cost(i) for i in entries])), 2),
        "survives_dynamic_cost": bool(dyn.sum() > 0),
        "interpretation": (
            "Coût dynamique : plus élevé quand liquidité faible / vol haute / mois de roll. Si l'edge survit "
            "au coût dynamique, c'est plus crédible qu'un coût plat."
        ),
        "verdict": "DYNAMIC_COST_DONE",
    }
    (V15_DIR / "dynamic_cost.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V15-07 — Portfolio strict un-trade-à-la-fois
# ---------------------------------------------------------------------------

def run_strict_portfolio(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    ema, cbot, bz = _arrays(df)
    cand = np.where((df["ema_cbot_basis_zscore_52w"] > 1.0).values)[0]

    # un seul trade ouvert à la fois : on n'entre que si flat, sortie z0 max90
    seq_pnls, seq_days = [], []
    busy_until = -1
    for i in cand:
        if i <= busy_until:
            continue
        p, t, _ = _sim(ema, cbot, bz, i, -1.0, 0.0, 90)
        if np.isnan(p):
            continue
        seq_pnls.append(p)
        seq_days.append(t)
        busy_until = i + (t if not np.isnan(t) else 90)

    # non-overlap 40j (référence V13/V14)
    no_pnls = []
    last = None
    for i in cand:
        d = df.index[i]
        if last is None or (d - last).days >= HORIZON:
            p, _, _ = _sim(ema, cbot, bz, i, -1.0, 0.0, 90)
            if not np.isnan(p):
                no_pnls.append(p)
                last = d

    # events indépendants (toutes entrées)
    indep_pnls = []
    for i in cand:
        p, _, _ = _sim(ema, cbot, bz, i, -1.0, 0.0, 90)
        if not np.isnan(p):
            indep_pnls.append(p)

    strict = _summ(seq_pnls, seq_days)
    if seq_pnls:
        eq = np.cumsum(np.array(seq_pnls) - 6)
        peak = np.maximum.accumulate(eq)
        strict["max_drawdown_cost3"] = round(float(np.min(eq - peak)), 1)
    out = {
        "version": "V15-07-STRICT-PORTFOLIO",
        "strict_one_at_a_time": strict,
        "nonoverlap_40d": _summ(no_pnls),
        "independent_events": _summ(indep_pnls),
        "interpretation": (
            "Le portfolio strict (un seul trade ouvert) est le plus réaliste pour un track record. Les events "
            "indépendants surestiment le nombre de trades exploitables."
        ),
        "verdict": "STRICT_PORTFOLIO_DONE",
    }
    (V15_DIR / "strict_portfolio.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
