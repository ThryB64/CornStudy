"""V6-01 — Expanded EMA/CBOT target laboratories."""

from __future__ import annotations

import json
from functools import lru_cache
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
from mais.research.ema_target_lab_v5 import build_target_frame as build_ema_target_frame_v5
from mais.research.ema_utils import binary_target_from_future_return, crop_year
from mais.research.experiment_registry_v6 import make_record, save_registry

_OUTPUT_DIR = ARTEFACTS_DIR / "v6"
_OUTPUT = _OUTPUT_DIR / "target_labs_v6.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "TARGET_LABS_V6.md"
_EMA_HORIZONS = (10, 20, 40, 60, 90, 120)
_CBOT_HORIZONS = (10, 20, 40, 60, 90)
_MIN_TRAIN = 120
_MIN_TEST = 20
_MIN_EVAL = 80

_FEATURES = [
    "ema_cbot_basis",
    "ema_cbot_basis_zscore_52w",
    "ema_front_vol_20d_adjusted",
    "corn_realized_vol_20",
    "corn_logret_20d",
    "corn_gas_ratio",
    "fedfunds_level_zscore",
    "drought_composite",
    "drought_d2plus",
    "crop_ge_pct",
    "crop_condition_momentum_2w",
    "cot_mm_net",
    "cot_mm_net_zscore",
    "wasde_ending_stocks",
    "wasde_stocks_to_use",
]


def _label(condition: pd.Series, valid: pd.Series) -> pd.Series:
    return pd.Series(np.where(valid, condition.astype(float), np.nan), index=condition.index, dtype="float64")


def _price_col(df: pd.DataFrame) -> str:
    for col in ("corn_close", "cbot_eur_t", "Close"):
        if col in df.columns and df[col].notna().sum() > 200:
            return col
    raise KeyError("No usable CBOT price column found")


def build_target_frames_v6() -> dict[str, pd.DataFrame]:
    """Build EMA and CBOT target frames with tail NaNs preserved."""
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    cbot = feats.sort_values("Date").reset_index(drop=True).copy()
    cbot["crop_year"] = cbot["Date"].apply(crop_year)
    cbot["month"] = cbot["Date"].dt.month
    price = pd.to_numeric(cbot[_price_col(cbot)], errors="coerce")
    for horizon in _CBOT_HORIZONS:
        ret = price.pct_change(horizon).shift(-horizon)
        cbot[f"cbot_return_h{horizon}"] = ret
        cbot[f"y_cbot_up_h{horizon}"] = binary_target_from_future_return(ret)
        cbot[f"y_cbot_large_up_3pct_h{horizon}"] = _label(ret > 0.03, ret.notna())
        cbot[f"y_cbot_large_down_3pct_h{horizon}"] = _label(ret < -0.03, ret.notna())
        cbot[f"y_cbot_rally_5pct_h{horizon}"] = _label(ret > 0.05, ret.notna())
        cbot[f"y_cbot_drawdown_5pct_h{horizon}"] = _label(ret < -0.05, ret.notna())
    if "wasde_stocks_to_use" in cbot.columns:
        tight = cbot["wasde_stocks_to_use"] <= cbot["wasde_stocks_to_use"].expanding(120).quantile(0.25).shift(1)
        cbot["y_cbot_up_when_stocks_tight_h60"] = _label(cbot["cbot_return_h60"] > 0, tight & cbot["cbot_return_h60"].notna())
    if "cot_mm_net_zscore" in cbot.columns:
        short = cbot["cot_mm_net_zscore"] <= -1.0
        long = cbot["cot_mm_net_zscore"] >= 1.0
        cbot["y_cbot_up_when_cot_extreme_short_h60"] = _label(cbot["cbot_return_h60"] > 0, short & cbot["cbot_return_h60"].notna())
        cbot["y_cbot_down_when_cot_extreme_long_h60"] = _label(cbot["cbot_return_h60"] < 0, long & cbot["cbot_return_h60"].notna())

    ema = build_ema_target_frame_v5(_EMA_HORIZONS)
    return {"ema": ema, "cbot": cbot}


