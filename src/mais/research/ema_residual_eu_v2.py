"""NB2-05 — Résidu européen EMA/CBOT et catalogue des chocs."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, PROJECT_ROOT
from mais.research.ema_utils import binary_target_from_condition, crop_year

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_residual_eu_v2.json"
_CATALOGUE_OUTPUT = _STUDY_DIR / "eu_event_catalogue.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_RESIDUAL_EU_V2.md"


def _load_data() -> pd.DataFrame:
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    keep = [
        "Date",
        "ema_front_price",
        "cbot_eur_t",
        "ema_cbot_basis",
        "ema_cbot_basis_zscore_52w",
        "ema_front_vol_20d_adjusted",
        "corn_realized_vol_20",
        "corn_gas_ratio",
        "corn_gas_corr60",
    ]
    df = feats[[c for c in keep if c in feats.columns]].copy()
    df = df[df["ema_front_price"].notna() & df["cbot_eur_t"].notna()].sort_values("Date").reset_index(drop=True)
    df["ema_ret"] = df["ema_front_price"].pct_change()
    df["cbot_ret"] = df["cbot_eur_t"].pct_change()
    df["basis_chg"] = df["ema_cbot_basis"].diff()
    df["crop_year"] = df["Date"].apply(crop_year)
    return df.dropna(subset=["ema_ret", "cbot_ret", "basis_chg"]).reset_index(drop=True)


def _fit_coefficients(train: pd.DataFrame) -> np.ndarray:
    x = train[["cbot_ret", "basis_chg"]].values
    y = train["ema_ret"].values
    xc = np.column_stack([np.ones(len(x)), x])
    coefs, _, _, _ = np.linalg.lstsq(xc, y, rcond=None)
    return coefs


def _compute_oof_residuals(df: pd.DataFrame) -> pd.DataFrame:
    crop_years = sorted(df["crop_year"].unique())
    rows = []
    for idx in range(3, len(crop_years)):
        train_years = crop_years[:idx]
        test_year = crop_years[idx]
        train = df[df["crop_year"].isin(train_years)]
        test = df[df["crop_year"] == test_year].copy()
        if len(train) < 200 or len(test) < 20:
            continue
        coefs = _fit_coefficients(train)
        x_test = np.column_stack([np.ones(len(test)), test[["cbot_ret", "basis_chg"]].values])
        test["ema_residual_oof"] = test["ema_ret"] - x_test @ coefs
        test["beta_intercept_train"] = float(coefs[0])
        test["beta_cbot_train"] = float(coefs[1])
        test["beta_basis_train"] = float(coefs[2])
        rows.append(test)
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    sigma = out["ema_residual_oof"].std()
    out["residual_z"] = out["ema_residual_oof"] / sigma
    return out


def _event_catalogue(resid: pd.DataFrame, sigma: float) -> list[dict]:
    events = resid[resid["residual_z"].abs() >= sigma].copy()
    events["abs_z"] = events["residual_z"].abs()
    events = events.sort_values("abs_z", ascending=False)
    rows = []
    for _, row in events.iterrows():
        date = pd.Timestamp(row["Date"])
        rows.append({
            "date": str(date.date()),
            "year": int(date.year),
            "crop_year": int(row["crop_year"]),
            "threshold_sigma": sigma,
            "residual": float(row["ema_residual_oof"]),
            "residual_z": float(row["residual_z"]),
            "direction": "positive" if row["ema_residual_oof"] > 0 else "negative",
            "event_type_auto": _classify_event(date, row),
            "context": {
                "basis_zscore": _safe_float(row.get("ema_cbot_basis_zscore_52w")),
                "ema_vol_20d": _safe_float(row.get("ema_front_vol_20d_adjusted")),
                "corn_gas_ratio": _safe_float(row.get("corn_gas_ratio")),
            },
        })
    return rows


def _safe_float(value) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _classify_event(date: pd.Timestamp, row: pd.Series) -> str:
    year = int(date.year)
    basis_z = row.get("ema_cbot_basis_zscore_52w")
    vol = row.get("ema_front_vol_20d_adjusted")
    if year == 2022:
        return "ukraine_geopolitical_or_black_sea"
    if year in {2012, 2018}:
        return "weather_crisis_possible"
    if year == 2020:
        return "covid_market_stress"
    if pd.notna(basis_z) and abs(float(basis_z)) > 2:
        return "basis_dislocation"
    if pd.notna(vol) and float(vol) > 0.30:
        return "volatility_stress"
    return "unclassified_requires_manual_review"


def _driver_attribution(resid: pd.DataFrame) -> dict:
    drivers = [
        "ema_cbot_basis_zscore_52w",
        "ema_front_vol_20d_adjusted",
        "corn_realized_vol_20",
        "corn_gas_ratio",
        "corn_gas_corr60",
    ]
    out = {}
    for col in drivers:
        if col not in resid.columns:
            out[col] = {"status": "missing"}
            continue
        sub = resid[["ema_residual_oof", col]].dropna()
        if len(sub) < 30:
            out[col] = {"status": "insufficient_data", "n": int(len(sub))}
            continue
        out[col] = {
            "status": "available",
            "n": int(len(sub)),
            "corr_with_residual": float(sub["ema_residual_oof"].corr(sub[col])),
            "mean_driver_on_2sigma_events": float(resid.loc[resid["residual_z"].abs() >= 2, col].mean()),
            "mean_driver_overall": float(resid[col].mean()),
        }
    out["missing_driver_families"] = [
        "Open-Meteo EU/Ukraine not present in master features",
        "WASDE EU/Ukraine not present in master features",
        "EUR/USD direct series not present in master features",
        "TTF/ETS direct series not present in master features",
        "MARS monthly bulletin text not parsed",
    ]
    return out


def _predict_shocks(resid: pd.DataFrame) -> dict:
    work = resid.copy()
    sigma = work["ema_residual_oof"].std()
    work["future_resid_h20"] = work["ema_residual_oof"].shift(-20)
    work["shock_up_h20"] = binary_target_from_condition(
        work["future_resid_h20"] > 2 * sigma,
        work["future_resid_h20"].notna(),
    )
    work["shock_down_h20"] = binary_target_from_condition(
        work["future_resid_h20"] < -2 * sigma,
        work["future_resid_h20"].notna(),
    )
    feature_cols = [
        c for c in [
            "ema_cbot_basis_zscore_52w",
            "ema_front_vol_20d_adjusted",
            "corn_realized_vol_20",
            "corn_gas_ratio",
            "corn_gas_corr60",
        ] if c in work.columns
    ]
    for col in feature_cols:
        work[f"{col}_lag1"] = work[col].shift(1)
    lag_cols = [f"{c}_lag1" for c in feature_cols]
    out = {}
    for target in ["shock_up_h20", "shock_down_h20"]:
        sub = work[["crop_year", target, *lag_cols]].dropna()
        rows = []
        probs = []
        y_all = []
        crop_years = sorted(sub["crop_year"].unique())
        for idx in range(3, len(crop_years)):
            train = sub[sub["crop_year"].isin(crop_years[:idx])]
            test = sub[sub["crop_year"] == crop_years[idx]]
            if len(train) < 100 or len(test) < 20 or train[target].nunique() < 2:
                continue
            model = LogisticRegression(max_iter=500, class_weight="balanced", solver="liblinear")
            model.fit(train[lag_cols], train[target])
            pred = model.predict(test[lag_cols])
            prob = model.predict_proba(test[lag_cols])[:, 1]
            y = test[target].values
            rows.append({
                "crop_year": int(crop_years[idx]),
                "n_test": int(len(test)),
                "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
                "base_rate": float(y.mean()),
            })
            probs.extend(prob.tolist())
            y_all.extend(y.tolist())
        auc = float(roc_auc_score(y_all, probs)) if len(set(y_all)) > 1 else float("nan")
        out[target] = {
            "folds": rows,
            "auc_oof": auc,
            "mean_balanced_accuracy": float(np.mean([r["balanced_accuracy"] for r in rows])) if rows else float("nan"),
            "verdict": "EXPERIMENTAL_GO" if rows and auc >= 0.60 else "NO_GO_OR_INSUFFICIENT",
        }
    return out


def _leave_one_crisis_out(df: pd.DataFrame) -> dict:
    out = {}
    for year in [2012, 2020, 2021, 2022]:
        sub = df[df["Date"].dt.year != year]
        resid = _compute_oof_residuals(sub)
        if len(resid) == 0:
            out[f"without_{year}"] = {"error": "insufficient_data"}
            continue
        out[f"without_{year}"] = {
            "n_obs": int(len(resid)),
            "residual_std": float(resid["ema_residual_oof"].std()),
            "n_events_2sigma": int((resid["residual_z"].abs() >= 2).sum()),
            "n_events_3sigma": int((resid["residual_z"].abs() >= 3).sum()),
        }
    return out


def build_residual_eu_v2() -> dict:
    df = _load_data()
    resid = _compute_oof_residuals(df)
    events_2 = _event_catalogue(resid, 2.0)
    events_3 = _event_catalogue(resid, 3.0)
    predictability = _predict_shocks(resid)
    catalogue = {"events_2sigma": events_2, "events_3sigma": events_3}
    _CATALOGUE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _CATALOGUE_OUTPUT.write_text(json.dumps(catalogue, indent=2), encoding="utf-8")
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "residual_method": "OOF coefficients by crop year: ΔEMA_t - (β1_train×ΔCBOT_t + β2_train×Δbasis_t)",
        "n_residual_obs": int(len(resid)),
        "period_start": str(resid["Date"].min().date()) if len(resid) else None,
        "period_end": str(resid["Date"].max().date()) if len(resid) else None,
        "residual_stats": {
            "mean": float(resid["ema_residual_oof"].mean()),
            "std": float(resid["ema_residual_oof"].std()),
            "n_events_2sigma": len(events_2),
            "n_events_3sigma": len(events_3),
        },
        "event_catalogue_preview_3sigma": events_3[:25],
        "driver_attribution": _driver_attribution(resid),
        "shock_predictability": predictability,
        "leave_one_crisis_out": _leave_one_crisis_out(df),
        "key_findings": {
            "n_extreme_events_2sigma": len(events_2),
            "n_extreme_events_3sigma": len(events_3),
            "catalogue_path": str(_CATALOGUE_OUTPUT),
            "predictability_verdict_up": predictability["shock_up_h20"]["verdict"],
            "predictability_verdict_down": predictability["shock_down_h20"]["verdict"],
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
    stats = data["residual_stats"]
    lines = [
        "# EMA RESIDUAL EU V2",
        "",
        "> Résidu européen OOF. Source EMA exploratoire/proxy.",
        "",
        "## Méthode",
        "",
        data["residual_method"],
        "",
        "## Chocs",
        "",
        f"- Événements 2σ : {stats['n_events_2sigma']}",
        f"- Événements 3σ : {stats['n_events_3sigma']}",
        f"- Écart-type résiduel : {stats['std']:.4f}",
        "",
        "## Attribution",
        "",
        "Les familles météo EU, Ukraine, EUR/USD direct, TTF/ETS direct et MARS mensuel sont marquées manquantes si elles ne sont pas présentes dans le master features.",
        "",
        "## Verdict",
        "",
        "Le catalogue de chocs est exploitable pour analyse événementielle, mais la prédiction des chocs résiduels reste expérimentale.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_residual_eu_v2(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_residual_eu_v2()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_residual_eu_v2()
    print(f"Residual EU v2 saved -> {out}")
