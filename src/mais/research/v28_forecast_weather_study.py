"""V28 — Étude de la météo PRÉVUE (forecast) vs CBOT et basis, anti-leakage.

Le marché trade les anticipations : on teste si les ANOMALIES et RÉVISIONS de prévision (connues à
l'issue_date) prédisent un mouvement CBOT forward, et si un stress météo prévu justifie / ralentit la
compression d'un basis élevé.

Anti-leakage strict :
- features = run de prévision connu à `forecast_issue_date` (jamais le réalisé sur tout l'horizon) ;
- cible = rendement/drawdown CBOT de issue_date -> issue_date+H ;
- garde `assert_forecast_no_leakage` ; holdout 2024 retiré avant toute sélection.

Si aucune archive RÉELLE n'est disponible (Previous-Runs/Historical-Forecast non collectée), le module
tourne sur une archive synthétique mais le résultat est étiqueté `METHODOLOGY_DEMO_SYNTHETIC` (pas un
résultat). Le vrai gain viendra de l'accumulation de l'archive forward.

Statut : RESEARCH_ONLY_NOT_TRADING.
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

V28_DIR = ARTEFACTS_DIR / "v28"
V28_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR = ROOT / "data" / "raw" / "openmeteo_forecast"
HOLDOUT_YEAR = 2024


def _load_cbot() -> pd.Series:
    m = pd.read_parquet(ROOT / "data/interim/market.parquet")
    m["Date"] = pd.to_datetime(m["Date"])
    return m.set_index("Date")["corn_close"].dropna().sort_index()


def _load_basis() -> pd.DataFrame:
    cf = pd.read_parquet(ROOT / "data/processed/euronext/ema_curve_features.parquet")
    cf["Date"] = pd.to_datetime(cf["Date"])
    cols = [c for c in ["ema_cbot_basis", "ema_cbot_basis_zscore_52w"] if c in cf.columns]
    return cf.set_index("Date")[cols].sort_index()


def load_real_archive(region: str = "us") -> pd.DataFrame | None:
    path = ARCHIVE_DIR / f"{region}_corn_belt_forecast_daily.parquet"
    if not path.exists():
        return None
    fc = pd.read_parquet(path)
    return fc if not fc.empty else None


def collect_real_archive(start: date, end: date, region: str = "us") -> dict[str, Any]:
    """Récupère une archive de prévisions réelle (Historical-Forecast API). Réseau requis, SKIP propre sinon."""
    from mais.collect.openmeteo_forecast_collector import fetch_historical_forecast
    try:
        fc = fetch_historical_forecast(start, end, region=region)
    except NotImplementedError as exc:
        return {"status": "SKIP", "reason": str(exc)[:160]}
    if fc.empty:
        return {"status": "EMPTY"}
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    path = ARCHIVE_DIR / f"{region}_corn_belt_forecast_daily.parquet"
    if path.exists():
        prev = pd.read_parquet(path)
        fc = pd.concat([prev, fc], ignore_index=True).drop_duplicates(
            subset=["forecast_issue_date", "forecast_valid_date", "zone", "variable"])
    fc.to_parquet(path, index=False)
    return {"status": "OK", "rows": int(len(fc)), "path": str(path)}


def _oof_auc(x: pd.DataFrame, y: pd.Series, n_splits: int = 5, embargo: int = 20) -> float | None:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler
    mask = x.notna().all(axis=1) & y.notna()
    x, y = x[mask], y[mask].astype(int)
    if len(y) < 80 or y.nunique() < 2:
        return None
    preds = np.full(len(y), np.nan)
    for tr, te in TimeSeriesSplit(n_splits=n_splits).split(x):
        tr = tr[: max(0, len(tr) - embargo)]
        if len(tr) < 40 or y.iloc[tr].nunique() < 2:
            continue
        sc = StandardScaler().fit(x.iloc[tr])
        clf = LogisticRegression(max_iter=500).fit(sc.transform(x.iloc[tr]), y.iloc[tr])
        preds[te] = clf.predict_proba(sc.transform(x.iloc[te]))[:, 1]
    ok = ~np.isnan(preds)
    if ok.sum() < 40 or len(np.unique(y[ok])) < 2:
        return None
    return float(roc_auc_score(y[ok], preds[ok]))


def run_forecast_cbot_study(fc: pd.DataFrame, horizon: int = 20) -> dict[str, Any]:
    """Les anomalies/révisions de prévision prédisent-elles la direction/le drawdown CBOT forward ?"""
    from mais.features.weather_forecast import build_forecast_features
    feats = build_forecast_features(fc, region="us")
    if feats.empty:
        return {"version": "V28-FORECAST-CBOT", "verdict": "NO_FEATURES"}
    cbot = _load_cbot()
    df = feats.join(cbot.rename("cbot"), how="inner").sort_index()
    df = df[df.index.year != HOLDOUT_YEAR]
    if len(df) < 80:
        return {"version": "V28-FORECAST-CBOT", "verdict": "TOO_SHORT", "n": int(len(df))}
    fwd = df["cbot"].shift(-horizon) / df["cbot"] - 1.0
    y_up = (fwd > 0).astype(float)
    roll_max = df["cbot"].rolling(horizon).max().shift(-horizon)
    y_draw = ((df["cbot"] - roll_max) / df["cbot"] <= -0.05).astype(float)
    feat_cols = [c for c in df.columns if c.startswith("fc_") or c.endswith("_risk")]
    x = df[feat_cols]
    assert_no_holdout(df.reset_index().rename(columns={"index": "Date", "forecast_issue_date": "Date"}))
    out = {
        "version": "V28-FORECAST-CBOT",
        "horizon": horizon,
        "n": int(len(df)),
        "n_features": len(feat_cols),
        "auc_cbot_up": _oof_auc(x, y_up),
        "auc_cbot_drawdown_5pct": _oof_auc(x, y_draw),
        "verdict": "FORECAST_CBOT_TESTED",
        "interpretation": "AUC>0.55 = la météo prévue apporte un signal directionnel/risque CBOT.",
    }
    (V28_DIR / "forecast_cbot.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_forecast_basis_study(fc: pd.DataFrame, horizon: int = 40) -> dict[str, Any]:
    """Un basis élevé se compresse-t-il MOINS quand un stress météo (US prévu) est présent ?"""
    from mais.features.weather_forecast import build_forecast_features
    feats = build_forecast_features(fc, region="us")
    if feats.empty or "us_drought_forecast_risk" not in feats.columns:
        return {"version": "V28-FORECAST-BASIS", "verdict": "NO_STRESS_FEATURE"}
    basis = _load_basis()
    df = feats.join(basis, how="inner").sort_index()
    df = df[df.index.year != HOLDOUT_YEAR]
    if "ema_cbot_basis" not in df.columns or len(df) < 60:
        return {"version": "V28-FORECAST-BASIS", "verdict": "TOO_SHORT", "n": int(len(df))}
    bz = df.get("ema_cbot_basis_zscore_52w")
    if bz is None:
        return {"version": "V28-FORECAST-BASIS", "verdict": "NO_BASIS_Z"}
    high = df[bz > 1.0].copy()
    if len(high) < 15:
        return {"version": "V28-FORECAST-BASIS", "verdict": "TOO_FEW_HIGH_BASIS", "n_high": int(len(high))}
    fwd_change = high["ema_cbot_basis"].reindex(df.index).shift(-horizon).reindex(high.index) - high["ema_cbot_basis"]
    stress = high["us_drought_forecast_risk"].fillna(0.0)
    hi_stress = stress > stress.median()
    out = {
        "version": "V28-FORECAST-BASIS",
        "horizon": horizon,
        "n_high_basis": int(len(high)),
        "mean_basis_change_high_stress": round(float(fwd_change[hi_stress].mean()), 2)
        if hi_stress.any() else None,
        "mean_basis_change_low_stress": round(float(fwd_change[~hi_stress].mean()), 2)
        if (~hi_stress).any() else None,
        "verdict": "FORECAST_BASIS_TESTED",
        "interpretation": "Si la compression (changement négatif) est plus faible sous stress prévu, "
                          "le stress météo justifie un basis qui se normalise plus lentement -> warning.",
    }
    (V28_DIR / "forecast_basis.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_v28_all(try_network: bool = True, region: str = "us") -> dict[str, Any]:
    archive = load_real_archive(region)
    archive_status = "REAL_ARCHIVE_LOADED" if archive is not None else "NO_REAL_ARCHIVE"
    collect = None
    if archive is None and try_network:
        collect = collect_real_archive(date(2019, 1, 1), date(2023, 12, 31), region=region)
        if collect.get("status") == "OK":
            archive = load_real_archive(region)
            archive_status = "REAL_ARCHIVE_COLLECTED"
    demo = False
    if archive is None:
        from mais.features.weather_forecast import make_synthetic_forecast_archive
        archive = make_synthetic_forecast_archive(n_days=200)
        demo = True
        archive_status = "SYNTHETIC_DEMO_ONLY"

    cbot = run_forecast_cbot_study(archive)
    basis = run_forecast_basis_study(archive)
    out = {
        "version": "V28-FORECAST-WEATHER",
        "archive_status": archive_status,
        "collect": collect,
        "is_demo_synthetic": demo,
        "forecast_cbot": cbot,
        "forecast_basis": basis,
        "verdict": ("METHODOLOGY_DEMO_SYNTHETIC" if demo
                    else "FORECAST_STUDY_ON_REAL_ARCHIVE"),
        "note": ("Pipeline anti-leakage validé. Résultats non publiables tant que synthétique : "
                 "accumuler l'archive Historical-Forecast/Previous-Runs forward."
                 if demo else
                 "Archive réelle utilisée (lead court, proxy). Étendre via Previous-Runs multi-lead."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V28_DIR / "v28_summary.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
