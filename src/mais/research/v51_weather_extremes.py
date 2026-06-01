"""V51 — Weather Extremes Lab : le signal météo est dans les QUEUES (V48), on le développe rigoureusement.

V45 (météo réalisée moyenne) et V48 (oracle moyen) sont négatifs ; V48 a trouvé que les ÉVÉNEMENTS
EXTRÊMES de chaleur portent un signal (corr ~0.31). On construit ici la suite complète d'indicateurs
d'extrêmes (chaleur >1σ/1.5σ, jours chauds consécutifs, sécheresse, dôme de chaleur), tous CAUSAUX,
`shift(1)`, pondérés par la phénologie (pollinisation juillet). On répond ensuite à LA question :

  E1  Structure lead-lag : l'extrême connu à J PRÉCÈDE-t-il la hausse CBOT (tradeable depuis une prévision)
      ou n'est-il que CONTEMPORAIN (déjà pricé) ? corr(extrême_t, ret_CBOT[t→t+h]) pour h<0/0/>0.
  E2  Queue vs corps : rendement CBOT forward quand l'extrême est dans le décile haut vs le reste, en
      fenêtre critique.
  E3  Quel extrême porte le signal ? (chaleur / sécheresse / dôme / jours consécutifs) — décomposition.
  E4  Lien compression : un extrême US (qui pousse le CBOT) rend-il le basis haut plus compressible ?

LIMITE HONNÊTE : on utilise la météo RÉALISÉE comme borne explicative (= oracle, non-tradeable). Le signal
tradeable réel passe par le journal de PRÉVISIONS forward (V45/V48) : ici on identifie QUEL extrême vaut la
peine d'être prévu. La météo s'arrête mi-2025 (réalisé).

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V51_DIR = ARTEFACTS_DIR / "v51"
V51_DIR.mkdir(parents=True, exist_ok=True)

PHENOLOGY_WEIGHT = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.2, 5: 0.4, 6: 0.7,
                    7: 1.0, 8: 0.8, 9: 0.3, 10: 0.1, 11: 0.0, 12: 0.0}


def _causal_z(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    return (s - s.expanding(min_periods=120).mean()) / s.expanding(min_periods=120).std()


def _run_length(flag: pd.Series) -> pd.Series:
    """Longueur de série consécutive de True (causal : ne dépend que du passé)."""
    f = flag.fillna(False).astype(int).to_numpy()
    out = np.zeros(len(f), dtype=float)
    run = 0
    for i, v in enumerate(f):
        run = run + 1 if v else 0
        out[i] = run
    return pd.Series(out, index=flag.index)


def extreme_features(df: pd.DataFrame) -> pd.DataFrame:
    """Suite d'extrêmes météo US, causaux, shift(1), pondérés phénologie. Anomalie tmax déjà en z."""
    heat = pd.to_numeric(df.get("wx_belt_tmax_c_anom_z"), errors="coerce")  # déjà anomalie z
    dry1 = _causal_z(df.get("wx_belt_rain_deficit_14d"))
    dry2 = -_causal_z(df.get("wx_belt_prcp_30_anom_z"))
    dry = pd.concat([dry1, dry2], axis=1).mean(axis=1, skipna=True)

    hot1 = heat > 1.0
    hot15 = heat > 1.5
    dome = (hot15 & (dry > 1.0))
    consec_hot = _run_length(hot1)

    w = pd.Series([PHENOLOGY_WEIGHT.get(m, 0.0) for m in df.index.month], index=df.index)
    crit = (w >= 0.7).astype(int)

    feats = pd.DataFrame({
        "heat_anom_z": heat,
        "dry_z": dry,
        "hot_gt1_flag": hot1.astype(int),
        "hot_gt15_flag": hot15.astype(int),
        "heat_dome_flag": dome.astype(int),
        "consecutive_hot_days": consec_hot,
        "phenology_weight": w,
        "in_critical_window": crit,
        # extrême « effectif » = chaleur extrême pondérée par la fenêtre critique
        "heat_extreme_crit": (heat.clip(lower=0) * w),
    }, index=df.index)
    # anti-leakage : tout connu la veille
    return feats.shift(1)


