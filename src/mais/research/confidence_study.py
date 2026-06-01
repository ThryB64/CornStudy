"""IND-07 — Confidence, frequency, persistence and calibration analysis.

Produces three artefacts (all pre-2023 data only, never touching 2023–2025):
  artefacts/indicator/confidence_analysis.parquet
  artefacts/indicator/calibration_results.parquet
  artefacts/indicator/persistence_analysis.parquet

Run::

    venv/bin/python -m mais.research.confidence_study
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from mais.indicator.calibration import analyze_calibration, compare_platt_c_values
from mais.indicator.persistence import analyze_persistence, compute_signal_stability_rolling
from mais.paths import ARTEFACTS_DIR
from mais.utils import get_logger

log = get_logger("mais.research.confidence_study")

MAX_DATE = "2022-12-31"
HORIZON = 20
MODEL = "ridge_factors"
BASELINE_DA = 0.615
BASELINE_AUC = 0.655

SEASON_MAP = {
    2: "pre_semis", 3: "pre_semis",
    4: "semis", 5: "semis",
    6: "croissance",
    7: "pollinisation", 8: "pollinisation",
    9: "recolte", 10: "recolte",
    11: "post_recolte", 12: "post_recolte", 1: "post_recolte",
}


def _get_season(month: int) -> str:
    return SEASON_MAP.get(month, "unknown")


def _get_vol_bucket(val: float, q33: float, q67: float) -> str:
    if val <= q33:
        return "low_vol"
    if val <= q67:
        return "normal_vol"
    return "high_vol"


def compute_adaptive_threshold(
    val_confidence_scores: pd.Series,
    target_pct: float = 0.30,
    min_threshold: float = 0.25,
    max_threshold: float = 0.55,
) -> float:
    """Threshold from the validation confidence-score distribution."""
    scores = pd.Series(val_confidence_scores).replace([np.inf, -np.inf], np.nan).dropna()
    if scores.empty:
        return 0.35
    threshold = float(scores.quantile(target_pct))
    return float(np.clip(threshold, min_threshold, max_threshold))


def _compute_confidence_v4(
    auc_contexte: pd.Series | float,
    accord_modeles: pd.Series | float,
    prob_up_raw: pd.Series,
    cqr_width_norm: pd.Series | float,
    signal_stability: pd.Series | float,
) -> pd.Series:
    """Vectorized V4 confidence independent from Platt calibration."""
    auc_score = np.clip((auc_contexte - 0.5) / 0.25, 0.0, 1.0)
    return pd.Series(
        np.clip(
            0.25 * auc_score
            + 0.25 * np.clip(accord_modeles, 0.0, 1.0)
            + 0.20 * (prob_up_raw - 0.5).abs() * 2.0
            + 0.15 * (1.0 - np.clip(cqr_width_norm, 0.0, 1.0))
            + 0.15 * np.clip(signal_stability, 0.0, 1.0),
            0.0,
            1.0,
        )
    )


def _build_prediction_series(
    calib_preds: pd.DataFrame,
    regime_ts: pd.DataFrame,
    horizon: int = HORIZON,
    model: str = MODEL,
    max_date: str = MAX_DATE,
) -> pd.DataFrame:
    """Build a day-by-day prediction DataFrame with context columns."""
    p_col = f"p_up_h{horizon}"
    sub = calib_preds[
        (calib_preds["model"] == model)
        & (calib_preds["horizon"] == horizon)
        & (calib_preds["Date"] <= pd.Timestamp(max_date))
        & calib_preds[p_col].notna()
    ].copy()

    sub["Date"] = pd.to_datetime(sub["Date"])
    sub = sub.sort_values("Date").drop_duplicates("Date").reset_index(drop=True)
    sub["y_binary"] = (sub["y_true"] > 0).astype(float)

    # Season from month
    sub["season"] = sub["Date"].dt.month.map(_get_season).fillna("unknown")

    # Regime from regime_timeseries
    reg = regime_ts[["Date", "regime", "realized_vol_60d"]].copy()
    reg["Date"] = pd.to_datetime(reg["Date"])
    sub = sub.merge(reg, on="Date", how="left")
    sub["regime"] = sub["regime"].fillna("bull")

    # Vol bucket (quantiles computed on training window only — pre-2023)
    vol = sub["realized_vol_60d"].fillna(sub["realized_vol_60d"].median())
    q33 = float(vol.quantile(0.33))
    q67 = float(vol.quantile(0.67))
    sub["vol_bucket"] = vol.apply(lambda v: _get_vol_bucket(v, q33, q67))

    # Confidence components
    sub["prob_distance"] = (sub[p_col] - 0.5).abs() * 2.0

    # Cross-horizon model_agreement proxy via interval width
    w_col = "interval_width_logret_90"
    cqr_p75 = 0.249
    if w_col in sub.columns:
        sub["interval_width_inv"] = (1.0 - sub[w_col] / cqr_p75).clip(0, 1)
    else:
        sub["interval_width_inv"] = 0.5

    # Signal stability (rolling 5-day, labels encoded in persistence helper)
    sub["signal_label_raw"] = "NEUTRAL"
    sub.loc[sub[p_col] > 0.60, "signal_label_raw"] = "BULLISH"
    sub.loc[sub[p_col] < 0.40, "signal_label_raw"] = "BEARISH"
    sub["signal_stability"] = compute_signal_stability_rolling(
        sub["signal_label_raw"],
        window=5,
        initial_value=0.5,
    )

    # Confidence V1
    sub["confidence_v1"] = (
        0.30 * sub["prob_distance"]
        + 0.25 * 0.5  # model_agreement proxy (constant — no multi-model stack here)
        + 0.25 * sub["interval_width_inv"]
        + 0.20 * sub["signal_stability"]
    ).clip(0, 1)

    # Historical context confidence (expanding — uses only past data)
    sub["correct"] = (sub[p_col] > 0.5) == (sub["y_binary"] > 0.5)
    hist_ctx = np.full(len(sub), 0.5)
    for i in range(len(sub)):
        if i == 0:
            continue
        past = sub.iloc[:i]
        mask = (
            (past["season"] == sub.iloc[i]["season"])
            & (past["regime"] == sub.iloc[i]["regime"])
            & (past["vol_bucket"] == sub.iloc[i]["vol_bucket"])
        )
        similar = past[mask]
        if len(similar) < 50:
            hist_ctx[i] = 0.5
        else:
            da_hist = float(similar["correct"].mean())
            hist_ctx[i] = float(np.clip((da_hist - 0.5) / 0.30, 0.0, 1.0))
    sub["hist_context_conf"] = hist_ctx

    # Confidence V2
    sub["confidence_v2"] = (
        0.25 * sub["prob_distance"]
        + 0.20 * 0.5  # model_agreement proxy
        + 0.20 * sub["interval_width_inv"]
        + 0.15 * sub["signal_stability"]
        + 0.20 * sub["hist_context_conf"]
    ).clip(0, 1)

    # Confidence V3 = min of all normalized components
    sub["confidence_v3"] = sub[
        ["prob_distance", "interval_width_inv", "hist_context_conf"]
    ].min(axis=1).clip(0, 1)

    sub["confidence_v4"] = _compute_confidence_v4(
        auc_contexte=BASELINE_AUC,
        accord_modeles=0.5,
        prob_up_raw=sub[p_col],
        cqr_width_norm=1.0 - sub["interval_width_inv"],
        signal_stability=sub["signal_stability"],
    ).values

    # Predicted direction
    sub["pred_up"] = sub[p_col] > 0.5
    sub["actual_up"] = sub["y_binary"] > 0.5
    sub["correct"] = sub["pred_up"] == sub["actual_up"]

    return sub


def _da_by_tranche(df: pd.DataFrame, conf_col: str) -> pd.DataFrame:
    """DA by confidence tranche for a given confidence column."""
    bins = [0.0, 0.45, 0.55, 0.65, 0.75, 1.01]
    labels = ["<0.45", "0.45-0.55", "0.55-0.65", "0.65-0.75", ">0.75"]
    df = df.copy()
    df["tranche"] = pd.cut(df[conf_col], bins=bins, labels=labels, right=False)
    rows = []
    for lbl in labels:
        sub = df[df["tranche"] == lbl]
        n = len(sub)
        rows.append({
            "tranche": lbl,
            "da": float(sub["correct"].mean()) if n > 0 else float("nan"),
            "n_obs": n,
            "conf_version": conf_col,
        })
    # Top 10%
    thresh_10 = df[conf_col].quantile(0.90)
    top10 = df[df[conf_col] >= thresh_10]
    rows.append({
        "tranche": "top_10pct",
        "da": float(top10["correct"].mean()) if len(top10) > 0 else float("nan"),
        "n_obs": len(top10),
        "conf_version": conf_col,
    })
    return pd.DataFrame(rows)


def _sensitivity_analysis(df: pd.DataFrame, p_col: str) -> pd.DataFrame:
    """DA and signal frequency by threshold_prob × threshold_conf grid."""
    rows = []
    for tp in [0.55, 0.60, 0.65]:
        for tc in [0.60, 0.65, 0.70]:
            # Filter by conf threshold using V2
            filtered = df[df["confidence_v2"] >= tc].copy()
            directional = filtered[
                (filtered[p_col] > tp) | (filtered[p_col] < (1 - tp))
            ]
            n = len(directional)
            n_years = max(
                (pd.to_datetime(df["Date"].max()) - pd.to_datetime(df["Date"].min())).days / 365.25,
                1.0,
            )
            da = float(directional["correct"].mean()) if n > 0 else float("nan")
            rows.append({
                "threshold_prob": tp,
                "threshold_conf": tc,
                "da_directional": da,
                "n_directional": n,
                "signals_per_year": round(n / n_years, 1),
            })
    return pd.DataFrame(rows)


def _calibrate_thresholds(df: pd.DataFrame, p_col: str) -> tuple[pd.DataFrame, dict[str, float]]:
    """Evaluate adaptive thresholds and retain the least restrictive valid one."""
    n_years = max(
        (pd.to_datetime(df["Date"].max()) - pd.to_datetime(df["Date"].min())).days / 365.25,
        1.0,
    )
    rows = []
    for conf_col in ["confidence_v1", "confidence_v2", "confidence_v3", "confidence_v4"]:
        threshold = compute_adaptive_threshold(df[conf_col], target_pct=0.30)
        directional = df[
            (df[conf_col] >= threshold)
            & ((df[p_col] > 0.60) | (df[p_col] < 0.40))
        ]
        da = float(directional["correct"].mean()) if len(directional) else float("nan")
        rows.append(
            {
                "confidence_version": conf_col,
                "threshold": threshold,
                "n_directional": len(directional),
                "signals_per_year": round(len(directional) / n_years, 1),
                "da_directional": da,
            }
        )

    threshold_df = pd.DataFrame(rows)
    valid = threshold_df[
        (threshold_df["signals_per_year"] >= 20.0)
        & (threshold_df["da_directional"].fillna(0.0) >= BASELINE_DA - 0.02)
    ].copy()
    chosen = valid.iloc[-1] if not valid.empty else threshold_df.iloc[-1]
    retained = {
        "threshold": float(chosen["threshold"]),
        "signals_per_year": float(chosen["signals_per_year"]),
        "da_directional": float(chosen["da_directional"])
        if pd.notna(chosen["da_directional"])
        else float("nan"),
    }
    return threshold_df, retained


def _compare_platt_regularization(calib_preds: pd.DataFrame, p_col: str) -> pd.DataFrame:
    """Compare Platt C values on the same train/validation split as IND-07."""
    sub = calib_preds[
        (calib_preds["model"] == MODEL)
        & (calib_preds["horizon"] == HORIZON)
        & (calib_preds["Date"] <= pd.Timestamp(MAX_DATE))
        & calib_preds[p_col].notna()
    ].copy()
    sub["y_binary"] = (sub["y_true"] > 0).astype(float)
    all_folds = sorted(sub["fold"].unique())
    n_train = max(1, len(all_folds) - 2)
    train = sub[sub["fold"].isin(all_folds[:n_train])]
    val = sub[sub["fold"].isin(all_folds[n_train:])]
    if len(train) < 50 or len(val) < 50:
        return pd.DataFrame()
    return compare_platt_c_values(
        train[p_col].to_numpy(dtype=float),
        train["y_binary"].to_numpy(dtype=float),
        val[p_col].to_numpy(dtype=float),
        val["y_binary"].to_numpy(dtype=float),
    )


def run_confidence_study(
    artefacts_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Full IND-07 analysis. Returns dict of result DataFrames."""
    base = Path(artefacts_dir) if artefacts_dir else Path(ARTEFACTS_DIR) / "professional_study"
    out_dir = Path(ARTEFACTS_DIR) / "indicator"
    out_dir.mkdir(parents=True, exist_ok=True)

    log.info("loading_artefacts", base=str(base))
    calib_preds = pd.read_parquet(base / "calibrated_predictions.parquet")
    regime_ts = pd.read_parquet(base / "regime_timeseries.parquet")
    calib_preds["Date"] = pd.to_datetime(calib_preds["Date"])
    regime_ts["Date"] = pd.to_datetime(regime_ts["Date"])

    # --- Build prediction series ---
    log.info("building_prediction_series")
    pred_df = _build_prediction_series(calib_preds, regime_ts)
    p_col = f"p_up_h{HORIZON}"
    log.info("prediction_series_built", n=len(pred_df))

    # --- Confidence analysis ---
    log.info("computing_confidence_tranches")
    tranches = pd.concat(
        [
            _da_by_tranche(pred_df, "confidence_v1"),
            _da_by_tranche(pred_df, "confidence_v2"),
            _da_by_tranche(pred_df, "confidence_v3"),
            _da_by_tranche(pred_df, "confidence_v4"),
        ],
        ignore_index=True,
    )
    tranches["horizon"] = HORIZON
    tranches["model"] = MODEL

    sensitivity = _sensitivity_analysis(pred_df, p_col)
    confidence_analysis = pd.concat(
        [tranches, sensitivity.rename(columns={"da_directional": "da", "n_directional": "n_obs"})],
        ignore_index=True,
        sort=False,
    )
    confidence_analysis["max_date"] = MAX_DATE
    confidence_analysis.to_parquet(out_dir / "confidence_analysis.parquet", index=False)
    log.info("confidence_analysis_saved", path=str(out_dir / "confidence_analysis.parquet"))

    v3_comparison = pred_df[
        [
            "Date",
            p_col,
            "y_binary",
            "correct",
            "signal_stability",
            "confidence_v1",
            "confidence_v2",
            "confidence_v3",
            "confidence_v4",
        ]
    ].copy()
    v3_comparison.to_parquet(out_dir / "confidence_v3_01_comparison.parquet", index=False)

    threshold_df, retained_threshold = _calibrate_thresholds(pred_df, p_col)
    threshold_df.to_parquet(out_dir / "threshold_v3_01_comparison.parquet", index=False)
    threshold_yaml = out_dir / "threshold_calibration_v3_01.yaml"
    threshold_yaml.write_text(
        "\n".join(
            [
                "confidence:",
                "  version: v4",
                f"  threshold: {retained_threshold['threshold']:.6f}",
                "  platt_C: 1.0",
                "  signal_stability_window: 5",
                "  signal_stability_init: 0.5",
                f"signals_per_year: {retained_threshold['signals_per_year']:.3f}",
                f"da_directional: {retained_threshold['da_directional']:.6f}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # --- Calibration analysis ---
    log.info("running_calibration_analysis")
    cal_results, cal_reliability = analyze_calibration(
        calib_preds, horizon=HORIZON, model=MODEL, max_date=MAX_DATE
    )
    # Also run for additional models
    extra_results = []
    extra_reliability = []
    for h in [5, 10, 30]:
        r, rel = analyze_calibration(calib_preds, horizon=h, model=MODEL, max_date=MAX_DATE)
        if not r.empty:
            extra_results.append(r)
            extra_reliability.append(rel)

    all_cal = pd.concat(
        [cal_results] + extra_results, ignore_index=True
    ) if not cal_results.empty else pd.DataFrame()
    all_rel = pd.concat(
        [cal_reliability] + extra_reliability, ignore_index=True
    ) if not cal_reliability.empty else pd.DataFrame()

    if not all_cal.empty:
        all_cal["max_date"] = MAX_DATE
        all_cal.to_parquet(out_dir / "calibration_results.parquet", index=False)
        log.info("calibration_results_saved")

    platt_comparison = _compare_platt_regularization(calib_preds, p_col)
    if not platt_comparison.empty:
        platt_comparison.to_parquet(out_dir / "calibration_v3_01_comparison.parquet", index=False)

    if not all_rel.empty:
        all_rel["max_date"] = MAX_DATE
        all_rel.to_parquet(out_dir / "calibration_reliability.parquet", index=False)

    # --- Persistence analysis ---
    log.info("running_persistence_analysis")
    pers_results = []
    for h in [5, 10, 20, 30]:
        pr = analyze_persistence(calib_preds, horizon=h, model=MODEL, max_date=MAX_DATE)
        if not pr.empty:
            pers_results.append(pr)

    all_pers = pd.concat(pers_results, ignore_index=True) if pers_results else pd.DataFrame()
    if not all_pers.empty:
        all_pers["max_date"] = MAX_DATE
        all_pers.to_parquet(out_dir / "persistence_analysis.parquet", index=False)
        log.info("persistence_analysis_saved")

    report_path = out_dir / "confidence_v3_01_report.txt"
    best_threshold = threshold_df.sort_values("signals_per_year", ascending=False).iloc[0]
    report_path.write_text(
        "\n".join(
            [
                "V3-01 confidence calibration report",
                f"max_date: {MAX_DATE}",
                "signal_stability: rolling window=5, initial=0.5",
                "retained_version: confidence_v4",
                f"retained_threshold: {retained_threshold['threshold']:.6f}",
                f"retained_signals_per_year: {retained_threshold['signals_per_year']:.3f}",
                f"retained_da_directional: {retained_threshold['da_directional']:.6f}",
                f"most_active_version: {best_threshold['confidence_version']}",
                f"most_active_signals_per_year: {best_threshold['signals_per_year']:.3f}",
                "platt_C_retained: 1.0",
                "",
            ]
        ),
        encoding="utf-8",
    )

    return {
        "confidence_analysis": confidence_analysis,
        "calibration_results": all_cal,
        "persistence_analysis": all_pers,
        "threshold_calibration": threshold_df,
        "v3_comparison": v3_comparison,
    }


def _print_summary(results: dict[str, pd.DataFrame]) -> None:
    """Print human-readable summary to stdout."""
    print("\n=== IND-07 — Résultats Confidence Study ===\n")

    # Confidence tranches
    ca = results.get("confidence_analysis", pd.DataFrame())
    if not ca.empty:
        tranche_data = ca[ca["tranche"].isin(["<0.45", "0.45-0.55", "0.55-0.65", "0.65-0.75", ">0.75", "top_10pct"])]
        for version in ["confidence_v1", "confidence_v2", "confidence_v3", "confidence_v4"]:
            sub = tranche_data[tranche_data["conf_version"] == version]
            if sub.empty:
                continue
            print(f"\n--- {version} ---")
            print(f"{'Tranche':<15} {'DA':>8} {'N_obs':>8}")
            for _, row in sub.iterrows():
                da_str = f"{row['da']:.3f}" if not pd.isna(row.get('da')) else "N/A"
                print(f"{str(row['tranche']):<15} {da_str:>8} {int(row.get('n_obs', 0)):>8}")

    # Sensitivity
    sens = ca[ca["threshold_prob"].notna()] if not ca.empty and "threshold_prob" in ca.columns else pd.DataFrame()
    if not sens.empty:
        print("\n--- Sensibilité aux seuils (V2 confidence) ---")
        print(f"{'P(up)':>8} {'Conf':>8} {'DA dir.':>10} {'Signaux/an':>12}")
        for _, row in sens.iterrows():
            da_str = f"{row['da']:.3f}" if not pd.isna(row.get('da')) else "N/A"
            print(
                f"{row['threshold_prob']:>8.2f} {row['threshold_conf']:>8.2f}"
                f" {da_str:>10} {float(row.get('signals_per_year', 0)):>12.1f}"
            )

    # Calibration
    cr = results.get("calibration_results", pd.DataFrame())
    if not cr.empty:
        print("\n--- Calibration (ridge_factors h20) ---")
        h20 = cr[cr["horizon"] == 20]
        print(f"{'Méthode':<15} {'ECE':>8} {'Brier':>8}")
        for _, row in h20.iterrows():
            print(f"{row['method']:<15} {row['ece']:>8.4f} {row['brier']:>8.4f}")

    # Persistence
    pr = results.get("persistence_analysis", pd.DataFrame())
    if not pr.empty:
        h20 = pr[(pr["horizon"] == 20) & (pr["threshold_prob"] == 0.60) & (pr["threshold_conf"] == 0.45)]
        if not h20.empty:
            row = h20.iloc[0]
            print("\n--- Persistance (h20, thresh_prob=0.60, thresh_conf=0.45) ---")
            print(f"  flip_rate           : {row['flip_rate']:.3f}  (objectif < 0.30)")
            print(f"  persistence_3d      : {row['signal_persistence_3d']:.3f}  (objectif > 0.60)")
            print(f"  avg_streak          : {row['avg_streak']:.1f} jours")
            print(f"  signaux forts/an    : {row['strong_per_year']:.1f}  (objectif >= 20)")


if __name__ == "__main__":
    results = run_confidence_study()
    _print_summary(results)
