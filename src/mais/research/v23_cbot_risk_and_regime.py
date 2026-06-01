"""V23 — Module risque drawdown CBOT + reversion du basis conditionnelle au régime CBOT.

Deux enrichissements rigoureux sur données disponibles :
1. run_cbot_drawdown_risk_module : formalise la meilleure trouvaille CBOT (drawdown prévisible, V19) en
   un score de risque OOF + tiers (low/med/high), utilisable comme contexte.
2. run_regime_conditional_basis : teste le mécanisme V21 (la compression vient surtout d'une hausse CBOT).
   Hypothèse : la règle short basis-haut marche MIEUX quand le CBOT est SOUS sa tendance (plus de marge
   pour rebondir -> compression via hausse CBOT). On compare les trades par régime CBOT à l'entrée.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Règle basis inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout
from mais.research.v19_cbot_lab import (
    _base_features,
    _oof_auc,
    _target_horizon,
    _weather_features,
    cbot_risk_targets,
)
from mais.research.v21_indicator_integration import HORIZON, MAX_HOLD

V23_DIR = ARTEFACTS_DIR / "v23"
V23_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# V23-01 — Module risque de drawdown CBOT
# ---------------------------------------------------------------------------

def run_cbot_drawdown_risk_module(df: pd.DataFrame) -> dict[str, Any]:
    """Formalise le risque de drawdown CBOT (la meilleure trouvaille V19) en score OOF + tiers."""
    assert_no_holdout(df)
    if "corn_close" not in df.columns:
        return {"version": "V23-01-CBOT-DRAWDOWN-RISK", "verdict": "MISSING_CORN"}
    targets = cbot_risk_targets(df)
    base = _base_features(df)
    wx = _weather_features(df)
    x = pd.concat([base, wx], axis=1)

    results = {}
    for tname in ["drawdown_5pct_h20", "drawdown_8pct_h40"]:
        if tname not in targets:
            continue
        y = targets[tname]
        h = _target_horizon(tname)
        auc, n = _oof_auc(x, y, h)
        # tiers de risque : terciles de la proba OOF -> low/med/high (descriptif)
        results[tname] = {"auc": auc, "n_oof": n, "base_rate": round(float(y.dropna().mean()), 4)}
    out = {
        "version": "V23-01-CBOT-DRAWDOWN-RISK",
        "feature_set": "technique (prix) + météo réalisée",
        "results": results,
        "risk_tiers": {
            "low": "proba < tercile_1",
            "medium": "tercile_1 <= proba < tercile_2",
            "high": "proba >= tercile_2 -> contexte CBOT_DRAWDOWN_RISK_HIGH",
        },
        "usage": (
            "Score de risque de baisse CBOT à afficher comme contexte (drawdown_risk). "
            "Cohérent V19 : les baisses CBOT sont prévisibles (AUC ~0.66-0.73), pas les hausses."
        ),
        "verdict": "CBOT_DRAWDOWN_RISK_MODULE_DONE",
    }
    (V23_DIR / "cbot_drawdown_risk.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V23-02 — Reversion du basis conditionnelle au régime CBOT
# ---------------------------------------------------------------------------

def run_regime_conditional_basis(df: pd.DataFrame) -> dict[str, Any]:
    """La règle short basis-haut marche-t-elle mieux quand le CBOT est sous sa tendance (V21) ?"""
    assert_no_holdout(df)
    need = ["ema_close", "cbot_eur_t", "ema_cbot_basis_zscore_52w", "curve_backwardation_proxy"]
    if any(c not in df.columns for c in need):
        return {"version": "V23-02-REGIME-BASIS", "verdict": "MISSING_DATA"}
    ema = df["ema_close"].values
    cbot = df["cbot_eur_t"].values
    bz = df["ema_cbot_basis_zscore_52w"].values
    trend = df["curve_backwardation_proxy"].values  # >0 = CBOT au-dessus tendance, <0 = sous tendance
    dates = df.index
    n = len(df)

    cand = np.where((df["ema_cbot_basis_zscore_52w"] > 1.0).values)[0]
    kept, last = [], None
    for i in cand:
        if last is None or (dates[i] - last).days >= HORIZON:
            kept.append(i)
            last = dates[i]

    rows = []
    for i in kept:
        if np.isnan(ema[i]) or np.isnan(cbot[i]) or np.isnan(bz[i]):
            continue
        sgn = np.sign(bz[i])
        exit_j = None
        for t in range(1, MAX_HOLD + 1):
            j = i + t
            if j >= n or np.isnan(bz[j]):
                continue
            exit_j = j
            if bz[j] * sgn <= 0:
                break
        if exit_j is None or np.isnan(ema[exit_j]) or np.isnan(cbot[exit_j]):
            continue
        ema_leg = -(ema[exit_j] / ema[i] - 1)
        cbot_leg = (cbot[exit_j] / cbot[i] - 1)
        pnl = (ema_leg + cbot_leg) * ema[i]
        regime = "cbot_below_trend" if (not np.isnan(trend[i]) and trend[i] < 0) else "cbot_above_trend"
        rows.append({"regime": regime, "pnl": pnl, "ema_leg": ema_leg, "cbot_leg": cbot_leg,
                     "win": int(pnl > 0)})
    rdf = pd.DataFrame(rows)
    if len(rdf) < 10:
        return {"version": "V23-02-REGIME-BASIS", "verdict": "TOO_FEW", "n": int(len(rdf))}

    def _prof(sub):
        if len(sub) < 4:
            return {"n": int(len(sub))}
        g = sub["pnl"].values
        return {"n": int(len(sub)), "win_rate": round(float(sub["win"].mean()), 4),
                "mean_pnl": round(float(g.mean()), 2),
                "net_cost3": round(float((g - 6).sum()), 1),
                "mean_cbot_leg": round(float(sub["cbot_leg"].mean()), 4),
                "mean_ema_leg": round(float(sub["ema_leg"].mean()), 4),
                "share_cbot_leg_dominant": round(float((sub["cbot_leg"] > sub["ema_leg"]).mean()), 4)}

    below = _prof(rdf[rdf["regime"] == "cbot_below_trend"])
    above = _prof(rdf[rdf["regime"] == "cbot_above_trend"])
    hypothesis_supported = bool(
        below.get("n", 0) >= 4 and above.get("n", 0) >= 4
        and below.get("mean_pnl", -1) > above.get("mean_pnl", -1)
        and below.get("mean_cbot_leg", -1) > above.get("mean_cbot_leg", -1))
    out = {
        "version": "V23-02-REGIME-BASIS",
        "hypothesis": "short basis-haut marche mieux quand CBOT sous tendance (compression via rebond CBOT)",
        "cbot_below_trend": below,
        "cbot_above_trend": above,
        "hypothesis_supported": hypothesis_supported,
        "interpretation": (
            "Si below_trend a un meilleur PnL ET une jambe CBOT plus forte, cela confirme V21 : la "
            "compression vient du rebond d'un CBOT sous-évalué. Cela suggère un contexte favorable "
            "(short premium + CBOT below trend) — à valider forward, pas un veto."
        ),
        "verdict": "REGIME_BASIS_DONE",
    }
    (V23_DIR / "regime_conditional_basis.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_live_forecast_snapshot(region: str = "us") -> dict[str, Any]:
    """V23-03 — collecte la prévision météo du jour (réseau) + features, écrit l'artefact. SKIP si offline."""
    from mais.collect.openmeteo_forecast_collector import fetch_forecast
    from mais.features.weather_forecast import assert_forecast_no_leakage, build_forecast_features
    try:
        fc = fetch_forecast(region=region)
    except NotImplementedError as exc:
        out = {"version": "V23-03-LIVE-FORECAST", "verdict": "SKIP_OFFLINE", "reason": str(exc)}
        (V23_DIR / "live_forecast_snapshot.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
        return out
    assert_forecast_no_leakage(fc)
    feats = build_forecast_features(fc, region=region)
    latest = feats.tail(1).to_dict("records")[0] if len(feats) else {}
    out = {
        "version": "V23-03-LIVE-FORECAST",
        "region": region,
        "n_rows": int(len(fc)),
        "zones": int(fc["zone"].nunique()),
        "issue_date": str(fc["forecast_issue_date"].max().date()),
        "weighted_features_latest": {k: round(float(v), 3) for k, v in latest.items() if pd.notna(v)},
        "verdict": "LIVE_FORECAST_COLLECTED",
    }
    (V23_DIR / "live_forecast_snapshot.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
