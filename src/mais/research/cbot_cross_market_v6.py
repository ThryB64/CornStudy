"""V6-05 — CBOT, cross-market, decomposition and event studies."""

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

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.experiment_registry_v6 import make_record, save_registry
from mais.research.meta_model_premium_v6 import build_meta_model_frame
from mais.research.target_labs_v6 import build_target_frames_v6

_OUTPUT_DIR = ARTEFACTS_DIR / "v6"
_OUTPUT = _OUTPUT_DIR / "cbot_cross_market_v6.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "CBOT_CROSS_MARKET_V6.md"
_MIN_TRAIN = 180
_MIN_TEST = 25

_CBOT_TARGETS = [
    "y_cbot_up_h60",
    "y_cbot_drawdown_5pct_h20",
    "y_cbot_large_down_3pct_h90",
]
_CBOT_BASE = [
    "corn_logret_5d",
    "corn_logret_20d",
    "corn_realized_vol_20",
    "corn_realized_vol_60",
    "wasde_stocks_to_use_ratio",
    "wasde_exports",
    "cot_mm_net",
    "cot_mm_short_pct",
    "crop_ge_zscore_seasonal",
    "drought_composite",
    "fedfunds_level_zscore",
    "corn_gas_ratio",
]
_EMA_PREMIUM = [
    "ema_cbot_basis",
    "ema_cbot_basis_zscore_52w",
    "ema_front_vol_20d_adjusted",
    "cbot_eur_t",
    "ema_oi_total",
    "ema_volume_total",
]
_EMA_META_PREFIXES = ("pred_ema_", "meta_")


def _present(df: pd.DataFrame, cols: list[str]) -> list[str]:
    return [col for col in cols if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]


def _oof_logistic(df: pd.DataFrame, *, target: str, features: list[str]) -> pd.DataFrame:
    work = df[["Date", "crop_year", target, *features]].copy()
    for col in features:
        work[f"{col}_x"] = work[col].shift(1)
    x_cols = [f"{col}_x" for col in features]
    work = work.replace([np.inf, -np.inf], np.nan).dropna(subset=[target])
    rows = []
    years = sorted(work["crop_year"].dropna().unique())
    for idx in range(3, len(years)):
        train = work[work["crop_year"].isin(years[:idx])]
        test = work[work["crop_year"].eq(years[idx])]
        if len(train) < _MIN_TRAIN or len(test) < _MIN_TEST or train[target].nunique() < 2 or test[target].nunique() < 2:
            continue
        fold_cols = [
            col
            for col in x_cols
            if train[col].notna().sum() >= min(80, max(20, int(len(train) * 0.10)))
            and test[col].notna().sum() > 0
            and train[col].nunique(dropna=True) > 1
        ]
        if not fold_cols:
            continue
        medians = train[fold_cols].median(numeric_only=True).fillna(0.0)
        model = LogisticRegression(max_iter=700, class_weight="balanced", solver="liblinear")
        model.fit(train[fold_cols].fillna(medians), train[target])
        prob = model.predict_proba(test[fold_cols].fillna(medians))[:, 1]
        out = test[["Date", "crop_year", target]].rename(columns={target: "y_true"}).copy()
        out["prob"] = prob
        out["y_pred"] = (prob >= 0.5).astype(float)
        rows.append(out)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _metrics(pred: pd.DataFrame, *, target: str, feature_set: str) -> dict:
    row = {"target": target, "feature_set": feature_set, "n": int(len(pred))}
    if pred.empty or pred["y_true"].nunique() < 2:
        return {**row, "status": "SKIPPED"}
    return {
        **row,
        "status": "OK",
        "base_rate": float(pred["y_true"].mean()),
        "da": float(accuracy_score(pred["y_true"], pred["y_pred"])),
        "balanced_accuracy": float(balanced_accuracy_score(pred["y_true"], pred["y_pred"])),
        "auc": float(roc_auc_score(pred["y_true"], pred["prob"])),
        "mcc": float(matthews_corrcoef(pred["y_true"], pred["y_pred"])),
    }


def _cross_market_cbot() -> list[dict]:
    cbot = build_target_frames_v6()["cbot"].copy()
    meta = build_meta_model_frame()
    meta_cols = ["Date", *[col for col in meta.columns if col.startswith(_EMA_META_PREFIXES)]]
    cbot = cbot.merge(meta[meta_cols], on="Date", how="left")
    feature_sets = {
        "cbot_base": _present(cbot, _CBOT_BASE),
        "cbot_plus_ema_premium": _present(cbot, [*_CBOT_BASE, *_EMA_PREMIUM]),
        "cbot_plus_ema_meta": _present(cbot, [*_CBOT_BASE, *[col for col in meta_cols if col != "Date"]]),
        "cbot_full_cross_market": _present(cbot, [*_CBOT_BASE, *_EMA_PREMIUM, *[col for col in meta_cols if col != "Date"]]),
    }
    rows = []
    raw = {}
    for target in _CBOT_TARGETS:
        if target not in cbot.columns:
            continue
        for name, features in feature_sets.items():
            pred = _oof_logistic(cbot, target=target, features=features)
            raw[(target, name)] = pred
            rows.append(_metrics(pred, target=target, feature_set=name))
    lookup = {(row["target"], row["feature_set"]): row for row in rows if row["status"] == "OK"}
    enriched = []
    for row in rows:
        out = dict(row)
        base = lookup.get((row["target"], "cbot_base"))
        if row["status"] == "OK" and base:
            out["delta_auc_vs_cbot_base"] = float(row["auc"] - base["auc"])
            out["delta_ba_vs_cbot_base"] = float(row["balanced_accuracy"] - base["balanced_accuracy"])
        enriched.append(out)
    return enriched


