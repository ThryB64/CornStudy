"""Economic EMA storage decision study."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mais.features.ema_targets import EMA_TARGETS_PARQUET
from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, PROJECT_ROOT
from mais.research.ema_benchmark import _load_selected_features, build_feature_sets
from mais.research.ema_data_audit import SOURCE_QUALITY_NOTE
from mais.research.ema_feature_selector import EMA_FEATURE_SELECTION_REPORT
from mais.research.proxy_audit import assert_no_proxy_in_benchmark

EMA_STORAGE_ECONOMIC_JSON = ARTEFACTS_DIR / "ema_study" / "ema_storage_economic_study.json"
EMA_STORAGE_ECONOMIC_MD = PROJECT_ROOT / "docs" / "EMA_STORAGE_ECONOMIC_STUDY.md"
STORAGE_VALUE_COLS = {
    "1m": "y_storage_value_1m_raw",
    "3m": "y_storage_value_3m_raw",
    "6m": "y_storage_value_6m_raw",
}
LEGACY_STORAGE_VALUE_COLS = {
    "1m": "y_storage_value_1m",
    "3m": "y_storage_value_3m",
    "6m": "y_storage_value_6m",
}
DEFAULT_MARGINS_EUR_T = (0.0, 3.0, 5.0)


def run_ema_storage_economic_study(
    *,
    features_path: Path = FEATURES_PARQUET,
    ema_targets_path: Path = EMA_TARGETS_PARQUET,
    selection_report_path: Path = EMA_FEATURE_SELECTION_REPORT,
    output_json_path: Path = EMA_STORAGE_ECONOMIC_JSON,
    output_markdown_path: Path = EMA_STORAGE_ECONOMIC_MD,
    max_date: str | pd.Timestamp = "2022-12-31",
    margins_eur_t: tuple[float, ...] = DEFAULT_MARGINS_EUR_T,
) -> dict[str, Any]:
    """Run economic storage baselines and predicted-value strategies."""
    features = pd.read_parquet(features_path)
    targets = pd.read_parquet(ema_targets_path)
    selected = _load_selected_features(selection_report_path)
    work = build_storage_frame(features, targets, max_date=max_date)
    assert_no_proxy_in_benchmark(work)
    feature_sets = _feature_sets(selected, work.columns)
    baselines = storage_strategy_baselines(work)
    model_rows: list[dict[str, Any]] = []
    for feature_set, columns in feature_sets.items():
        predictions = walk_forward_storage_value(work, columns=columns, value_col=_value_col(work, "3m"))
        for margin in margins_eur_t:
            model_rows.append(
                evaluate_storage_strategy(
                    predictions,
                    value_col=_value_col(work, "3m"),
                    strategy_name=f"{feature_set}_pred_value_margin_{margin:g}",
                    decision=predictions["predicted_storage_value"].gt(float(margin)),
                    margin_eur_t=float(margin),
                )
            )
    best_model = _best_strategy(model_rows)
    payload = {
        "source_quality_note": SOURCE_QUALITY_NOTE,
        "max_date": str(max_date),
        "value_columns": {label: _value_col(work, label) for label in ("1m", "3m", "6m")},
        "margins_eur_t": list(margins_eur_t),
        "n_rows": int(len(work)),
        "baselines": baselines,
        "model_strategies": model_rows,
        "best_model_strategy": best_model,
        "decision": decide_storage_economic_value(best_model, baselines),
    }
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    output_markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def build_storage_frame(features: pd.DataFrame, targets: pd.DataFrame, *, max_date: str | pd.Timestamp) -> pd.DataFrame:
    """Join features and EMA storage targets."""
    work = features.copy()
    work["Date"] = pd.to_datetime(work["Date"]).dt.normalize()
    target = targets.copy()
    target["Date"] = pd.to_datetime(target["Date"]).dt.normalize()
    wanted = ["Date", *[col for col in [*STORAGE_VALUE_COLS.values(), *LEGACY_STORAGE_VALUE_COLS.values()] if col in target.columns]]
    out = work.merge(target[wanted], on="Date", how="inner")
    out = out[out["Date"] <= pd.Timestamp(max_date)].copy()
    if "ema_data_availability_score" in out.columns:
        out = out[pd.to_numeric(out["ema_data_availability_score"], errors="coerce") > 0].copy()
    return out.sort_values("Date").reset_index(drop=True)


def storage_strategy_baselines(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Evaluate never/always/oracle storage baselines."""
    out: dict[str, dict[str, Any]] = {}
    value_3m = _value_col(frame, "3m")
    out["never_store"] = evaluate_storage_strategy(
        frame[["Date", value_3m]].dropna().copy(),
        value_col=value_3m,
        strategy_name="never_store",
        decision=pd.Series(False, index=frame[["Date", value_3m]].dropna().index),
    )
    for label in ("1m", "3m", "6m"):
        col = _value_col(frame, label)
        sub = frame[["Date", col]].dropna().copy()
        out[f"always_store_{label}"] = evaluate_storage_strategy(
            sub,
            value_col=col,
            strategy_name=f"always_store_{label}",
            decision=pd.Series(True, index=sub.index),
        )
        out[f"oracle_store_{label}"] = evaluate_storage_strategy(
            sub,
            value_col=col,
            strategy_name=f"oracle_store_{label}",
            decision=pd.to_numeric(sub[col], errors="coerce").gt(0),
        )
    return out


