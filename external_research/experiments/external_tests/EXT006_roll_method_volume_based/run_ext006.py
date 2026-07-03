"""EXT006 — Audit du roll de la serie continue mais + prototype volume-causal.

Volets:
  V1 EMA historique : dates de roll du front (deja tracees), regle implicite
     (days_to_expiry au roll), sauts au roll, raw vs adjusted.
  V2 CBOT vendeur : pas d'identite de contrat -> retours dans les fenetres de
     roll presumees (10 derniers jours de bourse de fev/avr/juin/aout/nov,
     echeances H,K,N,U,Z) vs hors fenetres.
  V3 prototype causal : segment multi-contrats EMA 2025+ , roll decide quand
     volume(J-1) du contrat suivant > volume(J-1) du contrat courant.

Anti-fuite: decision de roll sur J-1 uniquement; aucun parametre optimise;
CSV de RollFutures jamais utilises.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
RESULTS = ROOT / "external_research" / "results" / "external_tests" / \
    "EXT006_roll_method_volume_based"

CBOT_DELIVERY_MONTHS = [3, 5, 7, 9, 12]  # H K N U Z
ROLL_WINDOW_DAYS = 10  # derniers jours de bourse du mois precedant l'echeance


def v1_ema_rolls() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw = pd.read_parquet(ROOT / "data" / "processed" / "euronext" /
                          "ema_front_continuous_raw.parquet")
    raw["date"] = pd.to_datetime(raw["date"])
    raw = raw.sort_values("date").reset_index(drop=True)
    raw["ret"] = np.log(raw["price"]).diff()

    adj_path = ROOT / "data" / "processed" / "euronext" / \
        "ema_front_continuous_adjusted.parquet"
    adj = pd.read_parquet(adj_path) if adj_path.exists() else None
    if adj is not None:
        adj["date"] = pd.to_datetime(adj["date"])
        price_col = "adjusted_price" if "adjusted_price" in adj.columns else "price"
        adj = adj.sort_values("date").reset_index(drop=True)
        adj["ret"] = np.log(adj[price_col]).diff()

    rolls = raw[raw["roll_event"] == True].copy()  # noqa: E712
    roll_rows = []
    for _, r in rolls.iterrows():
        i = raw.index[raw["date"] == r["date"]][0]
        prev = raw.iloc[i - 1] if i > 0 else None
        roll_rows.append({
            "date": r["date"],
            "from_contract": r.get("prev_contract_code"),
            "to_contract": r.get("contract_code"),
            "days_to_expiry_new": r.get("days_to_expiry"),
            "dte_old_at_roll": prev.get("days_to_expiry") if prev is not None else np.nan,
            "price_new": r["price"],
            "price_old_prev_day": prev["price"] if prev is not None else np.nan,
            "roll_day_logret_raw": r["ret"],
            "roll_adjustment": r.get("roll_adjustment", np.nan),
        })
    roll_dates = pd.DataFrame(roll_rows)

    raw["is_roll_day"] = raw["roll_event"].fillna(False).astype(bool)
    stats = []
    for label, mask in [("roll_days", raw["is_roll_day"]),
                        ("normal_days", ~raw["is_roll_day"])]:
        r = raw.loc[mask, "ret"].dropna()
        stats.append({"series": "ema_front_raw", "group": label, "n": len(r),
                      "mean_logret": r.mean(), "mean_abs_logret": r.abs().mean(),
                      "std_logret": r.std(), "p95_abs": r.abs().quantile(0.95)})
    if adj is not None:
        adj_roll = adj["date"].isin(roll_dates["date"])
        for label, mask in [("roll_days", adj_roll), ("normal_days", ~adj_roll)]:
            r = adj.loc[mask, "ret"].dropna()
            stats.append({"series": "ema_front_adjusted", "group": label, "n": len(r),
                          "mean_logret": r.mean(), "mean_abs_logret": r.abs().mean(),
                          "std_logret": r.std(), "p95_abs": r.abs().quantile(0.95)})
    return roll_dates, pd.DataFrame(stats), raw


def v2_cbot_windows() -> pd.DataFrame:
    db = pd.read_parquet(ROOT / "data" / "interim" / "database.parquet")
    db["Date"] = pd.to_datetime(db["Date"])
    s = db.set_index("Date")["corn_close"].dropna()
    ret = np.log(s).diff().dropna()
    gap = None
    if "corn_gap_overnight_pct" in db.columns:
        gap = db.set_index("Date")["corn_gap_overnight_pct"].reindex(ret.index)

    # fenetre = ROLL_WINDOW_DAYS derniers jours de bourse du mois precedant
    # un mois d'echeance (fev, avr, juin, aout, nov)
    pre_delivery = [m - 1 if m > 1 else 12 for m in CBOT_DELIVERY_MONTHS]
    idx = ret.index
    in_window = pd.Series(False, index=idx)
    for (_y, m), grp in pd.Series(idx, index=idx).groupby([idx.year, idx.month]):
        if m in pre_delivery:
            last_days = grp.index[-ROLL_WINDOW_DAYS:]
            in_window.loc[last_days] = True

    rows = []
    for label, mask in [("presumed_roll_window", in_window), ("outside", ~in_window)]:
        r = ret[mask]
        row = {"series": "cbot_corn_vendor", "group": label, "n": len(r),
               "mean_logret": r.mean(), "mean_abs_logret": r.abs().mean(),
               "std_logret": r.std(), "p95_abs": r.abs().quantile(0.95)}
        if gap is not None:
            g = gap[mask].dropna()
            row["mean_abs_gap_pct"] = g.abs().mean()
            row["p95_abs_gap_pct"] = g.abs().quantile(0.95)
        rows.append(row)
    return pd.DataFrame(rows)


def v3_volume_prototype() -> tuple[pd.DataFrame, pd.DataFrame]:
    d = pd.read_parquet(ROOT / "data" / "processed" / "euronext" /
                        "ema_contract_daily.parquet")
    d["date"] = pd.to_datetime(d["date"])
    d = d[d["date"] >= "2025-01-01"].copy()
    d = d.dropna(subset=["close_or_last"])
    d = d.sort_values(["date", "expiry_date"])

    multi = d.groupby("date").size()
    dates = multi[multi >= 2].index.sort_values()
    if len(dates) < 20:
        return pd.DataFrame(), pd.DataFrame()

    vol_hist: dict[tuple, float] = {}
    current = None
    rows = []
    for dt in dates:
        day = d[d["date"] == dt].sort_values("expiry_date")
        codes = day["contract_code"].tolist()
        if current not in codes:
            current = codes[0]  # premier choix: contrat le plus proche
        cur_row = day[day["contract_code"] == current].iloc[0]
        later = day[day["expiry_date"] > cur_row["expiry_date"]]
        switched = False
        if not later.empty:
            nxt = later.iloc[0]
            v_cur = vol_hist.get((current,))
            v_nxt = vol_hist.get((nxt["contract_code"],))
            # decision CAUSALE: volumes memorises de J-1 uniquement
            if v_cur is not None and v_nxt is not None and v_nxt > v_cur or cur_row["days_to_expiry"] <= 3:
                current = nxt["contract_code"]
                cur_row = nxt
                switched = True
        for _, c in day.iterrows():
            vol_hist[(c["contract_code"],)] = c["volume"]
        rows.append({"date": dt, "contract_volume_roll": current,
                     "price_volume_roll": cur_row["close_or_last"],
                     "rolled_today": switched,
                     "dte": cur_row["days_to_expiry"]})
    proto = pd.DataFrame(rows)

    # comparaison au front expiry-based du projet sur le meme segment
    raw = pd.read_parquet(ROOT / "data" / "processed" / "euronext" /
                          "ema_front_continuous_raw.parquet")
    raw["date"] = pd.to_datetime(raw["date"])
    front = raw[raw["date"].isin(proto["date"])][["date", "contract_code", "price"]]
    front = front.rename(columns={"contract_code": "contract_front",
                                  "price": "price_front"})
    cmp_df = proto.merge(front, on="date", how="inner")
    cmp_df["same_contract"] = cmp_df["contract_volume_roll"] == cmp_df["contract_front"]
    cmp_df["price_diff"] = cmp_df["price_volume_roll"] - cmp_df["price_front"]
    return proto, cmp_df


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)

    roll_dates, ema_stats, raw = v1_ema_rolls()
    roll_dates.to_csv(RESULTS / "roll_dates.csv", index=False)
    raw[["date", "contract_code", "price", "days_to_expiry", "is_roll_day"]].to_csv(
        RESULTS / "continuous_current.csv", index=False)

    cbot_stats = v2_cbot_windows()
    artifacts = pd.concat([ema_stats, cbot_stats], ignore_index=True)
    artifacts.to_csv(RESULTS / "roll_artifacts_metrics.csv", index=False)

    proto, cmp_df = v3_volume_prototype()
    if not proto.empty:
        proto.to_csv(RESULTS / "continuous_volume_roll.csv", index=False)
        agree = cmp_df["same_contract"].mean()
        diff_days = cmp_df[~cmp_df["same_contract"]]
        comp = pd.DataFrame([{
            "segment": "2025+_multi_contrats",
            "n_days": len(cmp_df),
            "pct_same_contract": agree,
            "n_disagree": len(diff_days),
            "mean_abs_price_diff_when_disagree":
                diff_days["price_diff"].abs().mean() if len(diff_days) else 0.0,
            "n_rolls_volume_method": int(proto["rolled_today"].sum()),
        }])
    else:
        comp = pd.DataFrame([{"segment": "2025+_multi_contrats",
                              "n_days": 0, "note": "segment multi-contrats insuffisant"}])
    comp.to_csv(RESULTS / "roll_comparison_metrics.csv", index=False)

    print("=== EMA rolls historiques ===")
    print(f"{len(roll_dates)} rolls; dte_old au roll: "
          f"median={roll_dates['dte_old_at_roll'].median()}, "
          f"min={roll_dates['dte_old_at_roll'].min()}, "
          f"max={roll_dates['dte_old_at_roll'].max()}")
    print(artifacts.to_string(index=False))
    if not proto.empty:
        print("\n=== Prototype volume-causal 2025+ ===")
        print(comp.to_string(index=False))


if __name__ == "__main__":
    main()
