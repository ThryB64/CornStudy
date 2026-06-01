"""V45 — Météo & stress cultural : la météo (défavorable = sécheresse/chaleur) explique-t-elle le cours ?

Thèse agronomique : un stress hydrique/thermique sur la fenêtre critique du maïs (pollinisation, ~juillet
US) réduit le rendement attendu -> le CBOT monte. On teste ça PROPREMENT et SANS FUITE :

- Indice de stress cultural US CAUSAL et PHÉNOLOGIQUE, construit depuis la météo RÉALISÉE connue à J
  (anomalies corn-belt + sécheresse), pondéré par la fenêtre critique (juillet > juin/août > reste).
- E1 : le stress US connu à J précède-t-il une HAUSSE du CBOT ? (OOF honnête + rendement conditionnel).
- E2 : le stress US justifie-t-il un basis EU haut / le rend-il moins compressible ? (lien V28/V40, contexte).
- Forward : journal append-only des PRÉVISIONS (US+EU, daté à l'émission) = l'équivalent météo du forward
  officiel EMA, anti-leakage par construction (prévision émise à J, jamais réécrite).

Limite honnête : le master ne contient que la météo US réalisée (pas EU) -> le stress EU est data-gated et
n'existe qu'en forward (collecteur Open-Meteo EU). On ne simule rien.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT
from mais.registry.holdout_lock import assert_no_holdout

V45_DIR = ARTEFACTS_DIR / "v45"
V45_DIR.mkdir(parents=True, exist_ok=True)
WX_JOURNAL_DIR = ROOT / "data" / "official_forward"
WX_JOURNAL = WX_JOURNAL_DIR / "weather_forecast_journal.jsonl"

# Poids phénologique US : pollinisation/remplissage = juillet critique, juin/août importants.
PHENOLOGY_WEIGHT = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.2, 5: 0.4, 6: 0.7,
                    7: 1.0, 8: 0.8, 9: 0.3, 10: 0.1, 11: 0.0, 12: 0.0}


def _causal_z(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    return (s - s.expanding(min_periods=120).mean()) / s.expanding(min_periods=120).std()


def crop_stress_index(df: pd.DataFrame) -> pd.DataFrame:
    """Indice de stress cultural US causal (hot+dry), pondéré phénologie, connu à J (shift(1))."""
    heat = _causal_z(df.get("wx_belt_tmax_c_anom_z"))           # chaud
    dry1 = _causal_z(df.get("wx_belt_rain_deficit_14d"))        # déficit pluie 14j
    dry2 = -_causal_z(df.get("wx_belt_prcp_30_anom_z"))         # prcp basse = sec
    drought = _causal_z(df.get("drought_composite"))            # sécheresse %
    comp = pd.concat([heat, dry1, dry2, drought], axis=1)
    raw = comp.mean(axis=1, skipna=True)                        # stress brut (z moyen)
    w = pd.Series([PHENOLOGY_WEIGHT.get(m, 0.0) for m in df.index.month], index=df.index)
    stress = (raw * w)
    out = pd.DataFrame({
        "stress_raw": raw,
        "phenology_weight": w,
        "crop_stress_us": stress.shift(1),                      # anti-leakage : connu la veille
        "in_critical_window": (w >= 0.7).astype(int),
    }, index=df.index)
    return out


def us_stress_vs_cbot(df: pd.DataFrame, horizon: int = 20) -> dict[str, Any]:
    """E1 : un stress US connu à J précède-t-il une hausse du CBOT ?"""
    s = crop_stress_index(df)["crop_stress_us"]
    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce")
    fwd_ret = cbot.shift(-horizon) / cbot - 1.0
    m = s.notna() & fwd_ret.notna()
    if m.sum() < 200:
        return {"verdict": "TOO_SHORT"}
    corr = round(float(np.corrcoef(s[m], fwd_ret[m])[0, 1]), 3)
    # rendement forward conditionnel : stress élevé (top tercile) vs reste, en fenêtre critique
    crit = m & (df["wx_belt_tmax_c_anom_z"].notna()) & (crop_stress_index(df)["in_critical_window"] == 1)
    cond = {}
    if crit.sum() > 80:
        sc = s[crit]
        thr = sc.quantile(0.66)
        hi = fwd_ret[crit & (s >= thr)]
        lo = fwd_ret[crit & (s < thr)]
        cond = {"n_critical": int(crit.sum()),
                "fwd_ret_high_stress": round(float(hi.mean()), 4) if len(hi) else None,
                "fwd_ret_low_stress": round(float(lo.mean()), 4) if len(lo) else None}
    auc = _oof_auc(pd.DataFrame({"stress": s[m]}), (fwd_ret[m] > 0).astype(float), horizon)
    high_stress_bullish = bool(corr > 0.05 or (cond.get("fwd_ret_high_stress") or -1) >
                               (cond.get("fwd_ret_low_stress") or 0))
    return {
        "horizon": horizon,
        "corr_stress_fwd_cbot": corr,
        "conditional_fwd_return": cond,
        "oof_auc_cbot_up": round(auc, 3) if auc is not None else None,
        "high_stress_precedes_cbot_up": high_stress_bullish,
        "verdict": ("US_STRESS_RELATED_TO_CBOT" if (auc is not None and auc >= 0.55) or corr >= 0.08
                    else "US_STRESS_WEAK_PREDICTOR"),
        "reading": ("Stress cultural US (chaud+sec en fenêtre critique) connu à J vs hausse CBOT à H jours. "
                    "Conforme à l'agronomie si stress -> CBOT monte. n et signal à confirmer en forward."),
    }


def us_stress_vs_basis(df: pd.DataFrame, horizon: int = 40) -> dict[str, Any]:
    """E2 : le stress US (qui pousse le CBOT) rend-il le basis haut PLUS compressible (CBOT rattrape) ?"""
    s = crop_stress_index(df)["crop_stress_us"]
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    drop = basis - basis.shift(-horizon)  # >0 = compression
    high = bz >= 1.0
    m = s.notna() & drop.notna() & high
    if m.sum() < 60:
        return {"verdict": "TOO_FEW_HIGH_BASIS", "n": int(m.sum())}
    thr = s[m].quantile(0.5)
    hi = drop[m & (s >= thr)]
    lo = drop[m & (s < thr)]
    return {
        "horizon": horizon,
        "n_high_basis": int(m.sum()),
        "compression_high_us_stress": round(float(hi.mean()), 2) if len(hi) else None,
        "compression_low_us_stress": round(float(lo.mean()), 2) if len(lo) else None,
        "us_stress_helps_compression": bool(len(hi) and len(lo) and hi.mean() > lo.mean()),
        "reading": ("Quand le basis est haut, un stress US élevé (CBOT poussé à la hausse) devrait AIDER la "
                    "compression par rattrapage CBOT. À l'inverse, un stress EU (data-gated) justifierait le "
                    "basis et le rendrait moins compressible -> à mesurer en forward via le journal EU."),
    }


def _oof_auc(x: pd.DataFrame, y: pd.Series, horizon: int) -> float | None:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler
    mask = x.notna().all(axis=1) & y.notna()
    x, y = x[mask], y[mask].astype(int)
    if len(y) < 200 or y.nunique() < 2:
        return None
    pred = np.full(len(y), np.nan)
    for tr, te in TimeSeriesSplit(n_splits=5).split(x):
        tr = tr[: max(0, len(tr) - horizon)]
        if len(tr) < 100 or y.iloc[tr].nunique() < 2:
            continue
        sc = StandardScaler().fit(x.iloc[tr])
        clf = LogisticRegression(max_iter=500).fit(sc.transform(x.iloc[tr]), y.iloc[tr])
        pred[te] = clf.predict_proba(sc.transform(x.iloc[te]))[:, 1]
    ok = ~np.isnan(pred)
    if ok.sum() < 100 or len(np.unique(y[ok])) < 2:
        return None
    return float(roc_auc_score(y[ok], pred[ok]))


HOT_THRESHOLD_C = 32.0  # seuil de stress chaleur maïs (pollinisation)


def _max_consecutive(flags: list[bool]) -> int:
    best = run = 0
    for v in flags:
        run = run + 1 if v else 0
        best = max(best, run)
    return best


def _forward_stress_from_forecast(fc: pd.DataFrame) -> dict[str, float] | None:
    """Stress prévu (lead 1-10) : moyenne, pic de chaleur, ET persistance (jours consécutifs >32°C).

    V51 : la PERSISTANCE de la chaleur prévue (jours consécutifs) porte plus de signal que l'intensité d'un
    seul jour -> on l'enregistre désormais dans le journal forward.
    """
    if fc is None or len(fc) == 0:
        return None
    f = fc[fc["lead_time_days"].between(1, 10)] if "lead_time_days" in fc.columns else fc
    piv = f.pivot_table(index="forecast_valid_date", columns="variable", values="value", aggfunc="mean")
    if "tmax" not in piv.columns:
        return None
    tmax = piv["tmax"].sort_index()
    tmax_mean = float(tmax.mean())
    tmax_peak = float(tmax.max())
    consec_hot = _max_consecutive([bool(v >= HOT_THRESHOLD_C) for v in tmax.to_numpy()])
    prcp = piv.get("precipitation", piv.get("prcp"))
    dry = -(float(prcp.mean())) if prcp is not None else 0.0
    return {"mean": round(tmax_mean + 0.1 * dry, 3), "peak_tmax": round(tmax_peak, 2),
            "consecutive_hot_days": int(consec_hot)}


def collect_weather_forecast_forward(try_network: bool = True) -> dict[str, Any]:
    """Forward : prévision US+EU émise aujourd'hui -> stress prévu, append-only daté à l'émission."""
    rec: dict[str, Any] = {"issue_date": date.today().isoformat(), "status": "WAITING_NETWORK"}
    if not try_network:
        return rec
    try:
        from mais.collect.openmeteo_forecast_collector import fetch_forecast
        for region in ("us", "eu"):
            try:
                fc = fetch_forecast(region=region)
                s = _forward_stress_from_forecast(fc)
                rec[f"forecast_stress_{region}"] = s["mean"] if s else None
                rec[f"forecast_peak_tmax_{region}"] = s["peak_tmax"] if s else None
                rec[f"forecast_consecutive_hot_days_{region}"] = s["consecutive_hot_days"] if s else None
                rec[f"n_rows_{region}"] = int(len(fc))
            except Exception as e:  # noqa: BLE001
                rec[f"forecast_stress_{region}"] = None
                rec[f"error_{region}"] = f"{type(e).__name__}: {str(e)[:80]}"
        rec["status"] = "OK" if rec.get("forecast_stress_us") is not None else "PARTIAL_OR_BLOCKED"
    except Exception as e:  # noqa: BLE001
        rec["status"] = f"COLLECTOR_ERROR: {type(e).__name__}"
    # append-only
    if rec["status"] == "OK":
        WX_JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
        import contextlib
        existing = set()
        if WX_JOURNAL.exists():
            for line in WX_JOURNAL.read_text(encoding="utf-8").splitlines():
                with contextlib.suppress(ValueError):
                    existing.add(json.loads(line).get("issue_date"))
        if rec["issue_date"] not in existing:
            with WX_JOURNAL.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
            rec["journal"] = "APPENDED"
        else:
            rec["journal"] = "ALREADY_LOGGED"
    return rec


def run_v45_weather(df: pd.DataFrame, try_network: bool = False) -> dict[str, Any]:
    assert_no_holdout(df)
    out = {
        "version": "V45-WEATHER-CROP-STRESS",
        "E1_us_stress_vs_cbot": us_stress_vs_cbot(df),
        "E2_us_stress_vs_basis": us_stress_vs_basis(df),
        "forward_collect": collect_weather_forecast_forward(try_network=try_network),
        "data_gated": {
            "eu_realized_weather": "Le master n'a que la météo US réalisée. Stress EU = forward only "
                                   "(collecteur Open-Meteo EU) -> justification météo du basis à mesurer en forward.",
            "historical_forecast_archive": "Open-Meteo historical-forecast time out ; on accumule le forward.",
        },
        "status": "RESEARCH_ONLY_NOT_TRADING",
        "note": "Stress US réalisé (anti-leakage, phénologie). Aucune touche à la règle figée.",
    }
    (V45_DIR / "v45_weather.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
