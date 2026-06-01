"""V9 — Indicateur structurel hybride de la prime EMA/CBOT.

Architecture issue de la synthèse V8 (docs/V8_DEEP_DIVE_RESULTATS.md §7) :
- Cœur : régression logistique structurelle 6 variables, OOF purged embargo, calibration
  Isotonic apprise sur train uniquement.
- Couche saisonnière : jul_aug direct, apr_jun inversé, jan_mar modéré, sep_nov + dec abstention.
- Couche règles mean-reversion : R2 (basis_z < -1.5 -> LONG), R5 (basis_z > 1.5 x jan-mar -> SHORT).
- Vetoes : data quality, liquidité OI, proximité WASDE, roll-risk proxy.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais utilisé ici.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V9_DIR = ARTEFACTS_DIR / "v9"
V9_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "y_rel_outperform_h40"
HORIZON = 40
STRUCTURAL_FEATURES = ["cbot_eur", "basis_z", "eurusd", "month_sin", "month_cos", "oi_proxy"]

# Saisons : labels descriptifs uniquement.
#
# IMPORTANT (correction V9) : l'hypothèse V8-SEASONAL-DEEP d'INVERSION apr-juin et
# d'ABSTENTION sep-déc a été FALSIFIÉE par l'OOF structurel V9. Décomposition mesurée
# sur y_rel_outperform_h40 (oof_cal, deadband) :
#   - cœur direct apr_jun DA = 0.707 (meilleure saison, NON inversée)
#   - cœur + inversion apr-juin -> DA chute à 0.476 (destruction du signal)
#   - cœur sep_nov DA = 0.63, déc DA = 0.71 -> l'abstention en bloc n'est pas justifiée
# Conclusion : on garde le cœur direct sur toutes les saisons. La saison sert seulement de
# label de driver et de marqueur de poche haute-confiance (jul_aug). Pas de flip, pas
# d'abstention saisonnière en bloc. Cf. docs/V9_STRUCTURAL_INDICATOR.md.
SEASON_HIGH_CONFIDENCE = (7, 8)  # jul_aug : poche connue (V8 top20 DA 0.89) -> label seulement
SEASON_RULE_R5 = (1, 2, 3)       # jan_mar : fenêtre de la règle tactique R5

# Mois de roll proxy : mois précédant les échéances actives EMA H/M/Q/X (Mar/Jun/Aug/Nov).
ROLL_MONTHS_PROXY = (2, 5, 7, 10)

ABSTAIN_MARGIN = 0.06   # bande morte autour de 0.5 sur la proba ajustée
RULE_CONFIDENCE = 0.80  # confiance attribuée quand une règle tactique se déclenche


def _ensure_rel_target(df: pd.DataFrame) -> pd.DataFrame:
    """Construit y_rel_outperform_h40 si absente (EMA surperforme CBOT sur 40j)."""
    out = df.copy()
    if TARGET in out.columns:
        return out
    ema_col = next((c for c in ["ema_close", "ema_front_price"] if c in out.columns), None)
    cbot_col = next((c for c in ["cbot_eur_t", "cbot_close_eur"] if c in out.columns), None)
    if ema_col and cbot_col:
        ema_ret = out[ema_col].pct_change(HORIZON).shift(-HORIZON)
        cbot_ret = out[cbot_col].pct_change(HORIZON).shift(-HORIZON)
        out[TARGET] = (ema_ret > cbot_ret).astype(float)
        out.loc[ema_ret.isna() | cbot_ret.isna(), TARGET] = np.nan
    return out


# Sous-ensemble recommandé après V10-F : retirer cbot_eur / month_sin / oi_proxy (bruit,
# signe instable). Le modèle 2 vars basis_z + month_cos atteint AUC 0.694 vs 0.656 (6 vars).
SIMPLIFIED_FEATURES = ["basis_z", "month_cos"]


def build_structural_frame(df: pd.DataFrame, features: list[str] | None = None) -> pd.DataFrame:
    """Variables structurelles, indexées par date. `features` restreint le sous-ensemble."""
    idx = df.index
    out = pd.DataFrame(index=idx)
    out["cbot_eur"] = df.get("cbot_eur_t", pd.Series(np.nan, index=idx))
    out["basis_z"] = df.get("ema_cbot_basis_zscore_52w", pd.Series(np.nan, index=idx))
    out["eurusd"] = df.get("eurusd", pd.Series(np.nan, index=idx))
    out["month_sin"] = np.sin(2 * np.pi * idx.month / 12)
    out["month_cos"] = np.cos(2 * np.pi * idx.month / 12)
    out["oi_proxy"] = df.get("ema_oi_total", pd.Series(np.nan, index=idx)).fillna(0.0)
    if features is not None:
        out = out[features]
    return out


def _ece(y_true: np.ndarray, proba: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.digitize(proba, bins[1:-1])
    ece = 0.0
    n = len(proba)
    for b in range(n_bins):
        mask = idx == b
        if mask.sum() == 0:
            continue
        conf = proba[mask].mean()
        acc = y_true[mask].mean()
        ece += (mask.sum() / n) * abs(acc - conf)
    return float(ece)


def fit_oof_structural(df: pd.DataFrame, embargo_days: int = HORIZON,
                       n_splits: int = 6, features: list[str] | None = None) -> dict[str, Any]:
    """OOF de la logistique structurelle + calibration Isotonic train-only.

    Renvoie les probas brutes et calibrées alignées sur l'index complet (NaN hors OOF).
    `features` restreint le sous-ensemble de variables (défaut : les 6).
    """
    df = _ensure_rel_target(df)
    x_all = build_structural_frame(df, features)
    y_all = df[TARGET]

    valid = y_all.notna() & x_all.notna().all(axis=1)
    x = x_all.loc[valid]
    y = y_all.loc[valid].astype(int)
    dates = x.index

    oof_raw = pd.Series(np.nan, index=df.index)
    oof_cal = pd.Series(np.nan, index=df.index)

    if len(x) < 200 or y.nunique() < 2:
        return {
            "verdict": "INSUFFICIENT_DATA", "n": int(len(x)),
            "oof_raw": oof_raw, "oof_cal": oof_cal,
        }

    means = x.mean()
    stds = x.std().replace(0.0, 1.0)
    x_std = (x - means) / stds

    tscv = TimeSeriesSplit(n_splits=n_splits)
    raw_vals = np.full(len(x), np.nan)
    cal_vals = np.full(len(x), np.nan)
    n_folds = 0
    for tr, te in tscv.split(x_std):
        train_end = dates[tr[-1]]
        te_purged = np.array(
            [i for i in te if dates[i] > train_end + pd.Timedelta(days=embargo_days)]
        )
        if len(tr) < 80 or len(te_purged) < 10 or y.iloc[tr].nunique() < 2:
            continue
        clf = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
        clf.fit(x_std.iloc[tr], y.iloc[tr])
        p_tr = clf.predict_proba(x_std.iloc[tr])[:, 1]
        p_te = clf.predict_proba(x_std.iloc[te_purged])[:, 1]
        raw_vals[te_purged] = p_te
        # Calibration Isotonic apprise sur le train uniquement
        try:
            iso = IsotonicRegression(out_of_bounds="clip")
            iso.fit(p_tr, y.iloc[tr].values)
            cal_vals[te_purged] = iso.predict(p_te)
        except Exception:
            cal_vals[te_purged] = p_te
        n_folds += 1

    have = ~np.isnan(raw_vals)
    oof_raw.loc[dates[have]] = raw_vals[have]
    oof_cal.loc[dates[have]] = cal_vals[have]

    yv = y.values[have]
    metrics: dict[str, Any] = {"n_oof": int(have.sum()), "n_folds": n_folds}
    if have.sum() >= 30 and len(np.unique(yv)) > 1:
        metrics["auc_raw"] = round(float(roc_auc_score(yv, raw_vals[have])), 4)
        metrics["auc_cal"] = round(float(roc_auc_score(yv, cal_vals[have])), 4)
        metrics["balanced_accuracy"] = round(
            float(balanced_accuracy_score(yv, (cal_vals[have] > 0.5).astype(int))), 4
        )
        metrics["brier_raw"] = round(float(brier_score_loss(yv, raw_vals[have])), 4)
        metrics["brier_cal"] = round(float(brier_score_loss(yv, cal_vals[have])), 4)
        metrics["ece_raw"] = round(_ece(yv, raw_vals[have]), 4)
        metrics["ece_cal"] = round(_ece(yv, cal_vals[have]), 4)
        n_top = max(int(have.sum() * 0.20), 5)
        order = np.argsort(-cal_vals[have])[:n_top]
        metrics["top20_da"] = round(float(yv[order].mean()), 4)

    return {"verdict": "OK", "metrics": metrics, "oof_raw": oof_raw, "oof_cal": oof_cal}


def _veto_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Drapeaux veto par date, depuis les colonnes réelles disponibles."""
    idx = df.index
    v = pd.DataFrame(index=idx)
    dq = df.get("ema_data_availability_score", pd.Series(np.nan, index=idx))
    v["veto_data_quality"] = dq.fillna(0.0) < 0.4

    oi = df.get("ema_oi_total", pd.Series(np.nan, index=idx))
    oi_floor = oi[oi > 0].quantile(0.10) if (oi > 0).any() else 0.0
    v["veto_liquidity"] = oi.fillna(0.0) < oi_floor

    dtw = df.get("days_to_next_wasde", pd.Series(np.nan, index=idx))
    v["veto_event_wasde"] = dtw.fillna(99) <= 2

    v["veto_roll_proxy"] = pd.Series(idx.month, index=idx).isin(ROLL_MONTHS_PROXY).values
    return v


