"""V176 — Indicateur COMPOSITE de la prime EMA/CBOT : synthèse de toutes les découvertes.

La baseline reste INTOUCHÉE : l'entrée candidate est toujours z>1 (paliers 1/1.5/2, objectifs z→0.5/z→0).
V176 ajoute une COUCHE DE LECTURE règle-basée (aucun fit) qui combine les découvertes triangulées :

  intensity      0/1/2  paliers STRONG/EXTREME (V130 : demi-vie rétrécit avec l'extrême ; V173 : EXTREME
                        survit à 8 €/t/jambe)
  confirmed      0/1    z >= 1.2 (V131 : les marginaux z<1.2 sous-performent, 6.09 vs 14.14 €/t)
  cbot_support   0/1    momentum CBOT 60 j > 0 (V10-E : DA 0.69 en uptrend ; V39-E4 : ADVERSE ÷2 PnL ×2 ;
                        V173 : above_trend survit à 8 €/t)
  summer         0/1    juin-août (V167 : pic des départs, compression 1.45z ; V173 : survit à 8 €/t)
  subst_risk     0/-1   blé/maïs élevé (z>1) : substitution soutient la prime (V36/V41 corr +0.59,
                        wheat_corn_z meilleur flag ADVERSE 0.653) -> malus

  COMPOSITE_SCORE = intensity + confirmed + cbot_support + summer + subst_risk   (plage -1..5)

Protocole d'évaluation (anti-multiplicité V172, holdout 2024 exclu) :
  - VARIANTES PRÉ-DÉCLARÉES (8) = la famille d'essais ; CHAQUE variante compte comme un essai.
  - simulation identique V17 (1 trade à la fois, sortie z0 max 90 j, stop -20), coût primaire
    3 €/t/jambe + slippage 0.5 (V173) ;
  - critères d'éligibilité DÉCLARÉS AVANT lecture des résultats : mean_net>0, hit>=0.55,
    >=1.5 trades/an, >=6 mois distincts, mean_net hors-été>0 (exigence year-round) ;
  - recommandation = variante éligible au meilleur Sharpe/trade, PUIS déflation DSR
    (n_trials = famille et 50) + PBO (années × variantes). Pas de DSR>0.5 -> on le DIT.

RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.audit.overfitting import deflated_sharpe_ratio, pbo_cscv, sharpe_stats
from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout
from mais.research.v17_research_indicator import MAX_HOLD, STOP_LOSS, _sim_detail

V176_DIR = ARTEFACTS_DIR / "v176"
V176_DIR.mkdir(parents=True, exist_ok=True)

Z_COL = "ema_cbot_basis_zscore_52w"
COST_PER_LEG = 3.0
SLIPPAGE_PER_LEG = 0.5
ROUND_TRIP_COST = 2 * (COST_PER_LEG + SLIPPAGE_PER_LEG)
MIN_Z_PERIODS = 252
SUMMER_MONTHS = (6, 7, 8)

ELIGIBILITY = {"mean_net_min": 0.0, "hit_min": 0.55, "trades_per_year_min": 1.5,
               "month_coverage_min": 6, "offseason_mean_net_min": 0.0}


def _expanding_z(s: pd.Series, min_periods: int = MIN_Z_PERIODS) -> pd.Series:
    m = s.expanding(min_periods).mean().shift(1)
    sd = s.expanding(min_periods).std().shift(1)
    return (s - m) / sd


def composite_components(df: pd.DataFrame) -> pd.DataFrame:
    """Composantes causales du score (tout est connu au jour t ; aucune valeur future)."""
    out = pd.DataFrame(index=df.index)
    z = pd.to_numeric(df[Z_COL], errors="coerce")
    out["basis_z"] = z
    out["intensity"] = np.select([z >= 2.0, z >= 1.5], [2, 1], default=0)
    out["confirmed"] = (z >= 1.2).astype(int)
    cbot = pd.to_numeric(df["cbot_eur_t"], errors="coerce")
    out["cbot_support"] = (cbot.pct_change(60) > 0).astype(int)
    months = pd.Series(df.index.month, index=df.index)
    out["summer"] = months.isin(SUMMER_MONTHS).astype(int)
    if "corn_wheat_ratio" in df.columns:
        # corn/wheat bas = blé/maïs haut = substitution soutient la prime -> malus
        wheat_corn_z = -_expanding_z(pd.to_numeric(df["corn_wheat_ratio"], errors="coerce"))
        out["subst_risk"] = np.where(wheat_corn_z > 1.0, -1, 0)
    else:
        out["subst_risk"] = 0
    out["composite_score"] = (out["intensity"] + out["confirmed"] + out["cbot_support"]
                              + out["summer"] + out["subst_risk"])
    return out


# Famille d'essais PRÉ-DÉCLARÉE : chaque entrée = un essai pour la déflation DSR.
VARIANTS: dict[str, dict[str, Any]] = {
    "baseline_all_z1": {"desc": "référence : tous les signaux z>1, sans filtre composite"},
    "confirmed_z12": {"filter": lambda c: c["confirmed"] == 1, "desc": "V131 seul : z>=1.2"},
    "support_and_confirmed": {"filter": lambda c: (c["confirmed"] == 1) & (c["cbot_support"] == 1),
                              "desc": "confirmation + support CBOT"},
    "score_ge1": {"filter": lambda c: c["composite_score"] >= 1, "desc": "score complet >=1"},
    "score_ge2": {"filter": lambda c: c["composite_score"] >= 2, "desc": "score complet >=2"},
    "score_ge3": {"filter": lambda c: c["composite_score"] >= 3, "desc": "score complet >=3"},
    "score_noseason_ge2": {"filter": lambda c: (c["composite_score"] - c["summer"]) >= 2,
                           "desc": "score SANS la composante été >=2 (design year-round)"},
    "extreme_only": {"filter": lambda c: c["intensity"] == 2, "desc": "z>=2 seul"},
}


def _simulate_variant(df: pd.DataFrame, comp: pd.DataFrame, flt) -> pd.DataFrame:
    ema = pd.to_numeric(df["ema_close"], errors="coerce").to_numpy()
    cbot = pd.to_numeric(df["cbot_eur_t"], errors="coerce").to_numpy()
    bz = comp["basis_z"].to_numpy()
    ok = pd.Series(True, index=df.index) if flt is None else flt(comp).fillna(False)
    dates = df.index
    rows, busy_until = [], -1
    for i in np.where((bz > 1.0) & ok.to_numpy())[0]:
        if i <= busy_until:
            continue
        res = _sim_detail(ema, cbot, bz, i, 0.0, MAX_HOLD, stop_loss=STOP_LOSS)
        if res is None:
            continue
        rows.append({"entry_date": dates[i], "year": int(dates[i].year),
                     "month": int(dates[i].month),
                     "score": int(comp["composite_score"].iloc[i]),
                     "gross": float(res["pnl"]), "net": float(res["pnl"]) - ROUND_TRIP_COST,
                     "days": int(res["days"])})
        busy_until = res["exit_pos"]
    return pd.DataFrame(rows)


def _variant_metrics(tr: pd.DataFrame, n_years_span: float) -> dict[str, Any]:
    if tr.empty:
        return {"n_trades": 0}
    off = tr[~tr["month"].isin(SUMMER_MONTHS)]
    st = sharpe_stats(tr["net"].to_numpy())
    return {
        "n_trades": int(len(tr)),
        "trades_per_year": round(len(tr) / n_years_span, 2),
        "pct_years_with_trade": round(tr["year"].nunique() / n_years_span, 3),
        "month_coverage": int(tr["month"].nunique()),
        "hit_rate_net": round(float((tr["net"] > 0).mean()), 3),
        "mean_net": round(float(tr["net"].mean()), 2),
        "total_net": round(float(tr["net"].sum()), 1),
        "sharpe_per_trade": round(st["sharpe"], 4),
        "median_days": float(tr["days"].median()),
        "offseason": {"n": int(len(off)),
                      "mean_net": round(float(off["net"].mean()), 2) if len(off) else None,
                      "hit": round(float((off["net"] > 0).mean()), 3) if len(off) else None},
        "by_month_counts": tr["month"].value_counts().sort_index().to_dict(),
    }


def _eligible(m: dict[str, Any]) -> bool:
    if m.get("n_trades", 0) == 0:
        return False
    off = m["offseason"]
    return (m["mean_net"] > ELIGIBILITY["mean_net_min"]
            and m["hit_rate_net"] >= ELIGIBILITY["hit_min"]
            and m["trades_per_year"] >= ELIGIBILITY["trades_per_year_min"]
            and m["month_coverage"] >= ELIGIBILITY["month_coverage_min"]
            and off["n"] > 0 and off["mean_net"] is not None
            and off["mean_net"] > ELIGIBILITY["offseason_mean_net_min"])


def run_v176_composite(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    df = df[pd.to_numeric(df[Z_COL], errors="coerce").notna()]
    comp = composite_components(df)
    n_years_span = max((df.index.max() - df.index.min()).days / 365.25, 1.0)

    all_trades: dict[str, pd.DataFrame] = {}
    metrics: dict[str, Any] = {}
    for name, spec in VARIANTS.items():
        tr = _simulate_variant(df, comp, spec.get("filter"))
        all_trades[name] = tr
        metrics[name] = {"desc": spec["desc"], **_variant_metrics(tr, n_years_span)}

    eligible = [n for n, m in metrics.items() if _eligible(m)]
    recommended = (max(eligible, key=lambda n: metrics[n]["sharpe_per_trade"])
                   if eligible else None)

    honesty: dict[str, Any] = {"n_trials_family": len(VARIANTS)}
    trial_sharpes = np.array([m.get("sharpe_per_trade", 0.0) for m in metrics.values()
                              if m.get("n_trades", 0) >= 5])
    if recommended and metrics[recommended]["n_trades"] >= 10:
        rets = all_trades[recommended]["net"].to_numpy()
        honesty["dsr_family"] = deflated_sharpe_ratio(rets, n_trials=len(VARIANTS),
                                                      trial_sharpes=trial_sharpes)
        honesty["dsr_50_trials"] = deflated_sharpe_ratio(rets, n_trials=50,
                                                         trial_sharpes=trial_sharpes)
    years = sorted({y for tr in all_trades.values() for y in tr.get("year", pd.Series([]))})
    if len(years) >= 10:
        mat = np.array([[all_trades[n][all_trades[n]["year"] == y]["net"].sum()
                         for n in VARIANTS] for y in years])
        honesty["pbo_years_x_variants"] = pbo_cscv(mat, n_splits=10)

    out = {
        "version": "V176-COMPOSITE",
        "verdict": ("COMPOSITE_RECOMMENDED_" + recommended.upper()) if recommended
        else "NO_VARIANT_MEETS_CRITERIA",
        "baseline_untouched": True,
        "cost_assumption": f"{COST_PER_LEG} €/t/jambe + {SLIPPAGE_PER_LEG} slippage (aller-retour "
                           f"{ROUND_TRIP_COST})",
        "eligibility_criteria_pre_declared": ELIGIBILITY,
        "eligible_variants": eligible,
        "recommended_variant": recommended,
        "variants": metrics,
        "honesty_pack": honesty,
        "guardrails": [
            "entrée candidate = baseline z>1 inchangée ; le composite ne fait que stratifier",
            "8 variantes pré-déclarées = 8 essais comptés dans la déflation DSR",
            "holdout 2024 exclu ; z proxy_implied -> revalidation forward officielle requise",
            "couverture annuelle mesurée (month_coverage, offseason) : exigence year-round dans "
            "l'éligibilité",
        ],
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V176_DIR / "v176_composite_results.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8")
    for name, tr in all_trades.items():
        if not tr.empty:
            tr.assign(entry_date=tr["entry_date"].astype(str)).to_json(
                V176_DIR / f"v176_trades_{name}.json", orient="records", indent=1)
    return out


# ---------------------------------------------------------------------------
# Lecture LIVE quotidienne (briques V151/V107 ; le head n'est PAS modifié)
# ---------------------------------------------------------------------------

def _read_artifact(rel: str) -> dict[str, Any]:
    try:
        return json.loads((ARTEFACTS_DIR / rel).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def run_v176_live() -> dict[str, Any]:
    """Score composite du jour à partir des briques live. Contexte descriptif, jamais un signal neuf."""
    head = {}
    try:
        from mais.paths import DATA_DIR
        head = json.loads((DATA_DIR / "premium" / "premium_daily_head.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    z = head.get("basis_z")
    if z is None:
        return {"version": "V176-LIVE", "verdict": "NO_LIVE_STATE",
                "status": "RESEARCH_ONLY_NOT_TRADING"}
    z = float(z)
    ctx = _read_artifact("v107/v107_context_refresh.json")
    comp_ctx = ctx.get("cbot_support_components") or {}
    from datetime import date
    month = int(str(head.get("as_of", date.today())).split("-")[1])

    components = {
        "intensity": 2 if z >= 2.0 else (1 if z >= 1.5 else 0),
        "confirmed": int(z >= 1.2),
        "cbot_support": int(bool(comp_ctx.get("uptrend_sma50") or comp_ctx.get("momentum20_pos"))),
        "summer": int(month in SUMMER_MONTHS),
        "subst_risk": -1 if comp_ctx.get("corn_cheap_vs_wheat") else 0,
    }
    score = sum(components.values())
    backtest = _read_artifact("v176/v176_composite_results.json")
    rec = backtest.get("recommended_variant")
    rec_metrics = (backtest.get("variants") or {}).get(rec, {}) if rec else {}
    out = {
        "version": "V176-LIVE",
        "verdict": "COMPOSITE_LIVE_BUILT",
        "as_of": head.get("as_of"),
        "basis_z": z,
        "in_baseline_signal": z > 1.0,
        "components": components,
        "composite_score": score,
        "qualified_confirmed_z12": z >= 1.2,
        "reading": (
            f"z {z} ({'signal baseline' if z > 1.0 else 'hors signal'}), score composite {score}/5. "
            + (f"Qualifié '{rec}' (backtest 2010-25 : hit {rec_metrics.get('hit_rate_net')}, "
               f"net {rec_metrics.get('mean_net')} €/t à coût 3+0.5, {rec_metrics.get('month_coverage')} "
               f"mois couverts). " if rec and z >= 1.2 else "")
            + "Contexte DESCRIPTIF (stratification de qualité), jamais un veto ni un nouveau seuil."),
        "context_freshness": ctx.get("fresh_within_gate"),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V176_DIR / "v176_live.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