def walk_forward_storage_value(
    frame: pd.DataFrame,
    *,
    columns: list[str],
    value_col: str,
    min_train_years: int = 3,
    n_splits: int = 8,
) -> pd.DataFrame:
    """Predict future storage value with expanding crop-year Ridge regression."""
    usable = [col for col in columns if col in frame.columns]
    work = frame[["Date", value_col, *usable]].dropna(subset=[value_col]).copy()
    work = work.replace([np.inf, -np.inf], np.nan).sort_values("Date").reset_index(drop=True)
    if not usable:
        return pd.DataFrame(columns=["Date", value_col, "predicted_storage_value", "validation_year"])
    predictions: list[pd.DataFrame] = []
    for train_idx, valid_idx, valid_year in _year_splits(work["Date"], min_train_years=min_train_years, n_splits=n_splits):
        if len(train_idx) == 0 or len(valid_idx) == 0:
            continue
        model = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
                ("scaler", StandardScaler()),
                ("ridge", Ridge(alpha=1.0)),
            ]
        )
        model.fit(work.loc[train_idx, usable], work.loc[train_idx, value_col].astype(float))
        pred = model.predict(work.loc[valid_idx, usable])
        predictions.append(
            pd.DataFrame(
                {
                    "Date": work.loc[valid_idx, "Date"].to_numpy(),
                    value_col: work.loc[valid_idx, value_col].to_numpy(dtype=float),
                    "predicted_storage_value": pred.astype(float),
                    "validation_year": int(valid_year),
                    "n_features": int(len(usable)),
                }
            )
        )
    if not predictions:
        return pd.DataFrame(columns=["Date", value_col, "predicted_storage_value", "validation_year"])
    return pd.concat(predictions, ignore_index=True)


def evaluate_storage_strategy(
    frame: pd.DataFrame,
    *,
    value_col: str,
    strategy_name: str,
    decision: pd.Series,
    margin_eur_t: float | None = None,
) -> dict[str, Any]:
    """Evaluate a storage decision in economic terms."""
    work = frame.copy()
    work["Date"] = pd.to_datetime(work["Date"]).dt.normalize()
    work = work.dropna(subset=[value_col]).copy()
    decision_aligned = pd.Series(decision, index=work.index).reindex(work.index).fillna(False).astype(bool)
    actual_value = pd.to_numeric(work[value_col], errors="coerce")
    gain = pd.Series(np.where(decision_aligned, actual_value, 0.0), index=work.index, dtype=float)
    oracle_gain = actual_value.clip(lower=0)
    years = work["Date"].dt.year
    annual_gain = gain.groupby(years).mean()
    annual_regret = (oracle_gain - gain).groupby(years).mean()
    return {
        "strategy": strategy_name,
        "margin_eur_t": _json_float(margin_eur_t),
        "n": int(len(work)),
        "avg_gain_eur_t": _json_float(gain.mean()),
        "median_gain_eur_t": _json_float(gain.median()),
        "pct_store": _json_float(decision_aligned.mean()),
        "pct_positive_days": _json_float((gain > 0).mean()),
        "years_positive": int((annual_gain > 0).sum()),
        "years_total": int(annual_gain.count()),
        "pct_years_positive": _json_float((annual_gain > 0).mean()) if len(annual_gain) else None,
        "worst_year": str(int(annual_gain.idxmin())) if len(annual_gain) else None,
        "worst_year_avg_gain_eur_t": _json_float(annual_gain.min()) if len(annual_gain) else None,
        "avg_regret_vs_oracle_eur_t": _json_float((oracle_gain - gain).mean()),
        "annual_gain_eur_t": {str(int(year)): _json_float(value) for year, value in annual_gain.items()},
        "annual_regret_eur_t": {str(int(year)): _json_float(value) for year, value in annual_regret.items()},
    }


