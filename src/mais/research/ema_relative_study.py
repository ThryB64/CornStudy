"""REL-EMA-02 — Étude relative EMA/CBOT multi-horizon."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    matthews_corrcoef,
    roc_auc_score,
)

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, PROJECT_ROOT
from mais.research.ema_utils import binary_target_from_future_return, bootstrap_ci, crop_year

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_relative_study.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_RELATIVE_STUDY.md"
_HORIZONS = (10, 20, 40, 60, 90)
_FEATURES = [
    "ema_cbot_basis",
    "ema_cbot_basis_zscore_52w",
    "ema_front_vol_20d_adjusted",
    "corn_realized_vol_20",
    "corn_logret_20d",
    "corn_gas_ratio",
    "fedfunds_level_zscore",
]


def build_relative_frame(horizons: tuple[int, ...] = _HORIZONS) -> pd.DataFrame:
    """Build EMA-CBOT relative returns and binary outperformance targets."""
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    df = feats[feats["ema_front_price"].notna() & feats["cbot_eur_t"].notna()].copy()
    df = df.sort_values("Date").reset_index(drop=True)
    df["crop_year"] = df["Date"].apply(crop_year)
    df["month"] = df["Date"].dt.month
    for horizon in horizons:
        ema_ret = df["ema_front_price"].pct_change(horizon).shift(-horizon)
        cbot_ret = df["cbot_eur_t"].pct_change(horizon).shift(-horizon)
        df[f"ema_return_h{horizon}"] = ema_ret
        df[f"cbot_eur_return_h{horizon}"] = cbot_ret
        df[f"relative_return_h{horizon}"] = ema_ret - cbot_ret
        df[f"y_ema_outperforms_cbot_h{horizon}"] = binary_target_from_future_return(
            df[f"relative_return_h{horizon}"]
        )
    return df


def _feature_columns(df: pd.DataFrame) -> list[str]:
    return [col for col in _FEATURES if col in df.columns]


def oof_relative_predictions(
    df: pd.DataFrame | None = None,
    *,
    horizon: int = 40,
    weekly: bool = False,
) -> pd.DataFrame:
    """Return OOF predictions for one relative EMA/CBOT horizon."""
    work = (df.copy() if df is not None else build_relative_frame()).sort_values("Date").reset_index(drop=True)
    target = f"y_ema_outperforms_cbot_h{horizon}"
    feature_cols = _feature_columns(work)
    for col in feature_cols:
        work[f"{col}_lag1"] = work[col].shift(1)
    lag_cols = [f"{col}_lag1" for col in feature_cols]
    cols = [
        "Date",
        "crop_year",
        "month",
        target,
        f"relative_return_h{horizon}",
        f"ema_return_h{horizon}",
        f"cbot_eur_return_h{horizon}",
        "ema_cbot_basis",
        "ema_cbot_basis_zscore_52w",
        *lag_cols,
    ]
    cols = [col for col in cols if col in work.columns]
    work = work[cols].replace([np.inf, -np.inf], np.nan).dropna(subset=[target, *lag_cols])
    if weekly:
        work = work.set_index("Date").resample("W-FRI").last().dropna(subset=[target, *lag_cols]).reset_index()
        work["crop_year"] = work["Date"].apply(crop_year)
        work["month"] = work["Date"].dt.month
    years = sorted(work["crop_year"].unique())
    predictions = []
    for idx in range(3, len(years)):
        train = work[work["crop_year"].isin(years[:idx])]
        test = work[work["crop_year"].eq(years[idx])]
        if len(train) < 100 or len(test) < 20 or train[target].nunique() < 2:
            continue
        model = LogisticRegression(max_iter=500, class_weight="balanced", solver="liblinear")
        model.fit(train[lag_cols], train[target])
        prob = model.predict_proba(test[lag_cols])[:, 1]
        pred = (prob >= 0.5).astype(float)
        out = test[[
            "Date",
            "crop_year",
            "month",
            target,
            f"relative_return_h{horizon}",
            f"ema_return_h{horizon}",
            f"cbot_eur_return_h{horizon}",
            "ema_cbot_basis",
            "ema_cbot_basis_zscore_52w",
        ]].copy()
        out = out.rename(columns={target: "y_true"})
        out["y_pred"] = pred
        out["prob"] = prob
        out["confidence"] = np.abs(prob - 0.5)
        out["horizon"] = int(horizon)
        out["frequency"] = "weekly" if weekly else "daily"
        predictions.append(out)
    return pd.concat(predictions, ignore_index=True) if predictions else pd.DataFrame()


def _evaluate_predictions(pred: pd.DataFrame, *, horizon: int, weekly: bool) -> dict:
    if pred.empty or pred["y_true"].nunique() < 2:
        return {
            "horizon": int(horizon),
            "frequency": "weekly" if weekly else "daily",
            "status": "SKIPPED",
            "reason": "no_valid_oof_predictions",
            "n": int(len(pred)),
        }
    y = pred["y_true"].astype(float)
    y_pred = pred["y_pred"].astype(float)
    correct = y.eq(y_pred).astype(float)
    ci = bootstrap_ci(correct.to_numpy(), np.mean, n_draws=500)
    top_n = max(1, int(len(pred) * 0.20))
    top = pred.nlargest(top_n, "confidence")
    annual = (
        pred.assign(correct=correct)
        .groupby("crop_year")
        .agg(n=("correct", "size"), da=("correct", "mean"), base_rate=("y_true", "mean"))
        .reset_index()
    )
    return {
        "horizon": int(horizon),
        "frequency": "weekly" if weekly else "daily",
        "status": "OK",
        "n": int(len(pred)),
        "base_rate": float(y.mean()),
        "da": float(accuracy_score(y, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y, y_pred)),
        "auc": float(roc_auc_score(y, pred["prob"])),
        "mcc": float(matthews_corrcoef(y, y_pred)),
        "top20_da": float(accuracy_score(top["y_true"], top["y_pred"])),
        "ci95_da_lo": ci["ci_lo"],
        "ci95_da_hi": ci["ci_hi"],
        "annual_stability_share_da_ge_53": float((annual["da"] >= 0.53).mean()),
        "annual_results": annual.to_dict(orient="records"),
    }


def _distribution(df: pd.DataFrame) -> dict:
    out = {}
    for horizon in _HORIZONS:
        rel = df[f"relative_return_h{horizon}"].dropna()
        target = df[f"y_ema_outperforms_cbot_h{horizon}"].dropna()
        out[str(horizon)] = {
            "n": int(len(rel)),
            "mean": float(rel.mean()),
            "std": float(rel.std()),
            "p05": float(rel.quantile(0.05)),
            "p50": float(rel.quantile(0.50)),
            "p95": float(rel.quantile(0.95)),
            "base_rate": float(target.mean()) if len(target) else float("nan"),
        }
    return out


def _seasonal_summary(pred: pd.DataFrame) -> list[dict]:
    if pred.empty:
        return []
    seasonal = (
        pred.assign(correct=pred["y_true"].eq(pred["y_pred"]).astype(float))
        .groupby("month")
        .agg(n=("correct", "size"), da=("correct", "mean"), base_rate=("y_true", "mean"))
        .reset_index()
    )
    return seasonal.to_dict(orient="records")


def build_relative_study() -> dict:
    df = build_relative_frame()
    daily_results = []
    weekly_results = []
    for horizon in _HORIZONS:
        daily_results.append(_evaluate_predictions(oof_relative_predictions(df, horizon=horizon), horizon=horizon, weekly=False))
        weekly_results.append(_evaluate_predictions(oof_relative_predictions(df, horizon=horizon, weekly=True), horizon=horizon, weekly=True))
    valid = [row for row in daily_results if row.get("status") == "OK"]
    best = max(valid, key=lambda row: (row.get("auc", -1), row.get("balanced_accuracy", -1)), default={})
    h40_pred = oof_relative_predictions(df, horizon=40)
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "scope": "EMA relative to CBOT converted in EUR/t; not absolute EMA direction.",
        "horizons": list(_HORIZONS),
        "relative_return_distribution": _distribution(df),
        "daily_results": daily_results,
        "weekly_results": weekly_results,
        "seasonal_h40": _seasonal_summary(h40_pred),
        "top20_h40_summary": _evaluate_predictions(h40_pred.nlargest(max(1, int(len(h40_pred) * 0.20)), "confidence"), horizon=40, weekly=False),
        "key_findings": {
            "best_horizon": best.get("horizon"),
            "best_daily_auc": best.get("auc"),
            "best_daily_da": best.get("da"),
            "best_daily_balanced_accuracy": best.get("balanced_accuracy"),
            "best_top20_da": best.get("top20_da"),
            "h40_auc": next((row.get("auc") for row in daily_results if row.get("horizon") == 40), None),
            "h40_weekly_auc": next((row.get("auc") for row in weekly_results if row.get("horizon") == 40), None),
            "verdict": "RELATIVE_EMA_CBOT_SIGNAL_CONFIRMED" if best.get("auc", 0) >= 0.60 else "RELATIVE_SIGNAL_WEAK",
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


def _fmt(value: object, digits: int = 3) -> str:
    if value is None:
        return "N/A"
    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return str(value)
    return "N/A" if not np.isfinite(value_float) else f"{value_float:.{digits}f}"


def _write_markdown(data: dict, path: Path) -> None:
    k = data["key_findings"]
    lines = [
        "# EMA RELATIVE STUDY",
        "",
        "> Étude reproductible de la performance relative EMA/CBOT. Ce n'est pas une prédiction de direction EMA absolue.",
        "",
        "## Verdict",
        "",
        f"- Verdict : {k['verdict']}",
        f"- Meilleur horizon : H{k.get('best_horizon')}",
        f"- AUC daily meilleur horizon : {_fmt(k.get('best_daily_auc'))}",
        f"- Balanced accuracy : {_fmt(k.get('best_daily_balanced_accuracy'))}",
        f"- Top20 DA : {_fmt(k.get('best_top20_da'))}",
        "",
        "## Résultats daily",
        "",
        "| Horizon | n | Base rate | DA | AUC | Balanced acc. | Top20 DA | Stabilité annuelle |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["daily_results"]:
        if row.get("status") != "OK":
            continue
        lines.append(
            f"| {row['horizon']} | {row['n']} | {_fmt(row['base_rate'])} | {_fmt(row['da'])} | "
            f"{_fmt(row['auc'])} | {_fmt(row['balanced_accuracy'])} | {_fmt(row['top20_da'])} | "
            f"{_fmt(row['annual_stability_share_da_ge_53'])} |"
        )
    lines += [
        "",
        "## Résultats weekly",
        "",
        "| Horizon | n | DA | AUC | Balanced acc. | Top20 DA |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["weekly_results"]:
        if row.get("status") != "OK":
            continue
        lines.append(
            f"| {row['horizon']} | {row['n']} | {_fmt(row['da'])} | {_fmt(row['auc'])} | "
            f"{_fmt(row['balanced_accuracy'])} | {_fmt(row['top20_da'])} |"
        )
    lines += [
        "",
        "## Lecture",
        "",
        "La cible relative retire le moteur mondial CBOT et isole mieux la prime européenne. C'est le cœur prédictif actuel de l'étude EMA.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_relative_study(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_relative_study()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_relative_study()
    print(f"Relative EMA/CBOT study saved -> {out}")
