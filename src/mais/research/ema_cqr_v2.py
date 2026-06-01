"""NB2-10 — CQR sur returns EMA, basis_change et relative_return."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, PROJECT_ROOT
from mais.research.ema_utils import crop_year

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_cqr_v2.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_CQR_V2.md"


def _load_dataset() -> pd.DataFrame:
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    df = feats[feats["ema_front_price"].notna() & feats["cbot_eur_t"].notna()].copy()
    df = df.sort_values("Date").reset_index(drop=True)
    horizon = 20
    df["return_ema_h20"] = np.log(df["ema_front_price"]).diff(horizon).shift(-horizon)
    df["return_cbot_h20"] = np.log(df["cbot_eur_t"]).diff(horizon).shift(-horizon)
    df["relative_return_h20"] = df["return_ema_h20"] - df["return_cbot_h20"]
    df["basis_change_h20"] = df["ema_cbot_basis"].shift(-horizon) - df["ema_cbot_basis"]
    df["vol_regime"] = np.where(df.get("ema_front_vol_20d_adjusted", 0) > 0.25, "high_vol", "normal")
    df["crop_year"] = df["Date"].apply(crop_year)
    return df


def _features(df: pd.DataFrame) -> list[str]:
    cols = [
        "ema_cbot_basis",
        "ema_cbot_basis_zscore_52w",
        "ema_front_vol_20d_adjusted",
        "corn_realized_vol_20",
        "corn_logret_20d",
        "corn_gas_ratio",
    ]
    out = []
    for col in cols:
        if col in df.columns:
            df[f"{col}_lag1"] = df[col].shift(1)
            out.append(f"{col}_lag1")
    return out


def _fit_quantile(x, y, alpha: float):
    model = GradientBoostingRegressor(
        loss="quantile",
        alpha=alpha,
        n_estimators=80,
        max_depth=2,
        learning_rate=0.05,
        random_state=42,
    )
    model.fit(x, y)
    return model


def _winkler(y: np.ndarray, lo: np.ndarray, hi: np.ndarray, alpha: float = 0.10) -> float:
    width = hi - lo
    below = y < lo
    above = y > hi
    score = width + (2 / alpha) * (lo - y) * below + (2 / alpha) * (y - hi) * above
    return float(np.mean(score))


def _evaluate_target(df: pd.DataFrame, target: str) -> dict:
    feature_cols = _features(df)
    sub = df[["Date", "crop_year", "vol_regime", target, *feature_cols]].replace([np.inf, -np.inf], np.nan).dropna()
    crop_years = sorted(sub["crop_year"].unique())
    fold_rows = []
    test_records = []
    for idx in range(4, len(crop_years)):
        train_full = sub[sub["crop_year"].isin(crop_years[:idx])]
        test = sub[sub["crop_year"] == crop_years[idx]]
        if len(train_full) < 300 or len(test) < 20:
            continue
        split = int(len(train_full) * 0.80)
        train = train_full.iloc[:split]
        cal = train_full.iloc[split:]
        q10 = _fit_quantile(train[feature_cols], train[target], 0.10)
        q50 = _fit_quantile(train[feature_cols], train[target], 0.50)
        q90 = _fit_quantile(train[feature_cols], train[target], 0.90)
        cal_lo = q10.predict(cal[feature_cols])
        cal_hi = q90.predict(cal[feature_cols])
        cal_y = cal[target].values
        nonconformity = np.maximum(cal_lo - cal_y, cal_y - cal_hi)
        qhat = float(np.quantile(nonconformity, 0.90))
        lo = q10.predict(test[feature_cols]) - qhat
        mid = q50.predict(test[feature_cols])
        hi = q90.predict(test[feature_cols]) + qhat
        y = test[target].values
        covered = (y >= lo) & (y <= hi)
        fold_rows.append({
            "crop_year": int(crop_years[idx]),
            "n_test": int(len(test)),
            "coverage": float(covered.mean()),
            "winkler": _winkler(y, lo, hi),
            "mean_interval_width": float(np.mean(hi - lo)),
            "qhat": qhat,
        })
        test_records.append(pd.DataFrame({
            "Date": test["Date"].values,
            "vol_regime": test["vol_regime"].values,
            "y": y,
            "lo": lo,
            "mid": mid,
            "hi": hi,
            "covered": covered,
        }))
    all_test = pd.concat(test_records, ignore_index=True) if test_records else pd.DataFrame()
    by_regime = {}
    if len(all_test):
        for regime, reg_df in all_test.groupby("vol_regime"):
            by_regime[str(regime)] = {
                "n": int(len(reg_df)),
                "coverage": float(reg_df["covered"].mean()),
                "winkler": _winkler(reg_df["y"].values, reg_df["lo"].values, reg_df["hi"].values),
            }
    coverage = float(all_test["covered"].mean()) if len(all_test) else float("nan")
    return {
        "target": target,
        "folds": fold_rows,
        "coverage_overall": coverage,
        "winkler_overall": _winkler(all_test["y"].values, all_test["lo"].values, all_test["hi"].values) if len(all_test) else float("nan"),
        "coverage_by_vol_regime": by_regime,
        "coverage_by_year": {str(r["crop_year"]): r["coverage"] for r in fold_rows},
        "verdict": "CQR_GO" if coverage >= 0.88 else "CQR_NO_GO",
    }


@lru_cache(maxsize=1)
def build_cqr_v2() -> dict:
    df = _load_dataset()
    targets = ["return_ema_h20", "basis_change_h20", "relative_return_h20"]
    results = [_evaluate_target(df.copy(), target) for target in targets]
    best = max(results, key=lambda r: r["coverage_overall"] if r["coverage_overall"] == r["coverage_overall"] else -1)
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "target_coverage": 0.90,
        "minimum_acceptance_coverage": 0.88,
        "protocol": "Quantile GBM q10/q50/q90, calibration 20%, test walk-forward crop year, conformal qhat.",
        "results": results,
        "key_findings": {
            "best_target": best["target"],
            "best_coverage": best["coverage_overall"],
            "best_verdict": best["verdict"],
            "overall_verdict": "CQR_GO" if any(r["coverage_overall"] >= 0.88 for r in results) else "CQR_NO_GO",
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
        "# EMA CQR V2",
        "",
        "> CQR sur returns/basis/relative returns, pas sur prix absolus.",
        "",
        "## Verdict",
        "",
        f"- Meilleure cible : {k['best_target']}",
        f"- Meilleure couverture : {k['best_coverage']:.1%}",
        f"- Verdict global : {k['overall_verdict']}",
        "",
        "| Target | Coverage | Winkler | Verdict |",
        "|---|---:|---:|---|",
    ]
    for row in data["results"]:
        lines.append(f"| {row['target']} | {row['coverage_overall']:.1%} | {row['winkler_overall']:.3f} | {row['verdict']} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_cqr_v2(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_cqr_v2()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_cqr_v2()
    print(f"CQR v2 saved -> {out}")
