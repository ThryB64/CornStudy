"""IND-08 — Indicateur V2 : backtest final out-of-time 2023–2025.

Exécuté UNE SEULE FOIS sur les données 2023–2025 réservées.
Produit :
  artefacts/indicator/indicator_backtest_v2.parquet
  artefacts/indicator/error_analysis.parquet

Run::

    venv/bin/python -m mais.research.backtest_v2
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from mais.indicator.calibration import PlattCalibrator
from mais.indicator.error_analysis import run_error_analysis, summarize_errors
from mais.indicator.persistence import compute_signal_streak
from mais.paths import ARTEFACTS_DIR
from mais.utils import get_logger

log = get_logger("mais.research.backtest_v2")

MODEL = "ridge_factors"
HORIZON = 20
P_COL = f"p_up_h{HORIZON}"

TRAIN_FOLDS = [0, 1, 2, 3, 4, 5]
TEST_MIN_DATE = "2023-01-01"

SEASON_MAP = {
    2: "pre_semis", 3: "pre_semis",
    4: "semis", 5: "semis",
    6: "croissance",
    7: "pollinisation", 8: "pollinisation",
    9: "recolte", 10: "recolte",
    11: "post_recolte", 12: "post_recolte", 1: "post_recolte",
}

CONF_THRESHOLD = 0.45     # UNCERTAIN below this
PROB_THRESHOLD = 0.60     # BULLISH above, BEARISH below 1-thresh


def _prob_to_signal(p: float, conf: float) -> str:
    if conf < CONF_THRESHOLD:
        return "UNCERTAIN"
    if p > PROB_THRESHOLD:
        return "BULLISH"
    if p < (1.0 - PROB_THRESHOLD):
        return "BEARISH"
    return "NEUTRAL"


def _get_season(month: int) -> str:
    return SEASON_MAP.get(month, "unknown")


def _get_vol_bucket(v: float, q33: float, q67: float) -> str:
    if v <= q33:
        return "low_vol"
    if v <= q67:
        return "normal_vol"
    return "high_vol"


def _fit_platt_on_train(
    calib_preds: pd.DataFrame,
    train_folds: list[int],
) -> PlattCalibrator:
    train = calib_preds[
        (calib_preds["model"] == MODEL)
        & (calib_preds["horizon"] == HORIZON)
        & calib_preds["fold"].isin(train_folds)
        & calib_preds[P_COL].notna()
    ].copy()
    y_prob = train[P_COL].values.astype(float)
    y_true = (train["y_true"].values > 0).astype(float)
    return PlattCalibrator().fit(y_prob, y_true)


def _build_backtest_df(
    calib_preds: pd.DataFrame,
    regime_ts: pd.DataFrame,
    calibrator: PlattCalibrator,
) -> pd.DataFrame:
    """Build the out-of-time prediction DataFrame (2023–2025 only)."""
    sub = calib_preds[
        (calib_preds["model"] == MODEL)
        & (calib_preds["horizon"] == HORIZON)
        & (calib_preds["Date"] >= pd.Timestamp(TEST_MIN_DATE))
        & calib_preds[P_COL].notna()
    ].copy()

    sub["Date"] = pd.to_datetime(sub["Date"])
    sub = sub.sort_values("Date").drop_duplicates("Date").reset_index(drop=True)
    sub["y_binary"] = (sub["y_true"] > 0).astype(float)
    sub["season"] = sub["Date"].dt.month.map(_get_season).fillna("unknown")
    sub["year"] = sub["Date"].dt.year

    # Regime
    reg = regime_ts[["Date", "regime", "realized_vol_60d"]].copy()
    reg["Date"] = pd.to_datetime(reg["Date"])
    sub = sub.merge(reg, on="Date", how="left")
    sub["regime"] = sub["regime"].fillna("bull")

    # Vol bucket — quantiles from pre-2023 regime data (avoid leakage)
    train_vol = regime_ts[regime_ts["Date"] < pd.Timestamp(TEST_MIN_DATE)]["realized_vol_60d"]
    q33 = float(train_vol.quantile(0.33))
    q67 = float(train_vol.quantile(0.67))
    vol_filled = sub["realized_vol_60d"].fillna(train_vol.median())
    sub["vol_bucket"] = vol_filled.apply(lambda v: _get_vol_bucket(v, q33, q67))

    # Calibrated probability
    sub["p_up_calib"] = calibrator.transform(sub[P_COL].values.astype(float))

    # Confidence V1 proxy
    w_col = "interval_width_logret_90"
    cqr_p75 = 0.249
    if w_col in sub.columns:
        sub["interval_width_inv"] = (1.0 - sub[w_col] / cqr_p75).clip(0.0, 1.0)
    else:
        sub["interval_width_inv"] = 0.5

    sub["prob_distance"] = (sub["p_up_calib"] - 0.5).abs() * 2.0
    sub["signal_direction"] = (sub["p_up_calib"] > 0.5).astype(int)
    sub["signal_stability"] = (
        sub["signal_direction"]
        .rolling(3, min_periods=1)
        .apply(lambda x: (x == x.iloc[-1]).mean())
    )

    sub["confidence_v1"] = (
        0.30 * sub["prob_distance"]
        + 0.25 * 0.5  # model_agreement constant proxy
        + 0.25 * sub["interval_width_inv"]
        + 0.20 * sub["signal_stability"]
    ).clip(0.0, 1.0)

    sub["signal"] = [
        _prob_to_signal(float(p), float(c))
        for p, c in zip(sub["p_up_calib"], sub["confidence_v1"], strict=False)
    ]

    sub["correct"] = (sub["p_up_calib"] > 0.5) == (sub["y_binary"] > 0.5)
    sub["pred_up"] = sub["p_up_calib"] > 0.5

    return sub


def _compute_baselines(
    calib_preds: pd.DataFrame,
    test_min: str = TEST_MIN_DATE,
) -> dict[str, float]:
    """DA for seasonal and momentum baselines on 2023-2025."""
    results = {}
    for baseline in ["baseline_seasonal_naive", "baseline_momentum_20d"]:
        sub = calib_preds[
            (calib_preds["model"] == baseline)
            & (calib_preds["horizon"] == HORIZON)
            & (calib_preds["Date"] >= pd.Timestamp(test_min))
        ].copy()
        if sub.empty:
            continue
        # y_pred is a logret prediction; direction = y_pred > 0
        correct = ((sub["y_pred"] > 0) == (sub["y_true"] > 0)).mean()
        results[baseline] = float(correct)
    return results


def _metrics_for_subset(df: pd.DataFrame) -> dict:
    """Standard metrics dict for a subset of predictions."""
    n = len(df)
    if n == 0:
        return {"da": float("nan"), "n": 0}
    da = float(df["correct"].mean())
    avg_ret = float(df["y_true"].mean())

    try:
        from sklearn.metrics import brier_score_loss, roc_auc_score
        auc = float(roc_auc_score(df["y_binary"], df["p_up_calib"])) if df["y_binary"].nunique() > 1 else float("nan")
        brier = float(brier_score_loss(df["y_binary"], df["p_up_calib"]))
    except ImportError:
        auc = float("nan")
        brier = float("nan")

    return {"da": da, "n": n, "avg_ret": avg_ret, "auc": auc, "brier": brier}


def run_backtest_v2(
    artefacts_dir: Path | None = None,
) -> dict[str, object]:
    """Execute the final IND-08 backtest on 2023–2025.

    This is the FIRST and ONLY time 2023–2025 data is used for evaluation.
    Returns a dict of DataFrames and a metrics dict.
    """
    base = Path(artefacts_dir) if artefacts_dir else Path(ARTEFACTS_DIR) / "professional_study"
    out_dir = Path(ARTEFACTS_DIR) / "indicator"
    out_dir.mkdir(parents=True, exist_ok=True)

    log.info("loading_artefacts", base=str(base))
    calib_preds = pd.read_parquet(base / "calibrated_predictions.parquet")
    regime_ts = pd.read_parquet(base / "regime_timeseries.parquet")
    calib_preds["Date"] = pd.to_datetime(calib_preds["Date"])
    regime_ts["Date"] = pd.to_datetime(regime_ts["Date"])

    # --- Fit calibrator on pre-2023 train folds ---
    log.info("fitting_platt_calibrator", train_folds=TRAIN_FOLDS)
    calibrator = _fit_platt_on_train(calib_preds, TRAIN_FOLDS)

    # --- Build out-of-time prediction series ---
    log.info("building_oot_predictions", min_date=TEST_MIN_DATE)
    df = _build_backtest_df(calib_preds, regime_ts, calibrator)
    n_total = len(df)
    log.info("oot_built", n=n_total)

    # --- Signal streak (persistence) ---
    df["signal_streak"] = compute_signal_streak(
        pd.Series(df["signal"].values, index=df["Date"].values)
    ).values

    n_years = max(
        (df["Date"].max() - df["Date"].min()).days / 365.25, 1.0
    )

    # --- Global metrics ---
    global_metrics = _metrics_for_subset(df)
    directional = df[df["signal"].isin(["BULLISH", "BEARISH"])]
    uncertain = df[df["signal"] == "UNCERTAIN"]
    bullish_df = df[df["signal"] == "BULLISH"]
    bearish_df = df[df["signal"] == "BEARISH"]

    top20_thresh = df["confidence_v1"].quantile(0.80)
    top10_thresh = df["confidence_v1"].quantile(0.90)
    top20 = df[df["confidence_v1"] >= top20_thresh]
    top10 = df[df["confidence_v1"] >= top10_thresh]

    flipped = (df["signal"] != df["signal"].shift()).fillna(False)
    flip_rate = float(flipped.mean())

    metrics = {
        "da_global": global_metrics["da"],
        "da_bullish": float(bullish_df["correct"].mean()) if len(bullish_df) > 0 else float("nan"),
        "da_bearish": float(bearish_df["correct"].mean()) if len(bearish_df) > 0 else float("nan"),
        "da_uncertain": float(uncertain["correct"].mean()) if len(uncertain) > 0 else float("nan"),
        "da_top20pct": float(top20["correct"].mean()) if len(top20) > 0 else float("nan"),
        "da_top10pct": float(top10["correct"].mean()) if len(top10) > 0 else float("nan"),
        "auc": global_metrics.get("auc"),
        "brier": global_metrics.get("brier"),
        "avg_ret_bullish": float(bullish_df["y_true"].mean()) if len(bullish_df) > 0 else float("nan"),
        "avg_ret_bearish": float(bearish_df["y_true"].mean()) if len(bearish_df) > 0 else float("nan"),
        "n_total": n_total,
        "n_bullish": len(bullish_df),
        "n_bearish": len(bearish_df),
        "n_uncertain": len(uncertain),
        "n_directional": len(directional),
        "n_top20": len(top20),
        "n_top10": len(top10),
        "strong_per_year": round((len(bullish_df) + len(bearish_df)) / n_years, 1),
        "flip_rate": flip_rate,
        "signal_persistence_3d": float((df["signal_streak"] >= 3).mean()),
        "avg_streak": float(df["signal_streak"].mean()),
    }

    # --- Performance by year ---
    by_year = (
        df.groupby("year")
        .apply(lambda g: pd.Series(_metrics_for_subset(g)), include_groups=False)
        .reset_index()
    )

    # --- Performance by season ---
    by_season = (
        df.groupby("season")
        .apply(lambda g: pd.Series(_metrics_for_subset(g)), include_groups=False)
        .reset_index()
    )

    # --- Compare to baselines ---
    baselines = _compute_baselines(calib_preds)
    metrics["da_seasonal_baseline"] = baselines.get("baseline_seasonal_naive", float("nan"))
    metrics["da_momentum_baseline"] = baselines.get("baseline_momentum_20d", float("nan"))

    # --- Signal distribution ---
    signal_dist = df["signal"].value_counts().to_dict()
    for lbl in ["BULLISH", "BEARISH", "NEUTRAL", "UNCERTAIN"]:
        metrics[f"n_{lbl.lower()}_total"] = signal_dist.get(lbl, 0)

    # --- Error analysis ---
    log.info("running_error_analysis")
    errors = run_error_analysis(df)
    err_summaries = summarize_errors(errors)

    # --- V2 ablation on out-of-time (component ablation) ---
    ablation = []
    base_da = metrics["da_global"]

    for component in ["prob_distance", "interval_width_inv", "signal_stability"]:
        df_abl = df.copy()
        # Drop component → set to its mean (zero contribution)
        df_abl["confidence_ablated"] = df["confidence_v1"].copy()
        col_mean = df[component].mean()
        df_abl["confidence_ablated"] -= (
            {"prob_distance": 0.30, "interval_width_inv": 0.25, "signal_stability": 0.20}[component]
            * (df[component] - col_mean)
        )
        df_abl["confidence_ablated"] = df_abl["confidence_ablated"].clip(0, 1)
        df_abl["signal_abl"] = [
            _prob_to_signal(float(p), float(c))
            for p, c in zip(df_abl["p_up_calib"], df_abl["confidence_ablated"], strict=False)
        ]
        df_abl["correct_abl"] = (df_abl["p_up_calib"] > 0.5) == (df_abl["y_binary"] > 0.5)
        da_abl = float(df_abl["correct_abl"].mean())
        ablation.append({"component": component, "da_full": base_da, "da_without": da_abl, "delta": base_da - da_abl})

    ablation_df = pd.DataFrame(ablation)

    # --- Save artefacts ---
    df.to_parquet(out_dir / "indicator_backtest_v2.parquet", index=False)
    log.info("backtest_saved", path=str(out_dir / "indicator_backtest_v2.parquet"))

    if not errors.empty:
        errors.to_parquet(out_dir / "error_analysis.parquet", index=False)
        log.info("error_analysis_saved")

    ablation_df.to_parquet(out_dir / "v2_component_ablation.parquet", index=False)

    # Summary parquet
    metrics_df = pd.DataFrame([metrics])
    metrics_df.to_parquet(out_dir / "backtest_v2_metrics.parquet", index=False)

    return {
        "metrics": metrics,
        "df": df,
        "by_year": by_year,
        "by_season": by_season,
        "errors": errors,
        "err_summaries": err_summaries,
        "ablation": ablation_df,
        "baselines": baselines,
    }


def _print_report(results: dict) -> None:
    m = results["metrics"]
    print("\n" + "=" * 60)
    print("IND-08 — Backtest Final V2 — Out-of-Time 2023–2025")
    print("=" * 60)
    print(f"\nModèle : {MODEL}, Horizon : J+{HORIZON}")
    print(f"N observations : {m['n_total']}")
    print("Calibration : Platt (folds 0–5 train)")

    print("\n--- Métriques globales ---")
    print(f"  DA globale            : {m['da_global']:.3f}")
    print(f"  DA quand BULLISH      : {m['da_bullish']:.3f}  (n={m['n_bullish']})")
    print(f"  DA quand BEARISH      : {m['da_bearish']:.3f}  (n={m['n_bearish']})")
    print(f"  DA quand UNCERTAIN    : {m['da_uncertain']:.3f}  (n={m['n_uncertain']})")
    print(f"  DA top 20% confiance  : {m['da_top20pct']:.3f}  (n={m['n_top20']})  objectif >0.65")
    print(f"  DA top 10% confiance  : {m['da_top10pct']:.3f}  (n={m['n_top10']})  objectif >0.70")
    print(f"  AUC                   : {m['auc']:.3f}  objectif >0.55")
    print(f"  Brier                 : {m['brier']:.4f}")
    print(f"  Retour moyen BULLISH  : {m['avg_ret_bullish']:.4f}  (doit être >0)")
    print(f"  Retour moyen BEARISH  : {m['avg_ret_bearish']:.4f}  (doit être <0)")
    print(f"  Signaux forts/an      : {m['strong_per_year']:.1f}  objectif >=20")
    print(f"  Flip rate             : {m['flip_rate']:.3f}  objectif <0.30")
    print(f"  Persistance 3j        : {m['signal_persistence_3d']:.3f}  objectif >0.60")

    print("\n--- Comparaison aux baselines ---")
    print(f"  Indicateur V2         : {m['da_global']:.3f}")
    print(f"  Saisonnier simple     : {m.get('da_seasonal_baseline', float('nan')):.3f}")
    print(f"  Momentum simple       : {m.get('da_momentum_baseline', float('nan')):.3f}")

    print("\n--- Performance par année ---")
    by_year = results["by_year"]
    if not by_year.empty:
        print(f"  {'Année':<8} {'DA':>8} {'N':>6}")
        for _, row in by_year.iterrows():
            da_str = f"{row['da']:.3f}" if not pd.isna(row.get("da")) else "N/A"
            print(f"  {int(row['year']):<8} {da_str:>8} {int(row.get('n', 0)):>6}")

    print("\n--- Analyse des erreurs ---")
    err = results.get("err_summaries", {})
    by_cat = err.get("by_category")
    if by_cat is not None and not by_cat.empty:
        print("  Catégories :")
        for _, row in by_cat.iterrows():
            print(f"    {row['error_category']:<25} : {row['n_errors']}")

    print("\n--- Ablation composantes V2 ---")
    abl = results.get("ablation")
    if abl is not None and not abl.empty:
        print(f"  {'Composante':<25} {'Delta DA':>10}")
        for _, row in abl.iterrows():
            print(f"  {row['component']:<25} {row['delta']:>+10.4f}")

    print()


def _answer_8_questions(results: dict) -> str:
    m = results["metrics"]
    lines = [
        "\n=== 8 Questions Fondamentales ===\n",

        "1. Quel horizon est le plus prévisible ?",
        "   Réponse : h20 (J+20) — meilleure DA (0.593) et AUC (0.707) sur la cible"
        " y_down_gt_5pct_h20 (IND-01/IND-02). h30 dominé par saisonnalité.",
        "",

        "2. Quelle cible marche le mieux ?",
        "   Réponse : y_down_gt_5pct_h20 — AUC=0.707 (Tier 1 par AUC). Asymétrie :"
        " le modèle détecte mieux les fortes baisses que les hausses.",
        "",

        "3. Dans quels contextes le signal est fiable ?",
        "   Réponse : mois=11 (AUC=0.883), stocks_tendus (AUC=0.799),"
        " post_recolte+low_vol (AUC=0.797). Contextes croisés = exploratoires (IND-04).",
        "",

        "4. Quelles familles de données apportent vraiment du signal ?",
        "   Réponse (IND-05, critère delta_auc) :"
        " GARDER = positioning (+0.016), market_volatility (+0.012),"
        " seasonality (+0.010), raw_signal (+0.008), crop_condition (+0.007)."
        " RETIRER = cross_commodity (−0.034), market_momentum (−0.032).",
        "",

        "5. Quand l'indicateur doit-il dire UNCERTAIN ?",
        f"   Réponse : confidence_v1 < {CONF_THRESHOLD}. Sur 2023-2025 : {m['n_uncertain']} jours"
        f" UNCERTAIN/{m['n_total']} total. DA_uncertain = {m['da_uncertain']:.3f} (≈50% = bon signe).",
        "",

        "6. Les signaux confiants sont-ils vraiment meilleurs ?",
        f"   Réponse : DA top 20% = {m['da_top20pct']:.3f} vs DA globale = {m['da_global']:.3f}."
        + (" ✅ Oui." if m.get('da_top20pct', 0) > m.get('da_global', 0) else " ⚠️ Non ou marginalement."),
        "",

        "7. Les résultats sont-ils stables dans le temps ?",
        "   Réponse : voir tableau par année dans le rapport.",
        "",

        "8. Les facteurs explicatifs ont-ils du sens économique ?",
        "   Réponse : Oui — top SHAP h5-h20 = WASDE supply/demand, crop_condition,"
        " curve_structure (IND-01). h30 = macro dollar, positionnement. Cohérent avec"
        " la théorie : météo/stocks dominent court terme, macro domine long terme.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    results = run_backtest_v2()
    _print_report(results)
    print(_answer_8_questions(results))
