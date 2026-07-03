"""EXT025 — Evaluation des benchmarks: RMSE/MAE/R2/DA + Diebold-Mariano vs RW.

DM: perte quadratique, variance HAC (Bartlett, lag h-1), ajustement Harvey.
Headline = segment eval_pre2024 (holdout 2024 verrouille, rapporte a part).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
RESULTS = ROOT / "external_research" / "results" / "external_tests" / \
    "EXT025_random_walk_and_futures_price_benchmark"


def dm_test(e_model: np.ndarray, e_ref: np.ndarray, h: int) -> tuple[float, float]:
    """DM stat (modele vs reference, perte quadratique). <0 = modele meilleur."""
    d = e_model ** 2 - e_ref ** 2
    n = len(d)
    if n < 30:
        return np.nan, np.nan
    dbar = d.mean()
    lag = max(h - 1, 0)
    gamma0 = np.var(d, ddof=0)
    var = gamma0
    for k in range(1, lag + 1):
        w = 1.0 - k / (lag + 1.0)
        cov = np.mean((d[k:] - dbar) * (d[:-k] - dbar))
        var += 2.0 * w * cov
    if var <= 0:
        return np.nan, np.nan
    dm = dbar / np.sqrt(var / n)
    harvey = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    dm *= harvey
    from math import erf, sqrt
    p = 2.0 * (1.0 - 0.5 * (1.0 + erf(abs(dm) / sqrt(2.0))))
    return float(dm), float(p)


def metrics_block(g: pd.DataFrame) -> dict:
    err = g["pred"] - g["actual"]
    actual_dir = np.sign(g["actual"] - g["p_t"])
    pred_dir = np.sign(g["pred"] - g["p_t"])
    directional = pred_dir != 0
    da = float((pred_dir[directional] == actual_dir[directional]).mean()) if directional.any() else np.nan
    ss_res = float((err ** 2).sum())
    ss_tot = float(((g["actual"] - g["actual"].mean()) ** 2).sum())
    return {
        "n": len(g),
        "rmse": float(np.sqrt((err ** 2).mean())),
        "mae": float(err.abs().mean()),
        "r2": 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan,
        "direction_accuracy": da,
    }


def main() -> None:
    preds = pd.read_csv(RESULTS / "predictions_ext025.csv", parse_dates=["date", "target_date"])
    preds["year"] = preds["date"].dt.year
    preds["period"] = pd.cut(preds["year"], bins=[1999, 2009, 2015, 2019, 2026],
                             labels=["2000-2009", "2010-2015", "2016-2019", "2020+"])

    rows, dm_rows, comp_rows = [], [], []
    for (series, segment, h, model), g in preds.groupby(["series", "segment", "horizon", "model"]):
        m = metrics_block(g)
        m.update(series=series, segment=segment, horizon=h, model=model)
        rows.append(m)
    metrics = pd.DataFrame(rows)

    eval_seg = preds[preds["segment"] == "eval_pre2024"]
    for (series, h), g in eval_seg.groupby(["series", "horizon"]):
        piv = g.pivot_table(index="date", columns="model", values="pred")
        actual = g.pivot_table(index="date", columns="model", values="actual")["rw"]
        if "rw" not in piv.columns:
            continue
        e_ref = (piv["rw"] - actual).dropna()
        for model in piv.columns:
            if model == "rw":
                continue
            e_m = (piv[model] - actual).reindex(e_ref.index).dropna()
            common = e_m.index.intersection(e_ref.index)
            dm, p = dm_test(e_m.loc[common].values, e_ref.loc[common].values, h)
            dm_rows.append({"series": series, "horizon": h, "model": model,
                            "vs": "rw", "dm_stat": dm, "p_value": p,
                            "better_than_rw": bool(dm < 0) if not np.isnan(dm) else None})
        # comparaison par periode
        for period, gp in g.groupby("period", observed=True):
            for model, gm in gp.groupby("model"):
                m = metrics_block(gm)
                m.update(series=series, horizon=h, model=model, period=str(period))
                comp_rows.append(m)

    pd.DataFrame(rows).to_csv(RESULTS / "metrics_ext025.csv", index=False)
    pd.DataFrame(comp_rows).to_csv(RESULTS / "comparison_ext025.csv", index=False)
    pd.DataFrame(dm_rows).to_csv(RESULTS / "dm_tests_ext025.csv", index=False)

    # resume console
    head = metrics[(metrics["segment"] == "eval_pre2024")]
    piv = head.pivot_table(index=["series", "horizon"], columns="model", values="rmse")
    print("RMSE (eval_pre2024):")
    print(piv.round(2).to_string())
    dm = pd.DataFrame(dm_rows)
    if not dm.empty:
        beat = dm[(dm["better_than_rw"]) & (dm["p_value"] < 0.1)]
        print(f"\nBenchmarks battant la RW (p<0.10): {len(beat)}/{len(dm)}")
        if len(beat):
            print(beat.to_string(index=False))


if __name__ == "__main__":
    main()
