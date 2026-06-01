"""EMA-V5-01 — Target lab for new EMA premium targets."""

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
from mais.research.ema_utils import binary_target_from_future_return, bootstrap_ci, crop_year

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_target_lab_v5.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_TARGET_LAB_V5.md"
_HORIZONS = (20, 40, 90)
_MIN_TRAIN = 120
_MIN_TEST = 20
_MIN_EVAL = 60

_BASE_FEATURES = [
    "ema_cbot_basis",
    "ema_cbot_basis_zscore_52w",
    "ema_front_vol_20d_adjusted",
    "corn_realized_vol_20",
    "corn_logret_20d",
    "corn_gas_ratio",
    "fedfunds_level_zscore",
]

_OPTIONAL_FEATURES = [
    "eurusd_return_20d",
    "eurusd_logret_20d",
    "ttf_return_20d",
    "ttf_logret_20d",
    "eu_heat_stress_days_4w",
    "eu_precip_deficit_30d",
    "eu_gdd_anomaly",
    "wasde_eu_stock_use_ratio",
    "wasde_eu_production",
    "wasde_ukraine_exports",
]


def _label(condition: pd.Series, valid: pd.Series) -> pd.Series:
    values = np.where(valid, condition.astype(float), np.nan)
    return pd.Series(values, index=condition.index, dtype="float64")


def _target_specs(horizon: int) -> list[dict]:
    return [
        {
            "name": f"y_rel_outperform_h{horizon}",
            "family": "relative_direction",
            "description": "EMA outperforms CBOT in EUR/t.",
        },
        {
            "name": f"y_rel_large_outperform_h{horizon}",
            "family": "relative_tail",
            "description": "EMA outperformance exceeds +1.0 percentage point.",
        },
        {
            "name": f"y_rel_large_underperform_h{horizon}",
            "family": "relative_tail",
            "description": "EMA underperformance exceeds -1.0 percentage point.",
        },
        {
            "name": f"y_basis_compress_h{horizon}",
            "family": "basis_reversion",
            "description": "Absolute basis z-score compresses by at least 0.25 from a stressed state.",
        },
        {
            "name": f"y_basis_reverts_to_normal_h{horizon}",
            "family": "basis_reversion",
            "description": "Extreme basis z-score returns near normal.",
        },
        {
            "name": f"y_basis_widens_h{horizon}",
            "family": "basis_continuation",
            "description": "Absolute basis z-score widens by at least 0.25.",
        },
        {
            "name": f"y_rel_outperform_after_cbot_weak_h{horizon}",
            "family": "conditional_relative",
            "description": "EMA outperforms after a weak past CBOT momentum regime.",
        },
        {
            "name": f"y_rel_outperform_when_basis_extreme_h{horizon}",
            "family": "conditional_relative",
            "description": "EMA outperforms when the current basis is already extreme.",
        },
    ]


def build_target_frame(horizons: tuple[int, ...] = _HORIZONS) -> pd.DataFrame:
    """Build exploratory EMA premium targets without converting future NaNs to zeros."""
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    df = feats[feats["ema_front_price"].notna() & feats["cbot_eur_t"].notna()].copy()
    df = df.sort_values("Date").reset_index(drop=True)
    df["crop_year"] = df["Date"].apply(crop_year)
    df["month"] = df["Date"].dt.month

    basis_z = df["ema_cbot_basis_zscore_52w"]
    abs_basis_z = basis_z.abs()
    cbot_weak_now = df.get("corn_logret_20d", pd.Series(np.nan, index=df.index)) < 0

    for horizon in horizons:
        ema_ret = df["ema_front_price"].pct_change(horizon).shift(-horizon)
        cbot_ret = df["cbot_eur_t"].pct_change(horizon).shift(-horizon)
        rel_ret = ema_ret - cbot_ret
        future_basis_z = basis_z.shift(-horizon)
        future_abs_basis_z = future_basis_z.abs()

        df[f"ema_return_h{horizon}"] = ema_ret
        df[f"cbot_eur_return_h{horizon}"] = cbot_ret
        df[f"relative_return_h{horizon}"] = rel_ret
        df[f"basis_z_change_h{horizon}"] = future_basis_z - basis_z
        df[f"abs_basis_z_change_h{horizon}"] = future_abs_basis_z - abs_basis_z

        df[f"y_rel_outperform_h{horizon}"] = binary_target_from_future_return(rel_ret)
        df[f"y_rel_large_outperform_h{horizon}"] = _label(rel_ret > 0.01, rel_ret.notna())
        df[f"y_rel_large_underperform_h{horizon}"] = _label(rel_ret < -0.01, rel_ret.notna())

        stressed = abs_basis_z >= 1.0
        extreme = abs_basis_z >= 1.5
        df[f"y_basis_compress_h{horizon}"] = _label(
            future_abs_basis_z <= abs_basis_z - 0.25,
            stressed & future_abs_basis_z.notna(),
        )
        df[f"y_basis_reverts_to_normal_h{horizon}"] = _label(
            future_abs_basis_z <= 0.75,
            extreme & future_abs_basis_z.notna(),
        )
        df[f"y_basis_widens_h{horizon}"] = _label(
            future_abs_basis_z >= abs_basis_z + 0.25,
            stressed & future_abs_basis_z.notna(),
        )
        df[f"y_rel_outperform_after_cbot_weak_h{horizon}"] = _label(
            rel_ret > 0,
            cbot_weak_now & rel_ret.notna(),
        )
        df[f"y_rel_outperform_when_basis_extreme_h{horizon}"] = _label(
            rel_ret > 0,
            extreme & rel_ret.notna(),
        )
    return df


