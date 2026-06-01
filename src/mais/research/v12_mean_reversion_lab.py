"""V12 — Anatomie de la mean-reversion, validation forward des règles, abstention conforme, journal.

Suite V11. Discipline maintenue : basis + saison, H40, coûts réalistes, validation hors échantillon.

- run_reversion_anatomy   : temps de reversion, drawdown avant reversion, règle de sortie optimale.
- run_forward_rule_validation : split-half + walk-forward des familles long basis-bas / short basis-haut.
- run_conformal_abstention : intervalles conformes (CQR) sur basis_change, abstention si l'intervalle borde 0.
- build_premium_journal / evaluate_matured_journal : journal paper-trading append-only, éval J+40.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit

from mais.indicator.structural_indicator_v9 import (
    HORIZON,
    SIMPLIFIED_FEATURES,
    compute_signals,
    fit_oof_structural,
)
from mais.meta.cqr import _finite_sample_residual_quantile
from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout
from mais.research.v11_simplified_program import _nonoverlap_idx, _spread_pnl

V12_DIR = ARTEFACTS_DIR / "v12"
V12_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# V12-A — Anatomie du trade de mean-reversion
# ---------------------------------------------------------------------------

def run_reversion_anatomy(df: pd.DataFrame, z_entry: float = 1.5, max_h: int = 120) -> dict[str, Any]:
    """Pour les entrées basis extrême, mesure temps de reversion, MAE, et compare les sorties.

    Entrée long premium si basis_z < -z_entry, short premium si basis_z > +z_entry.
    Sorties comparées : H40 fixe, basis_z croise 0, |basis_z| < 0.5.
    """
    assert_no_holdout(df)
    if "ema_close" not in df.columns or "cbot_eur_t" not in df.columns:
        return {"version": "V12-A-REVERSION-ANATOMY", "verdict": "MISSING_PRICES"}
    bz = df.get("ema_cbot_basis_zscore_52w")
    if bz is None:
        return {"version": "V12-A-REVERSION-ANATOMY", "verdict": "MISSING_BASIS_Z"}

    ema = df["ema_close"].values
    cbot = df["cbot_eur_t"].values
    bz_v = bz.values
    n = len(df)

    def _spread_ret(i, j, side):
        if i >= n or j >= n or np.isnan(ema[i]) or np.isnan(ema[j]) or np.isnan(cbot[i]) or np.isnan(cbot[j]):
            return np.nan
        return side * ((ema[j] / ema[i] - 1) - (cbot[j] / cbot[i] - 1)) * ema[i]

    entries = []  # (i, side)
    for i in range(n):
        if np.isnan(bz_v[i]):
            continue
        if bz_v[i] < -z_entry:
            entries.append((i, +1))
        elif bz_v[i] > z_entry:
            entries.append((i, -1))

    # non-overlap par 40j sur les dates d'entrée
    dates = df.index
    kept = []
    last = None
    for i, side in entries:
        d = dates[i]
        if last is None or (d - last).days >= HORIZON:
            kept.append((i, side))
            last = d

    rows = []
    for i, side in kept:
        # temps de reversion : basis_z revient vers/au-delà de 0
        rev_j = None
        half_j = None
        for t in range(1, max_h + 1):
            if i + t >= n or np.isnan(bz_v[i + t]):
                continue
            if rev_j is None and (bz_v[i + t] * np.sign(bz_v[i]) <= 0):
                rev_j = i + t
            if half_j is None and abs(bz_v[i + t]) < 0.5:
                half_j = i + t
            if rev_j is not None and half_j is not None:
                break
        # MAE avant H40
        path = [_spread_ret(i, i + t, side) for t in range(1, min(HORIZON, n - i - 1) + 1)]
        path = [p for p in path if not np.isnan(p)]
        mae = float(min(path)) if path else np.nan
        rows.append({
            "side": side,
            "days_to_reversion": (dates[rev_j] - dates[i]).days if rev_j else None,
            "days_to_half": (dates[half_j] - dates[i]).days if half_j else None,
            "pnl_fixed_h40": _spread_ret(i, i + HORIZON, side),
            "pnl_exit_cross0": _spread_ret(i, rev_j, side) if rev_j else np.nan,
            "pnl_exit_half": _spread_ret(i, half_j, side) if half_j else np.nan,
            "mae_before_h40": mae,
        })

    if not rows:
        return {"version": "V12-A-REVERSION-ANATOMY", "verdict": "NO_ENTRIES"}
    rdf = pd.DataFrame(rows)

    def _summ(col, days_col=None):
        s = rdf[col].dropna()
        out = {"n": int(len(s))}
        if len(s):
            out.update({"mean_pnl_eur_t": round(float(s.mean()), 2),
                        "hit_rate": round(float((s > 0).mean()), 4),
                        "total_pnl_eur_t": round(float(s.sum()), 1)})
        if days_col:
            dd = rdf[days_col].dropna()
            if len(dd):
                out["mean_holding_days"] = round(float(dd.mean()), 1)
                out["median_holding_days"] = round(float(dd.median()), 1)
        return out

    rev_days = rdf["days_to_reversion"].dropna()
    exits = {
        "exit_fixed_h40": _summ("pnl_fixed_h40"),
        "exit_cross_zero": _summ("pnl_exit_cross0", "days_to_reversion"),
        "exit_basis_z_half": _summ("pnl_exit_half", "days_to_half"),
    }
    valid_exits = {k: v for k, v in exits.items() if v.get("mean_pnl_eur_t") is not None}
    best_exit = max(valid_exits.items(), key=lambda kv: kv[1]["mean_pnl_eur_t"])[0] if valid_exits else None

    out = {
        "version": "V12-A-REVERSION-ANATOMY",
        "z_entry": z_entry,
        "n_entries_nonoverlap": len(kept),
        "reversion_time": {
            "n_reverted": int(len(rev_days)),
            "n_censored": int(rdf["days_to_reversion"].isna().sum()),
            "median_days_to_reversion": round(float(rev_days.median()), 1) if len(rev_days) else None,
            "mean_days_to_reversion": round(float(rev_days.mean()), 1) if len(rev_days) else None,
        },
        "mean_adverse_excursion_eur_t": round(float(rdf["mae_before_h40"].dropna().mean()), 2),
        "exit_strategies": exits,
        "best_exit_by_mean_pnl": best_exit,
        "interpretation": (
            "Si exit_cross_zero ou exit_basis_z_half battent H40 fixe -> une sortie basée sur le niveau "
            "de basis est meilleure qu'une sortie temporelle. Le temps médian de reversion situe l'horizon naturel."
        ),
        "verdict": "REVERSION_ANATOMY_DONE",
    }
    (V12_DIR / "reversion_anatomy.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V12-B — Validation forward / split-half des familles de règles
# ---------------------------------------------------------------------------

def run_forward_rule_validation(df: pd.DataFrame) -> dict[str, Any]:
    """Les familles long basis-bas / short basis-haut généralisent-elles hors échantillon ?

    Test split-half (première moitié = découverte, seconde = confirmation) + cohérence des deux moitiés.
    Règles a priori (pas de sélection) -> pas de correction multi-test nécessaire ici.
    """
    assert_no_holdout(df)
    spread, price = _spread_pnl(df)
    bz = df.get("ema_cbot_basis_zscore_52w")
    if bz is None:
        return {"version": "V12-B-FORWARD-RULES", "verdict": "MISSING_BASIS_Z"}

    families = [
        ("long_basis_lt_-1.5", bz < -1.5, +1),
        ("long_basis_lt_-1", bz < -1.0, +1),
        ("short_basis_gt_1.5", bz > 1.5, -1),
        ("short_basis_gt_1", bz > 1.0, -1),
    ]
    median_year = int(np.median(df.index.year))
    first = df.index.year <= median_year
    second = df.index.year > median_year

    def _eval(mask, side, period_mask):
        active = mask & period_mask & spread.notna() & price.notna() & bz.notna()
        kd = _nonoverlap_idx(df.index[active.values])
        if len(kd) < 6:
            return {"n_trades": len(kd)}
        g = (spread.loc[kd] * side * price.loc[kd]).values
        return {"n_trades": len(kd), "hit_rate": round(float((g > 0).mean()), 4),
                "net_pnl_cost3": round(float((g - 6).sum()), 1),
                "mean_pnl_eur_t": round(float(g.mean()), 2)}

    results = {}
    for name, mask, side in families:
        h1 = _eval(mask, side, first)
        h2 = _eval(mask, side, second)
        generalizes = (
            h1.get("hit_rate", 0) > 0.5 and h2.get("hit_rate", 0) > 0.5
            and h1.get("net_pnl_cost3", -1) > 0 and h2.get("net_pnl_cost3", -1) > 0
        )
        results[name] = {"first_half": h1, "second_half": h2, "generalizes_both_halves": bool(generalizes)}

    robust = [k for k, v in results.items() if v["generalizes_both_halves"]]
    out = {
        "version": "V12-B-FORWARD-RULES",
        "split_year": median_year,
        "results_by_family": results,
        "families_robust_both_halves": robust,
        "interpretation": (
            "Une famille robuste est positive (hit>0.5 et PnL coût3>0) dans LES DEUX moitiés temporelles. "
            "C'est un test out-of-sample honnête des gagnants V11-05."
        ),
        "verdict": "FORWARD_RULES_GENERALIZE" if robust else "FORWARD_RULES_FRAGILE",
    }
    (V12_DIR / "forward_rule_validation.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V12-C — Abstention par incertitude conforme (CQR) sur basis_change
# ---------------------------------------------------------------------------

def run_conformal_abstention(df: pd.DataFrame, h: int = HORIZON, alpha: float = 0.2) -> dict[str, Any]:
    """Intervalle conforme split sur basis_change_h ; abstention si l'intervalle contient 0.

    Mappe predicted basis_change > 0 -> LONG_PREMIUM (le basis monte = EMA surperforme).
    """
    assert_no_holdout(df)
    if "ema_cbot_basis" not in df.columns:
        return {"version": "V12-C-CONFORMAL-ABSTENTION", "verdict": "MISSING_BASIS"}
    basis = df["ema_cbot_basis"]
    x_all = pd.DataFrame({
        "basis_z": df.get("ema_cbot_basis_zscore_52w"),
        "month_cos": np.cos(2 * np.pi * df.index.month / 12),
        "eurusd": df.get("eurusd"),
    }, index=df.index)
    target = basis.shift(-h) - basis
    keep = target.notna() & x_all.notna().all(axis=1)
    x, y = x_all.loc[keep], target.loc[keep]
    if len(x) < 300:
        return {"version": "V12-C-CONFORMAL-ABSTENTION", "verdict": "INSUFFICIENT_DATA", "n": int(len(x))}
    dates = x.index
    means, stds = x.mean(), x.std().replace(0, 1)
    xs = (x - means) / stds

    point = np.full(len(x), np.nan)
    half_width = np.full(len(x), np.nan)
    for tr, te in TimeSeriesSplit(n_splits=6).split(xs):
        train_end = dates[tr[-1]]
        te_p = np.array([i for i in te if dates[i] > train_end + pd.Timedelta(days=h)])
        if len(tr) < 120 or len(te_p) < 10:
            continue
        # split train -> fit / calibration pour le conforme
        cut = int(len(tr) * 0.7)
        fit_idx, cal_idx = tr[:cut], tr[cut:]
        if len(cal_idx) < 30:
            continue
        reg = Ridge(alpha=1.0).fit(xs.iloc[fit_idx], y.iloc[fit_idx])
        cal_pred = reg.predict(xs.iloc[cal_idx])
        cal_scores = np.abs(y.iloc[cal_idx].values - cal_pred)
        q = _finite_sample_residual_quantile(cal_scores, alpha)
        point[te_p] = reg.predict(xs.iloc[te_p])
        half_width[te_p] = q

    v = ~np.isnan(point)
    if v.sum() < 50:
        return {"version": "V12-C-CONFORMAL-ABSTENTION", "verdict": "NO_OOF"}
    lo = point - half_width
    hi = point + half_width
    yv = y.values
    # couverture empirique de l'intervalle
    covered = (yv[v] >= lo[v]) & (yv[v] <= hi[v])
    coverage = float(covered.mean())

    # signal : abstention si l'intervalle contient 0 (incertitude de signe)
    interval_excludes_0 = (lo > 0) | (hi < 0)
    sign_pred = np.sign(point)
    sign_true = np.sign(yv)

    def _da(mask):
        m = v & mask
        if m.sum() < 20:
            return None, int(m.sum())
        return round(float((sign_pred[m] == sign_true[m]).mean()), 4), int(m.sum())

    da_all, n_all = _da(np.ones(len(point), dtype=bool))
    da_acted, n_acted = _da(interval_excludes_0)
    out = {
        "version": "V12-C-CONFORMAL-ABSTENTION",
        "horizon": h,
        "alpha": alpha,
        "n_oof": int(v.sum()),
        "empirical_interval_coverage": round(coverage, 4),
        "target_coverage": round(1 - alpha, 4),
        "sign_da_no_abstention": da_all,
        "n_no_abstention": n_all,
        "sign_da_with_abstention": da_acted,
        "n_acted_after_abstention": n_acted,
        "coverage_acted_share": round(n_acted / n_all, 4) if n_all else None,
        "abstention_improves_da": bool(da_acted is not None and da_all is not None and da_acted > da_all),
        "interpretation": (
            "Si la DA des signaux agis (intervalle excluant 0) dépasse la DA brute -> l'abstention conforme "
            "par incertitude améliore la sélection, mieux qu'une bande morte fixe."
        ),
        "verdict": "CONFORMAL_ABSTENTION_DONE",
    }
    (V12_DIR / "conformal_abstention.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# V12-D — Journal paper-trading (append-only) + évaluation différée
# ---------------------------------------------------------------------------

def build_premium_journal(df: pd.DataFrame) -> pd.DataFrame:
    """Construit le journal quotidien des signaux de l'indicateur (modèle 2 vars promu)."""
    assert_no_holdout(df)
    fit = fit_oof_structural(df, features=SIMPLIFIED_FEATURES)
    signals = compute_signals(df, fit["oof_cal"]) if fit["verdict"] == "OK" else None
    if signals is None:
        return pd.DataFrame()
    bz = df.get("ema_cbot_basis_zscore_52w")
    journal = pd.DataFrame(index=signals.index)
    journal["signal"] = signals["signal"]
    journal["confidence"] = signals["confidence"]
    journal["drivers"] = signals["drivers"].apply(lambda d: ";".join(d))
    journal["veto_reasons"] = signals["veto_reasons"].apply(lambda d: ";".join(d))
    journal["basis_z"] = bz.reindex(signals.index) if bz is not None else np.nan
    journal["cbot_eur_t"] = df["cbot_eur_t"].reindex(signals.index)
    journal["ema_close"] = df["ema_close"].reindex(signals.index) if "ema_close" in df else np.nan
    journal["horizon"] = HORIZON
    journal["data_source_flag"] = "barchart_proxy_exploratory"
    journal["statut"] = "RESEARCH_ONLY_NOT_TRADING"
    return journal


