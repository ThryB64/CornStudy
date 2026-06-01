"""NB2-03 — Étude complète du basis EMA/CBOT avec validation OOF."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, PROJECT_ROOT
from mais.research.ema_basis_formal import build_basis_formal
from mais.research.ema_utils import bootstrap_ci, crop_year

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_basis_v2.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_BASIS_V2.md"
_HORIZONS = [20, 40, 60]
_THRESHOLDS = [1.0, 1.5, 2.0, 2.5]


def _load_basis() -> pd.DataFrame:
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    cols = ["Date", "ema_front_price", "cbot_eur_t", "ema_cbot_basis"]
    df = feats.loc[feats["ema_cbot_basis"].notna(), cols].copy()
    df = df.sort_values("Date").reset_index(drop=True)
    df["crop_year"] = df["Date"].apply(crop_year)
    return df


def _basis_zscore(df: pd.DataFrame) -> pd.Series:
    basis = df["ema_cbot_basis"]
    mean = basis.ewm(span=60, min_periods=60, adjust=False).mean().shift(1)
    std = basis.ewm(span=60, min_periods=60, adjust=False).std().shift(1)
    return ((basis - mean) / std.replace(0, np.nan)).rename("basis_zscore_ewm60_shift1")


def _acf_pacf(series: pd.Series, max_lag: int = 20) -> dict:
    clean = series.dropna()
    acf = {str(lag): float(clean.autocorr(lag)) for lag in range(1, max_lag + 1)}
    try:
        from statsmodels.tsa.stattools import pacf
        vals = pacf(clean, nlags=max_lag)
        pacf_dict = {str(lag): float(vals[lag]) for lag in range(1, max_lag + 1)}
    except Exception:
        pacf_dict = {}
    return {"acf": acf, "pacf": pacf_dict}


def _regime_stats(df: pd.DataFrame) -> dict:
    z = df["basis_zscore"]
    regimes = {
        "high_z_gt_1_5": z > 1.5,
        "high_z_gt_2_0": z > 2.0,
        "low_z_lt_minus_1_5": z < -1.5,
        "low_z_lt_minus_2_0": z < -2.0,
        "normal_abs_z_le_1_5": z.abs() <= 1.5,
    }
    out = {}
    for name, mask in regimes.items():
        idx = mask.fillna(False)
        out[name] = {
            "n_days": int(idx.sum()),
            "pct_days": float(idx.mean()),
            "mean_basis": float(df.loc[idx, "ema_cbot_basis"].mean()) if idx.any() else float("nan"),
            "avg_duration_days": _avg_run_length(idx),
        }
    return out


def _avg_run_length(mask: pd.Series) -> float:
    lengths = []
    current = 0
    for value in mask.astype(bool):
        if value:
            current += 1
        elif current:
            lengths.append(current)
            current = 0
    if current:
        lengths.append(current)
    return float(np.mean(lengths)) if lengths else 0.0


def _binom_p_value(n_success: int, n_total: int) -> float:
    if n_total == 0:
        return float("nan")
    try:
        from scipy.stats import binomtest
        return float(binomtest(n_success, n_total, p=0.5, alternative="greater").pvalue)
    except Exception:
        return float("nan")


def _bh_q_values(p_values: list[float]) -> list[float]:
    arr = np.array([1.0 if np.isnan(p) else p for p in p_values], dtype=float)
    n = len(arr)
    order = np.argsort(arr)
    q = np.empty(n)
    prev = 1.0
    for rank, idx in enumerate(order[::-1], start=1):
        true_rank = n - rank + 1
        val = min(prev, arr[idx] * n / true_rank)
        q[idx] = val
        prev = val
    return [float(x) for x in q]


def _evaluate_events(df: pd.DataFrame, threshold: float, horizon: int) -> pd.DataFrame:
    work = df.copy()
    work["future_basis"] = work["ema_cbot_basis"].shift(-horizon)
    work["basis_change_h"] = work["future_basis"] - work["ema_cbot_basis"]
    high = work["basis_zscore"] >= threshold
    low = work["basis_zscore"] <= -threshold
    events = work[high | low].copy()
    events["expected_change_sign"] = np.where(events["basis_zscore"] >= threshold, -1, 1)
    events["actual_change_sign"] = np.sign(events["basis_change_h"])
    events["correct"] = events["expected_change_sign"] == events["actual_change_sign"]
    return events.dropna(subset=["basis_change_h"])


def _walk_forward_oof(df: pd.DataFrame, weekly: bool = False) -> list[dict]:
    if weekly:
        tmp = df.set_index("Date")[["ema_cbot_basis", "basis_zscore"]].resample("W-FRI").last().dropna().reset_index()
        tmp["crop_year"] = tmp["Date"].apply(crop_year)
        horizons = [4, 8, 12]
    else:
        tmp = df
        horizons = _HORIZONS

    crop_years = sorted(tmp["crop_year"].dropna().unique())
    rows = []
    for horizon in horizons:
        for threshold in _THRESHOLDS:
            fold_rows = []
            for idx in range(3, len(crop_years)):
                test_year = crop_years[idx]
                test = tmp[tmp["crop_year"] == test_year]
                events = _evaluate_events(test, threshold, horizon)
                if len(events) == 0:
                    continue
                n_success = int(events["correct"].sum())
                fold_rows.append({
                    "crop_year": int(test_year),
                    "n": int(len(events)),
                    "hit_rate": float(n_success / len(events)),
                    "mean_basis_change": float(events["basis_change_h"].mean()),
                })
            if not fold_rows:
                rows.append({
                    "frequency": "weekly" if weekly else "daily",
                    "horizon": int(horizon),
                    "threshold": threshold,
                    "n_events": 0,
                    "error": "no_events",
                })
                continue
            total_n = int(sum(r["n"] for r in fold_rows))
            weighted_hits = sum(r["hit_rate"] * r["n"] for r in fold_rows)
            hit_rate = float(weighted_hits / total_n)
            expanded = np.concatenate([np.repeat(r["hit_rate"], r["n"]) for r in fold_rows])
            ci = bootstrap_ci(expanded, np.mean, n_draws=500)
            successes = int(round(hit_rate * total_n))
            rows.append({
                "frequency": "weekly" if weekly else "daily",
                "horizon": int(horizon),
                "threshold": threshold,
                "n_events": total_n,
                "hit_rate": hit_rate,
                "da": hit_rate,
                "ci95_lo": ci["ci_lo"],
                "ci95_hi": ci["ci_hi"],
                "p_value_gt_50": _binom_p_value(successes, total_n),
                "annual_stability": fold_rows,
                "verdict": "GO" if hit_rate >= 0.55 and ci["ci_lo"] > 0.50 else "NO_GO",
            })
    q_values = _bh_q_values([r.get("p_value_gt_50", np.nan) for r in rows])
    for row, q in zip(rows, q_values, strict=False):
        row["bh_q_value"] = q
        row["bh_significant_5pct"] = bool(q < 0.05)
    return rows


def _period_stability(df: pd.DataFrame) -> dict:
    periods = {
        "2010_2014": (2010, 2014),
        "2015_2019": (2015, 2019),
        "2020_2022": (2020, 2022),
        "2023_2026": (2023, 2026),
    }
    out = {}
    for name, (start, end) in periods.items():
        sub = df[df["Date"].dt.year.between(start, end)]
        events = _evaluate_events(sub, threshold=2.0, horizon=60)
        out[name] = {
            "n_events_h60_z2": int(len(events)),
            "hit_rate_h60_z2": float(events["correct"].mean()) if len(events) else float("nan"),
            "mean_basis": float(sub["ema_cbot_basis"].mean()) if len(sub) else float("nan"),
        }
    return out


def build_basis_v2() -> dict:
    df = _load_basis()
    df["basis_zscore"] = _basis_zscore(df)
    formal = build_basis_formal()
    daily = _walk_forward_oof(df, weekly=False)
    weekly = _walk_forward_oof(df, weekly=True)
    best_daily = max((r for r in daily if "hit_rate" in r), key=lambda r: r["hit_rate"], default={})
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "basis_stats": formal["basis_stats"],
        "stationarity": formal["stationarity"],
        "ar1": formal["ar1"],
        "acf_pacf": _acf_pacf(df["ema_cbot_basis"]),
        "zscore_method": "EWM span=60, min_periods=60, shift(1)",
        "regime_stats": _regime_stats(df),
        "walk_forward_oof": daily,
        "weekly_validation": weekly,
        "period_stability": _period_stability(df),
        "anti_confusion": "Le basis peut revenir vers sa moyenne de 3 façons : EMA baisse, CBOT monte, ou les deux évoluent ensemble. basis_reversion ≠ EMA up.",
        "key_findings": {
            "basis_mean_eur_t": formal["basis_stats"]["mean"],
            "basis_pct_positive": formal["basis_stats"]["pct_positive"],
            "ar1_phi": formal["ar1"]["phi"],
            "half_life_days": formal["ar1"]["half_life_days"],
            "best_daily_horizon": best_daily.get("horizon"),
            "best_daily_threshold": best_daily.get("threshold"),
            "best_daily_hit_rate": best_daily.get("hit_rate"),
            "best_daily_bh_q": best_daily.get("bh_q_value"),
        },
    }


def _json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return str(obj.date())
    if isinstance(obj, bool):
        return bool(obj)
    raise TypeError(f"Not serialisable: {type(obj)}")


def _write_markdown(data: dict, path: Path) -> None:
    k = data["key_findings"]
    lines = [
        "# EMA BASIS V2",
        "",
        "> Résultat principal EMA Phase 2. Source exploratoire/proxy, validation OOF stricte.",
        "",
        "## Verdict",
        "",
        f"- Basis moyen : {k['basis_mean_eur_t']:.2f} €/t.",
        f"- Basis positif : {k['basis_pct_positive']:.1%} du temps.",
        f"- AR(1) phi : {k['ar1_phi']:.3f}, demi-vie : {k['half_life_days']:.1f} jours.",
        f"- Meilleur signal OOF daily : H{k['best_daily_horizon']} z>{k['best_daily_threshold']} hit-rate {k['best_daily_hit_rate']:.1%}.",
        "",
        "## Règle anti-confusion",
        "",
        data["anti_confusion"],
        "",
        "## Validation OOF",
        "",
        "| Fréquence | Horizon | Seuil | n | DA | IC95 | q BH | Verdict |",
        "|---|---:|---:|---:|---:|---|---:|---|",
    ]
    for row in data["walk_forward_oof"]:
        if "hit_rate" not in row:
            continue
        lines.append(
            f"| {row['frequency']} | {row['horizon']} | {row['threshold']} | {row['n_events']} | "
            f"{row['hit_rate']:.1%} | [{row['ci95_lo']:.1%}; {row['ci95_hi']:.1%}] | "
            f"{row['bh_q_value']:.3f} | {row['verdict']} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_basis_v2(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_basis_v2()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_basis_v2()
    print(f"Basis v2 saved -> {out}")