def compute_signals(df: pd.DataFrame, oof_cal: pd.Series) -> pd.DataFrame:
    """Produit la sortie indicateur par date : signal, confidence, drivers, vetoes."""
    df = _ensure_rel_target(df)
    idx = df.index
    months = idx.month
    basis_z = df.get("ema_cbot_basis_zscore_52w", pd.Series(np.nan, index=idx))
    vetoes = _veto_frame(df)

    rows = []
    for i, date in enumerate(idx):
        m = int(months[i])
        p = oof_cal.iloc[i]
        bz = basis_z.iloc[i]
        veto_reasons = [c.replace("veto_", "") for c in vetoes.columns if bool(vetoes.iloc[i][c])]
        drivers: list[str] = []

        signal = "ABSTAIN"
        confidence = 0.0

        # 1. Vetoes durs -> abstention immédiate
        if veto_reasons:
            rows.append((date, signal, confidence, drivers, veto_reasons))
            continue

        # 2. Règles tactiques mean-reversion (rares, prioritaires sur le cœur)
        if not np.isnan(bz) and bz < -1.5:
            signal, confidence = "LONG_PREMIUM", RULE_CONFIDENCE
            drivers.append("R2_basis_z_lt_-1.5_mean_reversion")
            rows.append((date, signal, confidence, drivers, veto_reasons))
            continue
        if not np.isnan(bz) and bz > 1.5 and m in SEASON_RULE_R5:
            signal, confidence = "SHORT_PREMIUM", RULE_CONFIDENCE
            drivers.append("R5_basis_z_gt_1.5_jan_mar")
            rows.append((date, signal, confidence, drivers, veto_reasons))
            continue

        # 3. Cœur structurel DIRECT (pas d'inversion saisonnière : falsifiée OOF)
        if np.isnan(p):
            rows.append((date, "ABSTAIN", 0.0, drivers + ["no_model_proba"], veto_reasons))
            continue

        if p > 0.5 + ABSTAIN_MARGIN:
            signal = "LONG_PREMIUM"
        elif p < 0.5 - ABSTAIN_MARGIN:
            signal = "SHORT_PREMIUM"
        else:
            signal = "ABSTAIN"
            drivers.append("proba_in_deadband")
        confidence = round(float(abs(p - 0.5) * 2.0), 4)
        if m in SEASON_HIGH_CONFIDENCE:
            drivers.append("season_jul_aug_high_confidence_pocket")
        drivers.append(f"structural_p={round(float(p), 3)}")
        rows.append((date, signal, confidence, drivers, veto_reasons))

    out = pd.DataFrame(
        rows, columns=["date", "signal", "confidence", "drivers", "veto_reasons"]
    ).set_index("date")
    out["horizon"] = HORIZON
    out["statut"] = "RESEARCH_ONLY_NOT_TRADING"
    return out


