"""Backtest agricole de l'indicateur sur le prix Euronext (étape de visualisation).

Réutilise la mécanique validée du backtest CBOT (`cbot_sale_score_backtest` : ventes
partielles, cooldown, campagnes calendar/sep_aug/oct_sep) en l'appliquant au **prix Euronext**.
Pas de short, pas de buy, pas de levier ; ventes partielles seulement. ⚠️ Le prix Euronext est
à ~97 % un proxy (cf. `docs/EURONEXT_DATA_AUDIT.md`) → résultats **illustratifs**.
"""
from __future__ import annotations

import pandas as pd

from mais.indicator import cbot_sale_score_backtest as cbt


def _bt_cfg(cfg: dict) -> dict:
    """Adapte la config Euronext au format attendu par le backtest CBOT."""
    return {"rules": {"sell_fraction": float(cfg["backtest"]["sell_fraction"])},
            "backtest": {"sell_cooldown_sessions": int(cfg["cooldown"]["sell_partial_days"]),
                         "windows": cfg["backtest"]["windows"],
                         "cooldown_grid": cfg["backtest"]["cooldown_grid"]}}


def _bt_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return (frame[["euronext_price", "recommendation"]]
            .rename(columns={"euronext_price": "corn_close"}))


def run_backtest(frame: pd.DataFrame, cfg: dict, start: str, window: str = "calendar",
                 cooldown: int | None = None):
    return cbt.run_backtest(_bt_frame(frame), _bt_cfg(cfg), start, window, cooldown)


def run_all_campaigns(frame: pd.DataFrame, cfg: dict, start: str):
    """Comparaison campagnes (calendar/sep_aug/oct_sep) × cooldown sur l'historique Euronext."""
    return cbt.run_all_windows(_bt_frame(frame), _bt_cfg(cfg), start)
