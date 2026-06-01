"""NB2-09 — Volatilité EMA améliorée : régimes, HAR enrichi, prédiction OOF."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, PROJECT_ROOT
from mais.research.ema_residual_eu_v2 import _compute_oof_residuals
from mais.research.ema_residual_eu_v2 import _load_data as _load_residual_base
from mais.research.ema_utils import binary_target_from_condition, bootstrap_ci, crop_year
from mais.research.ema_volatility import build_volatility

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_volatility_v2.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_VOLATILITY_V2.md"


def _load_vol() -> pd.DataFrame:
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    cols = ["Date", "ema_front_price", "ema_cbot_basis_zscore_52w", "corn_realized_vol_20", "corn_gas_ratio"]
    df = feats[[c for c in cols if c in feats.columns]].copy()
    df = df[df["ema_front_price"].notna()].sort_values("Date").reset_index(drop=True)
    df["ema_ret"] = df["ema_front_price"].pct_change()
    for w in [20, 60, 90]:
        df[f"vol_{w}d"] = df["ema_ret"].rolling(w).std() * np.sqrt(252)
    df["vol_regime"] = pd.cut(
        df["vol_20d"],
        bins=[-np.inf, 0.20, 0.30, np.inf],
        labels=["normal", "elevated", "stress"],
    )
    resid = _compute_oof_residuals(_load_residual_base())[["Date", "ema_residual_oof"]]
    return df.merge(resid, on="Date", how="left").dropna(subset=["vol_20d"]).reset_index(drop=True)


def _regime_stats(df: pd.DataFrame) -> dict:
    out = {}
    for regime, sub in df.groupby("vol_regime", observed=False):
        out[str(regime)] = {
            "n_days": int(len(sub)),
            "pct_days": float(len(sub) / len(df)),
            "mean_vol_20d": float(sub["vol_20d"].mean()),
            "mean_return": float(sub["ema_ret"].mean()),
        }
    return out


def _ols_r2(df: pd.DataFrame, y_col: str, x_cols: list[str]) -> dict:
    sub = df[[y_col, *x_cols]].replace([np.inf, -np.inf], np.nan).dropna()
    if len(sub) < 50:
        return {"error": "insufficient_data", "n": int(len(sub))}
    y = sub[y_col].values
    x = sub[x_cols].values
    xc = np.column_stack([np.ones(len(x)), x])
    coefs, _, _, _ = np.linalg.lstsq(xc, y, rcond=None)
    pred = xc @ coefs
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return {
        "n": int(len(sub)),
        "r2": float(1 - ss_res / ss_tot) if ss_tot else float("nan"),
        "coefs": [float(c) for c in coefs],
        "x_cols": x_cols,
    }


def _har_models(df: pd.DataFrame) -> dict:
    work = df.copy()
    work["rv_target"] = work["ema_ret"].abs()
    work["rv_daily_lag"] = work["rv_target"].shift(1)
    work["rv_weekly_lag"] = work["vol_20d"].shift(1)
    work["rv_monthly_lag"] = work["vol_60d"].shift(1)
    work["basis_abs_z_lag"] = work.get("ema_cbot_basis_zscore_52w", pd.Series(index=work.index)).abs().shift(1)
    work["resid_abs_lag"] = work["ema_residual_oof"].abs().shift(1)
    work["stress_dummy"] = (work["vol_regime"] == "stress").astype(float).shift(1)
    return {
        "har_base": _ols_r2(work, "rv_target", ["rv_daily_lag", "rv_weekly_lag", "rv_monthly_lag"]),
        "har_plus_regime": _ols_r2(work, "rv_target", ["rv_daily_lag", "rv_weekly_lag", "rv_monthly_lag", "stress_dummy"]),
        "har_plus_basis": _ols_r2(work, "rv_target", ["rv_daily_lag", "rv_weekly_lag", "rv_monthly_lag", "basis_abs_z_lag"]),
        "har_plus_residual": _ols_r2(work, "rv_target", ["rv_daily_lag", "rv_weekly_lag", "rv_monthly_lag", "resid_abs_lag"]),
    }


def _event_vol(df: pd.DataFrame) -> dict:
    high_basis = df[df.get("ema_cbot_basis_zscore_52w", pd.Series(dtype=float)).abs() > 2]
    shocks = df[df["ema_residual_oof"].abs() > 2 * df["ema_residual_oof"].std()]
    return {
        "vol_mean_all": float(df["vol_20d"].mean()),
        "vol_mean_basis_abs_z_gt_2": float(high_basis["vol_20d"].mean()) if len(high_basis) else float("nan"),
        "vol_mean_residual_shock_2sigma": float(shocks["vol_20d"].mean()) if len(shocks) else float("nan"),
        "n_basis_events": int(len(high_basis)),
        "n_residual_shocks": int(len(shocks)),
    }


def _predict_high_vol(df: pd.DataFrame) -> dict:
    work = df.copy()
    future_vol = work["vol_20d"].shift(-20)
    work["target_high_vol_h20"] = binary_target_from_condition(
        future_vol > 0.25,
        future_vol.notna(),
    )
    features = [c for c in ["vol_20d", "vol_60d", "ema_cbot_basis_zscore_52w", "corn_realized_vol_20", "corn_gas_ratio"] if c in work.columns]
    for col in features:
        work[f"{col}_lag1"] = work[col].shift(1)
    lag_cols = [f"{c}_lag1" for c in features]
    work["crop_year"] = work["Date"].apply(crop_year)
    sub = work[["crop_year", "target_high_vol_h20", *lag_cols]].replace([np.inf, -np.inf], np.nan).dropna()
    rows = []
    y_all = []
    prob_all = []
    for idx in range(3, len(sorted(sub["crop_year"].unique()))):
        years = sorted(sub["crop_year"].unique())
        train = sub[sub["crop_year"].isin(years[:idx])]
        test = sub[sub["crop_year"] == years[idx]]
        if len(train) < 100 or len(test) < 20 or train["target_high_vol_h20"].nunique() < 2:
            continue
        model = LogisticRegression(max_iter=500, class_weight="balanced", solver="liblinear")
        model.fit(train[lag_cols], train["target_high_vol_h20"])
        prob = model.predict_proba(test[lag_cols])[:, 1]
        pred = (prob >= 0.5).astype(float)
        y = test["target_high_vol_h20"].values
        rows.append({
            "crop_year": int(years[idx]),
            "n": int(len(test)),
            "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
            "base_rate": float(y.mean()),
        })
        y_all.extend(y.tolist())
        prob_all.extend(prob.tolist())
    auc = float(roc_auc_score(y_all, prob_all)) if len(set(y_all)) > 1 else float("nan")
    ba_values = np.array([r["balanced_accuracy"] for r in rows])
    ci = bootstrap_ci(ba_values, np.mean, n_draws=500) if len(ba_values) else {}
    return {
        "target": "vol_regime_high_h20",
        "folds": rows,
        "auc_oof": auc,
        "mean_balanced_accuracy": float(np.mean(ba_values)) if len(ba_values) else float("nan"),
        "ci95_balanced_accuracy": ci,
        "verdict": "VOL_REGIME_SIGNAL" if auc >= 0.60 else "VOL_REGIME_NO_GO",
    }


def build_volatility_v2() -> dict:
    df = _load_vol()
    phase1 = build_volatility()
    har = _har_models(df)
    pred = _predict_high_vol(df)
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "phase1_reference": phase1.get("key_findings", {}),
        "vol_descriptive": {
            "mean_vol_20d": float(df["vol_20d"].mean()),
            "max_vol_20d": float(df["vol_20d"].max()),
            "mean_vol_60d": float(df["vol_60d"].mean()),
            "mean_vol_90d": float(df["vol_90d"].mean()),
        },
        "vol_regimes": _regime_stats(df),
        "garch_reference": phase1.get("garch_model", {}),
        "har_models": har,
        "vol_around_events": _event_vol(df),
        "vol_regime_prediction_oof": pred,
        "key_findings": {
            "mean_ann_vol": float(df["vol_20d"].mean()),
            "max_ann_vol": float(df["vol_20d"].max()),
            "har_base_r2": har["har_base"].get("r2"),
            "har_plus_basis_r2": har["har_plus_basis"].get("r2"),
            "vol_prediction_auc": pred["auc_oof"],
            "vol_prediction_verdict": pred["verdict"],
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
        "# EMA VOLATILITY V2",
        "",
        "> Volatilité EMA sur source exploratoire/proxy.",
        "",
        "## Résultats",
        "",
        f"- Vol annualisée moyenne : {k['mean_ann_vol']:.1%}",
        f"- Vol max : {k['max_ann_vol']:.1%}",
        f"- HAR base R² : {k['har_base_r2']:.3f}",
        f"- HAR + basis R² : {k['har_plus_basis_r2']:.3f}",
        f"- Prédiction régime vol AUC : {k['vol_prediction_auc']:.3f}",
        f"- Verdict : {k['vol_prediction_verdict']}",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_volatility_v2(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_volatility_v2()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_volatility_v2()
    print(f"Volatility v2 saved -> {out}")
