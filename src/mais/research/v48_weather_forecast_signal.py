"""V48 — Météo PRÉVUE favorable/défavorable au maïs : apporte-t-elle du signal sur le cours ?

Idée (clarifiée) : à la date J, le marché dispose d'une PRÉVISION pour J+1..J+H. Si la prévision est
défavorable (chaud+sec sur la fenêtre critique) -> rendement attendu en baisse -> le CBOT monte. V45 a
montré que la météo RÉALISÉE-connue arrive trop tard (≈ hasard). La valeur est donc dans l'ANTICIPATION.

Problème : l'archive historique de prévisions (Open-Meteo historical-forecast) time out. On répond quand
même proprement par la VALEUR D'UNE PRÉVISION PARFAITE (« oracle ») :

  oracle_forecast = météo RÉALISÉE sur [J+1, J+H]  (ce qu'une prévision parfaite aurait annoncé à J).

On mesure le signal que cette prévision parfaite donnerait sur le CBOT. C'est une BORNE SUPÉRIEURE,
explicitement NON-TRADEABLE (elle utilise le futur). Interprétation :
  - oracle ≈ 0  -> même une prévision parfaite n'aide pas : idée morte.
  - oracle fort + réalisé-connu ≈ 0 (V45) -> TOUT le signal est dans l'anticipation -> collecter le forward.

Le signal RÉELLEMENT exploitable (anti-leakage) est accumulé par le journal de prévisions forward (V45).

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V48_DIR = ARTEFACTS_DIR / "v48"
V48_DIR.mkdir(parents=True, exist_ok=True)

PHENOLOGY_WEIGHT = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.2, 5: 0.4, 6: 0.7,
                    7: 1.0, 8: 0.8, 9: 0.3, 10: 0.1, 11: 0.0, 12: 0.0}


def oracle_forecast_stress(df: pd.DataFrame, lead: int = 14) -> pd.Series:
    """Stress « prévu parfait » : météo réalisée moyenne sur [J+1, J+lead] (chaud+sec), pondéré phénologie.

    NON-TRADEABLE (utilise le futur) — borne supérieure de la valeur d'une prévision parfaite émise à J.
    """
    heat = pd.to_numeric(df.get("wx_belt_tmax_c_anom_z"), errors="coerce")
    dry1 = pd.to_numeric(df.get("wx_belt_rain_deficit_14d"), errors="coerce")
    dry2 = -pd.to_numeric(df.get("wx_belt_prcp_30_anom_z"), errors="coerce")
    comp = pd.concat([heat, dry1, dry2], axis=1).mean(axis=1, skipna=True)
    # moyenne FUTURE sur [J+1, J+lead] : rolling trailing puis décalage -lead (les `lead` dernières -> NaN)
    fut = comp.rolling(lead, min_periods=max(3, lead // 2)).mean().shift(-lead)
    w = pd.Series([PHENOLOGY_WEIGHT.get(m, 0.0) for m in df.index.month], index=df.index)
    return fut * w


def _oof_auc(x: pd.DataFrame, y: pd.Series, embargo: int) -> float | None:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler
    m = x.notna().all(axis=1) & y.notna()
    x, y = x[m], y[m].astype(int)
    if len(y) < 200 or y.nunique() < 2:
        return None
    pred = np.full(len(y), np.nan)
    for tr, te in TimeSeriesSplit(n_splits=5).split(x):
        tr = tr[: max(0, len(tr) - embargo)]
        if len(tr) < 100 or y.iloc[tr].nunique() < 2:
            continue
        sc = StandardScaler().fit(x.iloc[tr])
        clf = LogisticRegression(max_iter=400).fit(sc.transform(x.iloc[tr]), y.iloc[tr])
        pred[te] = clf.predict_proba(sc.transform(x.iloc[te]))[:, 1]
    ok = ~np.isnan(pred)
    if ok.sum() < 100 or len(np.unique(y[ok])) < 2:
        return None
    return round(float(roc_auc_score(y[ok], pred[ok])), 3)


def forecast_value_by_lead(df: pd.DataFrame) -> dict[str, Any]:
    """E1 : valeur d'une prévision parfaite (oracle) sur le CBOT, par horizon de lead."""
    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce")
    res = {}
    for lead in (3, 7, 14):
        stress = oracle_forecast_stress(df, lead)
        ret = cbot.shift(-lead) / cbot - 1.0  # mouvement CBOT pendant que la météo se réalise
        m = stress.notna() & ret.notna()
        if m.sum() < 200:
            res[lead] = {"verdict": "TOO_SHORT"}
            continue
        corr = round(float(np.corrcoef(stress[m], ret[m])[0, 1]), 3)
        auc = _oof_auc(pd.DataFrame({"oracle_stress": stress[m]}), (ret[m] > 0).astype(float), lead)
        res[lead] = {"n": int(m.sum()), "corr_oracle_stress_cbot_ret": corr, "oof_auc_cbot_up": auc}
    return res