def _feature_columns(df: pd.DataFrame) -> list[str]:
    exact = [col for col in [*_BASE_FEATURES, *_OPTIONAL_FEATURES] if col in df.columns]
    eu_weather = [
        col
        for col in df.columns
        if col.startswith("eu_") and any(token in col for token in ("gdd", "heat", "precip", "rain"))
    ]
    wasde_eu = [col for col in df.columns if col.startswith(("wasde_eu_", "wasde_ukraine_"))]
    seen = set()
    out = []
    for col in [*exact, *eu_weather, *wasde_eu]:
        if col not in seen and pd.api.types.is_numeric_dtype(df[col]):
            seen.add(col)
            out.append(col)
    return out


def _prepare_model_frame(df: pd.DataFrame, target: str) -> tuple[pd.DataFrame, list[str]]:
    feature_cols = _feature_columns(df)
    work = df[["Date", "crop_year", "month", target, *feature_cols]].copy()
    for col in feature_cols:
        work[f"{col}_lag1"] = work[col].shift(1)
    lag_cols = [f"{col}_lag1" for col in feature_cols]
    work = work[["Date", "crop_year", "month", target, *lag_cols]]
    work = work.replace([np.inf, -np.inf], np.nan).dropna(subset=[target, *lag_cols])
    return work, lag_cols


def _oof_for_target(df: pd.DataFrame, target: str) -> pd.DataFrame:
    work, lag_cols = _prepare_model_frame(df, target)
    years = sorted(work["crop_year"].unique())
    rows = []
    for idx in range(3, len(years)):
        train = work[work["crop_year"].isin(years[:idx])]
        test = work[work["crop_year"].eq(years[idx])]
        if (
            len(train) < _MIN_TRAIN
            or len(test) < _MIN_TEST
            or train[target].nunique() < 2
            or test[target].nunique() < 2
        ):
            continue
        model = LogisticRegression(max_iter=500, class_weight="balanced", solver="liblinear")
        model.fit(train[lag_cols], train[target])
        prob = model.predict_proba(test[lag_cols])[:, 1]
        out = test[["Date", "crop_year", "month", target]].copy()
        out = out.rename(columns={target: "y_true"})
        out["prob"] = prob
        out["y_pred"] = (prob >= 0.5).astype(float)
        out["confidence"] = np.abs(prob - 0.5)
        rows.append(out)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _metrics(pred: pd.DataFrame, *, target: str, horizon: int, family: str, description: str) -> dict:
    if len(pred) < _MIN_EVAL or pred["y_true"].nunique() < 2:
        return {
            "target": target,
            "horizon": int(horizon),
            "family": family,
            "description": description,
            "status": "SKIPPED",
            "n": int(len(pred)),
        }
    y = pred["y_true"].astype(float)
    y_pred = pred["y_pred"].astype(float)
    correct = y.eq(y_pred).astype(float)
    ci = bootstrap_ci(correct.to_numpy(), np.mean, n_draws=300)
    top_n = max(1, int(len(pred) * 0.20))
    top = pred.nlargest(top_n, "confidence")
    annual = (
        pred.assign(correct=correct)
        .groupby("crop_year")
        .agg(n=("correct", "size"), da=("correct", "mean"), base_rate=("y_true", "mean"))
        .reset_index()
    )
    return {
        "target": target,
        "horizon": int(horizon),
        "family": family,
        "description": description,
        "status": "OK",
        "n": int(len(pred)),
        "base_rate": float(y.mean()),
        "majority_accuracy": float(max(y.mean(), 1.0 - y.mean())),
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


def _verdict(row: dict) -> str:
    if row.get("status") != "OK":
        return "SKIPPED"
    if row["auc"] >= 0.70 and row["balanced_accuracy"] >= 0.62 and row["top20_da"] >= 0.70:
        return "PROMISING_TARGET"
    if row["auc"] >= 0.60 and row["balanced_accuracy"] >= 0.56:
        return "WATCHLIST_TARGET"
    return "NO_GO_TARGET"


@lru_cache(maxsize=1)
def build_target_lab_v5() -> dict:
    """Evaluate new EMA target variables with strict crop-year OOF."""
    df = build_target_frame()
    rows = []
    catalog = []
    for horizon in _HORIZONS:
        for spec in _target_specs(horizon):
            target = spec["name"]
            pred = _oof_for_target(df, target)
            row = _metrics(
                pred,
                target=target,
                horizon=horizon,
                family=spec["family"],
                description=spec["description"],
            )
            row["verdict"] = _verdict(row)
            rows.append(row)
            catalog.append({**spec, "horizon": int(horizon)})

    ok = [row for row in rows if row.get("status") == "OK"]
    promising = [row for row in ok if row["verdict"] == "PROMISING_TARGET"]
    watchlist = [row for row in ok if row["verdict"] == "WATCHLIST_TARGET"]
    best = max(ok, key=lambda row: (row["auc"], row["balanced_accuracy"], row["top20_da"]), default={})
    by_family = (
        pd.DataFrame(ok)
        .groupby("family")
        .agg(
            n_targets=("target", "count"),
            best_auc=("auc", "max"),
            best_balanced_accuracy=("balanced_accuracy", "max"),
            best_top20_da=("top20_da", "max"),
        )
        .reset_index()
        .to_dict(orient="records")
        if ok
        else []
    )
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "scope": "Exploratory EMA target laboratory focused on premium/basis targets, not raw EMA up/down.",
        "protocol": {
            "horizons": list(_HORIZONS),
            "validation": "strict crop-year expanding OOF",
            "feature_lag": "all model features shifted by 1 row",
            "tail_nan_policy": "future NaNs remain NaN and are dropped, never converted to zero",
        },
        "target_catalog": catalog,
        "results": rows,
        "family_summary": by_family,
        "key_findings": {
            "n_targets_tested": int(len(rows)),
            "n_ok": int(len(ok)),
            "n_promising": int(len(promising)),
            "n_watchlist": int(len(watchlist)),
            "best_target": best.get("target"),
            "best_family": best.get("family"),
            "best_horizon": best.get("horizon"),
            "best_auc": best.get("auc"),
            "best_balanced_accuracy": best.get("balanced_accuracy"),
            "best_top20_da": best.get("top20_da"),
            "interpretation": _interpretation(promising, watchlist, best),
        },
    }


