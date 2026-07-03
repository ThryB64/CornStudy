"""Backtest décisionnel simple du score de vente (étape 7).

Pas un bot de trading : on simule un **agriculteur** qui détient 1 unité de récolte au début
d'une **fenêtre de commercialisation** et doit tout vendre avant la fin. `SELL_PARTIAL` vend
une fraction (avec un **cooldown** minimal entre deux ventes, pour ne pas liquider toute la
récolte sur des signaux consécutifs) ; le solde est vendu au dernier jour. On compare le prix
moyen obtenu à des stratégies naïves (tout à la récolte, par tiers, DCA mensuel, attendre la
fin), et on teste plusieurs découpages de campagne (année civile, Sep-Aug, Oct-Sep). Jamais de
short, de levier ni de rachat. Plus haut = mieux pour le vendeur.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

STRAT_NAMES = ["score", "sell_all_start", "sell_thirds", "monthly_dca", "wait_year_end"]
BASELINES = ["sell_all_start", "sell_thirds", "monthly_dca", "wait_year_end"]


def _avg_price(sells: list[tuple[pd.Timestamp, float, float]]) -> float:
    tot = sum(f for _, f, _ in sells)
    if tot <= 0:
        return np.nan
    return float(sum(f * p for _, f, p in sells) / tot)


def _score_strategy(win: pd.DataFrame, sell_fraction: float, cooldown: int) -> list:
    """Vend `sell_fraction` à chaque SELL_PARTIAL, avec ≥ `cooldown` séances entre deux ventes."""
    sells, remaining, last_pos = [], 1.0, -(10 ** 9)
    for i, (dt, row) in enumerate(win.iterrows()):
        if remaining <= 1e-9:
            break
        if row["recommendation"] == "SELL_PARTIAL" and (i - last_pos) >= cooldown:
            f = min(sell_fraction, remaining)
            sells.append((dt, f, float(row["corn_close"])))
            remaining -= f
            last_pos = i
    if remaining > 1e-9:                      # solde vendu au dernier jour de la fenêtre
        sells.append((win.index[-1], remaining, float(win["corn_close"].iloc[-1])))
    return sells


def _baselines(win: pd.DataFrame) -> dict:
    px = win["corn_close"]
    idx = win.index
    out = {"sell_all_start": [(idx[0], 1.0, float(px.iloc[0]))],
           "wait_year_end": [(idx[-1], 1.0, float(px.iloc[-1]))]}
    thirds = []
    for off in (0, 60, 120):
        j = min(off, len(idx) - 1)
        thirds.append((idx[j], 1 / 3, float(px.iloc[j])))
    out["sell_thirds"] = thirds
    months = win.groupby([win.index.year, win.index.month])
    n = months.ngroups
    out["monthly_dca"] = [(g.index[0], 1.0 / n, float(g["corn_close"].iloc[0]))
                          for _key, g in months]
    return out


def _marketing_year(idx: pd.DatetimeIndex, window: str) -> np.ndarray:
    """Identifiant de campagne. calendar=année civile ; sep_aug/oct_sep=campagnes agricoles."""
    y, m = idx.year.to_numpy(), idx.month.to_numpy()
    if window == "calendar":
        return y
    if window == "sep_aug":
        return np.where(m >= 9, y, y - 1)
    if window == "oct_sep":
        return np.where(m >= 10, y, y - 1)
    raise ValueError(f"window inconnu: {window}")


def run_backtest(frame: pd.DataFrame, cfg: dict, start: str, window: str = "calendar",
                 cooldown: int | None = None, end: str | None = None):
    """Backtest par campagne sur [start, end]. Retourne (decisions_df, per_window_df, summary)."""
    sell_fraction = float(cfg["rules"]["sell_fraction"])
    if cooldown is None:
        cooldown = int(cfg.get("backtest", {}).get("sell_cooldown_sessions", 20))
    fr = frame[frame.index >= pd.Timestamp(start)].dropna(subset=["recommendation"]).copy()
    if end:
        fr = fr[fr.index <= pd.Timestamp(end)]
    fr["__my"] = _marketing_year(fr.index, window)
    rows, per_win = [], []
    for my, win in fr.groupby("__my"):
        if len(win) < 20:
            continue
        win = win.sort_index()
        label = f"{int(my)}" if window == "calendar" else f"{int(my)}-{int(my) + 1}"
        sells = {"score": _score_strategy(win, sell_fraction, cooldown), **_baselines(win)}
        prices = {k: _avg_price(v) for k, v in sells.items()}
        per_win.append({"window": window, "cooldown": cooldown, "campaign": label,
                        "n_days": len(win),
                        "n_sell_partial": int((win["recommendation"] == "SELL_PARTIAL").sum()),
                        "n_score_sells": len(sells["score"]),
                        "n_risk_high": int((win["recommendation"] == "RISK_HIGH").sum()),
                        **{f"avg_price_{k}": round(prices[k], 2) for k in STRAT_NAMES}})
        for k, v in sells.items():
            for dt, f, p in v:
                rows.append({"window": window, "cooldown": cooldown, "campaign": label,
                             "strategy": k, "date": dt.date(), "fraction": round(f, 4),
                             "price": round(p, 2)})
    dec = pd.DataFrame(rows)
    pw = pd.DataFrame(per_win)
    summary = {"window": window, "cooldown": cooldown,
               "period": f"{start}..{end or 'last'}", "campaigns": int(len(pw)),
               "sell_fraction": sell_fraction}
    if not pw.empty:
        for k in STRAT_NAMES:
            summary[f"mean_avg_price_{k}"] = round(float(pw[f"avg_price_{k}"].mean()), 2)
        for b in BASELINES:
            diff = pw["avg_price_score"] - pw[f"avg_price_{b}"]
            summary[f"score_vs_{b}_mean"] = round(float(diff.mean()), 2)
            summary[f"score_vs_{b}_won"] = int((diff > 0).sum())
            summary[f"score_vs_{b}_total"] = int(len(diff))
            summary[f"score_vs_{b}_max_regret"] = round(float((-diff).max()), 2)
    return dec, pw, summary


def run_all_windows(frame: pd.DataFrame, cfg: dict, start: str, end: str | None = None):
    """Compare windows x cooldowns. Retourne (comparison_df, per_window_df, calendar_summary)."""
    bt = cfg.get("backtest", {})
    windows = bt.get("windows", ["calendar", "sep_aug", "oct_sep"])
    grid = bt.get("cooldown_grid", [0, 20])
    comp_rows, all_pw, cal_summary = [], [], None
    for window in windows:
        for cd in grid:
            _dec, pw, summary = run_backtest(frame, cfg, start, window, cd, end)
            all_pw.append(pw)
            row = {"window": window, "cooldown": cd, "campaigns": summary["campaigns"]}
            for k in ("mean_avg_price_score", *[f"score_vs_{b}_mean" for b in BASELINES]):
                row[k] = summary.get(k)
            for b in BASELINES:
                row[f"score_vs_{b}_won"] = f"{summary.get(f'score_vs_{b}_won')}/" \
                                           f"{summary.get(f'score_vs_{b}_total')}"
            comp_rows.append(row)
            if window == "calendar" and cd == int(bt.get("sell_cooldown_sessions", 20)):
                cal_summary = summary
    comparison = pd.DataFrame(comp_rows)
    per_window = pd.concat([p for p in all_pw if not p.empty], ignore_index=True) \
        if any(not p.empty for p in all_pw) else pd.DataFrame()
    return comparison, per_window, cal_summary