def _target_columns(frame: pd.DataFrame, prefix: str) -> list[str]:
    return [col for col in frame.columns if col.startswith(prefix)]


def _present_features(df: pd.DataFrame) -> list[str]:
    return [col for col in _FEATURES if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]


def _support(frame: pd.DataFrame, target: str) -> dict:
    y = frame[target].dropna()
    yearly = frame.dropna(subset=[target]).groupby("crop_year")[target].agg(["size", "mean"]).reset_index()
    base_rate = float(y.mean()) if len(y) else None
    rare = bool(base_rate is not None and (base_rate < 0.05 or base_rate > 0.95))
    return {
        "target": target,
        "n": int(len(y)),
        "base_rate": base_rate,
        "rare": rare,
        "years_with_support": int((yearly["size"] >= 20).sum()) if not yearly.empty else 0,
        "yearly_support": yearly.rename(columns={"size": "n", "mean": "base_rate"}).to_dict(orient="records"),
    }


def _oof(frame: pd.DataFrame, target: str, features: list[str]) -> pd.DataFrame:
    work = frame[["Date", "crop_year", target, *features]].copy()
    for col in features:
        work[f"{col}_lag1"] = work[col].shift(1)
    lag_cols = [f"{col}_lag1" for col in features]
    work = work.replace([np.inf, -np.inf], np.nan).dropna(subset=[target, *lag_cols])
    rows = []
    years = sorted(work["crop_year"].unique())
    for idx in range(3, len(years)):
        train = work[work["crop_year"].isin(years[:idx])]
        test = work[work["crop_year"].eq(years[idx])]
        if len(train) < _MIN_TRAIN or len(test) < _MIN_TEST or train[target].nunique() < 2 or test[target].nunique() < 2:
            continue
        model = LogisticRegression(max_iter=500, class_weight="balanced", solver="liblinear")
        model.fit(train[lag_cols], train[target])
        prob = model.predict_proba(test[lag_cols])[:, 1]
        out = test[["Date", "crop_year", target]].rename(columns={target: "y_true"}).copy()
        out["prob"] = prob
        out["y_pred"] = (prob >= 0.5).astype(float)
        out["confidence"] = np.abs(prob - 0.5)
        rows.append(out)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _metrics(pred: pd.DataFrame, *, market: str, target: str) -> dict:
    if len(pred) < _MIN_EVAL or pred["y_true"].nunique() < 2:
        return {"market": market, "target": target, "status": "SKIPPED", "n_oof": int(len(pred))}
    y = pred["y_true"].astype(float)
    y_pred = pred["y_pred"].astype(float)
    top = pred.nlargest(max(1, int(len(pred) * 0.20)), "confidence")
    return {
        "market": market,
        "target": target,
        "status": "OK",
        "n_oof": int(len(pred)),
        "base_rate_oof": float(y.mean()),
        "da": float(accuracy_score(y, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y, y_pred)),
        "auc": float(roc_auc_score(y, pred["prob"])),
        "mcc": float(matthews_corrcoef(y, y_pred)),
        "top20_da": float(accuracy_score(top["y_true"], top["y_pred"])),
    }


def _verdict(row: dict) -> str:
    if row.get("status") != "OK":
        return "SKIPPED"
    if row["auc"] >= 0.70 and row["balanced_accuracy"] >= 0.62:
        return "PROMISING"
    if row["auc"] >= 0.60 and row["balanced_accuracy"] >= 0.55:
        return "WATCHLIST"
    return "NO_GO"


