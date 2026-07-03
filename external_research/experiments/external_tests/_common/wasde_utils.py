"""Chargement WASDE vintage anti-fuite (EXT007/EXT008).

Source unique : EXT026 `wasde_vintage_dataset.csv` (valeurs telles que publiees,
`available_from` = date de publication + 1 jour ouvre). Aucune valeur revisee,
aucune valeur avant sa disponibilite. Les features sont posees a `available_from`
puis forward-fill sur un calendrier quotidien complet (le harnais reindexe
ensuite sur le calendrier marche).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
VINTAGE = (ROOT / "external_research" / "results" / "external_tests" /
           "EXT026_wasde_vintage_pipeline" / "wasde_vintage_dataset.csv")
CAL = ROOT / "data" / "interim" / "usda_calendar.parquet"


def load_vintage() -> pd.DataFrame:
    w = pd.read_csv(VINTAGE)
    w["available_from"] = pd.to_datetime(w["available_from"])
    w = w.sort_values("available_from").reset_index(drop=True)
    return w


def _daily_ffill(events: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """events indexe par available_from -> serie quotidienne forward-fill."""
    full = pd.date_range(events.index.min(), pd.Timestamp("2025-12-31"), freq="D")
    return events[cols].reindex(events.index.union(full)).sort_index().ffill().reindex(full)


def release_features() -> tuple[pd.DataFrame, dict]:
    """EXT007 : niveaux publies + dummies calendrier connus ex ante."""
    w = load_vintage().set_index("available_from")
    levels = ["ending_stocks", "stocks_to_use_ratio", "production",
              "exports", "use_total", "avg_farm_price"]
    feats = _daily_ffill(w, levels)
    feats.columns = [f"wasde_{c}" for c in feats.columns]

    cal = pd.read_parquet(CAL)
    cal["Date"] = pd.to_datetime(cal["Date"])
    cal = cal.set_index("Date")
    calf = cal[["is_wasde_day", "days_since_last_wasde", "days_to_next_wasde",
                "is_grain_stocks_day", "is_acreage_day"]].copy()
    # fenetre post-rapport [J, J+10] (calendrier connu => zero fuite)
    calf["wasde_post_window"] = (cal["days_since_last_wasde"] <= 10).astype(float)
    out = feats.join(calf, how="left")
    fdict = {f"wasde_{c}": f"Niveau WASDE publie (vintage): {c}" for c in levels}
    fdict.update({
        "is_wasde_day": "Indicateur jour de publication WASDE (calendrier ex ante)",
        "days_since_last_wasde": "Jours depuis le dernier WASDE",
        "days_to_next_wasde": "Jours avant le prochain WASDE",
        "is_grain_stocks_day": "Indicateur jour Grain Stocks",
        "is_acreage_day": "Indicateur jour Acreage/Plantings",
        "wasde_post_window": "Fenetre post-rapport [J, J+10]",
    })
    return out, fdict


def revision_proxy_features() -> tuple[pd.DataFrame, dict]:
    """EXT008 : proxys de surprise = REVISIONS M-M-1 (PAS de consensus analystes).

    Terminologie : wasde_revision_proxy / wasde_surprise_proxy_non_consensus.
    La surprise standardisee divise la revision par l'ecart-type EXPANDANT des
    revisions passees de la meme variable (anti-fuite)."""
    w = load_vintage().sort_values("available_from").reset_index(drop=True)
    rev_vars = ["ending_stocks", "stocks_to_use_ratio", "production",
                "yield_per_acre", "exports", "use_total", "avg_farm_price"]
    cols, fdict = {}, {}
    for v in rev_vars:
        chg = w[f"{v}_chg_m1"]
        cols[f"rev_{v}"] = chg.to_numpy()
        # surprise standardisee : revision / std expandant des revisions passees
        std = chg.expanding(min_periods=8).std().shift(1)
        cols[f"revz_{v}"] = (chg / std).to_numpy()
        fdict[f"rev_{v}"] = f"Revision M-M-1 du chiffre {v} (proxy surprise non-consensus)"
        fdict[f"revz_{v}"] = f"Revision {v} standardisee par vol expandante des revisions"
    # surprise directionnelle du bilan : hausse des stocks de fin = deterioration (baissier)
    cols["balance_surprise_dir"] = np.sign(w["ending_stocks_chg_m1"].to_numpy())
    fdict["balance_surprise_dir"] = "Direction surprise bilan: +1 stocks en hausse (baissier), -1 baisse (haussier)"

    ev = pd.DataFrame(cols)
    ev.index = pd.to_datetime(w["available_from"])
    feats = _daily_ffill(ev, list(ev.columns))
    return feats, fdict
