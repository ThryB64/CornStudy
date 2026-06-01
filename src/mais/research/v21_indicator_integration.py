"""V21-IND — Intégration finale : contexte CBOT + décomposition du chemin de compression.

On relie les découvertes CBOT (V19) à l'indicateur de prime (V17) SANS changer la règle basis :
- decompose_compression_path : un short premium gagne si EMA baisse OU si CBOT monte plus vite. On mesure,
  sur les trades short basis-haut, COMMENT la compression s'est produite (jambe EMA vs jambe CBOT).
- compute_cbot_context : labels causaux de contexte CBOT (drawdown risk / tendance / biais météo) au jour J.
- compute_integrated_indicator : signal de prime (V17) + contexte CBOT, avec chemin probable.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Règle basis inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout
from mais.research.data_freshness import compute_freshness
from mais.research.v17_research_indicator import compute_indicator_v17
from mais.research.v18_weather_deep import weather_stress_index

V21_DIR = ARTEFACTS_DIR / "v21"
V21_DIR.mkdir(parents=True, exist_ok=True)

HORIZON = 40
MAX_HOLD = 90


# ---------------------------------------------------------------------------
# V21-IND-02 — Décomposition du chemin de compression
# ---------------------------------------------------------------------------

def decompose_compression_path(df: pd.DataFrame) -> dict[str, Any]:
    """Pour chaque trade short basis-haut, décompose le PnL en jambe EMA (short) et jambe CBOT (long).

    short premium = short EMA + long CBOT.
      ema_leg  = -(ema_exit/ema_entry - 1)   (positif si EMA baisse)
      cbot_leg = +(cbot_exit/cbot_entry - 1) (positif si CBOT monte)
    Chemin : EMA_DRIVEN / CBOT_DRIVEN / BOTH / ADVERSE.
    """
    assert_no_holdout(df)
    if "ema_close" not in df.columns or "cbot_eur_t" not in df.columns:
        return {"version": "V21-IND-02", "verdict": "MISSING_DATA"}
    ema = df["ema_close"].values
    cbot = df["cbot_eur_t"].values
    bz = df["ema_cbot_basis_zscore_52w"].values
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
            if bz[j] * sgn <= 0:
                exit_j = j
                break
            exit_j = j
        if exit_j is None or np.isnan(ema[exit_j]) or np.isnan(cbot[exit_j]):
            continue
        ema_ret = ema[exit_j] / ema[i] - 1
        cbot_ret = cbot[exit_j] / cbot[i] - 1
        ema_leg = -ema_ret  # short EMA
        cbot_leg = cbot_ret  # long CBOT
        total = ema_leg + cbot_leg
        if total <= 0:
            path = "ADVERSE"
        elif ema_leg > 0 and cbot_leg > 0:
            path = "BOTH"
        elif ema_leg >= cbot_leg:
            path = "EMA_DRIVEN"
        else:
            path = "CBOT_DRIVEN"
        rows.append({"entry_z": float(bz[i]), "ema_leg": ema_leg, "cbot_leg": cbot_leg,
                     "total": total, "path": path, "win": int(total > 0)})
    if not rows:
        return {"version": "V21-IND-02", "verdict": "NO_TRADES"}
    rdf = pd.DataFrame(rows)
    dist = rdf["path"].value_counts().to_dict()
    winners = rdf[rdf["win"] == 1]
    out = {
        "version": "V21-IND-02",
        "n_trades": int(len(rdf)),
        "path_distribution": {k: int(v) for k, v in dist.items()},
        "winners_path_distribution": {k: int(v) for k, v in winners["path"].value_counts().items()},
        "mean_ema_leg": round(float(rdf["ema_leg"].mean()), 4),
        "mean_cbot_leg": round(float(rdf["cbot_leg"].mean()), 4),
        "share_compression_via_cbot_up": round(float((rdf["path"] == "CBOT_DRIVEN").mean()), 4),
        "share_compression_via_ema_down": round(float((rdf["path"] == "EMA_DRIVEN").mean()), 4),
        "share_both": round(float((rdf["path"] == "BOTH").mean()), 4),
        "interpretation": (
            "Un short premium gagne si EMA baisse (ema_leg>0) ou si CBOT monte (cbot_leg>0). La répartition "
            "des chemins dit si la compression vient surtout d'une baisse EMA, d'une hausse CBOT, ou des deux."
        ),
        "verdict": "COMPRESSION_PATH_DECOMPOSED",
    }
    (V21_DIR / "compression_path.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V21-IND-01 — Contexte CBOT (labels causaux, observables au jour J)
# ---------------------------------------------------------------------------

def compute_cbot_context(df: pd.DataFrame) -> pd.DataFrame:
    """Labels de contexte CBOT par date (causaux) : tendance, vol, biais météo, risque drawdown."""
    idx = df.index
    trend = df.get("curve_backwardation_proxy", pd.Series(np.nan, index=idx))  # prix vs SMA252 (proxy tendance)
    vol = df.get("corn_realized_vol_20", pd.Series(np.nan, index=idx))
    vol_p80 = vol.quantile(0.80)
    stress = weather_stress_index(df)

    rows = []
    for i, d in enumerate(idx):
        tr = trend.iloc[i]
        v = vol.iloc[i]
        st = stress.iloc[i]
        below_trend = (not pd.isna(tr)) and tr < 0
        high_vol = (not pd.isna(v)) and v > vol_p80
        weather_bull = (not pd.isna(st)) and st > 0.5
        # risque de drawdown plus élevé en below_trend + high_vol (cf. V19 : drawdown prévisible)
        if below_trend and high_vol:
            dd_risk = "high"
        elif below_trend or high_vol:
            dd_risk = "medium"
        else:
            dd_risk = "low"
        ctx = "CBOT_NEUTRAL"
        if weather_bull:
            ctx = "CBOT_BULLISH_WEATHER"
        elif below_trend and high_vol:
            ctx = "CBOT_RISK_OFF"
        elif not below_trend:
            ctx = "CBOT_UPTREND"
        rows.append((d, ctx, dd_risk,
                     "above" if (not pd.isna(tr) and tr >= 0) else "below" if not pd.isna(tr) else "unknown",
                     "high" if high_vol else "normal",
                     round(float(st), 3) if not pd.isna(st) else np.nan))
    out = pd.DataFrame(rows, columns=["date", "cbot_context", "drawdown_risk", "cbot_trend",
                                      "vol_regime", "weather_stress"]).set_index("date")
    return out


# ---------------------------------------------------------------------------
# V21-IND-04 — Indicateur intégré (prime + contexte CBOT)
# ---------------------------------------------------------------------------

def compute_integrated_indicator(df: pd.DataFrame) -> pd.DataFrame:
    """Fusionne le signal de prime (V17) et le contexte CBOT (V21). Règle basis inchangée."""
    premium = compute_indicator_v17(df)
    # V17 expose déjà un 'cbot_context' (label de tendance simple) ; on garde la version riche V21.
    premium = premium.drop(columns=["cbot_context"], errors="ignore")
    context = compute_cbot_context(df)
    out = premium.join(context[["cbot_context", "drawdown_risk", "cbot_trend", "weather_stress"]], how="left")
    # chemin probable de compression : si CBOT bullish weather -> compression possible par hausse CBOT
    def _path_hint(row):
        if row["signal"] in ("NO_SIGNAL",) or str(row["signal"]).startswith("UNCERTAIN"):
            return ""
        if row.get("cbot_context") == "CBOT_BULLISH_WEATHER":
            return "compression_possible_via_CBOT_up (gain même si EMA ne baisse pas)"
        if row.get("cbot_context") == "CBOT_RISK_OFF":
            return "compression_possible_via_EMA_down (risk-off)"
        return "compression_mixte"
    out["compression_path_hint"] = out.apply(_path_hint, axis=1)
    return out


def run_integrated_indicator(df: pd.DataFrame) -> dict[str, Any]:
    """Construit l'indicateur intégré, décompose les chemins, écrit l'artefact + snapshot récent."""
    assert_no_holdout(df)
    path = decompose_compression_path(df)
    ind = compute_integrated_indicator(df)
    freshness = compute_freshness(df)
    actionable = ind[~ind["signal"].isin(["NO_SIGNAL"])]
    snapshot = None
    if len(actionable):
        last = actionable.iloc[-1]
        raw_signal = last["signal"]
        # GATE DE FRAÎCHEUR : si les données sont périmées, on n'émet PAS de signal.
        gated_signal = raw_signal if freshness["signal_allowed"] else "UNCERTAIN_DATA_STALE"
        snapshot = {
            "date": str(actionable.index[-1].date()),
            "premium_signal": gated_signal,
            "raw_signal_before_freshness_gate": raw_signal,
            "freshness_verdict": freshness["freshness_verdict"],
            "staleness_days": freshness["staleness_days"],
            "basis_z": round(float(last["basis_z"]), 3) if not pd.isna(last["basis_z"]) else None,
            "cbot_context": last.get("cbot_context"),
            "drawdown_risk": last.get("drawdown_risk"),
            "compression_path_hint": last.get("compression_path_hint") if freshness["signal_allowed"] else "",
            "objective_prudent": last.get("objective_prudent"),
            "objective_full": last.get("objective_full"),
        }
    out = {
        "version": "V21-IND-INTEGRATED",
        "freshness": freshness,
        "compression_path": {k: path.get(k) for k in
                             ["path_distribution", "share_compression_via_cbot_up",
                              "share_compression_via_ema_down", "share_both", "mean_ema_leg", "mean_cbot_leg"]},
        "context_distribution": ind["cbot_context"].value_counts().to_dict(),
        "latest_integrated_snapshot": snapshot,
        "note": "Contexte CBOT = information à côté du signal de prime. La règle basis (short basis-haut) reste inchangée. Gate de fraîcheur appliqué au signal live.",
        "verdict": "INTEGRATED_INDICATOR_DONE",
    }
    (V21_DIR / "integrated_indicator.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