@lru_cache(maxsize=1)
def build_target_labs_v6() -> dict:
    frames = build_target_frames_v6()
    results = []
    supports = []
    for market, frame in frames.items():
        target_prefix = "y_rel_" if market == "ema" else "y_cbot_"
        targets = _target_columns(frame, target_prefix)
        features = _present_features(frame)
        for target in targets:
            support = _support(frame, target)
            supports.append({"market": market, **support})
            pred = _oof(frame, target, features)
            row = _metrics(pred, market=market, target=target)
            row["verdict"] = _verdict(row)
            row["support_n"] = support["n"]
            row["base_rate_full"] = support["base_rate"]
            row["rare"] = support["rare"]
            results.append(row)
    ok = [row for row in results if row["status"] == "OK"]
    best_ema = max((row for row in ok if row["market"] == "ema"), key=lambda row: row["auc"], default={})
    best_cbot = max((row for row in ok if row["market"] == "cbot"), key=lambda row: row["auc"], default={})
    records = [
        make_record(
            experiment_id=f"V6-01-{row['market']}-{row['target']}",
            feature_set=f"{row['market']}_target_lab_v6",
            target=row["target"],
            horizon=_infer_horizon(row["target"]),
            model="logistic_baseline",
            cv_protocol="crop_year_oof",
            metrics={k: row[k] for k in ("auc", "balanced_accuracy", "top20_da") if k in row},
            verdict=row["verdict"],
            artefact_paths=["artefacts/v6/target_labs_v6.json"],
        )
        for row in ok[:25]
    ]
    registry = save_registry(records) if records else {}
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "scope": "Expanded V6 target labs for EMA premium and CBOT directional/risk targets.",
        "support": supports,
        "results": results,
        "registry": registry,
        "key_findings": {
            "n_targets": int(len(results)),
            "n_ok": int(len(ok)),
            "best_ema_target": best_ema.get("target"),
            "best_ema_auc": best_ema.get("auc"),
            "best_ema_balanced_accuracy": best_ema.get("balanced_accuracy"),
            "best_cbot_target": best_cbot.get("target"),
            "best_cbot_auc": best_cbot.get("auc"),
            "best_cbot_balanced_accuracy": best_cbot.get("balanced_accuracy"),
            "interpretation": _interpretation(best_ema, best_cbot),
        },
    }


def _infer_horizon(target: str) -> str:
    marker = "_h"
    if marker not in target:
        return "NA"
    return target.rsplit(marker, 1)[-1]


def _interpretation(best_ema: dict, best_cbot: dict) -> str:
    return (
        f"Best EMA target remains premium/relative ({best_ema.get('target')}); "
        f"best CBOT target is {best_cbot.get('target')}. Use these as auxiliary experts for V6 stacking."
    )


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


def _write_doc(data: dict, path: Path) -> None:
    key = data["key_findings"]
    lines = [
        "# TARGET LABS V6",
        "",
        "> Cibles auxiliaires EMA premium et CBOT pour alimenter le stacking V6.",
        "",
        "## Verdict",
        "",
        f"- Cibles testees : {key['n_targets']}",
        f"- Cibles OOF evaluables : {key['n_ok']}",
        f"- Meilleure cible EMA : `{key.get('best_ema_target')}` AUC {_fmt(key.get('best_ema_auc'))}",
        f"- Meilleure cible CBOT : `{key.get('best_cbot_target')}` AUC {_fmt(key.get('best_cbot_auc'))}",
        f"- Lecture : {key['interpretation']}",
        "",
        "## Resultats",
        "",
        "| Market | Target | Verdict | n OOF | AUC | Bal. acc | Top20 | Rare |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in data["results"]:
        lines.append(
            f"| {row['market']} | `{row['target']}` | {row['verdict']} | {row.get('n_oof', 0)} | "
            f"{_fmt(row.get('auc'))} | {_fmt(row.get('balanced_accuracy'))} | {_fmt(row.get('top20_da'))} | {row.get('rare')} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_target_labs_v6(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_target_labs_v6()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_doc(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_target_labs_v6()
    print(f"Target labs V6 saved -> {out}")