def _ema_cbot_meta_impact() -> list[dict]:
    frame = build_meta_model_frame()
    cbot_meta_cols = [col for col in frame.columns if col.startswith("pred_cbot_")]
    base = _present(frame, ["ema_cbot_basis", "ema_cbot_basis_zscore_52w", "ema_front_vol_20d_adjusted", "corn_logret_20d"])
    rows = []
    for target in ["y_rel_outperform_h40", "y_rel_outperform_h90"]:
        sets = {
            "ema_base": base,
            "ema_plus_cbot_meta": _present(frame, [*base, *cbot_meta_cols]),
        }
        target_rows = []
        for name, features in sets.items():
            pred = _oof_logistic(frame, target=target, features=features)
            target_rows.append(_metrics(pred, target=target, feature_set=name))
        lookup = {row["feature_set"]: row for row in target_rows if row["status"] == "OK"}
        for row in target_rows:
            out = dict(row)
            if row["status"] == "OK" and "ema_base" in lookup:
                out["delta_auc_vs_ema_base"] = float(row["auc"] - lookup["ema_base"]["auc"])
            rows.append(out)
    return rows


def _ols(y: pd.Series, x: pd.DataFrame) -> dict:
    frame = pd.concat([y.rename("y"), x], axis=1).replace([np.inf, -np.inf], np.nan).dropna()
    if len(frame) < 80:
        return {"status": "SKIPPED", "n": int(len(frame))}
    xmat = np.column_stack([np.ones(len(frame)), frame[x.columns].to_numpy(dtype=float)])
    yvec = frame["y"].to_numpy(dtype=float)
    beta, *_ = np.linalg.lstsq(xmat, yvec, rcond=None)
    fitted = xmat @ beta
    ss_tot = float(np.sum((yvec - yvec.mean()) ** 2))
    ss_res = float(np.sum((yvec - fitted) ** 2))
    return {
        "status": "OK",
        "n": int(len(frame)),
        "r2": float(1.0 - ss_res / ss_tot) if ss_tot else float("nan"),
        "intercept": float(beta[0]),
        "betas": {col: float(value) for col, value in zip(x.columns, beta[1:], strict=True)},
    }


def _decomposition() -> dict:
    frame = build_meta_model_frame().copy()
    rows = {}
    for horizon in [40, 90]:
        y = frame[f"relative_return_h{horizon}"] + frame[f"cbot_eur_return_h{horizon}"]
        x = frame[[f"cbot_eur_return_h{horizon}", f"basis_z_change_h{horizon}", "corn_gas_ratio", "ema_front_vol_20d_adjusted"]].copy()
        x.columns = ["cbot_eur_return", "basis_z_change", "corn_gas_ratio", "ema_vol"]
        rows[f"h{horizon}_all"] = _ols(y, x)
        crisis = frame["Date"].dt.year.isin([2020, 2021, 2022])
        rows[f"h{horizon}_normal"] = _ols(y[~crisis], x[~crisis])
        rows[f"h{horizon}_crisis"] = _ols(y[crisis], x[crisis])
    return rows


def _event_study() -> list[dict]:
    frame = build_meta_model_frame().copy()
    events = {
        "wasde_day": frame.get("is_wasde_day", pd.Series(False, index=frame.index)).fillna(0).astype(float) > 0,
        "basis_extreme_abs_z2": frame["ema_cbot_basis_zscore_52w"].abs() >= 2.0,
        "cbot_vol_top_decile": frame["corn_realized_vol_20"] >= frame["corn_realized_vol_20"].quantile(0.90),
        "gas_ratio_top_decile": frame["corn_gas_ratio"] >= frame["corn_gas_ratio"].quantile(0.90),
        "roll_proxy_month": frame["month"].isin([2, 5, 7, 10]),
    }
    rows = []
    for name, mask in events.items():
        sub = frame[mask].copy()
        for horizon in [40, 90]:
            col = f"relative_return_h{horizon}"
            target = f"y_rel_outperform_h{horizon}"
            usable = sub.dropna(subset=[col, target])
            rows.append({
                "event": name,
                "horizon": horizon,
                "n": int(len(usable)),
                "mean_relative_return": float(usable[col].mean()) if len(usable) else float("nan"),
                "median_relative_return": float(usable[col].median()) if len(usable) else float("nan"),
                "outperformance_rate": float(usable[target].mean()) if len(usable) else float("nan"),
            })
    return rows


