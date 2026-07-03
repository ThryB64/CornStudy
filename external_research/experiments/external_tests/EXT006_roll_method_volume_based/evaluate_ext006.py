"""EXT006 — Evaluation des artefacts de roll: sauts en EUR/t, echelle vs vol
quotidienne, test de Welch roll vs normal, flips du momentum 20j autour des
rolls (raw vs adjusted)."""
from __future__ import annotations

from math import erf, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
RESULTS = ROOT / "external_research" / "results" / "external_tests" / \
    "EXT006_roll_method_volume_based"


def welch_t(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    ma, mb = a.mean(), b.mean()
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    t = (ma - mb) / np.sqrt(va + vb)
    p = 2.0 * (1.0 - 0.5 * (1.0 + erf(abs(t) / sqrt(2.0))))  # approx normale
    return float(t), float(p)


def main() -> None:
    rolls = pd.read_csv(RESULTS / "roll_dates.csv", parse_dates=["date"])
    cont = pd.read_csv(RESULTS / "continuous_current.csv", parse_dates=["date"])
    cont = cont.sort_values("date").reset_index(drop=True)
    cont["ret"] = np.log(cont["price"]).diff()
    cont["dprice"] = cont["price"].diff()

    adj = pd.read_parquet(ROOT / "data" / "processed" / "euronext" /
                          "ema_front_continuous_adjusted.parquet")
    adj["date"] = pd.to_datetime(adj["date"])
    adj = adj.sort_values("date").reset_index(drop=True)
    adj["dprice_adj"] = adj["adjusted_price"].diff()

    # 1) sauts au roll en EUR/t (serie raw, variations de prix)
    is_roll = cont["is_roll_day"].astype(bool)
    jump = cont.loc[is_roll, "dprice"].abs()
    normal = cont.loc[~is_roll, "dprice"].abs().dropna()
    jump_adj = adj.loc[adj["date"].isin(rolls["date"]), "dprice_adj"].abs().dropna()
    normal_adj = adj.loc[~adj["date"].isin(rolls["date"]), "dprice_adj"].abs().dropna()

    t_raw, p_raw = welch_t(jump.values, normal.values)
    t_adj, p_adj = welch_t(jump_adj.values, normal_adj.values)

    # 2) flips momentum 20j autour des rolls: signe du momentum la veille vs
    #    le lendemain du roll, raw vs adjusted
    cont["mom20"] = cont["price"] - cont["price"].rolling(20).mean()
    adj["mom20_adj"] = adj["adjusted_price"] - adj["adjusted_price"].rolling(20).mean()
    flips_raw = flips_adj = checked = 0
    for d in rolls["date"]:
        i = cont.index[cont["date"] == d]
        j = adj.index[adj["date"] == d]
        if len(i) == 0 or len(j) == 0:
            continue
        i, j = i[0], j[0]
        if i < 1 or i + 1 >= len(cont) or j < 1 or j + 1 >= len(adj):
            continue
        checked += 1
        if np.sign(cont["mom20"].iloc[i - 1]) != np.sign(cont["mom20"].iloc[i + 1]):
            flips_raw += 1
        if np.sign(adj["mom20_adj"].iloc[j - 1]) != np.sign(adj["mom20_adj"].iloc[j + 1]):
            flips_adj += 1

    out = pd.DataFrame([
        {"metric": "n_rolls", "value": len(rolls)},
        {"metric": "rolls_per_year", "value": round(len(rolls) / 16.4, 2)},
        {"metric": "dte_old_at_roll_median", "value": rolls["dte_old_at_roll"].median()},
        {"metric": "raw_mean_abs_jump_eur_t_roll", "value": round(jump.mean(), 2)},
        {"metric": "raw_mean_abs_move_eur_t_normal", "value": round(normal.mean(), 2)},
        {"metric": "raw_jump_ratio", "value": round(jump.mean() / normal.mean(), 1)},
        {"metric": "raw_welch_t", "value": round(t_raw, 2)},
        {"metric": "raw_welch_p", "value": p_raw},
        {"metric": "adj_mean_abs_jump_eur_t_roll", "value": round(jump_adj.mean(), 2)},
        {"metric": "adj_mean_abs_move_eur_t_normal", "value": round(normal_adj.mean(), 2)},
        {"metric": "adj_jump_ratio", "value": round(jump_adj.mean() / normal_adj.mean(), 1)},
        {"metric": "adj_welch_t", "value": round(t_adj, 2)},
        {"metric": "adj_welch_p", "value": p_adj},
        {"metric": "mom20_flips_around_roll_raw", "value": f"{flips_raw}/{checked}"},
        {"metric": "mom20_flips_around_roll_adjusted", "value": f"{flips_adj}/{checked}"},
        {"metric": "raw_max_abs_jump_eur_t", "value": round(jump.max(), 2)},
        {"metric": "raw_p90_abs_jump_eur_t", "value": round(jump.quantile(0.9), 2)},
    ])
    out.to_csv(RESULTS / "roll_artifacts_metrics_detailed.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
