"""EXT025 — Benchmarks naifs (RW, RW+drift, naive return, MA20).

Genere les predictions de niveau P_{t+h} pour chaque serie cible et chaque
horizon, avec information passee uniquement. Sorties dans
external_research/results/external_tests/EXT025_.../predictions_ext025.csv

Anti-fuite: drift et MA estimes en expandant/roulant sur le passe strict;
aucune normalisation globale; pas de split random.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
RESULTS = ROOT / "external_research" / "results" / "external_tests" / \
    "EXT025_random_walk_and_futures_price_benchmark"

HORIZONS = [5, 10, 20, 30, 40, 90]
MIN_HISTORY = 252  # 1 an avant la premiere prediction
HOLDOUT_START = pd.Timestamp("2024-01-01")  # holdout verrouille: segment separe


def load_series() -> dict[str, pd.Series]:
    out: dict[str, pd.Series] = {}

    db = pd.read_parquet(ROOT / "data" / "interim" / "database.parquet")
    db["Date"] = pd.to_datetime(db["Date"])
    cbot = db.set_index("Date")["corn_close"].dropna()
    out["cbot_corn_usd"] = cbot

    ema = pd.read_parquet(
        ROOT / "data" / "processed" / "euronext" / "ema_front_continuous_raw.parquet")
    ema["date"] = pd.to_datetime(ema["date"])
    out["ema_front_eur"] = ema.set_index("date")["price"].dropna()

    # Basis EMA - CBOT en EUR/t si un taux eurusd est disponible.
    eurusd = None
    macro_path = ROOT / "data" / "interim" / "macro_fred.parquet"
    if macro_path.exists():
        macro = pd.read_parquet(macro_path)
        date_col = "Date" if "Date" in macro.columns else None
        cand = [c for c in macro.columns if "eurusd" in c.lower() or "dexuseu" in c.lower()]
        if date_col and cand:
            macro[date_col] = pd.to_datetime(macro[date_col])
            eurusd = macro.set_index(date_col)[cand[0]].dropna()
    if eurusd is not None:
        cbot_eur_t = (cbot / 100.0) * 39.3683 / eurusd  # cents/bu -> EUR/t
        basis = (out["ema_front_eur"] - cbot_eur_t).dropna()
        if len(basis) > 500:
            out["basis_ema_cbot_eur"] = basis
    return out


def build_predictions(price: pd.Series, horizons: list[int]) -> pd.DataFrame:
    """Predictions de P_{t+h} faites a la date t (info <= t)."""
    logp = np.log(price)
    ret1 = logp.diff()
    # drift expandant: moyenne des log-retours jusqu'a t inclus
    drift = ret1.expanding(min_periods=MIN_HISTORY).mean()
    ma20 = price.rolling(20).mean()

    rows = []
    idx = price.index
    n = len(idx)
    pos = np.arange(n)
    for h in horizons:
        tgt_pos = pos + h
        ok = tgt_pos < n
        t_idx = idx[ok]
        f_idx = idx[tgt_pos[ok]]
        p_t = price.values[ok]
        actual = price.values[tgt_pos[ok]]
        preds = {
            "rw": p_t,
            "rw_drift": p_t * np.exp(drift.values[ok] * h),
            "naive_last_return": p_t * np.exp(ret1.values[ok] * h),
            "ma20": ma20.values[ok],
        }
        for model, yhat in preds.items():
            rows.append(pd.DataFrame({
                "date": t_idx, "target_date": f_idx, "horizon": h,
                "model": model, "pred": yhat, "actual": actual, "p_t": p_t,
            }))
    df = pd.concat(rows, ignore_index=True)
    # historique minimal + drift defini
    first_ok = price.index[MIN_HISTORY] if len(price) > MIN_HISTORY else price.index[-1]
    df = df[df["date"] >= first_ok]
    df["segment"] = np.where(df["target_date"] >= HOLDOUT_START, "holdout_2024plus", "eval_pre2024")
    return df.dropna(subset=["pred"])


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    series = load_series()
    all_parts = []
    for name, s in series.items():
        s = s[~s.index.duplicated(keep="last")].sort_index()
        part = build_predictions(s, HORIZONS)
        part.insert(0, "series", name)
        all_parts.append(part)
        print(f"{name}: {len(s)} obs -> {len(part)} predictions")
    preds = pd.concat(all_parts, ignore_index=True)
    out = RESULTS / "predictions_ext025.csv"
    preds.to_csv(out, index=False)
    print(f"ecrit: {out} ({len(preds)} lignes)")
    if "basis_ema_cbot_eur" not in series:
        (RESULTS / "NOTE_basis_skipped.md").write_text(
            "# Note\n\nSerie basis non generee: aucun taux eurusd quotidien "
            "trouve dans data/interim (seul usd_index disponible). Le tableau "
            "de reference du basis sera produit quand une serie eurusd interne "
            "sera identifiee (DATA_BLOCKED partiel, sans impact sur CBOT/EMA).\n")


if __name__ == "__main__":
    main()