def _interpretation(promising: list[dict], watchlist: list[dict], best: dict) -> str:
    if promising:
        return (
            "Some non-raw EMA targets are promising; prioritize premium/basis targets before adding "
            "more models to raw EMA direction."
        )
    if watchlist:
        return "Several alternative EMA targets are watchlist candidates, but none is strong enough alone."
    if best:
        return "New targets do not beat the relative premium thesis; keep EMA/CBOT relative as the core target."
    return "No valid target experiment was produced."


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
    key = data["key_findings"]
    lines = [
        "# EMA TARGET LAB V5",
        "",
        "> Laboratoire de nouvelles cibles EMA centrees sur la prime europeenne, le basis et la performance relative.",
        "",
        "## Verdict",
        "",
        f"- Cibles testees : {key['n_targets_tested']}",
        f"- Cibles evaluables : {key['n_ok']}",
        f"- Cibles prometteuses : {key['n_promising']}",
        f"- Cibles watchlist : {key['n_watchlist']}",
        f"- Meilleure cible : `{key.get('best_target')}`",
        f"- Famille : `{key.get('best_family')}`",
        f"- Horizon : H{key.get('best_horizon')}",
        f"- AUC : {_fmt(key.get('best_auc'))}",
        f"- Balanced accuracy : {_fmt(key.get('best_balanced_accuracy'))}",
        f"- Top20 DA : {_fmt(key.get('best_top20_da'))}",
        f"- Lecture : {key['interpretation']}",
        "",
        "## Resultats",
        "",
        "| Target | Famille | H | Verdict | n | Base rate | DA | AUC | Bal. acc | MCC | Top20 |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["results"]:
        lines.append(
            f"| `{row['target']}` | {row['family']} | {row['horizon']} | {row['verdict']} | "
            f"{row.get('n', 0)} | {_fmt(row.get('base_rate'))} | {_fmt(row.get('da'))} | "
            f"{_fmt(row.get('auc'))} | {_fmt(row.get('balanced_accuracy'))} | "
            f"{_fmt(row.get('mcc'))} | {_fmt(row.get('top20_da'))} |"
        )
    lines += [
        "",
        "## Familles",
        "",
        "| Famille | n | Best AUC | Best bal. acc | Best top20 |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in data["family_summary"]:
        lines.append(
            f"| {row['family']} | {row['n_targets']} | {_fmt(row['best_auc'])} | "
            f"{_fmt(row['best_balanced_accuracy'])} | {_fmt(row['best_top20_da'])} |"
        )
    lines += [
        "",
        "## Limites",
        "",
        "- Source EMA historique exploratoire/proxy.",
        "- Les cibles conditionnelles reduisent parfois fortement l'echantillon.",
        "- Ces resultats ne sont pas des signaux de trading production.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_target_lab_v5(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_target_lab_v5()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_target_lab_v5()
    print(f"EMA target lab V5 saved -> {out}")
