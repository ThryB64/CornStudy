"""EMA price interval study with conformal baselines and CQR models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mais.features.ema_targets import EMA_TARGETS_PARQUET
from mais.meta.cqr import CQRModel, _finite_sample_residual_quantile
from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, PROJECT_ROOT
from mais.research.ema_data_audit import SOURCE_QUALITY_NOTE
from mais.research.ema_feature_selector import EMA_FEATURE_SELECTION_REPORT
from mais.research.proxy_audit import assert_no_proxy_in_benchmark

EMA_PRICE_CQR_JSON = ARTEFACTS_DIR / "ema_study" / "ema_price_cqr_study.json"
EMA_PRICE_CQR_MD = PROJECT_ROOT / "docs" / "EMA_PRICE_CQR_STUDY.md"
PRICE_TARGETS: dict[str, str] = {
    "h20": "y_price_h20_ema_raw",
    "h60": "y_price_h60_ema_raw",
}
BASELINE_CURRENT_PRICE_COL = "ema_front_price_lag1"
CBOT_CONVERTED_COL = "cbot_eur_t"
FALLBACK_PRICE_FEATURES: tuple[str, ...] = (
    "ema_front_price_lag1",
    "ema_liquid_price_lag1",
    "ema_harvest_nov_price_lag1",
    "ema_cbot_basis",
    "ema_cbot_basis_zscore_52w",
    "cbot_eur_t",
    "ema_oi_total",
    "ema_volume_total",
    "ema_front_return_5d_adjusted",
    "ema_front_vol_20d_adjusted",
)


def run_ema_price_cqr_study(
    *,
    features_path: Path = FEATURES_PARQUET,
    ema_targets_path: Path = EMA_TARGETS_PARQUET,
    selection_report_path: Path = EMA_FEATURE_SELECTION_REPORT,
    output_json_path: Path = EMA_PRICE_CQR_JSON,
    output_markdown_path: Path = EMA_PRICE_CQR_MD,
    max_date: str | pd.Timestamp = "2022-12-31",
    target_coverage: float = 0.90,
    n_splits: int = 8,
    min_train_years: int = 3,
    seasonal_lag: int = 252,
    n_estimators: int = 120,
) -> dict[str, Any]:
    """Run EMA price interval forecasts and write JSON/Markdown reports."""
    features = pd.read_parquet(features_path)
    targets = pd.read_parquet(ema_targets_path)
    selected = _load_selected_features(selection_report_path)
    payload_rows: list[dict[str, Any]] = []
    predictions_rows: list[pd.DataFrame] = []
    for horizon_label, target_col in PRICE_TARGETS.items():
        frame = build_price_frame(
            features,
            targets,
            target_col=target_col,
            max_date=max_date,
            seasonal_lag=seasonal_lag,
        )
        assert_no_proxy_in_benchmark(frame)
        feature_cols = build_price_feature_columns(selected, frame)
        configs = _model_configs(feature_cols, n_estimators=n_estimators)
        for config in configs:
            preds = walk_forward_price_intervals(
                frame,
                target_col=target_col,
                model_name=config["name"],
                model_kind=config["kind"],
                feature_cols=config.get("feature_cols", []),
                point_col=config.get("point_col"),
                target_coverage=target_coverage,
                n_splits=n_splits,
                min_train_years=min_train_years,
                n_estimators=n_estimators,
            )
            metrics = evaluate_price_intervals(
                preds,
                target_col=target_col,
                target_coverage=target_coverage,
            )
            payload_rows.append(
                {
                    "horizon": horizon_label,
                    "target_col": target_col,
                    "model": config["name"],
                    "kind": config["kind"],
                    "n_features": int(len(config.get("feature_cols", []))),
                    **metrics,
                }
            )
            if not preds.empty:
                predictions_rows.append(preds.assign(horizon=horizon_label, model=config["name"]))

    results = pd.DataFrame(payload_rows)
    decision = decide_price_cqr(results, target_coverage=target_coverage)
    payload = {
        "source_quality_note": SOURCE_QUALITY_NOTE,
        "max_date": str(max_date),
        "target_coverage": target_coverage,
        "targets": PRICE_TARGETS,
        "results": results.to_dict(orient="records"),
        "decision": decision,
    }
    if predictions_rows:
        pred_table = pd.concat(predictions_rows, ignore_index=True)
        payload["prediction_rows"] = int(len(pred_table))
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    output_markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def build_price_frame(
    features: pd.DataFrame,
    targets: pd.DataFrame,
    *,
    target_col: str,
    max_date: str | pd.Timestamp,
    seasonal_lag: int = 252,
) -> pd.DataFrame:
    """Join feature rows to one EMA future-price target."""
    if target_col not in targets.columns:
        raise ValueError(f"Missing EMA price target: {target_col}")
    work = _normalise_dates(features)
    target = _normalise_dates(targets)
    out = work.merge(target[["Date", target_col]], on="Date", how="inner")
    out = out[out["Date"] <= pd.Timestamp(max_date)].copy()
    if "ema_data_availability_score" in out.columns:
        out = out[pd.to_numeric(out["ema_data_availability_score"], errors="coerce") > 0].copy()
    out = out.sort_values("Date").reset_index(drop=True)
    out["seasonal_naive_price"] = pd.to_numeric(out[target_col], errors="coerce").shift(int(seasonal_lag))
    return out


def build_price_feature_columns(selected_features: list[str], frame: pd.DataFrame) -> list[str]:
    """Select numeric model features without leaking EMA price targets."""
    forbidden = {"Date", *PRICE_TARGETS.values(), "seasonal_naive_price"}
    selected = [
        col
        for col in selected_features
        if col in frame.columns
        and col not in forbidden
        and not str(col).startswith("y_")
        and "is_proxy" not in str(col)
    ]
    if selected:
        return selected
    return [col for col in FALLBACK_PRICE_FEATURES if col in frame.columns]


def walk_forward_price_intervals(
    frame: pd.DataFrame,
    *,
    target_col: str,
    model_name: str,
    model_kind: str,
    feature_cols: list[str] | None = None,
    point_col: str | None = None,
    target_coverage: float = 0.90,
    n_splits: int = 8,
    min_train_years: int = 3,
    n_estimators: int = 120,
) -> pd.DataFrame:
    """Produce walk-forward price intervals for one baseline or model."""
    work = frame[["Date", target_col, *(feature_cols or []), *([point_col] if point_col else [])]].copy()
    work = work.replace([np.inf, -np.inf], np.nan).dropna(subset=["Date", target_col])
    work = work.sort_values("Date").reset_index(drop=True)
    splits = _year_splits(work["Date"], min_train_years=min_train_years, n_splits=n_splits)
    rows: list[pd.DataFrame] = []
    for split_id, (train_idx, valid_idx, validation_year) in enumerate(splits, start=1):
        train_core_idx, cal_idx = _train_cal_split(train_idx)
        if len(train_core_idx) < 120 or len(cal_idx) < 40 or len(valid_idx) == 0:
            continue
        if model_kind == "baseline":
            fold = _baseline_interval_fold(
                work,
                target_col=target_col,
                point_col=str(point_col),
                cal_idx=cal_idx,
                valid_idx=valid_idx,
                target_coverage=target_coverage,
            )
        elif model_kind == "cqr":
            fold = _cqr_interval_fold(
                work,
                target_col=target_col,
                feature_cols=feature_cols or [],
                train_idx=train_core_idx,
                cal_idx=cal_idx,
                valid_idx=valid_idx,
                target_coverage=target_coverage,
                n_estimators=n_estimators,
            )
        else:
            fold = _split_conformal_model_fold(
                work,
                target_col=target_col,
                model_kind=model_kind,
                feature_cols=feature_cols or [],
                train_idx=train_core_idx,
                cal_idx=cal_idx,
                valid_idx=valid_idx,
                target_coverage=target_coverage,
                n_estimators=n_estimators,
            )
        if fold.empty:
            continue
        rows.append(
            fold.assign(
                model=model_name,
                model_kind=model_kind,
                target_col=target_col,
                split_id=split_id,
                validation_year=int(validation_year),
            )
        )
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def evaluate_price_intervals(
    predictions: pd.DataFrame,
    *,
    target_col: str,
    target_coverage: float = 0.90,
) -> dict[str, Any]:
    """Compute coverage, sharpness and Winkler loss for interval predictions."""
    if predictions.empty:
        return _empty_metrics("no predictions")
    work = predictions.dropna(subset=["y_true", "q_lo", "q_hi", "midpoint"]).copy()
    if work.empty:
        return _empty_metrics("no finite predictions")
    width = pd.to_numeric(work["q_hi"], errors="coerce") - pd.to_numeric(work["q_lo"], errors="coerce")
    covered = work["y_true"].between(work["q_lo"], work["q_hi"])
    winkler = winkler_loss(work["y_true"], work["q_lo"], work["q_hi"], alpha=1.0 - target_coverage)
    annual_coverage = covered.groupby(pd.to_datetime(work["Date"]).dt.year).mean()
    return {
        "status": "OK",
        "target_col": target_col,
        "n": int(len(work)),
        "coverage": _json_float(covered.mean()),
        "coverage_gap": _json_float(covered.mean() - target_coverage),
        "sharpness_mean_width": _json_float(width.mean()),
        "sharpness_median_width": _json_float(width.median()),
        "winkler_loss": _json_float(winkler.mean()),
        "midpoint_mae": _json_float(np.abs(work["midpoint"] - work["y_true"]).mean()),
        "annual_coverage": {str(int(year)): _json_float(value) for year, value in annual_coverage.items()},
        "annual_coverage_min": _json_float(annual_coverage.min()) if len(annual_coverage) else None,
        "years_at_or_above_coverage": int((annual_coverage >= target_coverage).sum()),
        "years_total": int(annual_coverage.count()),
    }


def winkler_loss(y_true: pd.Series, q_lo: pd.Series, q_hi: pd.Series, *, alpha: float) -> pd.Series:
    """Compute interval Winkler score; lower is better."""
    y = pd.to_numeric(y_true, errors="coerce")
    lo = pd.to_numeric(q_lo, errors="coerce")
    hi = pd.to_numeric(q_hi, errors="coerce")
    width = hi - lo
    lower_penalty = (2.0 / alpha) * (lo - y).clip(lower=0)
    upper_penalty = (2.0 / alpha) * (y - hi).clip(lower=0)
    return width + lower_penalty + upper_penalty


def decide_price_cqr(results: pd.DataFrame, *, target_coverage: float) -> dict[str, Any]:
    """Decide whether EMA price CQR is usable."""
    ok = results[results["status"].eq("OK")].copy()
    if ok.empty:
        return {"verdict": "CQR_PRICE_NO_GO", "reason": "No interval model produced predictions."}
    ok["coverage"] = pd.to_numeric(ok["coverage"], errors="coerce")
    ok["winkler_loss"] = pd.to_numeric(ok["winkler_loss"], errors="coerce")
    coverage_floor = target_coverage - 0.02
    covered = ok[ok["coverage"] >= coverage_floor].copy()
    best = covered.sort_values(["winkler_loss", "sharpness_mean_width"]).head(1)
    naive = ok[ok["model"].eq("naive_current")].groupby("horizon")["winkler_loss"].min()
    if best.empty:
        row = ok.sort_values("coverage", ascending=False).head(1).iloc[0]
        return {
            "verdict": "CQR_PRICE_NO_GO",
            "reason": "No model reached the minimum acceptable 88% empirical coverage.",
            "best_available": _row_summary(row),
        }
    row = best.iloc[0]
    naive_winkler = float(naive.get(row["horizon"], np.nan))
    beats_naive = np.isfinite(naive_winkler) and float(row["winkler_loss"]) < naive_winkler
    if float(row["coverage"]) >= target_coverage and beats_naive:
        verdict = "CQR_PRICE_PROMISING"
        reason = "Best interval reaches target coverage and improves Winkler loss versus naive current-price intervals."
    else:
        verdict = "CQR_PRICE_PARTIAL"
        reason = "At least one interval reaches acceptable coverage, but target coverage or naive improvement is incomplete."
    return {
        "verdict": verdict,
        "reason": reason,
        "best_interval": _row_summary(row),
        "naive_winkler_same_horizon": _json_float(naive_winkler),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    """Render the EMA price interval report."""
    lines = [
        "# EMA Price CQR Study",
        "",
        f"> {payload['source_quality_note']}",
        "",
        "## Verdict",
        "",
        f"- `{payload['decision']['verdict']}`: {payload['decision']['reason']}",
        "",
        "## Résultats",
        "",
        "| Horizon | Modèle | Coverage | Width mean | Winkler | MAE midpoint | N |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["results"]:
        lines.append(
            "| {horizon} | {model} | {coverage} | {width} | {winkler} | {mae} | {n} |".format(
                horizon=row["horizon"],
                model=row["model"],
                coverage=_fmt_pct(row.get("coverage")),
                width=_fmt_num(row.get("sharpness_mean_width")),
                winkler=_fmt_num(row.get("winkler_loss")),
                mae=_fmt_num(row.get("midpoint_mae")),
                n=row.get("n", 0),
            )
        )
    lines.extend(
        [
            "",
            "## Lecture",
            "",
            "- Le prix cible est le prix EMA futur brut, afin de produire une fourchette exploitable métier.",
            "- Les baselines sont conformalisées avec les résidus de calibration walk-forward.",
            "- `coverage` mesure la proportion de prix futurs contenus dans l'intervalle.",
            "- `Width mean` mesure la netteté : plus c'est bas, plus l'intervalle est exploitable.",
            "- `Winkler` pénalise à la fois les intervalles trop larges et les prix hors intervalle.",
        ]
    )
    return "\n".join(lines) + "\n"


def _model_configs(feature_cols: list[str], *, n_estimators: int) -> list[dict[str, Any]]:
    del n_estimators
    return [
        {"name": "naive_current", "kind": "baseline", "point_col": BASELINE_CURRENT_PRICE_COL},
        {"name": "seasonal_naive_1y", "kind": "baseline", "point_col": "seasonal_naive_price"},
        {"name": "cbot_converted", "kind": "baseline", "point_col": CBOT_CONVERTED_COL},
        {"name": "ridge_selected", "kind": "ridge", "feature_cols": feature_cols},
        {"name": "histgb_selected", "kind": "histgb", "feature_cols": feature_cols},
        {"name": "cqr_quantile_selected", "kind": "cqr", "feature_cols": feature_cols},
    ]


def _baseline_interval_fold(
    work: pd.DataFrame,
    *,
    target_col: str,
    point_col: str,
    cal_idx: np.ndarray,
    valid_idx: np.ndarray,
    target_coverage: float,
) -> pd.DataFrame:
    if point_col not in work.columns:
        return pd.DataFrame()
    cal = work.loc[cal_idx, ["Date", target_col, point_col]].dropna()
    test = work.loc[valid_idx, ["Date", target_col, point_col]].dropna()
    if cal.empty or test.empty:
        return pd.DataFrame()
    residuals = (cal[target_col].astype(float) - cal[point_col].astype(float)).abs().to_numpy()
    q = _finite_sample_residual_quantile(residuals, 1.0 - target_coverage)
    midpoint = test[point_col].astype(float)
    return pd.DataFrame(
        {
            "Date": test["Date"].to_numpy(),
            "y_true": test[target_col].to_numpy(dtype=float),
            "q_lo": (midpoint - q).to_numpy(dtype=float),
            "q_hi": (midpoint + q).to_numpy(dtype=float),
            "midpoint": midpoint.to_numpy(dtype=float),
        }
    )


def _split_conformal_model_fold(
    work: pd.DataFrame,
    *,
    target_col: str,
    model_kind: str,
    feature_cols: list[str],
    train_idx: np.ndarray,
    cal_idx: np.ndarray,
    valid_idx: np.ndarray,
    target_coverage: float,
    n_estimators: int,
) -> pd.DataFrame:
    if not feature_cols:
        return pd.DataFrame()
    model = _point_model(model_kind, n_estimators=n_estimators)
    train = work.loc[train_idx, [target_col, *feature_cols]].dropna(subset=[target_col])
    cal = work.loc[cal_idx, ["Date", target_col, *feature_cols]].dropna(subset=[target_col])
    test = work.loc[valid_idx, ["Date", target_col, *feature_cols]].dropna(subset=[target_col])
    if len(train) < 120 or len(cal) < 40 or test.empty:
        return pd.DataFrame()
    model.fit(train[feature_cols], train[target_col].astype(float))
    cal_pred = model.predict(cal[feature_cols])
    q = _finite_sample_residual_quantile(np.abs(cal[target_col].to_numpy(dtype=float) - cal_pred), 1.0 - target_coverage)
    pred = model.predict(test[feature_cols])
    return pd.DataFrame(
        {
            "Date": test["Date"].to_numpy(),
            "y_true": test[target_col].to_numpy(dtype=float),
            "q_lo": pred - q,
            "q_hi": pred + q,
            "midpoint": pred,
        }
    )


def _cqr_interval_fold(
    work: pd.DataFrame,
    *,
    target_col: str,
    feature_cols: list[str],
    train_idx: np.ndarray,
    cal_idx: np.ndarray,
    valid_idx: np.ndarray,
    target_coverage: float,
    n_estimators: int,
) -> pd.DataFrame:
    if not feature_cols:
        return pd.DataFrame()
    train = work.loc[train_idx, [target_col, *feature_cols]].dropna(subset=[target_col])
    cal = work.loc[cal_idx, ["Date", target_col, *feature_cols]].dropna(subset=[target_col])
    test = work.loc[valid_idx, ["Date", target_col, *feature_cols]].dropna(subset=[target_col])
    if len(train) < 120 or len(cal) < 40 or test.empty:
        return pd.DataFrame()
    model = CQRModel(coverage=target_coverage, n_estimators=n_estimators)
    model.fit(train[feature_cols], train[target_col], cal[feature_cols], cal[target_col])
    intervals = model.predict_intervals(test[feature_cols])
    return pd.DataFrame(
        {
            "Date": test["Date"].to_numpy(),
            "y_true": test[target_col].to_numpy(dtype=float),
            "q_lo": intervals["q_lo"].to_numpy(dtype=float),
            "q_hi": intervals["q_hi"].to_numpy(dtype=float),
            "midpoint": intervals["midpoint"].to_numpy(dtype=float),
        }
    )


def _point_model(model_kind: str, *, n_estimators: int) -> Pipeline:
    if model_kind == "histgb":
        reg = HistGradientBoostingRegressor(
            max_iter=n_estimators,
            learning_rate=0.05,
            l2_regularization=0.10,
            random_state=42,
        )
        return Pipeline([("imputer", SimpleImputer(strategy="median", keep_empty_features=True)), ("model", reg)])
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=1.0)),
        ]
    )


def _year_splits(
    dates: pd.Series,
    *,
    min_train_years: int,
    n_splits: int,
) -> list[tuple[np.ndarray, np.ndarray, int]]:
    years = pd.to_datetime(dates).dt.year.to_numpy()
    unique_years = sorted(pd.unique(years))
    validation_years = unique_years[min_train_years:]
    if n_splits:
        validation_years = validation_years[-int(n_splits) :]
    out: list[tuple[np.ndarray, np.ndarray, int]] = []
    for year in validation_years:
        train_idx = np.flatnonzero(years < year)
        valid_idx = np.flatnonzero(years == year)
        if len(train_idx) and len(valid_idx):
            out.append((train_idx, valid_idx, int(year)))
    return out


def _train_cal_split(train_idx: np.ndarray, *, cal_ratio: float = 0.20, min_cal: int = 80) -> tuple[np.ndarray, np.ndarray]:
    n_cal = max(min_cal, int(round(len(train_idx) * cal_ratio)))
    n_cal = min(n_cal, max(1, len(train_idx) // 2))
    return train_idx[:-n_cal], train_idx[-n_cal:]


def _load_selected_features(path: Path) -> list[str]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    selected = payload.get("selected_features", [])
    return [str(col) for col in selected] if isinstance(selected, list) else []


def _normalise_dates(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["Date"] = pd.to_datetime(work["Date"]).dt.normalize()
    return work


def _empty_metrics(reason: str) -> dict[str, Any]:
    return {
        "status": "SKIPPED",
        "reason": reason,
        "n": 0,
        "coverage": None,
        "coverage_gap": None,
        "sharpness_mean_width": None,
        "sharpness_median_width": None,
        "winkler_loss": None,
        "midpoint_mae": None,
        "annual_coverage": {},
        "annual_coverage_min": None,
        "years_at_or_above_coverage": 0,
        "years_total": 0,
    }


def _row_summary(row: pd.Series) -> dict[str, Any]:
    return {
        "horizon": row.get("horizon"),
        "model": row.get("model"),
        "coverage": _json_float(row.get("coverage")),
        "sharpness_mean_width": _json_float(row.get("sharpness_mean_width")),
        "winkler_loss": _json_float(row.get("winkler_loss")),
        "n": int(row.get("n", 0) or 0),
    }


def _fmt_pct(value: Any) -> str:
    if value is None:
        return "NA"
    return f"{float(value):.1%}"


def _fmt_num(value: Any) -> str:
    if value is None:
        return "NA"
    return f"{float(value):.3f}"


def _json_float(value: Any) -> float | None:
    if value is None:
        return None
    out = float(value)
    return out if np.isfinite(out) else None


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (np.integer, np.floating)):
        return _json_float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


if __name__ == "__main__":
    result = run_ema_price_cqr_study()
    print(json.dumps(_json_ready(result), indent=2, ensure_ascii=False))