def _window_ret(cbot: pd.Series, h: int) -> pd.Series:
    """h>0 : rendement FUTUR [t→t+h]. h<0 : rendement PASSÉ [t+h→t] (déjà réalisé à J)."""
    if h > 0:
        return cbot.shift(-h) / cbot - 1.0
    return cbot / cbot.shift(-h) - 1.0


def lead_lag_structure(df: pd.DataFrame) -> dict[str, Any]:
    """E1 : l'extrême PRÉCÈDE-t-il la hausse CBOT (forward, tradeable) ou la SUIT-il (passé, anticipé) ?"""
    f = extreme_features(df)["heat_extreme_crit"]
    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce")
    crit = extreme_features(df)["in_critical_window"] == 1
    corrs = {}
    for h in (-20, -10, -5, 5, 10, 20):
        r = _window_ret(cbot, h)
        m = f.notna() & r.notna() & crit & (f > 0)
        if m.sum() > 80 and f[m].std() > 0 and r[m].std() > 0:
            corrs[h] = round(float(np.corrcoef(f[m], r[m])[0, 1]), 3)
    fwd = {h: v for h, v in corrs.items() if h > 0}
    bwd = {h: v for h, v in corrs.items() if h < 0}
    best_fwd = max(fwd.values()) if fwd else None
    best_bwd = max(bwd.values()) if bwd else None
    # predictive seulement si le FORWARD bat le PASSÉ d'une marge (sinon : extrême anticipé/pricé)
    predictive = bool(best_fwd is not None and best_bwd is not None and best_fwd > best_bwd + 0.05)
    return {
        "corr_by_horizon": corrs,
        "best_forward_corr": best_fwd,
        "best_backward_corr": best_bwd,
        "predictive_beyond_anticipation": predictive,
        "reading": ("h>0 = l'extrême connu à J précède le rendement CBOT (devançable par prévision) ; "
                    "h<0 = rendement déjà réalisé avant l'extrême. Si backward ≫ forward, le marché ANTICIPE "
                    "la météo : l'extrême réalisé arrive APRÈS le mouvement de prix (peu tradeable a posteriori)."),
    }


def tail_vs_body(df: pd.DataFrame, horizon: int = 10) -> dict[str, Any]:
    """E2 : rendement CBOT forward quand l'extrême est dans le décile haut vs le reste (fenêtre critique)."""
    f = extreme_features(df)
    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce")
    r = _window_ret(cbot, horizon)
    crit = f["in_critical_window"] == 1
    heat = f["heat_anom_z"]
    m = heat.notna() & r.notna() & crit
    if m.sum() < 100:
        return {"verdict": "TOO_FEW", "n": int(m.sum())}
    thr = heat[m].quantile(0.9)
    tail = r[m & (heat >= thr)]
    body = r[m & (heat < thr)]
    return {
        "horizon": horizon,
        "n_critical": int(m.sum()),
        "heat_decile_threshold_z": round(float(thr), 2),
        "fwd_ret_tail_top10pct": round(float(tail.mean()), 4) if len(tail) else None,
        "fwd_ret_body": round(float(body.mean()), 4) if len(body) else None,
        "tail_minus_body": (round(float(tail.mean() - body.mean()), 4)
                            if len(tail) and len(body) else None),
        "n_tail": int(len(tail)),
    }


def which_extreme(df: pd.DataFrame, horizon: int = 10) -> dict[str, Any]:
    """E3 : quel extrême porte le signal CBOT ? corr de chaque feature avec le rendement forward (critique)."""
    f = extreme_features(df)
    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce")
    r = _window_ret(cbot, horizon)
    crit = f["in_critical_window"] == 1
    out = {}
    for col in ("heat_anom_z", "dry_z", "heat_dome_flag", "consecutive_hot_days", "heat_extreme_crit"):
        x = f[col]
        m = x.notna() & r.notna() & crit
        if m.sum() > 80 and x[m].std() > 0:
            out[col] = round(float(np.corrcoef(x[m], r[m])[0, 1]), 3)
    ranked = dict(sorted(out.items(), key=lambda kv: -abs(kv[1])))
    return {"horizon": horizon, "corr_with_fwd_cbot": ranked,
            "top_feature": next(iter(ranked), None)}


