"""NB2-01 — Contrats, rolls et architecture raw/adjusted EMA."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import (
    ARTEFACTS_DIR,
    EMA_FRONT_ADJUSTED,
    EMA_FRONT_RAW,
    EMA_HARVEST_NOV,
    PROJECT_ROOT,
)
from mais.research.ema_contracts_rolls import build_contracts_rolls

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_contracts_v2.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_CONTRACTS_V2.md"


def _load_series(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def _return_comparison() -> dict:
    raw = _load_series(EMA_FRONT_RAW)
    adj = _load_series(EMA_FRONT_ADJUSTED)
    merged = raw[["date", "price"]].rename(columns={"price": "raw_price"}).merge(
        adj[["date", "adjusted_price", "price"]].rename(columns={"price": "adj_series_price"}),
        on="date",
        how="inner",
    )
    merged["raw_ret_20d"] = merged["raw_price"].pct_change(20)
    merged["adj_ret_20d"] = merged["adjusted_price"].pct_change(20)
    sub = merged[["raw_ret_20d", "adj_ret_20d"]].dropna()
    return {
        "n_overlap": int(len(merged)),
        "corr_20d_returns": float(sub["raw_ret_20d"].corr(sub["adj_ret_20d"])),
        "direction_agreement_20d": float((np.sign(sub["raw_ret_20d"]) == np.sign(sub["adj_ret_20d"])).mean()),
        "mean_abs_return_diff_20d": float((sub["raw_ret_20d"] - sub["adj_ret_20d"]).abs().mean()),
    }


def _harvest_coverage() -> dict:
    if not EMA_HARVEST_NOV.exists():
        return {"error": "ema_harvest_nov_missing"}
    df = _load_series(EMA_HARVEST_NOV)
    df["crop_year"] = np.where(df["date"].dt.month >= 10, df["date"].dt.year, df["date"].dt.year - 1)
    rows = {}
    for cy, sub in df.groupby("crop_year"):
        rows[int(cy)] = {
            "n_days": int(len(sub)),
            "start": str(sub["date"].min().date()),
            "end": str(sub["date"].max().date()),
        }
    return {
        "n_rows": int(len(df)),
        "n_crop_years": int(len(rows)),
        "by_crop_year": rows,
    }


def build_contracts_v2() -> dict:
    base = build_contracts_rolls()
    return_comp = _return_comparison()
    harvest = _harvest_coverage()
    key = base["key_findings"]
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "base_contracts_rolls": base,
        "front_raw_vs_adjusted_returns": return_comp,
        "harvest_nov_coverage": harvest,
        "recommendation": {
            "raw": "Utiliser pour prix absolu de marché et niveaux EMA.",
            "adjusted": "Utiliser pour rendements, momentum, volatilité et features techniques traversant les rolls.",
            "no_roll": "Utiliser pour sensibilité roll quand horizon disponible ; H60 quasi inutilisable sans roll.",
        },
        "key_findings": {
            "n_rolls": key.get("n_rolls_front"),
            "avg_roll_gap_eur_t": key.get("avg_roll_gap_eur_t"),
            "max_roll_gap_eur_t": key.get("max_roll_gap_eur_t"),
            "pct_H20_windows_with_roll": key.get("pct_H20_windows_with_roll"),
            "pct_H40_windows_with_roll": key.get("pct_H40_windows_with_roll"),
            "pct_H60_windows_with_roll": key.get("pct_H60_windows_with_roll"),
            "pct_dates_2plus_contracts": key.get("pct_dates_2plus_contracts"),
            "raw_adjusted_direction_agreement_20d": return_comp["direction_agreement_20d"],
        },
    }


def _json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return str(obj.date())
    raise TypeError(f"Not serialisable: {type(obj)}")


def _write_markdown(data: dict, path: Path) -> None:
    k = data["key_findings"]
    lines = [
        "# EMA CONTRACTS V2",
        "",
        "> Source EMA exploratoire/proxy. La courbe multi-maturité reste partielle.",
        "",
        "## Résultats clés",
        "",
        "| Métrique | Valeur |",
        "|---|---:|",
        f"| Rolls front | {k['n_rolls']} |",
        f"| Gap moyen absolu | {k['avg_roll_gap_eur_t']:.2f} €/t |",
        f"| Gap max absolu | {k['max_roll_gap_eur_t']:.2f} €/t |",
        f"| Fenêtres H20 avec roll | {k['pct_H20_windows_with_roll']:.1%} |",
        f"| Fenêtres H40 avec roll | {k['pct_H40_windows_with_roll']:.1%} |",
        f"| Fenêtres H60 avec roll | {k['pct_H60_windows_with_roll']:.1%} |",
        f"| Dates avec >=2 contrats | {k['pct_dates_2plus_contracts']:.1%} |",
        "",
        "## Recommandation",
        "",
        "- Série raw : prix absolu de marché.",
        "- Série adjusted : rendements, momentum, volatilité et features techniques.",
        "- Série no-roll : analyse de sensibilité uniquement, car H60 traverse presque toujours un roll.",
        "",
        "## Conclusion",
        "",
        "Les rolls sont un risque méthodologique majeur. Les résultats EMA doivent toujours préciser raw/adjusted/no-roll.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_contracts_v2(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_contracts_v2()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_contracts_v2()
    print(f"Contracts v2 saved -> {out}")
