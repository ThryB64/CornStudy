"""V18-LIT — Réplication des familles de littérature et test d'intégration à l'indicateur.

Pour chaque famille (théorie du stockage, convergence, non-convergence, event study, COT, météo,
inter-commodités, options), on teste si elle améliore la PRÉDICTION DE COMPRESSION du basis
(basis_change_h40 < 0) AU-DELÀ de la baseline `basis_z + month_cos`, en OOF strict.

Verdict ∈ {ADD_TO_INDICATOR, WATCHLIST, KEEP_AS_EXPLANATION, NO_GO, DATA_BLOCKED}.
L'indicateur V17 ne change pas tant qu'une famille n'a pas obtenu ADD_TO_INDICATOR.

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

V18_DIR = ARTEFACTS_DIR / "v18"
V18_DIR.mkdir(parents=True, exist_ok=True)

HORIZON = 40
BASELINE_COLS = ["basis_z", "month_cos"]


def _frame(df: pd.DataFrame) -> pd.DataFrame:
    idx = df.index
    f = pd.DataFrame(index=idx)
    f["basis_z"] = df.get("ema_cbot_basis_zscore_52w")
    f["month_cos"] = np.cos(2 * np.pi * idx.month / 12)
    return f


def _compression_target(df: pd.DataFrame, h: int = HORIZON) -> pd.Series:
    b = df["ema_cbot_basis"]
    chg = b.shift(-h) - b
    y = (chg < 0).astype(float)
    y[chg.isna()] = np.nan
    return y


def _oof_auc(x: pd.DataFrame, y: pd.Series, embargo: int = HORIZON) -> tuple[float | None, int]:
    keep = y.notna() & x.notna().all(axis=1)
    xk, yk = x.loc[keep], y.loc[keep].astype(int)
    if len(xk) < 150 or yk.nunique() < 2:
        return None, int(len(xk))
    dates = xk.index
    means, stds = xk.mean(), xk.std().replace(0, 1)
    xs = (xk - means) / stds
    oof = np.full(len(xk), np.nan)
    for tr, te in TimeSeriesSplit(n_splits=6).split(xs):
        train_end = dates[tr[-1]]
        te_p = np.array([i for i in te if dates[i] > train_end + pd.Timedelta(days=embargo)])
        if len(tr) < 80 or len(te_p) < 10 or yk.iloc[tr].nunique() < 2:
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
        return "ADD_TO_INDICATOR"
    if delta > 0.005:
        return "WATCHLIST"
    if delta > -0.005:
        return "KEEP_AS_EXPLANATION"
    return "NO_GO"


def _augment_test(df: pd.DataFrame, family_cols: list[str], name: str) -> dict[str, Any]:
    cols = [c for c in family_cols if c in df.columns and df[c].notna().sum() > 300]
    base = _frame(df)
    y = _compression_target(df)
    base_auc, n_base = _oof_auc(base, y)
    if not cols:
        return {"family": name, "verdict": "DATA_BLOCKED", "available_cols": [],
                "baseline_auc": base_auc}
    aug = base.copy()
    for c in cols:
        aug[c] = df[c]
    aug_auc, n_aug = _oof_auc(aug, y)
    delta = round(aug_auc - base_auc, 4) if (aug_auc and base_auc) else None
    return {"family": name, "cols_used": cols, "baseline_auc": base_auc,
            "augmented_auc": aug_auc, "delta_auc": delta, "n_oof": n_aug,
            "verdict": _verdict(delta)}


# ---------------------------------------------------------------------------
# V18-BASIS-01 — Modèles de convergence (économétrie)
# ---------------------------------------------------------------------------

def run_basis_convergence(df: pd.DataFrame) -> dict[str, Any]:
    """AR(1)/OU half-life global + threshold (par |z|) + régime (par vol). Calibre les sorties."""
    assert_no_holdout(df)
    bz = df.get("ema_cbot_basis_zscore_52w")
    if bz is None:
        return {"version": "V18-BASIS-01", "verdict": "MISSING_BASIS_Z"}

    def _half_life(s: pd.Series):
        s = s.dropna()
        if len(s) < 150:
            return None
        lag = s.shift(1).dropna()
        cur = s.loc[lag.index]
        if lag.std() == 0:
            return None
        phi = float(np.cov(cur.values, lag.values)[0, 1] / np.var(lag.values))
        return round(-np.log(2) / np.log(phi), 1) if 0 < phi < 1 else None

    global_hl = _half_life(bz)

    # threshold AR : reversion plus rapide quand |z| extrême ?
    hl_moderate = _half_life(bz.where(bz.abs() <= 1.5))
    hl_extreme = _half_life(bz.where(bz.abs() > 1.5))

    # régime de volatilité CBOT
    vol = df.get("corn_realized_vol_20")
    hl_lowvol = hl_highvol = None
    if vol is not None:
        med = vol.median()
        hl_lowvol = _half_life(bz.where(vol <= med))
        hl_highvol = _half_life(bz.where(vol > med))

    out = {
        "version": "V18-BASIS-01-CONVERGENCE",
        "global_half_life_days": global_hl,
        "half_life_moderate_abs_z_le_1.5": hl_moderate,
        "half_life_extreme_abs_z_gt_1.5": hl_extreme,
        "half_life_low_vol": hl_lowvol,
        "half_life_high_vol": hl_highvol,
        "interpretation": (
            "OU/AR(1) confirme la mean-reversion. Si la demi-vie diffère par régime (|z| ou vol), la sortie "
            "devrait être conditionnelle. Calibre z→0/z→0.5 et le plafond temps."
        ),
        "verdict": "KEEP_AS_EXPLANATION",
    }
    (V18_DIR / "basis_convergence.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# Familles testées par augmentation OOF
# ---------------------------------------------------------------------------

def run_storage_replication(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    out = _augment_test(df, ["ema_curve_slope_6", "ema_contango_flag", "ema_roll_yield_ann",
                             "ema_carry_front_second", "curve_backwardation_proxy", "ema_oi_total"],
                        "theory_of_storage_curve")
    out["version"] = "V18-STORE-01"
    out["data_note"] = "Vraies features de courbe EMA rares (~332 obs) ; surtout proxy/OI exploitables."
    (V18_DIR / "storage_replication.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_event_study_wasde(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    out = _augment_test(df, ["wasde_ending_stocks_surprise_vs_trend", "wasde_production_surprise_vs_trend",
                             "wasde_exports_surprise_vs_trend", "days_to_next_wasde"],
                        "wasde_event_study")
    out["version"] = "V18-EVENT-01"
    (V18_DIR / "event_study_wasde.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_cot_replication(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    out = _augment_test(df, ["cot_mm_net_pct_oi_x", "cot_mm_long_pct", "cot_mm_short_pct", "cot_mm_net"],
                        "cot_positioning")
    out["version"] = "V18-COT-01"
    (V18_DIR / "cot_replication.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_weather_replication(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    out = _augment_test(df, ["wx_belt_heat_days_38c_30", "wx_belt_rain_deficit_14d",
                             "wx_belt_gdd_accumulated", "drought_composite"],
                        "weather_crop_stress")
    out["version"] = "V18-WEATHER-01"
    (V18_DIR / "weather_replication.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_commodity_replication(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    out = _augment_test(df, ["corn_soy_ratio", "corn_wheat_ratio", "corn_oil_ratio", "corn_gas_ratio",
                             "spread_corn_wheat"],
                        "cross_commodity")
    out["version"] = "V18-COMMOD-01"
    (V18_DIR / "commodity_replication.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_options_replication(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    iv_cols = [c for c in df.columns if any(k in c.lower() for k in ["implied", "iv_", "skew_iv", "put_call"])]
    out = {"version": "V18-OPTIONS-01", "family": "implied_volatility",
           "available_iv_cols": iv_cols,
           "verdict": "DATA_BLOCKED",
           "note": "Pas de volatilité implicite CBOT corn dans le dataset (les y_skew_* sont des cibles, pas des inputs IV)."}
    (V18_DIR / "options_replication.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V18-LIT — Synthèse / matrice des verdicts
# ---------------------------------------------------------------------------

def run_replication_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Exécute toutes les réplications et agrège la matrice des verdicts."""
    assert_no_holdout(df)
    runs = {
        "storage": run_storage_replication(df),
        "convergence": run_basis_convergence(df),
        "wasde_event": run_event_study_wasde(df),
        "cot": run_cot_replication(df),
        "weather": run_weather_replication(df),
        "commodity": run_commodity_replication(df),
        "options": run_options_replication(df),
    }
    matrix = {}
    for k, r in runs.items():
        matrix[k] = {"verdict": r.get("verdict"),
                     "delta_auc": r.get("delta_auc"),
                     "baseline_auc": r.get("baseline_auc"),
                     "augmented_auc": r.get("augmented_auc")}
    to_add = [k for k, v in matrix.items() if v["verdict"] == "ADD_TO_INDICATOR"]
    watch = [k for k, v in matrix.items() if v["verdict"] == "WATCHLIST"]
    out = {
        "version": "V18-LIT-SUMMARY",
        "baseline": "basis_z + month_cos predict compression (basis_change_h40<0)",
        "matrix": matrix,
        "families_to_add": to_add,
        "families_watchlist": watch,
        "decision": (
            "Aucune famille n'atteint ADD_TO_INDICATOR : l'indicateur reste basis_z + saison."
            if not to_add else
            f"Familles à intégrer (delta AUC > +0.02) : {to_add}"),
        "verdict": "REPLICATION_SUMMARY_DONE",
        "reminder": "L'indicateur V17 ne change que sur ADD_TO_INDICATOR robuste. Ne pas sur-filtrer.",
    }
    (V18_DIR / "replication_summary.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