def decide_storage_economic_value(
    best_model: dict[str, Any] | None,
    baselines: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Decide whether the economic storage strategy is useful enough."""
    if best_model is None:
        return {"verdict": "NO_VALID_STORAGE_MODEL", "reason": "No model strategy was evaluated."}
    never = baselines.get("never_store", {})
    always_3m = baselines.get("always_store_3m", {})
    gain = _safe_float(best_model.get("avg_gain_eur_t"))
    years_pos = _safe_float(best_model.get("pct_years_positive"))
    regret = _safe_float(best_model.get("avg_regret_vs_oracle_eur_t"))
    always_gain = _safe_float(always_3m.get("avg_gain_eur_t"))
    never_gain = _safe_float(never.get("avg_gain_eur_t"))
    min_material_gain = 1.0
    min_partial_gain = 0.25
    if (
        gain > max(always_gain, never_gain, 0.0) + min_material_gain
        and years_pos >= 0.60
        and regret < _safe_float(always_3m.get("avg_regret_vs_oracle_eur_t"))
    ):
        verdict = "STORAGE_ECONOMIC_PROMISING"
        reason = "Best strategy has positive average gain, beats baselines and is positive in most validation years."
    elif gain > max(always_gain, never_gain, 0.0) + min_partial_gain:
        verdict = "STORAGE_ECONOMIC_PARTIAL"
        reason = "Best strategy improves average gain materially but does not clear the year-stability criterion."
    else:
        verdict = "STORAGE_ECONOMIC_NO_GO"
        reason = "No model strategy beats simple economic baselines by a material margin."
    return {"verdict": verdict, "reason": reason, "best_strategy": best_model}


def render_markdown(payload: dict[str, Any]) -> str:
    """Render storage economic report."""
    lines = [
        "# EMA Storage Economic Study",
        "",
        f"> {payload['source_quality_note']}",
        "",
        "## Verdict",
        "",
        f"- `{payload['decision']['verdict']}`: {payload['decision']['reason']}",
        "",
        "## Baselines",
        "",
        *_strategy_lines(payload["baselines"].values()),
        "",
        "## Model Strategies",
        "",
        *_strategy_lines(payload["model_strategies"]),
        "",
        "## Interpretation",
        "",
        "- La métrique principale est le gain net moyen EUR/t, pas la DA seule.",
        "- Les stratégies avec marge ne stockent que si la valeur prédite dépasse le seuil économique.",
        "- Les résultats restent exploratoires tant que les coûts de stockage locaux et financiers ne sont pas personnalisés.",
        "",
    ]
    return "\n".join(lines)


def _feature_sets(selected: list[str], available: pd.Index) -> dict[str, list[str]]:
    sets = build_feature_sets(selected, available_columns=set(available))
    return {
        "cbot_only": sets["cbot_only"],
        "ema_curve_only": sets["ema_curve_only"],
        "cbot_ema_combined": sets["cbot_ema_combined"],
        "selected_full": [col for col in selected if col in set(available)],
    }


def _year_splits(dates: pd.Series, *, min_train_years: int, n_splits: int) -> list[tuple[np.ndarray, np.ndarray, int]]:
    years = pd.to_datetime(dates).dt.year.to_numpy()
    unique_years = sorted(pd.unique(years))
    validation_years = unique_years[min_train_years:][-int(n_splits) :]
    splits: list[tuple[np.ndarray, np.ndarray, int]] = []
    for year in validation_years:
        train_idx = np.flatnonzero(years < year)
        valid_idx = np.flatnonzero(years == year)
        if len(train_idx) and len(valid_idx):
            splits.append((train_idx, valid_idx, int(year)))
    return splits


def _value_col(frame: pd.DataFrame, label: str) -> str:
    preferred = STORAGE_VALUE_COLS[label]
    if preferred in frame.columns:
        return preferred
    legacy = LEGACY_STORAGE_VALUE_COLS[label]
    if legacy in frame.columns:
        return legacy
    raise ValueError(f"Missing EMA storage value column for {label}")


def _best_strategy(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    valid = [row for row in rows if row.get("avg_gain_eur_t") is not None]
    if not valid:
        return None
    return max(valid, key=lambda row: (_safe_float(row.get("avg_gain_eur_t")), _safe_float(row.get("pct_years_positive"))))


def _strategy_lines(strategies: Any) -> list[str]:
    return [
        f"- `{row['strategy']}`: gain={_fmt(row.get('avg_gain_eur_t'))} EUR/t, "
        f"median={_fmt(row.get('median_gain_eur_t'))}, store={_pct(row.get('pct_store'))}, "
        f"years+={row.get('years_positive')}/{row.get('years_total')}, "
        f"regret={_fmt(row.get('avg_regret_vs_oracle_eur_t'))}"
        for row in strategies
    ]


def _safe_float(value: Any) -> float:
    if value is None:
        return math.nan
    try:
        out = float(value)
    except (TypeError, ValueError):
        return math.nan
    return out if math.isfinite(out) else math.nan


def _json_float(value: Any) -> float | None:
    out = _safe_float(value)
    return out if math.isfinite(out) else None


def _fmt(value: Any) -> str:
    out = _safe_float(value)
    return "N/A" if not math.isfinite(out) else f"{out:.3f}"


def _pct(value: Any) -> str:
    out = _safe_float(value)
    return "N/A" if not math.isfinite(out) else f"{out * 100:.1f}%"


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_ready(v) for v in value]
    if isinstance(value, tuple):
        return [_json_ready(v) for v in value]
    if isinstance(value, (np.integer, np.floating)):
        return _json_float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, float):
        return _json_float(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


if __name__ == "__main__":
    report = run_ema_storage_economic_study()
    print(json.dumps(_json_ready(report["decision"]), indent=2, ensure_ascii=False))
