"""V19-CBOT-LAB — Pousser le CBOT : cibles de risque + interactions COT/WASDE/météo + phénologie.

On ne cherche plus « CBOT up/down » brut, mais les RISQUES (grandes baisses, rallyes, pics de vol) et les
INTERACTIONS (météo × COT, météo × WASDE) pendant les phases agronomiques sensibles. Tout sur météo
RÉALISÉE (la météo prévue = infrastructure séparée, WAITING_DATA archive).

Chaque famille est testée OOF vs une baseline technique ; verdict
∈ {ADD_TO_CBOT_MODEL, WATCHLIST, KEEP_AS_EXPLANATION, NO_GO}.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import TimeSeriesSplit

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout
from mais.research.v18_weather_deep import weather_stress_index

V19_DIR = ARTEFACTS_DIR / "v19"
V19_DIR.mkdir(parents=True, exist_ok=True)

# Fenêtre de pollinisation/remplissage US (juin-août) = phase critique rendement
POLLINATION_MONTHS = (6, 7, 8)


# ---------------------------------------------------------------------------
# Cibles de risque CBOT
# ---------------------------------------------------------------------------

def cbot_risk_targets(df: pd.DataFrame) -> dict[str, pd.Series]:
    c = df["corn_close"]
    out: dict[str, pd.Series] = {}
    for h, pct in [(10, 3), (20, 5), (40, 8)]:
        fwd_min = c.shift(-1).rolling(h).min().shift(-(h - 1))
        fwd_max = c.shift(-1).rolling(h).max().shift(-(h - 1))
        dd = (fwd_min / c - 1 < -pct / 100).astype(float)
        dd[c.shift(-h).isna()] = np.nan
        out[f"drawdown_{pct}pct_h{h}"] = dd
        ra = (fwd_max / c - 1 > pct / 100).astype(float)
        ra[c.shift(-h).isna()] = np.nan
        out[f"rally_{pct}pct_h{h}"] = ra
    # pic de volatilité : vol réalisée future > vol courante (×1.5)
    ret = np.log(c).diff()
    cur_vol = ret.rolling(10).std()
    fwd_vol = ret.shift(-10).rolling(10).std()
    vs = (fwd_vol > 1.5 * cur_vol).astype(float)
    vs[fwd_vol.isna() | cur_vol.isna()] = np.nan
    out["vol_spike_h10"] = vs
    # direction (référence)
    up = (c.shift(-20) / c - 1 > 0).astype(float)
    up[c.shift(-20).isna()] = np.nan
    out["up_h20"] = up
    return out


# ---------------------------------------------------------------------------
# Jeux de features
# ---------------------------------------------------------------------------

def _base_features(df: pd.DataFrame) -> pd.DataFrame:
    idx = df.index
    f = pd.DataFrame(index=idx)
    for c in ["corn_logret_1d", "corn_logret_5d", "corn_logret_20d", "corn_realized_vol_20",
              "corn_rsi_14", "corn_macd_hist", "corn_atr_14"]:
        if c in df.columns:
            f[c] = df[c]
    f["month_sin"] = np.sin(2 * np.pi * idx.month / 12)
    f["month_cos"] = np.cos(2 * np.pi * idx.month / 12)
    return f


def _weather_features(df: pd.DataFrame) -> pd.DataFrame:
    idx = df.index
    f = pd.DataFrame(index=idx)
    for c in ["wx_belt_heat_days_38c_30", "wx_belt_rain_deficit_14d", "wx_belt_gdd_accumulated",
              "drought_composite"]:
        if c in df.columns:
            f[c] = df[c]
    stress = weather_stress_index(df)
    f["wx_stress"] = stress
    # pondération phénologique : stress en pollinisation (juin-août) compte plus
    pollination = pd.Series(idx.month, index=idx).isin(POLLINATION_MONTHS).astype(float)
    f["wx_stress_pollination"] = (stress.fillna(0) * pollination).values
    return f


def _cot_features(df: pd.DataFrame) -> pd.DataFrame:
    idx = df.index
    f = pd.DataFrame(index=idx)
    for c in ["cot_mm_net_pct_oi_x", "cot_mm_long_pct", "cot_mm_short_pct", "cot_mm_net"]:
        if c in df.columns:
            f[c] = df[c]
    return f


def _wasde_features(df: pd.DataFrame) -> pd.DataFrame:
    idx = df.index
    f = pd.DataFrame(index=idx)
    for c in ["wasde_ending_stocks_surprise_vs_trend", "wasde_production_surprise_vs_trend",
              "wasde_exports_surprise_vs_trend"]:
        if c in df.columns:
            f[c] = df[c]
    return f


def _interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """COT × météo (short covering) et WASDE × météo (choc fondamental combiné)."""
    idx = df.index
    f = pd.DataFrame(index=idx)
    stress = weather_stress_index(df).fillna(0)
    cot = df.get("cot_mm_net_pct_oi_x", pd.Series(0.0, index=idx)).fillna(0)
    wasde_es = df.get("wasde_ending_stocks_surprise_vs_trend", pd.Series(0.0, index=idx)).fillna(0)
    # météo bullish (stress↑) × fonds très short (cot net négatif) -> short covering potentiel
    f["wx_x_cot"] = (stress * cot).values
    # météo bullish × surprise stocks baissière -> choc combiné
    f["wx_x_wasde_stocks"] = (stress * (-wasde_es)).values
    return f


# ---------------------------------------------------------------------------
# OOF AUC
# ---------------------------------------------------------------------------

def _oof_auc(x: pd.DataFrame, y: pd.Series, embargo: int) -> tuple[float | None, int]:
    keep = y.notna() & x.notna().all(axis=1)
    xk, yk = x.loc[keep], y.loc[keep].astype(int)
    if len(xk) < 200 or yk.nunique() < 2:
        return None, int(len(xk))
    dates = xk.index
    means, stds = xk.mean(), xk.std().replace(0, 1)
    xs = (xk - means) / stds
    oof = np.full(len(xk), np.nan)
    for tr, te in TimeSeriesSplit(n_splits=6).split(xs):
        train_end = dates[tr[-1]]
        te_p = np.array([i for i in te if dates[i] > train_end + pd.Timedelta(days=embargo)])
        if len(tr) < 100 or len(te_p) < 10 or yk.iloc[tr].nunique() < 2:
            continue
        clf = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
        clf.fit(xs.iloc[tr], yk.iloc[tr])
        oof[te_p] = clf.predict_proba(xs.iloc[te_p])[:, 1]
    v = ~np.isnan(oof)
    if v.sum() < 50 or len(np.unique(yk.values[v])) < 2:
        return None, int(v.sum())
    return round(float(roc_auc_score(yk.values[v], oof[v])), 4), int(v.sum())


def _verdict(delta: float | None) -> str:
    if delta is None:
        return "NO_GO"
    if delta > 0.02:
        return "ADD_TO_CBOT_MODEL"
    if delta > 0.005:
        return "WATCHLIST"
    if delta > -0.005:
        return "KEEP_AS_EXPLANATION"
    return "NO_GO"


def _target_horizon(name: str) -> int:
    for h in (40, 20, 10):
        if f"h{h}" in name:
            return h
    return 20


# ---------------------------------------------------------------------------
# V19-CBOT — lab risque + familles
# ---------------------------------------------------------------------------

def run_cbot_risk_lab(df: pd.DataFrame) -> dict[str, Any]:
    """Pour chaque cible de risque CBOT : baseline technique vs + météo / COT / WASDE / interactions."""
    assert_no_holdout(df)
    if "corn_close" not in df.columns:
        return {"version": "V19-CBOT-RISK-LAB", "verdict": "MISSING_CORN"}
    targets = cbot_risk_targets(df)
    base = _base_features(df)
    wx = _weather_features(df)
    cot = _cot_features(df)
    wasde = _wasde_features(df)
    inter = _interaction_features(df)

    results = {}
    for tname, y in targets.items():
        h = _target_horizon(tname)
        b_auc, n_b = _oof_auc(base, y, h)
        if b_auc is None:
            results[tname] = {"baseline_auc": None, "n": n_b}
            continue
        row = {"baseline_auc": b_auc, "base_rate": round(float(y.dropna().mean()), 4), "n_oof": n_b}
        for fam_name, fam in [("weather", wx), ("cot", cot), ("wasde", wasde),
                              ("weather+interactions", pd.concat([wx, inter], axis=1))]:
            aug = pd.concat([base, fam], axis=1)
            a_auc, _ = _oof_auc(aug, y, h)
            delta = round(a_auc - b_auc, 4) if a_auc else None
            row[fam_name] = {"auc": a_auc, "delta": delta, "verdict": _verdict(delta)}
        results[tname] = row

    # meilleures combinaisons (delta > 0.02)
    adds = []
    for t, r in results.items():
        for fam in ["weather", "cot", "wasde", "weather+interactions"]:
            if isinstance(r.get(fam), dict) and r[fam].get("verdict") == "ADD_TO_CBOT_MODEL":
                adds.append({"target": t, "family": fam, "delta": r[fam]["delta"], "auc": r[fam]["auc"]})
    out = {
        "version": "V19-CBOT-RISK-LAB",
        "targets_tested": list(targets.keys()),
        "results": results,
        "families_adding_value": adds,
        "interpretation": (
            "On cherche si la météo (réalisée), le COT, le WASDE ou leurs interactions améliorent la "
            "prédiction des RISQUES CBOT (drawdown/rally/vol) au-delà des seules techniques de prix."
        ),
        "verdict": "CBOT_RISK_LAB_DONE",
    }
    (V19_DIR / "cbot_risk_lab.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_cot_weather_interaction(df: pd.DataFrame) -> dict[str, Any]:
    """Hypothèse short-covering : météo bullish + fonds très short -> rally CBOT plus probable."""
    assert_no_holdout(df)
    targets = cbot_risk_targets(df)
    base = _base_features(df)
    wx = _weather_features(df)
    cot = _cot_features(df)
    inter = _interaction_features(df)[["wx_x_cot"]]

    results = {}
    for tname in ["rally_5pct_h20", "rally_8pct_h40", "drawdown_5pct_h20"]:
        if tname not in targets:
            continue
        y = targets[tname]
        h = _target_horizon(tname)
        b_auc, _ = _oof_auc(pd.concat([base, wx, cot], axis=1), y, h)
        i_auc, _ = _oof_auc(pd.concat([base, wx, cot, inter], axis=1), y, h)
        delta = round(i_auc - b_auc, 4) if (b_auc and i_auc) else None
        results[tname] = {"auc_wx_cot": b_auc, "auc_with_interaction": i_auc, "delta": delta,
                          "verdict": _verdict(delta)}
    out = {
        "version": "V19-COT-WEATHER",
        "results": results,
        "hypothesis": "wx_stress × cot_mm_net (fonds short + météo bullish) augmente la proba de rally (short covering)",
        "verdict": "COT_WEATHER_DONE",
    }
    (V19_DIR / "cot_weather_interaction.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
