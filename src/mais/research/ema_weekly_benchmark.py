"""NB-EMA-13/FIX-EMA-04 — Benchmarks hebdomadaires EMA généralisés."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, PROJECT_ROOT
from mais.research.ema_utils import bootstrap_ci

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_weekly_benchmark.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_WEEKLY_BENCHMARK.md"
_HORIZONS_WEEKS = (4, 8, 12)


def _to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """Resample EMA front price to weekly (Friday close)."""
    df = df.set_index("Date")
    weekly = df["ema_front_price"].resample("W-FRI").last().dropna()
    weekly_cbot = df["cbot_eur_t"].resample("W-FRI").last()
    weekly_basis = df["ema_cbot_basis"].resample("W-FRI").last()
    wdf = pd.DataFrame({"ema_price": weekly, "cbot_price": weekly_cbot, "basis": weekly_basis})
    wdf = wdf.dropna(subset=["ema_price", "cbot_price", "basis"])
    wdf["basis_z_52w"] = (
        (wdf["basis"] - wdf["basis"].rolling(52, min_periods=26).mean())
        / wdf["basis"].rolling(52, min_periods=26).std()
    ).shift(1)
    wdf["ema_ret_1w"] = wdf["ema_price"].pct_change()
    wdf["ema_vol_12w"] = wdf["ema_ret_1w"].rolling(12, min_periods=8).std() * np.sqrt(52)
    vol_q75 = wdf["ema_vol_12w"].expanding(min_periods=52).quantile(0.75).shift(1)
    wdf["vol_high_signal"] = wdf["ema_vol_12w"] > vol_q75
    return wdf.reset_index()


def _weekly_da_naive(wdf: pd.DataFrame, horizon_weeks: int = 4) -> dict:
    """DA de la tendance naïve : sign(ret_semaine_précédente) == sign(ret_futur_H semaines)."""
    price = wdf["ema_price"]
    ret_past = price.pct_change(1)
    ret_fut = price.pct_change(horizon_weeks).shift(-horizon_weeks)
    aligned = pd.concat([ret_past, ret_fut], axis=1).dropna()
    aligned.columns = ["past", "future"]
    da = float((np.sign(aligned["past"]) == np.sign(aligned["future"])).mean())
    ci = bootstrap_ci(
        (np.sign(aligned["past"]) == np.sign(aligned["future"])).values.astype(float),
        np.mean, n_draws=500,
    )
    return {"horizon_weeks": horizon_weeks, "da_naive_trend": da, "ci_lo": ci["ci_lo"], "ci_hi": ci["ci_hi"], "n": int(len(aligned))}


def _weekly_return_stats(wdf: pd.DataFrame) -> dict:
    price = wdf["ema_price"]
    ret_1w = price.pct_change(1).dropna()
    ret_4w = price.pct_change(4).dropna()
    return {
        "n_weeks": int(len(wdf)),
        "mean_ret_1w": float(ret_1w.mean()),
        "std_ret_1w": float(ret_1w.std()),
        "mean_ret_4w": float(ret_4w.mean()),
        "std_ret_4w": float(ret_4w.std()),
        "pct_up_weeks": float((ret_1w > 0).mean()),
        "sharpe_weekly": float(ret_1w.mean() / ret_1w.std()) if ret_1w.std() > 0 else float("nan"),
    }


def _direction_eval(
    *,
    label: str,
    horizon_weeks: int,
    y_true: pd.Series,
    y_pred: pd.Series,
    min_n: int = 40,
) -> dict:
    aligned = pd.concat([y_true.rename("y_true"), y_pred.rename("y_pred")], axis=1).dropna()
    if len(aligned) < min_n or aligned["y_true"].nunique() < 2:
        return {
            "label": label,
            "horizon_weeks": int(horizon_weeks),
            "status": "SKIPPED",
            "reason": "insufficient_data_or_single_class",
            "n": int(len(aligned)),
        }
    y = aligned["y_true"].astype(float)
    pred = aligned["y_pred"].astype(float)
    correct = y.eq(pred).astype(float)
    ci = bootstrap_ci(correct.to_numpy(), np.mean, n_draws=500)
    base_rate = float(y.mean())
    majority = float(max(base_rate, 1.0 - base_rate))
    da = float(correct.mean())
    return {
        "label": label,
        "horizon_weeks": int(horizon_weeks),
        "status": "OK",
        "n": int(len(aligned)),
        "base_rate": base_rate,
        "majority_baseline_da": majority,
        "da": da,
        "lift_vs_majority": float(da - majority),
        "ci95_lo": ci["ci_lo"],
        "ci95_hi": ci["ci_hi"],
        "verdict": "WEEKLY_GO" if da >= 0.53 and ci["ci_lo"] >= 0.50 else "WEEKLY_NO_GO",
    }


def _basis_reversion_eval(wdf: pd.DataFrame, horizon_weeks: int) -> dict:
    basis = wdf["basis"]
    z = wdf["basis_z_52w"]
    future_basis = basis.shift(-horizon_weeks)
    event = z.abs() >= 1.5
    reverts = ((z >= 1.5) & (future_basis < basis)) | ((z <= -1.5) & (future_basis > basis))
    aligned = pd.concat([reverts.rename("reverts"), event.rename("event"), future_basis.rename("future")], axis=1)
    aligned = aligned[aligned["event"] & aligned["future"].notna()]
    if len(aligned) < 20:
        return {
            "label": "basis_reversion",
            "horizon_weeks": int(horizon_weeks),
            "status": "SKIPPED",
            "reason": "insufficient_extreme_basis_events",
            "n": int(len(aligned)),
        }
    correct = aligned["reverts"].astype(float)
    ci = bootstrap_ci(correct.to_numpy(), np.mean, n_draws=500)
    hit_rate = float(correct.mean())
    return {
        "label": "basis_reversion",
        "horizon_weeks": int(horizon_weeks),
        "status": "OK",
        "n": int(len(aligned)),
        "hit_rate": hit_rate,
        "ci95_lo": ci["ci_lo"],
        "ci95_hi": ci["ci_hi"],
        "verdict": "WEEKLY_GO" if hit_rate >= 0.53 and ci["ci_lo"] >= 0.50 else "WEEKLY_NO_GO",
    }


def _generalised_weekly_results(wdf: pd.DataFrame) -> list[dict]:
    rows = []
    for horizon in _HORIZONS_WEEKS:
        ema_future_ret = wdf["ema_price"].pct_change(horizon).shift(-horizon)
        cbot_future_ret = wdf["cbot_price"].pct_change(horizon).shift(-horizon)
        relative_future_ret = ema_future_ret - cbot_future_ret
        ema_momentum_pred = (wdf["ema_price"].pct_change() > 0).astype(float)
        relative_basis_pred = (wdf["basis_z_52w"] < 0).astype(float)
        future_vol = wdf["ema_ret_1w"].rolling(horizon, min_periods=max(2, horizon // 2)).std().shift(-horizon) * np.sqrt(52)
        vol_threshold = wdf["ema_vol_12w"].expanding(min_periods=52).quantile(0.75).shift(1)
        rows.append(
            _direction_eval(
                label="ema_direct_momentum",
                horizon_weeks=horizon,
                y_true=(ema_future_ret > 0).where(ema_future_ret.notna()),
                y_pred=ema_momentum_pred,
            )
        )
        rows.append(
            _direction_eval(
                label="relative_ema_outperformance_basis_z",
                horizon_weeks=horizon,
                y_true=(relative_future_ret > 0).where(relative_future_ret.notna()),
                y_pred=relative_basis_pred.where(wdf["basis_z_52w"].notna()),
            )
        )
        rows.append(_basis_reversion_eval(wdf, horizon))
        rows.append(
            _direction_eval(
                label="ema_vol_high_persistence",
                horizon_weeks=horizon,
                y_true=(future_vol > vol_threshold).where(future_vol.notna() & vol_threshold.notna()),
                y_pred=wdf["vol_high_signal"].astype(float).where(wdf["vol_high_signal"].notna()),
            )
        )
    return rows


def build_weekly_benchmark() -> dict:
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    df = feats[feats["ema_front_price"].notna() & feats["cbot_eur_t"].notna()].copy()
    df = df[["Date", "ema_front_price", "cbot_eur_t", "ema_cbot_basis"]].sort_values("Date").reset_index(drop=True)

    wdf = _to_weekly(df)
    ret_stats = _weekly_return_stats(wdf)
    generalised = _generalised_weekly_results(wdf)
    da_h4w = _weekly_da_naive(wdf, horizon_weeks=4)
    da_h8w = _weekly_da_naive(wdf, horizon_weeks=8)
    ok_rows = [row for row in generalised if row.get("status") == "OK"]
    best = max(ok_rows, key=lambda row: row.get("da", row.get("hit_rate", 0.0)), default={})

    return {
        "n_weeks": int(len(wdf)),
        "period_start": str(wdf["Date"].min().date()),
        "period_end": str(wdf["Date"].max().date()),
        "weekly_return_stats": ret_stats,
        "da_naive_trend_H4w": da_h4w,
        "da_naive_trend_H8w": da_h8w,
        "generalised_weekly_results": generalised,
        "basis_signal_H4w": next(
            (row for row in generalised if row.get("label") == "basis_reversion" and row.get("horizon_weeks") == 4),
            {},
        ),
        "key_findings": {
            "da_naive_H4w": da_h4w.get("da_naive_trend"),
            "da_naive_H8w": da_h8w.get("da_naive_trend"),
            "basis_signal_da": next(
                (
                    row.get("hit_rate")
                    for row in generalised
                    if row.get("label") == "basis_reversion" and row.get("horizon_weeks") == 4
                ),
                None,
            ),
            "best_weekly_label": best.get("label"),
            "best_weekly_horizon": best.get("horizon_weeks"),
            "best_weekly_score": best.get("da", best.get("hit_rate")),
            "ema_direct_weekly_verdicts": {
                str(row["horizon_weeks"]): row.get("verdict")
                for row in generalised
                if row.get("label") == "ema_direct_momentum"
            },
            "pct_up_weeks": ret_stats["pct_up_weeks"],
            "note": "Benchmark hebdomadaire descriptif/rule-based, sans modèle complexe. Seuil WEEKLY_GO : score >= 53% et CI basse >= 50%.",
        },
    }


def save_weekly_benchmark(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_weekly_benchmark()

    def _convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return str(obj.date())
        raise TypeError(f"Not serialisable: {type(obj)}")

    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=_convert)
    _write_markdown(data, _DOC_OUTPUT)
    return path


def _write_markdown(data: dict, path: Path) -> None:
    k = data["key_findings"]
    lines = [
        "# EMA WEEKLY BENCHMARK",
        "",
        "> Benchmark vendredi→vendredi H4/H8/H12 semaines après correction des targets.",
        "",
        "## Verdict",
        "",
        f"- Meilleur signal hebdomadaire : {k.get('best_weekly_label')} H{k.get('best_weekly_horizon')}w",
        f"- Score meilleur signal : {k.get('best_weekly_score'):.1%}" if k.get("best_weekly_score") is not None else "- Score meilleur signal : N/A",
        f"- EMA direct weekly : {k.get('ema_direct_weekly_verdicts')}",
        "",
        "Weekly réduit le bruit quotidien, mais ne transforme pas automatiquement EMA direct en signal validé.",
        "",
        "## Résultats généralisés",
        "",
        "| Signal | Horizon | n | Score | IC95 | Verdict |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in data["generalised_weekly_results"]:
        score = row.get("da", row.get("hit_rate"))
        score_text = "N/A" if score is None else f"{score:.1%}"
        ci = "N/A"
        if row.get("ci95_lo") is not None and row.get("ci95_hi") is not None:
            ci = f"[{row['ci95_lo']:.1%}; {row['ci95_hi']:.1%}]"
        lines.append(
            f"| {row.get('label')} | {row.get('horizon_weeks')} | {row.get('n', 0)} | "
            f"{score_text} | {ci} | {row.get('verdict', row.get('status'))} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    out = save_weekly_benchmark()
    print(f"Weekly benchmark saved → {out}")