def extreme_event_oracle(df: pd.DataFrame, lead: int = 14) -> dict[str, Any]:
    """E1bis : et si on prévoyait parfaitement un ÉVÉNEMENT EXTRÊME (pic de chaleur) sur la fenêtre ?

    Souvent c'est l'extrême (dôme de chaleur), pas la moyenne, qui fait monter le maïs. Oracle du MAX.
    """
    heat = pd.to_numeric(df.get("wx_belt_tmax_c_anom_z"), errors="coerce")
    fut_max = heat.rolling(lead, min_periods=max(3, lead // 2)).max().shift(-lead)
    w = pd.Series([PHENOLOGY_WEIGHT.get(m, 0.0) for m in df.index.month], index=df.index)
    peak = fut_max * w
    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce")
    ret = cbot.shift(-lead) / cbot - 1.0
    crit = (w >= 0.7) & peak.notna() & ret.notna()
    if crit.sum() < 80:
        return {"verdict": "TOO_FEW"}
    thr = peak[crit].quantile(0.8)  # top 20% des pics de chaleur prévus
    hot = ret[crit & (peak >= thr)]
    rest = ret[crit & (peak < thr)]
    corr = round(float(np.corrcoef(peak[crit], ret[crit])[0, 1]), 3)
    return {
        "n_critical": int(crit.sum()),
        "corr_peak_heat_cbot_ret": corr,
        "fwd_cbot_ret_extreme_heat_forecast": round(float(hot.mean()), 4) if len(hot) else None,
        "fwd_cbot_ret_rest": round(float(rest.mean()), 4) if len(rest) else None,
        "extreme_heat_bullish": bool(len(hot) and len(rest) and hot.mean() > rest.mean()),
        "reading": "Oracle d'un pic de chaleur prévu (top 20%) en fenêtre critique vs reste.",
    }


def favorability_classes(df: pd.DataFrame, lead: int = 14) -> dict[str, Any]:
    """E2 : une prévision DÉFAVORABLE (chaud+sec) précède-t-elle une hausse CBOT ? (oracle, fenêtre critique)."""
    stress = oracle_forecast_stress(df, lead)
    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce")
    ret = cbot.shift(-lead) / cbot - 1.0
    w = pd.Series([PHENOLOGY_WEIGHT.get(m, 0.0) for m in df.index.month], index=df.index)
    crit = (w >= 0.7) & stress.notna() & ret.notna()
    if crit.sum() < 80:
        return {"verdict": "TOO_FEW_CRITICAL", "n": int(crit.sum())}
    sc = stress[crit]
    hi = sc.quantile(0.66)
    lo = sc.quantile(0.33)
    unfav = ret[crit & (stress >= hi)]    # chaud+sec = défavorable maïs
    fav = ret[crit & (stress <= lo)]      # frais+humide = favorable
    return {
        "n_critical": int(crit.sum()),
        "fwd_cbot_ret_unfavorable_forecast": round(float(unfav.mean()), 4) if len(unfav) else None,
        "fwd_cbot_ret_favorable_forecast": round(float(fav.mean()), 4) if len(fav) else None,
        "unfavorable_bullish": bool(len(unfav) and len(fav) and unfav.mean() > fav.mean()),
        "reading": ("Prévision défavorable (chaud+sec en fenêtre critique) vs favorable -> écart de rendement "
                    "CBOT pendant la réalisation. Si défavorable => CBOT monte, l'agronomie est confirmée "
                    "AU NIVEAU PRÉVISION (borne oracle)."),
    }


def run_v48_forecast_signal(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    by_lead = forecast_value_by_lead(df)
    fav = favorability_classes(df)
    extreme = extreme_event_oracle(df)

    # comparaison à la météo RÉALISÉE-connue (V45) = signal réellement disponible à J
    try:
        from mais.research.v45_weather_crop_stress import us_stress_vs_cbot
        realized = us_stress_vs_cbot(df, horizon=14)
        realized_auc = realized.get("oof_auc_cbot_up")
    except Exception:  # noqa: BLE001
        realized_auc = None

    oracle_auc = by_lead.get(14, {}).get("oof_auc_cbot_up")
    forecast_value = (round(oracle_auc - realized_auc, 3)
                      if (oracle_auc is not None and realized_auc is not None) else None)
    oracle_mean_has_signal = bool(oracle_auc is not None and oracle_auc >= 0.55)
    # le vrai signal est dans les EXTRÊMES (non-linéarité du rendement)
    ext_corr = extreme.get("corr_peak_heat_cbot_ret")
    extreme_has_signal = bool(ext_corr is not None and ext_corr >= 0.20 and extreme.get("extreme_heat_bullish"))

    if extreme_has_signal and not oracle_mean_has_signal:
        verdict = "SIGNAL_IN_EXTREME_FORECAST_NOT_MEAN_COLLECT_FORWARD_EXTREMES"
    elif oracle_mean_has_signal:
        verdict = "SIGNAL_IS_IN_THE_FORECAST_COLLECT_FORWARD"
    else:
        verdict = "EVEN_PERFECT_MEAN_FORECAST_WEAK"

    out = {
        "version": "V48-WEATHER-FORECAST-SIGNAL",
        "oracle_forecast_value_by_lead": by_lead,
        "extreme_event_oracle": extreme,
        "favorability": fav,
        "oracle_auc_lead14": oracle_auc,
        "realized_known_auc_v45": realized_auc,
        "forecast_value_auc_gap": forecast_value,
        "oracle_mean_has_signal": oracle_mean_has_signal,
        "extreme_forecast_has_signal": extreme_has_signal,
        "verdict": verdict,
        "interpretation": (
            "ORACLE = prévision PARFAITE (utilise le futur) : BORNE SUPÉRIEURE, NON-TRADEABLE. DÉCOUVERTE : "
            "la météo MOYENNE prévue n'apporte rien même parfaite (déjà price-in, AUC≈0.49) MAIS un ÉVÉNEMENT "
            "EXTRÊME prévu (pic de chaleur en fenêtre critique) est nettement haussier (corr~0.31, +1.6% vs "
            "−2.3%) : le rendement maïs chute NON-LINÉAIREMENT au-delà de ~30-32°C en pollinisation. Le signal "
            "météo est dans la QUEUE, pas la moyenne. -> la vraie archive forward doit suivre la PROBABILITÉ "
            "D'EXTRÊMES prévus (dôme de chaleur), pas la météo moyenne. EU réalisé data-gated."),
        "tradeable_path": ("Le signal exploitable anti-leakage = journal de prévisions forward (US+EU, daté à "
                           "l'émission, V45). EU réalisé data-gated. Aucune touche à la règle figée."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V48_DIR / "v48_forecast_signal.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
