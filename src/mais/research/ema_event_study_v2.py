"""NB2-08 — Event study EMA v2."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, PROJECT_ROOT

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_event_study_v2.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_EVENT_STUDY_V2.md"
_THRESHOLDS = [0.03, 0.05, 0.07]
_PRE_WINDOWS = [20, 10, 5, 1]
_POST_WINDOWS = [1, 5, 10, 20]


def _load_returns() -> pd.DataFrame:
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    cols = [
        "Date",
        "ema_front_price",
        "cbot_eur_t",
        "is_wasde_day",
        "ema_cbot_basis_zscore_52w",
        "ema_front_vol_20d_adjusted",
        "corn_gas_ratio",
    ]
    df = feats[[c for c in cols if c in feats.columns]].copy()
    df = df[df["ema_front_price"].notna()].sort_values("Date").reset_index(drop=True)
    df["ema_ret_1d"] = df["ema_front_price"].pct_change()
    df["cbot_ret_1d"] = df["cbot_eur_t"].pct_change() if "cbot_eur_t" in df.columns else np.nan
    return df


def _event_windows(df: pd.DataFrame, event_dates: list[pd.Timestamp]) -> dict:
    ret = df.set_index("Date")["ema_ret_1d"]
    idx = pd.Index(ret.index)
    out = {}
    for window in _PRE_WINDOWS:
        vals = []
        for date in event_dates:
            if date not in idx:
                continue
            pos = idx.get_loc(date)
            vals.append(float(ret.iloc[max(0, pos - window):pos].sum()))
        out[f"pre_{window}d_mean"] = float(np.nanmean(vals)) if vals else float("nan")
    for window in _POST_WINDOWS:
        vals = []
        for date in event_dates:
            if date not in idx:
                continue
            pos = idx.get_loc(date)
            vals.append(float(ret.iloc[pos + 1:pos + 1 + window].sum()))
        out[f"post_{window}d_mean"] = float(np.nanmean(vals)) if vals else float("nan")
        out[f"post_{window}d_bootstrap_ci"] = _bootstrap_mean(vals) if vals else None
    return out


def _bootstrap_mean(vals: list[float]) -> dict:
    arr = np.array(vals, dtype=float)
    rng = np.random.default_rng(42)
    draws = [float(np.mean(rng.choice(arr, size=len(arr), replace=True))) for _ in range(500)]
    return {"lo": float(np.percentile(draws, 2.5)), "hi": float(np.percentile(draws, 97.5))}


def _classify_event(row: pd.Series) -> str:
    date = pd.Timestamp(row["Date"])
    if int(date.year) == 2022:
        return "ukraine_black_sea"
    if row.get("is_wasde_day", 0) == 1:
        return "wasde_day"
    if pd.notna(row.get("ema_cbot_basis_zscore_52w")) and abs(float(row["ema_cbot_basis_zscore_52w"])) > 2:
        return "basis_dislocation"
    if pd.notna(row.get("ema_front_vol_20d_adjusted")) and float(row["ema_front_vol_20d_adjusted"]) > 0.30:
        return "volatility_stress"
    if int(date.day) in {15, 16, 17, 18, 19, 20}:
        return "mars_publication_window_proxy"
    return "unclassified"


def _threshold_events(df: pd.DataFrame) -> dict:
    out = {}
    for threshold in _THRESHOLDS:
        events = df[df["ema_ret_1d"].abs() >= threshold].copy()
        events["event_type"] = events.apply(_classify_event, axis=1)
        dates = events["Date"].tolist()
        out[f"abs_ret_gt_{int(threshold * 100)}pct"] = {
            "threshold": threshold,
            "n_events": int(len(events)),
            "windows": _event_windows(df, dates),
            "type_counts": {str(k): int(v) for k, v in events["event_type"].value_counts().to_dict().items()},
            "top_events": _top_events(events),
        }
    return out


def _top_events(events: pd.DataFrame) -> list[dict]:
    if len(events) == 0:
        return []
    top = events.assign(abs_ret=events["ema_ret_1d"].abs()).sort_values("abs_ret", ascending=False).head(20)
    rows = []
    for _, row in top.iterrows():
        rows.append({
            "date": str(pd.Timestamp(row["Date"]).date()),
            "ema_ret_1d": float(row["ema_ret_1d"]),
            "event_type": str(row["event_type"]),
            "basis_zscore": _safe_float(row.get("ema_cbot_basis_zscore_52w")),
        })
    return rows


def _safe_float(value):
    if value is None or pd.isna(value):
        return None
    return float(value)


def _named_windows(df: pd.DataFrame) -> dict:
    out = {}
    if "is_wasde_day" in df.columns:
        dates = df.loc[df["is_wasde_day"] == 1, "Date"].tolist()
        out["wasde_days"] = {"n_events": len(dates), "windows": _event_windows(df, dates)}
    mars_dates = df.loc[df["Date"].dt.day.between(15, 20), "Date"].tolist()
    out["mars_publication_window_proxy"] = {"n_events": len(mars_dates), "windows": _event_windows(df, mars_dates)}
    ukraine_dates = df.loc[df["Date"].dt.year == 2022, "Date"].tolist()
    out["ukraine_2022_window"] = {"n_events": len(ukraine_dates), "windows": _event_windows(df, ukraine_dates)}
    if "ema_cbot_basis_zscore_52w" in df.columns:
        basis_dates = df.loc[df["ema_cbot_basis_zscore_52w"].abs() > 2, "Date"].tolist()
        out["basis_z_abs_gt_2"] = {"n_events": len(basis_dates), "windows": _event_windows(df, basis_dates)}
    return out


def build_event_study_v2() -> dict:
    df = _load_returns()
    thresholds = _threshold_events(df)
    named = _named_windows(df)
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "n_obs": int(len(df)),
        "threshold_event_study": thresholds,
        "named_event_windows": named,
        "method": "Cumulative returns before/after event windows; bootstrap 500 for post windows.",
        "key_findings": {
            "n_events_gt_3pct": thresholds["abs_ret_gt_3pct"]["n_events"],
            "n_events_gt_5pct": thresholds["abs_ret_gt_5pct"]["n_events"],
            "n_events_gt_7pct": thresholds["abs_ret_gt_7pct"]["n_events"],
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
        "# EMA EVENT STUDY V2",
        "",
        "> Event study exploratoire sur source EMA proxy.",
        "",
        "## Grands mouvements",
        "",
        f"- |retour 1j| > 3% : {k['n_events_gt_3pct']}",
        f"- |retour 1j| > 5% : {k['n_events_gt_5pct']}",
        f"- |retour 1j| > 7% : {k['n_events_gt_7pct']}",
        "",
        "## Fenêtres",
        "",
        "Fenêtres pré-event : -20/-10/-5/-1 jours. Fenêtres post-event : +1/+5/+10/+20 jours.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_event_study_v2(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_event_study_v2()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_event_study_v2()
    print(f"Event study v2 saved -> {out}")