@lru_cache(maxsize=1)
def build_cbot_cross_market_v6() -> dict:
    cbot = _cross_market_cbot()
    ema = _ema_cbot_meta_impact()
    decomposition = _decomposition()
    events = _event_study()
    ok_cbot = [row for row in cbot if row["status"] == "OK"]
    ok_ema = [row for row in ema if row["status"] == "OK"]
    best_cbot = max(ok_cbot, key=lambda row: (row.get("delta_auc_vs_cbot_base", -999), row["auc"]), default={})
    best_ema = max(ok_ema, key=lambda row: (row.get("delta_auc_vs_ema_base", -999), row["auc"]), default={})
    records = [
        make_record(
            experiment_id=f"V6-05-{row['target']}-{row['feature_set']}",
            feature_set=row["feature_set"],
            target=row["target"],
            horizon=row["target"].rsplit("_h", 1)[-1] if "_h" in row["target"] else "NA",
            model="cross_market_logistic",
            cv_protocol="crop_year_oof_shift1",
            metrics={k: row[k] for k in ("auc", "balanced_accuracy", "mcc") if k in row},
            verdict="PROMISING" if row.get("auc", 0) >= 0.70 else "WATCHLIST" if row.get("auc", 0) >= 0.62 else "NO_GO",
            artefact_paths=["artefacts/v6/cbot_cross_market_v6.json"],
        )
        for row in [*ok_cbot, *ok_ema]
    ]
    registry = save_registry(records) if records else {}
    return {
        "source_quality": "exploratoire_barchart_proxy_for_ema_cross_market",
        "cbot_cross_market": cbot,
        "ema_cbot_meta_impact": ema,
        "ema_decomposition": decomposition,
        "event_study": events,
        "registry": registry,
        "key_findings": {
            "best_cbot_cross_market": best_cbot,
            "best_ema_cbot_meta": best_ema,
            "interpretation": _interpretation(best_cbot, best_ema, decomposition, events),
        },
    }


def _interpretation(best_cbot: dict, best_ema: dict, decomposition: dict, events: list[dict]) -> str:
    cbot_gain = best_cbot.get("delta_auc_vs_cbot_base", 0) or 0
    ema_gain = best_ema.get("delta_auc_vs_ema_base", 0) or 0
    if cbot_gain > 0.02 and ema_gain > 0.01:
        return "Cross-market signals add measurable OOF value in both directions."
    if cbot_gain > 0.02:
        return "EMA premium signals add value to selected CBOT risk targets; EMA still needs proxy caveats."
    if ema_gain > 0.01:
        return "CBOT meta-signals help EMA premium modestly, mostly as context."
    return "Cross-market signals are mostly explanatory; premium/basis remain the core EMA edge."


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


def _write_doc(data: dict, path: Path) -> None:
    lines = [
        "# CBOT CROSS MARKET V6",
        "",
        "> Études CBOT, croisement EMA/CBOT, décomposition EMA et event study premium.",
        "",
        f"- Source quality : `{data['source_quality']}`",
        f"- Lecture : {data['key_findings']['interpretation']}",
        "",
        "## CBOT Cross-Market",
        "",
        "| Target | Set | n | AUC | dAUC | BA | MCC |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in data["cbot_cross_market"]:
        lines.append(
            f"| `{row['target']}` | `{row['feature_set']}` | {row.get('n', 0)} | {row.get('auc', float('nan')):.3f} | "
            f"{row.get('delta_auc_vs_cbot_base', float('nan')):.3f} | {row.get('balanced_accuracy', float('nan')):.3f} | {row.get('mcc', float('nan')):.3f} |"
        )
    lines += ["", "## EMA Impact Of CBOT Meta", "", "| Target | Set | n | AUC | dAUC | BA |", "|---|---|---:|---:|---:|---:|"]
    for row in data["ema_cbot_meta_impact"]:
        lines.append(
            f"| `{row['target']}` | `{row['feature_set']}` | {row.get('n', 0)} | {row.get('auc', float('nan')):.3f} | "
            f"{row.get('delta_auc_vs_ema_base', float('nan')):.3f} | {row.get('balanced_accuracy', float('nan')):.3f} |"
        )
    lines += ["", "## Decomposition", ""]
    for name, row in data["ema_decomposition"].items():
        lines.append(f"- `{name}` : status={row.get('status')}, n={row.get('n')}, r2={row.get('r2')}")
    lines += ["", "## Event Study", "", "| Event | H | n | Mean rel ret | Outperform rate |", "|---|---:|---:|---:|---:|"]
    for row in data["event_study"]:
        lines.append(
            f"| `{row['event']}` | {row['horizon']} | {row['n']} | {row['mean_relative_return']:.4f} | {row['outperformance_rate']:.3f} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_cbot_cross_market_v6(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_cbot_cross_market_v6()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_doc(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_cbot_cross_market_v6()
    print(f"CBOT cross-market V6 saved -> {out}")