def _evaluate_signals(df: pd.DataFrame, signals: pd.DataFrame) -> dict[str, Any]:
    """Accuracy directionnelle des signaux non-abstenus vs y_rel_outperform_h40."""
    df = _ensure_rel_target(df)
    y = df[TARGET]
    pred_long = signals["signal"] == "LONG_PREMIUM"
    pred_short = signals["signal"] == "SHORT_PREMIUM"
    active = (pred_long | pred_short) & y.notna()
    n_active = int(active.sum())
    out: dict[str, Any] = {
        "n_total": int(len(signals)),
        "n_active": n_active,
        "coverage": round(n_active / len(signals), 4) if len(signals) else 0.0,
        "n_long": int((pred_long & y.notna()).sum()),
        "n_short": int((pred_short & y.notna()).sum()),
        "n_abstain": int((signals["signal"] == "ABSTAIN").sum()),
    }
    if n_active >= 20:
        correct = np.where(pred_long[active], y[active] > 0.5, y[active] <= 0.5)
        out["directional_accuracy"] = round(float(correct.mean()), 4)
        # Accuracy par tier de confiance
        conf = signals.loc[active, "confidence"].values
        tiers = {"low_<0.3": conf < 0.3, "mid_0.3-0.6": (conf >= 0.3) & (conf < 0.6),
                 "high_>=0.6": conf >= 0.6}
        by_tier = {}
        for name, mask in tiers.items():
            if mask.sum() >= 10:
                by_tier[name] = {"n": int(mask.sum()),
                                 "accuracy": round(float(correct[mask].mean()), 4)}
        out["accuracy_by_confidence_tier"] = by_tier
    return out


