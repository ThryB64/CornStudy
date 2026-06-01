"""Collecteur Euronext Milling Wheat (EBM) OFFICIEL — vrais settlements blé meunier MATIF.

Même endpoint AJAX que l'EMA (maïs), produit EBM/DPAR. Sert à construire le ratio de substitution
EUROPÉEN blé/maïs (MATIF wheat / MATIF corn) — plus pertinent que le ratio CBOT pour expliquer le basis EU
(la substitution fourragère est locale, cf. V36/V40). Réseau requis ; snapshot du jour seulement (pas
d'historique profond) -> on accumule en append-only forward.

Usage :
    from mais.collect.euronext_milling_wheat import fetch_milling_wheat, save_milling_wheat_snapshot
    df = fetch_milling_wheat()
    save_milling_wheat_snapshot()  # -> data/raw/euronext_milling_wheat/milling_wheat_daily.parquet
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from mais.collect.euronext_endpoint_probe import fetch_endpoint_html
from mais.collect.euronext_official_live import parse_official_prices
from mais.paths import PROJECT_ROOT as ROOT

OUT_DIR = ROOT / "data" / "raw" / "euronext_milling_wheat"
EBM_ENDPOINT = "https://live.euronext.com/en/ajax/getPricesFutures/commodities-futures/EBM/DPAR"
EBM_PRODUCT_PAGE = "https://live.euronext.com/en/product/commodity-futures/EBM-DPAR"


def fetch_milling_wheat(timeout: int = 30) -> pd.DataFrame:
    """Snapshot officiel du jour (EBM). Lève NotImplementedError proprement si réseau indisponible."""
    try:
        html = fetch_endpoint_html(url=EBM_ENDPOINT, timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        raise NotImplementedError(f"euronext EBM indisponible (réseau ?): {exc}") from exc
    price_date, rows = parse_official_prices(html)
    if not rows:
        raise NotImplementedError("euronext EBM : aucune ligne parsée (format changé ?)")
    df = pd.DataFrame(rows)
    df["contract_code"] = df["contract_code"].str.replace("EMA_", "EBM_", regex=False)
    df["product_code"] = "EBM"
    df.insert(0, "price_date", pd.Timestamp(price_date) if price_date else pd.Timestamp("today").normalize())
    return df


def save_milling_wheat_snapshot() -> dict[str, Any]:
    """Append-only du snapshot EBM du jour. Jamais de réécriture du passé."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "milling_wheat_daily.parquet"
    try:
        df = fetch_milling_wheat()
    except NotImplementedError as exc:
        return {"status": "SKIP", "reason": str(exc)}
    if path.exists():
        prev = pd.read_parquet(path)
        key = ["price_date", "contract_code"]
        combined = (pd.concat([prev, df], ignore_index=True)
                    .drop_duplicates(subset=key, keep="last"))
        n_added = len(combined) - len(prev)
    else:
        combined = df
        n_added = len(df)
    combined.to_parquet(path, index=False)
    return {"status": "OK", "price_date": str(df["price_date"].iloc[0].date()),
            "n_contracts": int(len(df)), "n_added": int(n_added), "n_total": int(len(combined)),
            "path": str(path),
            "most_liquid": df.loc[df["open_interest"].idxmax(), "contract_code"]
            if df["open_interest"].notna().any() else None}
