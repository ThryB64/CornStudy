"""V16 — Explication économique du basis EMA/CBOT : fair value, structure de courbe, drivers.

Suite V15. Question centrale : peut-on EXPLIQUER pourquoi le basis est haut et quand il se compresse ?
Discipline : on teste des explications économiques, on ne fait pas un gros modèle prédictif opaque.

- run_basis_fair_value : basis_fair = f(saison, FX, énergie) ; mispricing = basis - fair ;
  mispricing prédit-il la compression mieux que basis_z ?
- run_curve_structure : basis haut + contango (surprix) se compresse-t-il mieux que basis haut +
  backwardation (tension durable) ? Sur les vraies features de courbe (sous-échantillon).
- run_basis_drivers : régression du basis sur les fondamentaux disponibles ; R² et drivers.
  Données EU/Ukraine/énergie-EU non jointes -> WAITING_DATA documenté.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import TimeSeriesSplit

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V16_DIR = ARTEFACTS_DIR / "v16"
V16_DIR.mkdir(parents=True, exist_ok=True)

HORIZON = 40
FUNDAMENTALS = ["month_sin", "month_cos", "eurusd", "usd_index_close",
                "oil_close", "gas_close", "corn_gas_ratio", "corn_oil_ratio"]


def _fundamentals_frame(df: pd.DataFrame) -> pd.DataFrame:
    idx = df.index
    x = pd.DataFrame(index=idx)
    x["month_sin"] = np.sin(2 * np.pi * idx.month / 12)
    x["month_cos"] = np.cos(2 * np.pi * idx.month / 12)
    for c in ["eurusd", "usd_index_close", "oil_close", "gas_close", "corn_gas_ratio", "corn_oil_ratio"]:
        x[c] = df.get(c, pd.Series(np.nan, index=idx))
    return x


def _expanding_z(s: pd.Series, min_periods: int = 120) -> pd.Series:
    mean = s.expanding(min_periods=min_periods).mean()
    std = s.expanding(min_periods=min_periods).std().replace(0, np.nan)
    return (s - mean) / std


def _basis_change(df: pd.DataFrame, h: int = HORIZON) -> pd.Series:
    b = df["ema_cbot_basis"]
    return b.shift(-h) - b


def _nonoverlap(dates: pd.DatetimeIndex, spacing: int = HORIZON):
    kept, last = [], None
    for d in dates:
        if last is None or (d - last).days >= spacing:
            kept.append(d)
            last = d
    return kept


# ---------------------------------------------------------------------------
# V16-01 — Fair value du basis
# ---------------------------------------------------------------------------

def run_basis_fair_value(df: pd.DataFrame) -> dict[str, Any]:
    """basis_fair OOF = f(fondamentaux) ; mispricing = basis - fair ; vs basis_z comme prédicteur."""
    assert_no_holdout(df)
    if "ema_cbot_basis" not in df.columns or "ema_cbot_basis_zscore_52w" not in df.columns:
        return {"version": "V16-01-FAIR-VALUE", "verdict": "MISSING_BASIS"}
    basis = df["ema_cbot_basis"]
    x = _fundamentals_frame(df)
    keep = basis.notna() & x.notna().all(axis=1)
    xk, bk = x.loc[keep], basis.loc[keep]
    if len(xk) < 300:
        return {"version": "V16-01-FAIR-VALUE", "verdict": "INSUFFICIENT", "n": int(len(xk))}
    dates = xk.index
    means, stds = xk.mean(), xk.std().replace(0, 1)
    xs = (xk - means) / stds

    # fair value OOF : prédire le basis contemporain depuis les fondamentaux (coeffs appris sur le passé)
    fair = pd.Series(np.nan, index=df.index)
    r2_folds = []
    fv = np.full(len(xk), np.nan)
    for tr, te in TimeSeriesSplit(n_splits=6).split(xs):
        if len(tr) < 100:
            continue
        reg = Ridge(alpha=1.0).fit(xs.iloc[tr], bk.iloc[tr])
        pred = reg.predict(xs.iloc[te])
        fv[te] = pred
        ss_res = float(np.sum((bk.iloc[te].values - pred) ** 2))
        ss_tot = float(np.sum((bk.iloc[te].values - bk.iloc[tr].mean()) ** 2))
        if ss_tot > 0:
            r2_folds.append(1 - ss_res / ss_tot)
    v = ~np.isnan(fv)
    fair.loc[dates[v]] = fv[v]
    mispricing = basis - fair
    mispricing_z = _expanding_z(mispricing)
    basis_z = df["ema_cbot_basis_zscore_52w"]

    # comparaison : prédire le signe de basis_change_h40 (compression = change < 0)
    target = _basis_change(df, HORIZON)
    y_compress = (target < 0).astype(float)  # 1 = compression
    y_compress[target.isna()] = np.nan

    def _signal_auc(sig):
        m = sig.notna() & y_compress.notna()
        if m.sum() < 50 or y_compress[m].nunique() < 2:
            return None, int(m.sum())
        # signal haut -> compression attendue (basis élevé descend) -> proba compression croissante avec sig
        return round(float(roc_auc_score(y_compress[m].astype(int), sig[m])), 4), int(m.sum())

    auc_basis_z, n_bz = _signal_auc(basis_z)
    auc_mispricing, n_mp = _signal_auc(mispricing_z)

    # comparaison règle de reversion : short quand signal > 1, sortie basis_z -> 0 (max 90j)
    def _short_rule(sig):
        entry = (sig > 1.0) & df["ema_close"].notna() & df["cbot_eur_t"].notna()
        kept = _nonoverlap(df.index[entry.fillna(False).values])
        ema = df["ema_close"]
        cbot = df["cbot_eur_t"]
        bz = basis_z
        pnls = []
        for d in kept:
            i = df.index.get_loc(d)
            e0, c0, z0 = ema.iloc[i], cbot.iloc[i], bz.iloc[i]
            if pd.isna(e0) or pd.isna(c0) or pd.isna(z0):
                continue
            sgn = np.sign(z0) if not pd.isna(z0) else 1
            pnl = np.nan
            for t in range(1, 91):
                if i + t >= len(df):
                    break
                ej, cj, zj = ema.iloc[i + t], cbot.iloc[i + t], bz.iloc[i + t]
                if pd.isna(ej) or pd.isna(cj):
                    continue
                pnl = -1.0 * ((ej / e0 - 1) - (cj / c0 - 1)) * e0
                if not pd.isna(zj) and zj * sgn <= 0:
                    break
            if not pd.isna(pnl):
                pnls.append(pnl)
        if len(pnls) < 5:
            return {"n": len(pnls)}
        g = np.array(pnls)
        return {"n": len(g), "hit_rate": round(float((g > 0).mean()), 4),
                "mean_pnl": round(float(g.mean()), 2),
                "net_cost3": round(float((g - 6).sum()), 1),
                "net_cost5": round(float((g - 10).sum()), 1)}

    rule_basis_z = _short_rule(basis_z)
    rule_mispricing = _short_rule(mispricing_z)

    mispricing_better = bool(
        (auc_mispricing or 0) > (auc_basis_z or 0)
        and rule_mispricing.get("net_cost5", -1e9) > rule_basis_z.get("net_cost5", -1e9))
    out = {
        "version": "V16-01-FAIR-VALUE",
        "fair_value_oof_r2_mean": round(float(np.mean(r2_folds)), 4) if r2_folds else None,
        "fundamentals": FUNDAMENTALS,
        "auc_compression_basis_z": auc_basis_z,
        "auc_compression_mispricing": auc_mispricing,
        "short_rule_basis_z": rule_basis_z,
        "short_rule_mispricing": rule_mispricing,
        "mispricing_beats_basis_z": mispricing_better,
        "interpretation": (
            "basis_fair capte la part 'normale' du basis (saison/FX/énergie). mispricing = anomalie pure. "
            "Si mispricing prédit la compression mieux que basis_z (AUC + PnL), c'est un meilleur signal."
        ),
        "verdict": "MISPRICING_BETTER" if mispricing_better else "BASIS_Z_REMAINS_BEST",
    }
    (V16_DIR / "basis_fair_value.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V16-02 — Structure de courbe : tension durable vs surprix compressible
# ---------------------------------------------------------------------------

def run_curve_structure(df: pd.DataFrame) -> dict[str, Any]:
    """Basis haut + contango (surprix) compresse-t-il mieux que basis haut + backwardation (tension) ?"""
    assert_no_holdout(df)
    basis_z = df.get("ema_cbot_basis_zscore_52w")
    if basis_z is None or "ema_close" not in df.columns:
        return {"version": "V16-02-CURVE-STRUCTURE", "verdict": "MISSING_DATA"}
    ema, cbot = df["ema_close"], df["cbot_eur_t"]

    def _reversion_pnl(entry_mask):
        kept = _nonoverlap(df.index[entry_mask.fillna(False).values])
        pnls = []
        for d in kept:
            i = df.index.get_loc(d)
            e0, c0, z0 = ema.iloc[i], cbot.iloc[i], basis_z.iloc[i]
            if pd.isna(e0) or pd.isna(c0) or pd.isna(z0):
                continue
            sgn = np.sign(z0)
            pnl = np.nan
            for t in range(1, 91):
                if i + t >= len(df):
                    break
                ej, cj, zj = ema.iloc[i + t], cbot.iloc[i + t], basis_z.iloc[i + t]
                if pd.isna(ej) or pd.isna(cj):
                    continue
                pnl = -1.0 * ((ej / e0 - 1) - (cj / c0 - 1)) * e0
                if not pd.isna(zj) and zj * sgn <= 0:
                    break
            if not pd.isna(pnl):
                pnls.append(pnl)
        if len(pnls) < 4:
            return {"n": len(pnls)}
        g = np.array(pnls)
        return {"n": len(g), "hit_rate": round(float((g > 0).mean()), 4),
                "mean_pnl": round(float(g.mean()), 2), "net_cost3": round(float((g - 6).sum()), 1)}

    high = basis_z > 1.0
    results = {}

    # (a) vraies features de courbe EMA (sous-échantillon ~332)
    if "ema_contango_flag" in df.columns and df["ema_contango_flag"].notna().sum() > 50:
        contango = df["ema_contango_flag"] == 1
        backward = df["ema_backwardation_flag"] == 1
        results["true_curve_subset"] = {
            "n_with_curve": int(df["ema_contango_flag"].notna().sum()),
            "high_basis_contango": _reversion_pnl(high & contango),
            "high_basis_backwardation": _reversion_pnl(high & backward),
        }

    # (b) proxy de tendance CBOT (price vs SMA252) comme contexte large
    if "curve_backwardation_proxy" in df.columns:
        prox = df["curve_backwardation_proxy"]
        med = prox.median()
        results["trend_proxy_context"] = {
            "note": "curve_backwardation_proxy = prix CBOT vs SMA252 (proxy de tendance, pas courbe pure)",
            "high_basis_proxy_above_median": _reversion_pnl(high & (prox > med)),
            "high_basis_proxy_below_median": _reversion_pnl(high & (prox <= med)),
        }

    out = {
        "version": "V16-02-CURVE-STRUCTURE",
        "hypothesis": "basis haut + contango (surprix) -> compression plus nette que basis haut + backwardation (tension durable)",
        "results": results,
        "data_limitation": "Vraies features de courbe EMA disponibles sur ~332 obs seulement (sous-échantillon).",
        "verdict": "CURVE_STRUCTURE_EXPLORATORY",
    }
    (V16_DIR / "curve_structure.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V16-03 — Drivers du basis (ce qui l'explique)
# ---------------------------------------------------------------------------

def run_basis_drivers(df: pd.DataFrame) -> dict[str, Any]:
    """Régression du basis sur les fondamentaux disponibles. R² + importance des drivers."""
    assert_no_holdout(df)
    if "ema_cbot_basis" not in df.columns:
        return {"version": "V16-03-BASIS-DRIVERS", "verdict": "MISSING_BASIS"}
    basis = df["ema_cbot_basis"]
    x = _fundamentals_frame(df)
    keep = basis.notna() & x.notna().all(axis=1)
    xk, bk = x.loc[keep], basis.loc[keep]
    if len(xk) < 300:
        return {"version": "V16-03-BASIS-DRIVERS", "verdict": "INSUFFICIENT", "n": int(len(xk))}
    means, stds = xk.mean(), xk.std().replace(0, 1)
    xs = (xk - means) / stds

    # R² OOF global
    r2s = []
    for tr, te in TimeSeriesSplit(n_splits=6).split(xs):
        if len(tr) < 100:
            continue
        reg = Ridge(alpha=1.0).fit(xs.iloc[tr], bk.iloc[tr])
        pred = reg.predict(xs.iloc[te])
        ss_res = float(np.sum((bk.iloc[te].values - pred) ** 2))
        ss_tot = float(np.sum((bk.iloc[te].values - bk.iloc[tr].mean()) ** 2))
        if ss_tot > 0:
            r2s.append(1 - ss_res / ss_tot)

    # coefficients standardisés (sur tout l'échantillon, descriptif)
    reg_full = Ridge(alpha=1.0).fit(xs, bk)
    coefs = {c: round(float(w), 3) for c, w in zip(xs.columns, reg_full.coef_, strict=False)}
    ranked = sorted(coefs.items(), key=lambda kv: -abs(kv[1]))

    out = {
        "version": "V16-03-BASIS-DRIVERS",
        "n_obs": int(len(xk)),
        "oof_r2_mean": round(float(np.mean(r2s)), 4) if r2s else None,
        "standardized_coefficients": coefs,
        "top_drivers": [k for k, _ in ranked[:4]],
        "available_fundamentals": FUNDAMENTALS,
        "missing_eu_data_waiting": [
            "EC MARS (rendement EU)", "FranceAgriMer (bilans)", "Eurostat COMEXT (imports/exports)",
            "Ukraine exports / FOB", "TTF gas EU", "fret / BDI", "météo EU pondérée",
        ],
        "interpretation": (
            "R² OOF mesure la part du basis expliquée par saison/FX/énergie. Les drivers EU spécifiques "
            "(MARS, FranceAgriMer, Ukraine, TTF) ne sont pas dans le dataset courant -> WAITING_DATA. "
            "Un R² faible signifie que le basis est surtout une prime locale non capturée par ces fondamentaux."
        ),
        "verdict": "BASIS_DRIVERS_DONE",
    }
    (V16_DIR / "basis_drivers.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
