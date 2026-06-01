"""NB-EMA-02 — Analyse formelle des contrats EMA et impact des rolls."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, EMA_CONTRACT_DAILY, EMA_FRONT_ADJUSTED, EMA_FRONT_RAW

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_contracts_rolls.json"
_MONTH_CODES = ["H", "M", "Q", "X"]


def _load_series(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def _crop_year(date: pd.Timestamp) -> int:
    return date.year if date.month >= 10 else date.year - 1


def _contract_lifecycle(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["crop_year"] = df["date"].apply(_crop_year)
    lifecycle: dict = {}
    for cy in sorted(df["crop_year"].unique()):
        sub = df[df["crop_year"] == cy]
        contracts: dict = {}
        for mc in _MONTH_CODES:
            rows = sub[sub["month_code"] == mc].sort_values("date")
            if len(rows):
                contracts[mc] = {
                    "first_date": str(rows["date"].min().date()),
                    "last_date": str(rows["date"].max().date()),
                    "n_days": int(len(rows)),
                }
        lifecycle[int(cy)] = contracts
    return lifecycle


def _roll_gap_stats(adj: pd.DataFrame) -> dict:
    rolls = adj[adj["roll_event"].notna() & (adj["roll_adjustment"].notna()) & (adj["roll_adjustment"] != 0)].copy()
    if len(rolls) == 0:
        return {"n_rolls": 0, "error": "no_rolls_found"}
    gaps = rolls["roll_adjustment"].abs()
    top10 = rolls.nlargest(10, "roll_adjustment")[["date", "roll_adjustment", "contract_code", "prev_contract_code"]].copy()
    top10["date"] = top10["date"].astype(str)
    return {
        "n_rolls": int(len(rolls)),
        "mean_abs_gap": float(gaps.mean()),
        "median_abs_gap": float(gaps.median()),
        "q75_gap": float(gaps.quantile(0.75)),
        "max_abs_gap": float(gaps.max()),
        "pct_gaps_gt_5": float((gaps > 5).mean()),
        "pct_gaps_gt_15": float((gaps > 15).mean()),
        "top_10_largest": top10.to_dict(orient="records"),
    }


def _pct_windows_crossing_roll(adj: pd.DataFrame, horizons: list[int]) -> dict[str, float]:
    roll_dates = set(adj.loc[adj["roll_event"].notna() & (adj["roll_adjustment"] != 0), "date"].dt.date)
    dates = adj["date"].sort_values().reset_index(drop=True)
    result: dict = {}
    for h in horizons:
        has_roll = []
        for i, d in enumerate(dates):
            end_i = min(i + h, len(dates) - 1)
            end_d = dates.iloc[end_i].date()
            start_d = d.date()
            window_rolls = [rd for rd in roll_dates if start_d < rd <= end_d]
            has_roll.append(len(window_rolls) > 0)
        result[f"H{h}"] = float(np.mean(has_roll)) if has_roll else float("nan")
    return result


def _raw_vs_adjusted_corr(raw: pd.DataFrame, adj: pd.DataFrame) -> dict:
    merged = pd.merge(
        raw[["date", "price"]].rename(columns={"price": "price_raw"}),
        adj[["date", "price"]].rename(columns={"price": "price_adj"}),
        on="date", how="inner",
    )
    if len(merged) < 10:
        return {"error": "insufficient_overlap"}
    ret_raw = merged["price_raw"].pct_change().dropna()
    ret_adj = merged["price_adj"].pct_change().dropna()
    aligned = pd.concat([ret_raw, ret_adj], axis=1).dropna()
    corr = float(aligned.iloc[:, 0].corr(aligned.iloc[:, 1]))
    sign_raw = (ret_raw > 0).astype(int)
    sign_adj = (ret_adj > 0).astype(int)
    sign_aligned = pd.concat([sign_raw, sign_adj], axis=1).dropna()
    da_diff = float((sign_aligned.iloc[:, 0] == sign_aligned.iloc[:, 1]).mean())
    return {"corr_returns": corr, "direction_agreement_raw_vs_adj": da_diff}


def _active_contracts_dist(df: pd.DataFrame) -> dict:
    active = df.groupby("date")["month_code"].count()
    dist: dict = {}
    for k in range(6):
        dist[str(k)] = int((active == k).sum())
    dist["2+"] = int((active >= 2).sum())
    dist["pct_2plus"] = float((active >= 2).sum() / max(len(active), 1))
    return dist


def build_contracts_rolls() -> dict:
    df = pd.read_parquet(EMA_CONTRACT_DAILY)
    df["date"] = pd.to_datetime(df["date"])

    adj = _load_series(EMA_FRONT_ADJUSTED)
    raw = _load_series(EMA_FRONT_RAW)

    lifecycle = _contract_lifecycle(df)
    roll_stats = _roll_gap_stats(adj)
    pct_crossing = _pct_windows_crossing_roll(adj, horizons=[20, 40, 60])
    corr_stats = _raw_vs_adjusted_corr(raw, adj)
    active_dist = _active_contracts_dist(df)

    return {
        "contract_lifecycle_by_crop_year": lifecycle,
        "roll_stats": roll_stats,
        "pct_windows_crossing_roll": pct_crossing,
        "raw_vs_adjusted": corr_stats,
        "active_contracts_per_day": active_dist,
        "key_findings": {
            "n_rolls_front": roll_stats.get("n_rolls"),
            "avg_roll_gap_eur_t": roll_stats.get("mean_abs_gap"),
            "max_roll_gap_eur_t": roll_stats.get("max_abs_gap"),
            "pct_H20_windows_with_roll": pct_crossing.get("H20"),
            "pct_H40_windows_with_roll": pct_crossing.get("H40"),
            "pct_H60_windows_with_roll": pct_crossing.get("H60"),
            "pct_dates_2plus_contracts": active_dist.get("pct_2plus"),
        },
    }


def save_contracts_rolls(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_contracts_rolls()

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
    return path


if __name__ == "__main__":
    out = save_contracts_rolls()
    print(f"Contracts & rolls saved → {out}")