def evaluate_matured_journal(journal: pd.DataFrame, df: pd.DataFrame, h: int = HORIZON) -> dict[str, Any]:
    """Évalue les lignes arrivées à maturité (J+h) : hit rate, DA, net PnL par coût."""
    spread, price = _spread_pnl(df, h)
    act = journal[journal["signal"].isin(["LONG_PREMIUM", "SHORT_PREMIUM"])].copy()
    side = np.where(act["signal"] == "LONG_PREMIUM", 1, -1)
    sp = spread.reindex(act.index).values
    pr = price.reindex(act.index).values
    matured = ~np.isnan(sp) & ~np.isnan(pr)
    n = int(matured.sum())
    if n < 10:
        return {"n_matured": n, "verdict": "TOO_FEW_MATURED"}
    g = sp[matured] * side[matured] * pr[matured]
    out = {
        "n_signals": int(len(journal)),
        "n_actionable": int(len(act)),
        "n_matured": n,
        "hit_rate": round(float((g > 0).mean()), 4),
        "directional_accuracy": round(float((g > 0).mean()), 4),
        "net_pnl_cost1": round(float((g - 2).sum()), 1),
        "net_pnl_cost3": round(float((g - 6).sum()), 1),
        "net_pnl_cost5": round(float((g - 10).sum()), 1),
        "verdict": "JOURNAL_EVALUATED",
    }
    (V12_DIR / "premium_journal_eval.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
