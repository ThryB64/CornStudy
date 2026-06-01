"""Horizon sweep J+1 to J+100 for the maize direction indicator.

All default project runs are capped at 2022-12-31.  The 2023-2025 period is
reserved for already-consulted V2 backtests and is never used by this sweep.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import brier_score_loss, mean_squared_error, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mais.features import build_multi_horizon_targets
from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, INTERIM_DIR
from mais.utils import get_logger, read_table, write_parquet

log = get_logger("mais.research.horizon_sweep")

HORIZONS = [1, 2, 3, 4, 5, 7, 10, 12, 15, 18, 20, 22, 25, 28, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100]
MAX_DATE = pd.Timestamp("2022-12-31")
ML_MODELS = {"ridge_factors", "lgbm_factors"}


def build_horizon_targets(price_series: pd.Series | pd.DataFrame, horizons: list[int]) -> pd.DataFrame:
    """Build V3 sweep targets with the strict ``price.shift(-H) / price`` rule."""
    return build_multi_horizon_targets(price_series, horizons)


def run_single_horizon(
    features: pd.DataFrame,
    targets: pd.DataFrame,
    horizon: int,
    model_name: str = "ridge_factors",
    n_splits: int = 5,
    embargo_days: int | None = None,
    max_date: str | pd.Timestamp = MAX_DATE,
) -> dict[str, Any]:
    """Run one horizon with expanding walk-forward and embargo ``H``."""
    h = int(horizon)
    embargo = h if embargo_days is None else int(embargo_days)
    target_col = f"y_cont_h{h}"
    up_col = f"y_up_h{h}"
    if target_col not in targets.columns or up_col not in targets.columns:
        raise KeyError(f"Missing target columns for horizon {h}")

    work = _merge_features_targets(features, targets, target_col, up_col, max_date=max_date)
    feature_cols = _feature_columns(work, exclude={target_col, up_col})
    splits = _walk_forward_splits(len(work), n_splits=n_splits, embargo_days=embargo)
    if not splits:
        return _empty_result(h, model_name, len(work), reason="no valid walk-forward split")

    frames = []
    for fold, (train_idx, test_idx) in enumerate(splits):
        train = work.iloc[train_idx].copy()
        test = work.iloc[test_idx].copy()
        pred_cont, score = _predict_model(train, test, feature_cols, target_col, model_name)
        frames.append(
            pd.DataFrame(
                {
                    "Date": test["Date"].values,
                    "fold": fold,
                    "y_true_cont": test[target_col].to_numpy(dtype=float),
                    "y_true_up": test[up_col].to_numpy(dtype=int),
                    "y_pred_cont": pred_cont,
                    "y_score": score,
                }
            )
        )

    oof = pd.concat(frames, ignore_index=True)
    metrics = _metrics(oof)
    metrics.update(
        {
            "horizon": h,
            "model": model_name,
            "n_obs": int(len(work)),
            "n_obs_test": int(len(oof)),
            "n_folds": int(oof["fold"].nunique()),
            "test_start": str(pd.to_datetime(oof["Date"]).min().date()),
            "test_end": str(pd.to_datetime(oof["Date"]).max().date()),
            "max_train_or_test_date": str(pd.to_datetime(work["Date"]).max().date()),
            "embargo_days": embargo,
            "eligibility": "ok",
        }
    )
    return metrics


def run_horizon_sweep(
    features: pd.DataFrame,
    price_series: pd.Series | pd.DataFrame,
    output_dir: Path,
    horizons: list[int] | None = None,
    max_date: str | pd.Timestamp = MAX_DATE,
) -> pd.DataFrame:
    """Run the complete sweep and write parquet/csv/png/json/txt artefacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    active_horizons = list(HORIZONS if horizons is None else horizons)
    targets = build_horizon_targets(price_series, active_horizons)

    rows: list[dict[str, Any]] = []
    for h in active_horizons:
        rows.append(run_single_horizon(features, targets, h, "ridge_factors", max_date=max_date))
        rows.append(run_single_horizon(features, targets, h, "lgbm_factors", max_date=max_date))
        rows.append(_run_baseline(features, targets, h, "seasonal_naive", max_date=max_date))
        rows.append(_run_baseline(features, targets, h, "momentum_20d", max_date=max_date))

    results = pd.DataFrame(rows)
    results = _add_baseline_deltas(results)
    results["interpretable"] = results["n_obs_test"].fillna(0).astype(int) >= 100

    zone = identify_robust_zone(results)
    zone_payload = _zone_payload(results, zone)

    write_parquet(results, output_dir / "horizon_sweep_results.parquet")
    results.to_csv(output_dir / "horizon_sweep_results.csv", index=False)
    (output_dir / "horizon_sweep_zone.json").write_text(
        json.dumps(zone_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    plot_predictability_curve(results, output_dir / "horizon_sweep_curve.png")
    (output_dir / "horizon_sweep_report.txt").write_text(
        _report_text(results, zone_payload),
        encoding="utf-8",
    )
    return results


def identify_robust_zone(results_df: pd.DataFrame, min_da_gain: float = 0.02) -> list[int]:
    """Return horizons passing n_obs, baseline gain, and neighboring-zone guards."""
    best = _best_ml_by_horizon(results_df)
    if best.empty:
        return []

    eligible = []
    for _, row in best.iterrows():
        h = int(row["horizon"])
        if int(row.get("n_obs_test", 0)) < 100:
            continue
        if float(row.get("delta_da_vs_seasonal", np.nan)) < min_da_gain:
            continue
        eligible.append(h)

    if not eligible:
        return []

    robust: list[int] = []
    ordered = [h for h in HORIZONS if h in set(best["horizon"].astype(int))]
    eligible_set = set(eligible)
    for h in eligible:
        idx = ordered.index(h)
        local = ordered[max(0, idx - 3) : min(len(ordered), idx + 4)]
        local_eligible = [x for x in local if x in eligible_set]
        if len(local_eligible) >= min(3, len(local)):
            robust.append(h)
    return robust


def plot_predictability_curve(results_df: pd.DataFrame, output_path: Path) -> None:
    """Plot DA/AUC by horizon with seasonal and momentum baselines."""
    import matplotlib.pyplot as plt

    best = _best_ml_by_horizon(results_df)
    seasonal = results_df[results_df["model"] == "seasonal_naive"].sort_values("horizon")
    momentum = results_df[results_df["model"] == "momentum_20d"].sort_values("horizon")

    fig, ax1 = plt.subplots(figsize=(10, 5))
    if not best.empty:
        ax1.plot(best["horizon"], best["da"], marker="o", label="best ML DA")
        ax1.plot(best["horizon"], best["auc"], marker="s", label="best ML AUC")
    if not seasonal.empty:
        ax1.plot(seasonal["horizon"], seasonal["da"], linestyle="--", label="seasonal DA")
    if not momentum.empty:
        ax1.plot(momentum["horizon"], momentum["da"], linestyle=":", label="momentum DA")

    ax1.axhline(0.5, color="black", linewidth=0.8, alpha=0.4)
    ax1.set_xlabel("Horizon (business days)")
    ax1.set_ylabel("Score")
    ax1.set_title("V3-02 horizon sweep predictability")
    ax1.set_ylim(0.35, 0.75)
    ax1.grid(True, alpha=0.25)
    ax1.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def run_project_horizon_sweep(output_dir: Path | None = None) -> pd.DataFrame:
    """Load standard project artefacts and run V3-02."""
    features = pd.read_parquet(FEATURES_PARQUET)
    db = read_table(INTERIM_DIR / "database.parquet", date_col="Date")
    out = output_dir if output_dir is not None else ARTEFACTS_DIR / "indicator"
    return run_horizon_sweep(features, db[["Date", "corn_close"]], out)


def _merge_features_targets(
    features: pd.DataFrame,
    targets: pd.DataFrame,
    target_col: str,
    up_col: str,
    max_date: str | pd.Timestamp,
) -> pd.DataFrame:
    feat = features.copy()
    targ = targets.copy()
    feat["Date"] = pd.to_datetime(feat["Date"])
    targ["Date"] = pd.to_datetime(targ["Date"])
    max_ts = pd.Timestamp(max_date)
    merged = feat.merge(targ[["Date", target_col, up_col]], on="Date", how="inner")
    merged = merged[merged["Date"] <= max_ts].sort_values("Date").reset_index(drop=True)
    merged = merged.dropna(subset=[target_col, up_col]).reset_index(drop=True)
    return merged


def _feature_columns(work: pd.DataFrame, exclude: set[str]) -> list[str]:
    cols = []
    for col in work.columns:
        if col == "Date" or col in exclude or col.startswith("y_"):
            continue
        if pd.api.types.is_numeric_dtype(work[col]):
            cols.append(col)
    return cols


def _walk_forward_splits(
    n: int,
    n_splits: int = 5,
    embargo_days: int = 20,
) -> list[tuple[np.ndarray, np.ndarray]]:
    if n < 300:
        return []
    start = int(n * 0.60)
    remaining = n - start
    test_size = max(40, remaining // n_splits)
    splits = []
    for i in range(n_splits):
        test_start = start + i * test_size
        test_end = n if i == n_splits - 1 else min(n, test_start + test_size)
        train_end = max(1, test_start - max(embargo_days, 1))
        if test_start >= n or test_end - test_start < 30 or train_end < 200:
            continue
        splits.append((np.arange(0, train_end), np.arange(test_start, test_end)))
    return splits


def _predict_model(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    model_name: str,
) -> tuple[np.ndarray, np.ndarray]:
    x_train, x_test = _matrices(train, test, feature_cols)
    y_train = train[target_col].astype(float).to_numpy()
    model = _model(model_name)
    model.fit(x_train, y_train)
    pred = np.asarray(model.predict(x_test), dtype=float)
    scale = float(np.nanstd(y_train))
    if not math.isfinite(scale) or scale <= 1e-8:
        scale = 0.03
    score = 1.0 / (1.0 + np.exp(-np.clip(pred / scale, -50.0, 50.0)))
    return pred, np.clip(score, 0.0, 1.0)


def _model(model_name: str):
    if model_name == "ridge_factors":
        return Pipeline([("scaler", StandardScaler()), ("ridge", Ridge(alpha=3.0))])
    if model_name == "lgbm_factors":
        try:
            import lightgbm as lgb

            return lgb.LGBMRegressor(
                n_estimators=80,
                learning_rate=0.05,
                num_leaves=15,
                min_child_samples=40,
                lambda_l2=1.0,
                feature_fraction=0.8,
                bagging_fraction=0.8,
                bagging_freq=5,
                verbose=-1,
                random_state=42,
            )
        except ImportError:
            from sklearn.ensemble import HistGradientBoostingRegressor

            return HistGradientBoostingRegressor(
                max_iter=80,
                learning_rate=0.05,
                max_leaf_nodes=15,
                l2_regularization=1.0,
                random_state=42,
            )
    raise ValueError(model_name)


def _matrices(
    train: pd.DataFrame,
    test: pd.DataFrame,
    cols: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    imputer = SimpleImputer(strategy="median", keep_empty_features=True)
    x_train = train[cols].replace([np.inf, -np.inf], np.nan)
    x_test = test[cols].replace([np.inf, -np.inf], np.nan)
    return (
        pd.DataFrame(imputer.fit_transform(x_train), columns=cols),
        pd.DataFrame(imputer.transform(x_test), columns=cols),
    )


def _run_baseline(
    features: pd.DataFrame,
    targets: pd.DataFrame,
    horizon: int,
    model_name: str,
    max_date: str | pd.Timestamp,
) -> dict[str, Any]:
    h = int(horizon)
    target_col = f"y_cont_h{h}"
    up_col = f"y_up_h{h}"
    work = _merge_features_targets(features, targets, target_col, up_col, max_date=max_date)
    splits = _walk_forward_splits(len(work), n_splits=5, embargo_days=h)
    if not splits:
        return _empty_result(h, model_name, len(work), reason="no valid walk-forward split")

    frames = []
    work["momentum_20d"] = _price_momentum_proxy(work, target_col)
    for fold, (train_idx, test_idx) in enumerate(splits):
        train = work.iloc[train_idx].copy()
        test = work.iloc[test_idx].copy()
        if model_name == "seasonal_naive":
            pred, score = _seasonal_baseline(train, test, target_col)
        elif model_name == "momentum_20d":
            pred, score = _momentum_baseline(train, test)
        else:
            raise ValueError(model_name)
        frames.append(
            pd.DataFrame(
                {
                    "Date": test["Date"].values,
                    "fold": fold,
                    "y_true_cont": test[target_col].to_numpy(dtype=float),
                    "y_true_up": test[up_col].to_numpy(dtype=int),
                    "y_pred_cont": pred,
                    "y_score": score,
                }
            )
        )

    oof = pd.concat(frames, ignore_index=True)
    metrics = _metrics(oof)
    metrics.update(
        {
            "horizon": h,
            "model": model_name,
            "n_obs": int(len(work)),
            "n_obs_test": int(len(oof)),
            "n_folds": int(oof["fold"].nunique()),
            "test_start": str(pd.to_datetime(oof["Date"]).min().date()),
            "test_end": str(pd.to_datetime(oof["Date"]).max().date()),
            "max_train_or_test_date": str(pd.to_datetime(work["Date"]).max().date()),
            "embargo_days": h,
            "eligibility": "ok",
        }
    )
    return metrics


def _price_momentum_proxy(work: pd.DataFrame, target_col: str) -> pd.Series:
    if "corn_logret_1d" in work.columns:
        return pd.to_numeric(work["corn_logret_1d"], errors="coerce").rolling(20).sum().shift(1)
    if "factor_market_momentum" in work.columns:
        return pd.to_numeric(work["factor_market_momentum"], errors="coerce")
    return pd.Series(0.0, index=work.index)


def _seasonal_baseline(
    train: pd.DataFrame,
    test: pd.DataFrame,
    target_col: str,
) -> tuple[np.ndarray, np.ndarray]:
    fallback = float(train[target_col].mean())
    month_mean = train.groupby(train["Date"].dt.month)[target_col].mean()
    pred = test["Date"].dt.month.map(month_mean).astype(float).fillna(fallback).to_numpy()
    scale = float(train[target_col].std() or 0.03)
    score = 1.0 / (1.0 + np.exp(-np.clip(pred / scale, -50.0, 50.0)))
    return pred, np.clip(score, 0.0, 1.0)


def _momentum_baseline(train: pd.DataFrame, test: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    amplitude = float(train["momentum_20d"].abs().median())
    if not math.isfinite(amplitude) or amplitude <= 1e-8:
        amplitude = 0.01
    momentum = test["momentum_20d"].fillna(0.0).to_numpy(dtype=float)
    pred = np.where(momentum >= 0.0, amplitude, -amplitude)
    score = np.where(momentum >= 0.0, 1.0, 0.0).astype(float)
    return pred, score


def _metrics(oof: pd.DataFrame) -> dict[str, float]:
    y_true_cont = oof["y_true_cont"].to_numpy(dtype=float)
    y_true_up = oof["y_true_up"].to_numpy(dtype=int)
    y_pred_cont = oof["y_pred_cont"].to_numpy(dtype=float)
    y_score = np.clip(oof["y_score"].to_numpy(dtype=float), 0.0, 1.0)
    y_pred_up = y_pred_cont > 0.0
    confidence = np.abs(y_score - 0.5)
    top20_mask = confidence >= np.quantile(confidence, 0.80)
    out = {
        "da": float(np.mean(y_pred_up == y_true_up.astype(bool))),
        "auc": _auc(y_true_up, y_score),
        "brier": float(brier_score_loss(y_true_up, y_score)),
        "rmse": float(math.sqrt(mean_squared_error(y_true_cont, y_pred_cont))),
        "da_top20pct": float(np.mean(y_pred_up[top20_mask] == y_true_up[top20_mask].astype(bool)))
        if top20_mask.any()
        else np.nan,
        "strong_signal_freq": float((confidence >= np.quantile(confidence, 0.80)).mean()),
    }
    return out


def _auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    try:
        if len(np.unique(y_true)) < 2:
            return np.nan
        return float(roc_auc_score(y_true, y_score))
    except ValueError:
        return np.nan


def _add_baseline_deltas(results: pd.DataFrame) -> pd.DataFrame:
    out = results.copy()
    out["delta_da_vs_seasonal"] = np.nan
    out["delta_da_vs_momentum"] = np.nan
    for h, sub in out.groupby("horizon"):
        seasonal = sub.loc[sub["model"] == "seasonal_naive", "da"]
        momentum = sub.loc[sub["model"] == "momentum_20d", "da"]
        if not seasonal.empty:
            out.loc[out["horizon"] == h, "delta_da_vs_seasonal"] = out.loc[out["horizon"] == h, "da"] - float(
                seasonal.iloc[0]
            )
        if not momentum.empty:
            out.loc[out["horizon"] == h, "delta_da_vs_momentum"] = out.loc[out["horizon"] == h, "da"] - float(
                momentum.iloc[0]
            )
    return out


def _best_ml_by_horizon(results_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    ml = results_df[results_df["model"].isin(ML_MODELS)].copy()
    for _, sub in ml.groupby("horizon"):
        rows.append(sub.sort_values(["da", "auc"], ascending=False, na_position="last").iloc[0])
    return pd.DataFrame(rows).sort_values("horizon").reset_index(drop=True) if rows else pd.DataFrame()


def _zone_payload(results: pd.DataFrame, zone: list[int]) -> dict[str, Any]:
    best = _best_ml_by_horizon(results)
    if best.empty:
        return {"robust_zone": [], "best_horizon": None, "reason": "no ML results"}
    peak = best.sort_values(["da", "auc"], ascending=False, na_position="last").iloc[0]
    candidates = best[
        (best["n_obs_test"] >= 100)
        & ((best["da"] >= 0.60) | (best["auc"] >= 0.65) | (best["delta_da_vs_seasonal"] >= 0.02))
    ]["horizon"].astype(int).tolist()
    return {
        "robust_zone": zone,
        "candidate_horizons_for_v3_03": candidates,
        "guardrail_verdict": "robust_zone_found" if zone else "no_robust_zone_under_G1_G3",
        "best_horizon": int(peak["horizon"]),
        "best_model": str(peak["model"]),
        "best_da": float(peak["da"]),
        "best_auc": float(peak["auc"]) if pd.notna(peak["auc"]) else None,
        "n_horizons_tested": int(best["horizon"].nunique()),
        "n_robust_horizons": len(zone),
    }


def _report_text(results: pd.DataFrame, zone_payload: dict[str, Any]) -> str:
    best = _best_ml_by_horizon(results)
    filtered_nobs = best.loc[best["n_obs_test"] < 100, "horizon"].astype(int).tolist() if not best.empty else []
    beating = (
        best.loc[best["delta_da_vs_seasonal"] >= 0.02, "horizon"].astype(int).tolist()
        if not best.empty
        else []
    )
    lines = [
        "Horizon sweep V3-02 — résultats",
        "",
        f"Horizons testés : {int(results['horizon'].nunique()) if not results.empty else 0}",
        f"Meilleure zone robuste : {zone_payload.get('robust_zone', [])}",
        f"Verdict garde-fous : {zone_payload.get('guardrail_verdict')}",
        f"Horizons candidats V3-03 : {zone_payload.get('candidate_horizons_for_v3_03', [])}",
        f"Pic absolu : J+{zone_payload.get('best_horizon')} ({zone_payload.get('best_model')})",
        f"DA pic : {zone_payload.get('best_da')}",
        f"AUC pic : {zone_payload.get('best_auc')}",
        f"Horizons filtrés n_obs < 100 : {filtered_nobs}",
        f"Horizons battant seasonal +2pts DA : {beating}",
        "",
        "Top ML par horizon :",
    ]
    if not best.empty:
        for _, row in best.iterrows():
            lines.append(
                f"J+{int(row['horizon']):<3} {row['model']:<12} "
                f"DA={row['da']:.3f} AUC={row['auc']:.3f} "
                f"Δseasonal={row['delta_da_vs_seasonal']:.3f} n={int(row['n_obs_test'])}"
            )
    return "\n".join(lines) + "\n"


def _empty_result(horizon: int, model_name: str, n_obs: int, reason: str) -> dict[str, Any]:
    return {
        "horizon": int(horizon),
        "model": model_name,
        "n_obs": int(n_obs),
        "n_obs_test": 0,
        "n_folds": 0,
        "da": np.nan,
        "auc": np.nan,
        "brier": np.nan,
        "rmse": np.nan,
        "da_top20pct": np.nan,
        "strong_signal_freq": np.nan,
        "test_start": None,
        "test_end": None,
        "max_train_or_test_date": None,
        "embargo_days": int(horizon),
        "eligibility": reason,
    }


if __name__ == "__main__":
    run_project_horizon_sweep()