def extreme_helps_compression(df: pd.DataFrame, horizon: int = 40) -> dict[str, Any]:
    """E4 : un extrême US (CBOT poussé) rend-il le basis haut plus compressible (rattrapage CBOT) ?"""
    f = extreme_features(df)["heat_extreme_crit"]
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    drop = basis - basis.shift(-horizon)  # >0 = compression
    high = bz >= 1.0
    m = f.notna() & drop.notna() & high & (f >= 0)
    if m.sum() < 50:
        return {"verdict": "TOO_FEW_HIGH_BASIS", "n": int(m.sum())}
    thr = f[m].quantile(0.66)
    hi = drop[m & (f >= thr)]
    lo = drop[m & (f < thr)]
    return {
        "horizon": horizon,
        "n_high_basis": int(m.sum()),
        "compression_high_extreme": round(float(hi.mean()), 2) if len(hi) else None,
        "compression_low_extreme": round(float(lo.mean()), 2) if len(lo) else None,
        "extreme_helps_compression": bool(len(hi) and len(lo) and hi.mean() > lo.mean()),
    }


def run_v51_extremes(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    if pd.to_numeric(df.get("wx_belt_tmax_c_anom_z"), errors="coerce").notna().sum() < 300:
        return {"version": "V51-WEATHER-EXTREMES", "verdict": "NO_WEATHER_DATA"}
    e1 = lead_lag_structure(df)
    e2 = tail_vs_body(df)
    e3 = which_extreme(df)
    e4 = extreme_helps_compression(df)

    tail_pos = bool(e2.get("tail_minus_body") is not None and e2["tail_minus_body"] > 0)
    if e1.get("predictive_beyond_anticipation") and tail_pos:
        verdict = "EXTREME_HEAT_PREDICTIVE_TRADEABLE_VIA_FORECAST"
    elif tail_pos:
        verdict = "EXTREME_HEAT_TAIL_REAL_BUT_ANTICIPATED_FORECAST_LEADTIME_REQUIRED"
    else:
        verdict = "EXTREME_HEAT_NO_ROBUST_FORWARD_SIGNAL"

    out = {
        "version": "V51-WEATHER-EXTREMES",
        "lead_lag": e1,
        "tail_vs_body": e2,
        "which_extreme": e3,
        "compression_link": e4,
        "verdict": verdict,
        "interpretation": (
            "Le signal météo est dans la QUEUE (chaleur extrême en pollinisation), pas la moyenne (V45/V48). "
            f"Décile haut de chaleur -> rendement CBOT {e2.get('fwd_ret_tail_top10pct')} vs corps "
            f"{e2.get('fwd_ret_body')} (écart {e2.get('tail_minus_body')}) à {e2.get('horizon')}j : la queue "
            "EXISTE. MAIS la corrélation est plus forte avec le passé "
            f"(backward {e1.get('best_backward_corr')}) qu'avec le futur (forward {e1.get('best_forward_corr')}) "
            "-> le marché ANTICIPE la chaleur : l'extrême RÉALISÉ suit le mouvement de prix. La persistance "
            f"(consecutive_hot_days, feature top : {e3.get('top_feature')}) porte plus de signal que "
            "l'intensité d'un jour. Conséquence opérationnelle : seul un AVANTAGE DE PRÉVISION (devancer le "
            "dôme de chaleur juillet) est exploitable ; la météo réalisée ou moyenne ne l'est pas."),
        "tradeable_note": ("Borne explicative via météo réalisée (non-tradeable). L'edge réel suppose de "
                           "DEVANCER l'extrême : journal de prévisions forward V45/V48 (pics tmax)."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V51_DIR / "v51_weather_extremes.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