def run_indicator_v9(df: pd.DataFrame, features: list[str] | None = SIMPLIFIED_FEATURES) -> dict[str, Any]:
    """V9-IND-01 — construit l'indicateur complet et écrit l'artefact.

    Défaut promu en V11 : modèle simplifié 2 variables (basis_z + month_cos), meilleur partout
    (AUC 0.694, ECE 0.059, rentable à coût 3) — cf. docs/V11_DISCIPLINED_PROGRAM.md. Passer
    `features=STRUCTURAL_FEATURES` pour l'ancien modèle 6 variables.
    """
    assert_no_holdout(df)
    fit = fit_oof_structural(df, features=features)
    if fit["verdict"] != "OK":
        out = {"version": "V9-IND-01", "verdict": fit["verdict"], "n": fit.get("n")}
        (V9_DIR / "structural_indicator_v9.json").write_text(
            json.dumps(out, indent=2, default=str), encoding="utf-8")
        return out

    signals = compute_signals(df, fit["oof_cal"])
    evaluation = _evaluate_signals(df, signals)

    # Snapshot exploitable le plus récent (signal non-abstain le plus récent)
    actionable = signals[signals["signal"] != "ABSTAIN"]
    snapshot = None
    if len(actionable):
        last = actionable.iloc[-1]
        snapshot = {
            "date": str(actionable.index[-1].date()),
            "signal": last["signal"],
            "confidence": float(last["confidence"]),
            "drivers": list(last["drivers"]),
            "horizon": int(last["horizon"]),
        }

    out = {
        "version": "V9-IND-01",
        "target": TARGET,
        "horizon": HORIZON,
        "model_features": features if features is not None else STRUCTURAL_FEATURES,
        "core_metrics": fit["metrics"],
        "signal_distribution": signals["signal"].value_counts().to_dict(),
        "evaluation": evaluation,
        "latest_actionable_snapshot": snapshot,
        "verdict": "RESEARCH_ONLY_NOT_TRADING",
        "calibration_note": (
            "Isotonic train-only ; ECE cal vs raw dans core_metrics."
        ),
    }
    (V9_DIR / "structural_indicator_v9.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_loyo(df: pd.DataFrame, features: list[str] | None = None) -> dict[str, Any]:
    """V9-IND-02 — leave-one-year-out sur le cœur structurel."""
    assert_no_holdout(df)
    df = _ensure_rel_target(df)
    x_all = build_structural_frame(df, features)
    y_all = df[TARGET]
    valid = y_all.notna() & x_all.notna().all(axis=1)
    x = x_all.loc[valid]
    y = y_all.loc[valid].astype(int)
    years = sorted(set(x.index.year))

    per_year = {}
    aucs = []
    for yr in years:
        test_mask = x.index.year == yr
        # Embargo : retire du train les lignes à moins de HORIZON jours de l'année test
        gap = pd.Timedelta(days=HORIZON)
        ystart, yend = pd.Timestamp(f"{yr}-01-01"), pd.Timestamp(f"{yr}-12-31")
        train_mask = ((x.index < ystart - gap) | (x.index > yend + gap))
        if test_mask.sum() < 20 or train_mask.sum() < 100 or y[train_mask].nunique() < 2:
            continue
        means = x[train_mask].mean()
        stds = x[train_mask].std().replace(0.0, 1.0)
        x_tr = (x[train_mask] - means) / stds
        x_te = (x[test_mask] - means) / stds
        clf = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
        clf.fit(x_tr, y[train_mask])
        p = clf.predict_proba(x_te)[:, 1]
        yt = y[test_mask].values
        rec: dict[str, Any] = {"n": int(test_mask.sum())}
        if len(np.unique(yt)) > 1:
            rec["auc"] = round(float(roc_auc_score(yt, p)), 4)
            rec["da"] = round(float(((p > 0.5).astype(int) == yt).mean()), 4)
            aucs.append(rec["auc"])
        per_year[str(yr)] = rec

    summary: dict[str, Any] = {"n_years_tested": len(per_year)}
    if aucs:
        summary.update({
            "mean_auc": round(float(np.mean(aucs)), 4),
            "std_auc": round(float(np.std(aucs)), 4),
            "min_auc": round(float(np.min(aucs)), 4),
            "max_auc": round(float(np.max(aucs)), 4),
            "n_years_auc_gt_055": int(sum(a > 0.55 for a in aucs)),
            "share_years_auc_gt_055": round(float(np.mean([a > 0.55 for a in aucs])), 4),
        })
        mean_auc = summary["mean_auc"]
        share = summary["share_years_auc_gt_055"]
        if mean_auc >= 0.58 and share >= 0.6:
            verdict = "LOYO_STABLE"
        elif mean_auc >= 0.55:
            verdict = "LOYO_FRAGILE"
        else:
            verdict = "LOYO_NO_GO"
    else:
        verdict = "INSUFFICIENT_DATA"

    out = {"version": "V9-IND-02", "per_year": per_year, "summary": summary, "verdict": verdict}
    (V9_DIR / "loyo_v9.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_backtest_v4(df: pd.DataFrame, signals: pd.DataFrame | None = None) -> dict[str, Any]:
    """V9-IND-03 — backtest spread EMA/CBOT H40 piloté par les signaux V9, coûts stressés."""
    assert_no_holdout(df)
    df = _ensure_rel_target(df)
    if "ema_close" not in df.columns or "cbot_eur_t" not in df.columns:
        return {"version": "V9-IND-03", "verdict": "MISSING_PRICES"}
    if signals is None:
        fit = fit_oof_structural(df)
        if fit["verdict"] != "OK":
            return {"version": "V9-IND-03", "verdict": fit["verdict"]}
        signals = compute_signals(df, fit["oof_cal"])

    ema_ret = df["ema_close"].pct_change(HORIZON).shift(-HORIZON)
    cbot_ret = df["cbot_eur_t"].pct_change(HORIZON).shift(-HORIZON)
    spread_ret = (ema_ret - cbot_ret)
    prices = df["ema_close"]

    sig = signals["signal"].reindex(df.index).fillna("ABSTAIN")
    side = pd.Series(0, index=df.index)
    side[sig == "LONG_PREMIUM"] = 1
    side[sig == "SHORT_PREMIUM"] = -1

    active = (side != 0) & spread_ret.notna() & prices.notna()
    idx_pos = np.where(active.values)[0]
    dates_arr = df.index.values

    # Non-overlap strict : un trade tous les >= HORIZON jours
    kept = []
    last_d = None
    for i in idx_pos:
        d = pd.Timestamp(dates_arr[i])
        if last_d is None or (d - last_d).days >= HORIZON:
            kept.append(i)
            last_d = d
    kept = np.array(kept, dtype=int)

    if len(kept) == 0:
        out = {"version": "V9-IND-03", "verdict": "NO_TRADES", "n_trades": 0}
        (V9_DIR / "backtest_v4.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
        return out

    ret = spread_ret.values[kept] * side.values[kept]
    gross_pnl = ret * prices.values[kept]            # €/t par trade, brut
    trade_years = pd.DatetimeIndex(dates_arr[kept]).year

    costs = [0, 1, 2, 3, 5, 8]
    by_cost = {}
    for c in costs:
        net = gross_pnl - 2 * c  # 2 legs
        equity = np.cumsum(net)
        peak = np.maximum.accumulate(equity)
        max_dd = float(np.min(equity - peak)) if len(equity) else 0.0
        gains = net[net > 0].sum()
        losses = -net[net < 0].sum()
        pf = float(gains / losses) if losses > 0 else float("inf")
        yearly = pd.Series(net, index=trade_years).groupby(level=0).sum()
        by_cost[f"cost_{c}"] = {
            "pnl_total_eur_t": round(float(net.sum()), 2),
            "pnl_mean_eur_t": round(float(net.mean()), 2),
            "hit_rate": round(float((net > 0).mean()), 4),
            "profit_factor": round(pf, 2) if np.isfinite(pf) else None,
            "max_drawdown_eur_t": round(max_dd, 2),
            "share_years_positive": round(float((yearly > 0).mean()), 4),
        }

    out = {
        "version": "V9-IND-03",
        "n_trades": int(len(kept)),
        "n_long": int((side.values[kept] == 1).sum()),
        "n_short": int((side.values[kept] == -1).sum()),
        "gross_hit_rate": round(float((gross_pnl > 0).mean()), 4),
        "by_cost_eur_t_per_leg": by_cost,
        "verdict": "RESEARCH_ONLY_NOT_TRADING",
        "note": "Spread proxy barchart_exploratory, slippage/bid-ask absents. Aucun claim trading.",
    }
    (V9_DIR / "backtest_v4.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_red_team_v2(df: pd.DataFrame, n_perms: int = 100,
                    features: list[str] | None = None) -> dict[str, Any]:
    """V9-IND-04 — permutation test sur l'AUC OOF du cœur structurel."""
    assert_no_holdout(df)
    fit = fit_oof_structural(df, features=features)
    if fit["verdict"] != "OK" or "auc_cal" not in fit["metrics"]:
        return {"version": "V9-IND-04", "verdict": "INSUFFICIENT_DATA"}
    observed = fit["metrics"]["auc_cal"]

    df2 = _ensure_rel_target(df)
    x_all = build_structural_frame(df2, features)
    y_all = df2[TARGET]
    valid = y_all.notna() & x_all.notna().all(axis=1)
    x = x_all.loc[valid]
    y = y_all.loc[valid].astype(int).values
    means = x.mean()
    stds = x.std().replace(0.0, 1.0)
    x_std = ((x - means) / stds).values
    dates = x.index

    rng = np.random.default_rng(42)
    tscv = TimeSeriesSplit(n_splits=6)
    folds = []
    for tr, te in tscv.split(x_std):
        train_end = dates[tr[-1]]
        te_p = np.array([i for i in te if dates[i] > train_end + pd.Timedelta(days=HORIZON)])
        if len(tr) >= 80 and len(te_p) >= 10:
            folds.append((tr, te_p))

    perm_aucs = []
    for _ in range(n_perms):
        yp = rng.permutation(y)
        oof = np.full(len(x_std), np.nan)
        for tr, te in folds:
            if len(np.unique(yp[tr])) < 2:
                continue
            clf = LogisticRegression(C=1.0, max_iter=500, random_state=0)
            clf.fit(x_std[tr], yp[tr])
            oof[te] = clf.predict_proba(x_std[te])[:, 1]
        m = ~np.isnan(oof)
        if m.sum() >= 30 and len(np.unique(yp[m])) > 1:
            perm_aucs.append(roc_auc_score(yp[m], oof[m]))

    perm_aucs = np.array(perm_aucs)
    p_value = float((np.sum(perm_aucs >= observed) + 1) / (len(perm_aucs) + 1)) if len(perm_aucs) else None
    out = {
        "version": "V9-IND-04",
        "observed_auc_cal": observed,
        "n_perms_valid": int(len(perm_aucs)),
        "perm_auc_mean": round(float(perm_aucs.mean()), 4) if len(perm_aucs) else None,
        "perm_auc_95pct": round(float(np.quantile(perm_aucs, 0.95)), 4) if len(perm_aucs) else None,
        "p_value": round(p_value, 4) if p_value is not None else None,
        "verdict": ("SIGNAL_PASS" if (p_value is not None and p_value <= 0.05)
                    else "SIGNAL_FAIL_OR_MARGINAL"),
    }
    (V9_DIR / "red_team_v2.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
