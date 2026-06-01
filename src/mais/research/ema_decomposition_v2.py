"""NB2-04 — Décomposition EMA descriptive vs prédictive."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, PROJECT_ROOT
from mais.research.ema_return_decomposition import build_return_decomposition
from mais.research.ema_utils import crop_year

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_decomposition_v2.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_DECOMPOSITION_V2.md"


def _load_data() -> pd.DataFrame:
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    cols = [
        "Date",
        "ema_front_price",
        "cbot_eur_t",
        "ema_cbot_basis",
        "ema_cbot_basis_zscore_52w",
        "ema_front_vol_20d_adjusted",
        "corn_realized_vol_20",
    ]
    df = feats.loc[feats["ema_front_price"].notna() & feats["cbot_eur_t"].notna(), [c for c in cols if c in feats.columns]].copy()
    df = df.sort_values("Date").reset_index(drop=True)
    df["ema_ret"] = df["ema_front_price"].pct_change()
    df["cbot_ret"] = df["cbot_eur_t"].pct_change()
    df["basis_chg"] = df["ema_cbot_basis"].diff()
    df["crop_year"] = df["Date"].apply(crop_year)
    return df


def _fit_r2(y: np.ndarray, x: np.ndarray) -> dict:
    x_c = np.column_stack([np.ones(len(x)), x])
    coefs, _, _, _ = np.linalg.lstsq(x_c, y, rcond=None)
    pred = x_c @ coefs
    return {
        "r2": float(r2_score(y, pred)),
        "coefs": [float(c) for c in coefs],
        "n": int(len(y)),
    }


def _descriptive_block(df: pd.DataFrame) -> dict:
    sub = df[["ema_ret", "cbot_ret", "basis_chg"]].dropna()
    cbot_only = _fit_r2(sub["ema_ret"].values, sub[["cbot_ret"]].values)
    cbot_basis = _fit_r2(sub["ema_ret"].values, sub[["cbot_ret", "basis_chg"]].values)
    return {
        "label": "DESCRIPTIF_NON_PREDICTIF",
        "equation": "ΔEMA_t = β1 × ΔCBOT_t + β2 × Δbasis_t + résidu_t",
        "warning": "Variables contemporaines. Résultat descriptif, NON prédictif.",
        "model_cbot_only": cbot_only,
        "model_cbot_plus_basis": cbot_basis,
        "incremental_r2_basis": float(cbot_basis["r2"] - cbot_only["r2"]),
    }


def _predictive_block(df: pd.DataFrame, horizon: int = 20) -> dict:
    work = df.copy()
    work[f"ema_ret_h{horizon}"] = work["ema_front_price"].pct_change(horizon).shift(-horizon)
    feature_cols = [
        "cbot_ret",
        "ema_cbot_basis",
        "ema_cbot_basis_zscore_52w",
        "ema_front_vol_20d_adjusted",
        "corn_realized_vol_20",
    ]
    feature_cols = [c for c in feature_cols if c in work.columns]
    for col in feature_cols:
        work[f"{col}_lag1"] = work[col].shift(1)
    lag_cols = [f"{c}_lag1" for c in feature_cols]
    sub = work[["Date", "crop_year", f"ema_ret_h{horizon}", *lag_cols]].dropna()
    crop_years = sorted(sub["crop_year"].unique())
    rows = []
    all_true = []
    all_pred = []
    for idx in range(3, len(crop_years)):
        train_years = crop_years[:idx]
        test_year = crop_years[idx]
        train = sub[sub["crop_year"].isin(train_years)]
        test = sub[sub["crop_year"] == test_year]
        if len(train) < 100 or len(test) < 20:
            continue
        model = Ridge(alpha=1.0)
        model.fit(train[lag_cols], train[f"ema_ret_h{horizon}"])
        pred = model.predict(test[lag_cols])
        y_true = test[f"ema_ret_h{horizon}"].values
        naive = np.repeat(train[f"ema_ret_h{horizon}"].mean(), len(test))
        rows.append({
            "crop_year": int(test_year),
            "n_test": int(len(test)),
            "r2_model": float(r2_score(y_true, pred)),
            "r2_naive_drift": float(r2_score(y_true, naive)),
        })
        all_true.extend(y_true.tolist())
        all_pred.extend(pred.tolist())
    return {
        "label": "PREDICTIF_SHIFT1_OOF",
        "equation": f"ΔEMA_t+{horizon} = f(features_t-1)",
        "horizon": horizon,
        "feature_cols_shifted": lag_cols,
        "folds": rows,
        "overall_oof_r2": float(r2_score(all_true, all_pred)) if all_true else float("nan"),
        "mean_fold_r2": float(np.mean([r["r2_model"] for r in rows])) if rows else float("nan"),
        "verdict": "PREDICTIVE_WEAK" if rows and np.mean([r["r2_model"] for r in rows]) > 0.02 else "PREDICTIVE_NO_GO",
    }


def _rolling_betas(df: pd.DataFrame, window: int = 260) -> dict:
    sub = df[["Date", "ema_ret", "cbot_ret", "basis_chg"]].dropna().reset_index(drop=True)
    rows = []
    for i in range(window, len(sub) + 1):
        win = sub.iloc[i - window:i]
        fit = _fit_r2(win["ema_ret"].values, win[["cbot_ret", "basis_chg"]].values)
        rows.append({
            "date": str(win["Date"].iloc[-1].date()),
            "r2": fit["r2"],
            "beta_cbot": fit["coefs"][1],
            "beta_basis": fit["coefs"][2],
        })
    return {
        "window": window,
        "n_windows": len(rows),
        "mean_beta_cbot": float(np.mean([r["beta_cbot"] for r in rows])) if rows else float("nan"),
        "mean_beta_basis": float(np.mean([r["beta_basis"] for r in rows])) if rows else float("nan"),
        "mean_r2": float(np.mean([r["r2"] for r in rows])) if rows else float("nan"),
    }


def _by_regime(df: pd.DataFrame) -> dict:
    work = df.copy()
    work["year_regime"] = np.select(
        [
            work["Date"].dt.year.between(2014, 2019),
            work["Date"].dt.year.between(2020, 2022),
            work["Date"].dt.year.between(2023, 2026),
        ],
        ["normal_2014_2019", "crisis_2020_2022", "post_crisis_2023_2026"],
        default="early_or_other",
    )
    out = {}
    for regime, sub in work.groupby("year_regime"):
        model_df = sub[["ema_ret", "cbot_ret", "basis_chg"]].dropna()
        if len(model_df) < 50:
            continue
        fit = _fit_r2(model_df["ema_ret"].values, model_df[["cbot_ret", "basis_chg"]].values)
        out[str(regime)] = {
            "n": fit["n"],
            "r2": fit["r2"],
            "beta_cbot": fit["coefs"][1],
            "beta_basis": fit["coefs"][2],
        }
    return out


def build_decomposition_v2() -> dict:
    df = _load_data()
    phase1 = build_return_decomposition()
    descriptive = _descriptive_block(df)
    predictive = _predictive_block(df, horizon=20)
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "phase1_reference": phase1.get("key_findings", {}),
        "descriptive_contemporaneous": descriptive,
        "predictive_shift1_oof": predictive,
        "rolling_260d": _rolling_betas(df),
        "by_regime": _by_regime(df),
        "key_findings": {
            "descriptive_r2_cbot_basis": descriptive["model_cbot_plus_basis"]["r2"],
            "descriptive_incremental_r2_basis": descriptive["incremental_r2_basis"],
            "predictive_oof_r2_h20": predictive["overall_oof_r2"],
            "predictive_verdict": predictive["verdict"],
            "mandatory_label": "DESCRIPTIF / PRÉDICTIF séparés sur chaque résultat.",
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
        "# EMA DECOMPOSITION V2",
        "",
        "> Source EMA exploratoire/proxy. Chaque bloc indique DESCRIPTIF ou PRÉDICTIF.",
        "",
        "## DESCRIPTIF",
        "",
        "Variables contemporaines : ΔEMA_t = β1 × ΔCBOT_t + β2 × Δbasis_t + résidu_t.",
        f"R² CBOT + basis : {k['descriptive_r2_cbot_basis']:.3f}.",
        f"Gain basis : {k['descriptive_incremental_r2_basis']:.3f}.",
        "",
        "Ce bloc est descriptif, NON prédictif.",
        "",
        "## PRÉDICTIF",
        "",
        "Variables décalées shift(1), walk-forward OOF.",
        f"R² OOF H20 : {k['predictive_oof_r2_h20']:.3f}.",
        f"Verdict : {k['predictive_verdict']}.",
        "",
        "## Conclusion",
        "",
        "La décomposition contemporaine explique EMA, mais la prédiction des retours EMA reste faible.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_decomposition_v2(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_decomposition_v2()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_decomposition_v2()
    print(f"Decomposition v2 saved -> {out}")
