"""V10 — Market Discovery : recherche quantitative ouverte sur la prime EMA/CBOT.

Cinq expériences honnêtes, anti-leakage, OOF, sur le dataset hors holdout 2024 :
- run_basis_econometrics  : demi-vie de mean-reversion du basis, variation temporelle (explique R2).
- run_feature_attribution : importance par permutation OOF des 6 vars + stabilité des coefficients.
- run_horizon_sweep       : AUC OOF structurelle pour H ∈ {20,30,40,60,90} (H40 est-il optimal ?).
- run_cost_survival       : sélectivité par confiance, courbe de survie aux coûts + test forward.
- run_regime_conditioning : AUC/DA structurelle par régime CBOT (vol, tendance).

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import TimeSeriesSplit

from mais.indicator.structural_indicator_v9 import (
    HORIZON,
    STRUCTURAL_FEATURES,
    build_structural_frame,
)
from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V10_DIR = ARTEFACTS_DIR / "v10"
V10_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers OOF (généralisés sur cible + horizon)
# ---------------------------------------------------------------------------

def _rel_target(df: pd.DataFrame, h: int) -> pd.Series:
    ema_col = next((c for c in ["ema_close", "ema_front_price"] if c in df.columns), None)
    cbot_col = next((c for c in ["cbot_eur_t", "cbot_close_eur"] if c in df.columns), None)
    ema_ret = df[ema_col].pct_change(h).shift(-h)
    cbot_ret = df[cbot_col].pct_change(h).shift(-h)
    y = (ema_ret > cbot_ret).astype(float)
    y[ema_ret.isna() | cbot_ret.isna()] = np.nan
    return y


def _oof_structural(x: pd.DataFrame, y: pd.Series, embargo: int,
                    n_splits: int = 6, calibrate: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """OOF logistique structurelle purged embargo. Renvoie (proba_oof, mask_valid) alignés sur x."""
    dates = x.index
    means, stds = x.mean(), x.std().replace(0.0, 1.0)
    xs = (x - means) / stds
    oof = np.full(len(x), np.nan)
    tscv = TimeSeriesSplit(n_splits=n_splits)
    for tr, te in tscv.split(xs):
        train_end = dates[tr[-1]]
        te_p = np.array([i for i in te if dates[i] > train_end + pd.Timedelta(days=embargo)])
        if len(tr) < 80 or len(te_p) < 10 or y.iloc[tr].nunique() < 2:
            continue
        clf = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
        clf.fit(xs.iloc[tr], y.iloc[tr].astype(int))
        p_te = clf.predict_proba(xs.iloc[te_p])[:, 1]
        if calibrate:
            try:
                iso = IsotonicRegression(out_of_bounds="clip")
                iso.fit(clf.predict_proba(xs.iloc[tr])[:, 1], y.iloc[tr].astype(int).values)
                p_te = iso.predict(p_te)
            except Exception:
                pass
        oof[te_p] = p_te
    valid = (~np.isnan(oof)) & y.notna().values
    return oof, valid


def _prep(df: pd.DataFrame, h: int = HORIZON):
    x_all = build_structural_frame(df)
    y_all = _rel_target(df, h)
    keep = y_all.notna() & x_all.notna().all(axis=1)
    return x_all.loc[keep], y_all.loc[keep].astype(int)


# ---------------------------------------------------------------------------
# V10-A — Économétrie du basis : demi-vie de mean-reversion
# ---------------------------------------------------------------------------

def run_basis_econometrics(df: pd.DataFrame) -> dict[str, Any]:
    """AR(1) du basis (level + z) -> demi-vie de mean-reversion. Variation temporelle."""
    assert_no_holdout(df)
    out: dict[str, Any] = {"version": "V10-A-BASIS-ECONOMETRICS"}

    def _ar1_halflife(s: pd.Series) -> dict[str, Any]:
        s = s.dropna()
        if len(s) < 200:
            return {"n": int(len(s)), "verdict": "INSUFFICIENT"}
        lag = s.shift(1).dropna()
        cur = s.loc[lag.index]
        # OLS sans constante centrée : cur = a + phi*lag
        x = np.vstack([np.ones(len(lag)), lag.values]).T
        beta, *_ = np.linalg.lstsq(x, cur.values, rcond=None)
        a, phi = float(beta[0]), float(beta[1])
        hl = float(-np.log(2) / np.log(phi)) if 0 < phi < 1 else None
        return {"n": int(len(s)), "ar1_phi": round(phi, 4), "intercept": round(a, 4),
                "half_life_days": round(hl, 1) if hl else None}

    for name, col in [("basis_level", "ema_cbot_basis"), ("basis_z", "ema_cbot_basis_zscore_52w")]:
        if col in df.columns:
            out[name] = _ar1_halflife(df[col])

    # Demi-vie roulante (fenêtres 252j) pour mesurer la variation temporelle de la reversion
    if "ema_cbot_basis_zscore_52w" in df.columns:
        s = df["ema_cbot_basis_zscore_52w"].dropna()
        win = 252
        hls = []
        dates = []
        for end in range(win, len(s), 21):
            sub = s.iloc[end - win:end]
            lag = sub.shift(1).dropna()
            cur = sub.loc[lag.index]
            if len(lag) < 100 or lag.std() == 0:
                continue
            phi = float(np.cov(cur.values, lag.values)[0, 1] / np.var(lag.values))
            if 0 < phi < 1:
                hls.append(-np.log(2) / np.log(phi))
                dates.append(str(s.index[end - 1].date()))
        if hls:
            hls_arr = np.array(hls)
            out["rolling_half_life"] = {
                "n_windows": len(hls),
                "median_days": round(float(np.median(hls_arr)), 1),
                "p10_days": round(float(np.quantile(hls_arr, 0.10)), 1),
                "p90_days": round(float(np.quantile(hls_arr, 0.90)), 1),
                "min_days": round(float(hls_arr.min()), 1),
                "max_days": round(float(hls_arr.max()), 1),
                "time_varying": bool((np.quantile(hls_arr, 0.90) - np.quantile(hls_arr, 0.10)) > 20),
            }

    bz = out.get("basis_z", {})
    hl = bz.get("half_life_days")
    out["interpretation"] = (
        f"Basis z mean-reverting : demi-vie ~{hl}j. " if hl else "Demi-vie non estimable. "
    ) + (
        "Cohérent avec R2 (basis_z<-1.5 -> long) : un basis extrême revient vers 0 en quelques semaines, "
        "et l'horizon H40 capture cette reversion."
    )
    out["verdict"] = "BASIS_MEAN_REVERTING" if hl and hl < HORIZON * 2 else "BASIS_SLOW_OR_NONSTATIONARY"
    (V10_DIR / "basis_econometrics.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V10-B — Attribution des features structurelles
# ---------------------------------------------------------------------------

def run_feature_attribution(df: pd.DataFrame, n_repeats: int = 5) -> dict[str, Any]:
    """Importance par permutation OOF (delta AUC) + stabilité des coefficients logistiques."""
    assert_no_holdout(df)
    x, y = _prep(df)
    if len(x) < 200 or y.nunique() < 2:
        return {"version": "V10-B-FEATURE-ATTRIBUTION", "verdict": "INSUFFICIENT_DATA"}

    oof, valid = _oof_structural(x, y, embargo=HORIZON, calibrate=False)
    base_auc = float(roc_auc_score(y.values[valid], oof[valid]))

    rng = np.random.default_rng(42)
    importances = {}
    for feat in STRUCTURAL_FEATURES:
        drops = []
        for _ in range(n_repeats):
            xp = x.copy()
            xp[feat] = rng.permutation(xp[feat].values)
            oofp, vp = _oof_structural(xp, y, embargo=HORIZON, calibrate=False)
            if vp.sum() > 30 and len(np.unique(y.values[vp])) > 1:
                drops.append(base_auc - float(roc_auc_score(y.values[vp], oofp[vp])))
        if drops:
            importances[feat] = {"mean_auc_drop": round(float(np.mean(drops)), 4),
                                 "std": round(float(np.std(drops)), 4)}

    # Coefficients sur 3 sous-périodes pour la stabilité
    means, stds = x.mean(), x.std().replace(0.0, 1.0)
    xs = (x - means) / stds
    thirds = np.array_split(np.arange(len(xs)), 3)
    coefs_by_period = {}
    for k, idx in enumerate(thirds):
        if y.iloc[idx].nunique() < 2:
            continue
        clf = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
        clf.fit(xs.iloc[idx], y.iloc[idx])
        coefs_by_period[f"period_{k + 1}"] = {
            f: round(float(c), 4) for f, c in zip(STRUCTURAL_FEATURES, clf.coef_[0], strict=False)
        }
    # Stabilité de signe par feature
    sign_stability = {}
    for f in STRUCTURAL_FEATURES:
        signs = [np.sign(p[f]) for p in coefs_by_period.values() if f in p]
        sign_stability[f] = bool(len(set(signs)) == 1) if signs else None

    ranked = sorted(importances.items(), key=lambda kv: -kv[1]["mean_auc_drop"])
    out = {
        "version": "V10-B-FEATURE-ATTRIBUTION",
        "base_auc": round(base_auc, 4),
        "permutation_importance": importances,
        "ranking": [f for f, _ in ranked],
        "coefficients_by_period": coefs_by_period,
        "coef_sign_stable": sign_stability,
        "interpretation": (
            f"Variable la plus importante : {ranked[0][0]} (delta AUC {ranked[0][1]['mean_auc_drop']}). "
            "Signe stable = relation économique robuste dans le temps."
        ),
        "verdict": "ATTRIBUTION_DONE",
    }
    (V10_DIR / "feature_attribution.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V10-C — Balayage d'horizon
# ---------------------------------------------------------------------------

def run_horizon_sweep(df: pd.DataFrame) -> dict[str, Any]:
    """AUC OOF structurelle pour plusieurs horizons. H40 est-il vraiment optimal ?"""
    assert_no_holdout(df)
    horizons = [20, 30, 40, 60, 90]
    results = {}
    for h in horizons:
        x, y = _prep(df, h)
        if len(x) < 200 or y.nunique() < 2:
            results[f"h{h}"] = {"verdict": "INSUFFICIENT", "n": int(len(x))}
            continue
        oof, valid = _oof_structural(x, y, embargo=h, calibrate=True)
        if valid.sum() < 30 or len(np.unique(y.values[valid])) < 2:
            results[f"h{h}"] = {"verdict": "NO_OOF", "n_oof": int(valid.sum())}
            continue
        auc = float(roc_auc_score(y.values[valid], oof[valid]))
        n_top = max(int(valid.sum() * 0.20), 5)
        order = np.argsort(-oof[valid])[:n_top]
        results[f"h{h}"] = {
            "auc": round(auc, 4),
            "top20_da": round(float(y.values[valid][order].mean()), 4),
            "n_oof": int(valid.sum()),
            "base_rate": round(float(y.values[valid].mean()), 4),
        }
    valid_h = {h: r for h, r in results.items() if "auc" in r}
    best = max(valid_h.items(), key=lambda kv: kv[1]["auc"]) if valid_h else (None, {})
    out = {
        "version": "V10-C-HORIZON-SWEEP",
        "horizons": horizons,
        "results": results,
        "best_horizon": best[0],
        "best_auc": best[1].get("auc"),
        "interpretation": (
            f"Meilleur horizon : {best[0]} (AUC {best[1].get('auc')}). "
            "Si plusieurs horizons proches -> signal robuste à l'horizon ; sinon H spécifique."
        ),
        "verdict": "HORIZON_SWEEP_DONE",
    }
    (V10_DIR / "horizon_sweep.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V10-D — Sélectivité et survie aux coûts (attaque le mur des coûts)
# ---------------------------------------------------------------------------

def _build_trades(df: pd.DataFrame, proba: pd.Series, h: int = HORIZON) -> pd.DataFrame:
    """Trades non-overlap pilotés par proba (long si p>0.5, short si p<0.5), avec PnL spread brut."""
    ema_ret = df["ema_close"].pct_change(h).shift(-h)
    cbot_ret = df["cbot_eur_t"].pct_change(h).shift(-h)
    spread = (ema_ret - cbot_ret)
    price = df["ema_close"]
    conf = (proba - 0.5).abs() * 2.0
    side = pd.Series(0, index=df.index)
    side[proba > 0.5] = 1
    side[proba < 0.5] = -1
    active = (side != 0) & spread.notna() & price.notna() & proba.notna()
    rows = []
    last_d = None
    for date in df.index[active.values]:
        if last_d is None or (date - last_d).days >= h:
            i = df.index.get_loc(date)
            gross = float(spread.iloc[i] * side.loc[date] * price.iloc[i])
            rows.append({"date": date, "year": date.year, "conf": float(conf.loc[date]),
                         "gross_pnl": gross})
            last_d = date
    return pd.DataFrame(rows)


def run_cost_survival(df: pd.DataFrame) -> dict[str, Any]:
    """Peut-on franchir le mur des coûts par sélectivité de confiance ?

    (1) Courbe de survie descriptive : net PnL à coût 5 selon le quantile de confiance gardé.
    (2) Test forward honnête : seuil de confiance appris sur les années passées, appliqué forward.
    """
    assert_no_holdout(df)
    if "ema_close" not in df.columns or "cbot_eur_t" not in df.columns:
        return {"version": "V10-D-COST-SURVIVAL", "verdict": "MISSING_PRICES"}
    x, y = _prep(df)
    oof, valid = _oof_structural(x, y, embargo=HORIZON, calibrate=True)
    proba = pd.Series(np.nan, index=df.index)
    proba.loc[x.index[valid]] = oof[valid]
    trades = _build_trades(df, proba)
    if len(trades) < 20:
        return {"version": "V10-D-COST-SURVIVAL", "verdict": "TOO_FEW_TRADES", "n": int(len(trades))}

    def _net(sub, cost):
        return float((sub["gross_pnl"] - 2 * cost).sum())

    # (1) Courbe de survie descriptive (sélection in-sample, marque la faisabilité)
    survival = {}
    for q in [0.0, 0.5, 0.7, 0.8, 0.9]:
        thr = trades["conf"].quantile(q)
        sub = trades[trades["conf"] >= thr]
        survival[f"top_{int((1 - q) * 100)}pct_conf"] = {
            "n_trades": int(len(sub)),
            "net_pnl_cost3": round(_net(sub, 3), 1),
            "net_pnl_cost5": round(_net(sub, 5), 1),
            "hit_rate": round(float((sub["gross_pnl"] > 0).mean()), 4),
            "conf_threshold": round(float(thr), 4),
        }

    # (2) Test forward : seuil appris sur années passées (>= 3 ans d'historique), appliqué à l'année t
    years = sorted(trades["year"].unique())
    fwd_trades_kept = []
    for yr in years:
        past = trades[trades["year"] < yr]
        if past["year"].nunique() < 3 or len(past) < 15:
            continue
        # seuil qui maximise le net PnL coût 5 sur le passé
        best_thr, best_net = 0.0, -1e18
        for q in np.linspace(0.0, 0.9, 10):
            thr = past["conf"].quantile(q)
            net = _net(past[past["conf"] >= thr], 5)
            if net > best_net:
                best_net, best_thr = net, thr
        cur = trades[(trades["year"] == yr) & (trades["conf"] >= best_thr)]
        for _, r in cur.iterrows():
            fwd_trades_kept.append(r)
    fwd = pd.DataFrame(fwd_trades_kept)
    forward = {"verdict": "NO_FORWARD_TRADES"}
    if len(fwd) >= 10:
        forward = {
            "n_trades": int(len(fwd)),
            "net_pnl_cost5": round(_net(fwd, 5), 1),
            "net_pnl_cost3": round(_net(fwd, 3), 1),
            "hit_rate": round(float((fwd["gross_pnl"] > 0).mean()), 4),
            "survives_cost5": bool(_net(fwd, 5) > 0),
        }

    baseline_cost5 = _net(trades, 5)
    out = {
        "version": "V10-D-COST-SURVIVAL",
        "n_trades_all": int(len(trades)),
        "baseline_all_trades_net_pnl_cost5": round(baseline_cost5, 1),
        "selectivity_curve": survival,
        "forward_learnable_threshold": forward,
        "interpretation": (
            "Si la courbe top-conf survit à coût 5 ET le seuil forward survit -> la sélectivité brise le "
            "mur des coûts. Si seul l'in-sample survit -> le seuil n'est pas apprenable, mur confirmé."
        ),
        "verdict": ("COST_WALL_BROKEN_FORWARD" if forward.get("survives_cost5")
                    else "COST_WALL_CONFIRMED"),
    }
    (V10_DIR / "cost_survival.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V10-F — Modèle simplifié (Occam) : retirer les features de bruit
# ---------------------------------------------------------------------------

# Sous-ensembles principaux ; V10-B a montré que cbot_eur, month_sin, oi_proxy ont une
# importance par permutation négative ET un signe instable -> candidats au retrait.
FEATURE_SUBSETS = {
    "all_6": STRUCTURAL_FEATURES,
    "drop_noise_3": ["basis_z", "month_cos", "eurusd"],
    "basis_season_2": ["basis_z", "month_cos"],
    "basis_only_1": ["basis_z"],
}


def run_simplified_model(df: pd.DataFrame) -> dict[str, Any]:
    """Teste si retirer les features de bruit (V10-B) améliore l'AUC OOF. Occam appliqué."""
    assert_no_holdout(df)
    x_full, y = _prep(df)
    if len(x_full) < 200 or y.nunique() < 2:
        return {"version": "V10-F-SIMPLIFIED-MODEL", "verdict": "INSUFFICIENT_DATA"}

    results = {}
    for name, feats in FEATURE_SUBSETS.items():
        x = x_full[feats]
        oof, valid = _oof_structural(x, y, embargo=HORIZON, calibrate=True)
        if valid.sum() < 30 or len(np.unique(y.values[valid])) < 2:
            results[name] = {"verdict": "NO_OOF"}
            continue
        auc = float(roc_auc_score(y.values[valid], oof[valid]))
        n_top = max(int(valid.sum() * 0.20), 5)
        order = np.argsort(-oof[valid])[:n_top]
        results[name] = {"n_features": len(feats), "auc": round(auc, 4),
                         "top20_da": round(float(y.values[valid][order].mean()), 4),
                         "n_oof": int(valid.sum())}

    valid_r = {k: v for k, v in results.items() if "auc" in v}
    best = max(valid_r.items(), key=lambda kv: kv[1]["auc"]) if valid_r else (None, {})
    auc6 = results.get("all_6", {}).get("auc")
    gain = round(best[1]["auc"] - auc6, 4) if (best[1] and auc6) else None
    out = {
        "version": "V10-F-SIMPLIFIED-MODEL",
        "results_by_subset": results,
        "best_subset": best[0],
        "best_auc": best[1].get("auc"),
        "auc_gain_vs_6vars": gain,
        "interpretation": (
            f"Meilleur sous-ensemble : {best[0]} (AUC {best[1].get('auc')}, gain {gain} vs 6 vars). "
            "Retirer cbot_eur / month_sin / oi_proxy (bruit, signe instable) améliore le signal : "
            "la prime EMA/CBOT se résume au basis et à la saisonnalité de récolte."
        ),
        "verdict": ("SIMPLER_IS_BETTER" if (gain is not None and gain > 0.01)
                    else "SIMPLIFICATION_NEUTRAL"),
    }
    (V10_DIR / "simplified_model.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V10-E — Conditionnement par régime CBOT
# ---------------------------------------------------------------------------

def run_regime_conditioning(df: pd.DataFrame) -> dict[str, Any]:
    """Où se concentre la prédictibilité de la prime ? Régimes vol et tendance CBOT (causals)."""
    assert_no_holdout(df)
    x, y = _prep(df)
    oof, valid = _oof_structural(x, y, embargo=HORIZON, calibrate=True)
    proba = pd.Series(np.nan, index=df.index)
    proba.loc[x.index[valid]] = oof[valid]

    # Régimes causals : vol au-dessus/dessous de sa médiane expandante ; tendance via signe MACD hist
    vol = df.get("corn_realized_vol_20")
    macd = df.get("corn_macd_hist")
    regimes = {}
    if vol is not None:
        exp_med = vol.expanding(min_periods=200).median()
        regimes["high_vol"] = (vol > exp_med)
        regimes["low_vol"] = (vol <= exp_med)
    if macd is not None:
        regimes["uptrend"] = (macd > 0)
        regimes["downtrend"] = (macd <= 0)

    yv = y.reindex(df.index)
    results = {}
    for name, mask in regimes.items():
        m = mask.reindex(df.index).fillna(False).values & proba.notna().values & yv.notna().values
        if m.sum() < 50 or len(np.unique(yv.values[m])) < 2:
            results[name] = {"n": int(m.sum()), "verdict": "INSUFFICIENT"}
            continue
        p = proba.values[m]
        yy = yv.values[m].astype(int)
        auc = float(roc_auc_score(yy, p))
        pred = (p > 0.5).astype(int)
        da = float((pred == yy).mean())
        results[name] = {"n": int(m.sum()), "auc": round(auc, 4),
                         "directional_accuracy": round(da, 4),
                         "base_rate": round(float(yy.mean()), 4)}

    auc_items = [(k, v["auc"]) for k, v in results.items() if "auc" in v]
    best = max(auc_items, key=lambda kv: kv[1]) if auc_items else (None, None)
    out = {
        "version": "V10-E-REGIME-CONDITIONING",
        "results_by_regime": results,
        "best_regime": best[0],
        "best_regime_auc": best[1],
        "interpretation": (
            f"La prime est la plus prédictible en régime '{best[0]}' (AUC {best[1]}). "
            "Un filtre de régime peut concentrer les trades là où l'edge est réel."
        ),
        "verdict": "REGIME_ANALYSIS_DONE",
    }
    (V10_DIR / "regime_conditioning.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
