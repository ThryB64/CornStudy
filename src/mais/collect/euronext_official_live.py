"""Collecteur Euronext EMA OFFICIEL (live) — vrais prix de règlement.

Source : endpoint AJAX officiel de la page produit EMA (Corn) Euronext Paris.
Fournit, pour chaque échéance active, bid/ask/last/open/high/low/SETTLEMENT/volume/open_interest — c'est-à-dire
les VRAIES données Euronext (pas le proxy Barchart). Réseau requis.

Usage :
    from mais.collect.euronext_official_live import fetch_official_ema, save_official_snapshot
    df = fetch_official_ema()              # snapshot officiel du jour
    save_official_snapshot()               # append-only -> data/raw/euronext_ema_official/official_daily.parquet

Le parser est robuste au format de table actuel (Delivery | Bid Ask Last Time +/- Vol Open High Low Settl. O.I).
Statut : officiel, mais snapshot du jour seulement (l'historique complet reste payant / à accumuler forward).
"""
from __future__ import annotations

import re
from datetime import date as date_cls
from typing import Any

import pandas as pd

from mais.collect.euronext_endpoint_probe import fetch_endpoint_html
from mais.paths import PROJECT_ROOT as ROOT

OUT_DIR = ROOT / "data" / "raw" / "euronext_ema_official"
MONTH_NUM = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
             "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
MONTH_CODE = {1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M",
              7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z"}


def _num(tok: str) -> float | None:
    tok = tok.strip().replace(",", "")
    if tok in ("-", "", "—"):
        return None
    try:
        return float(tok)
    except ValueError:
        return None


def parse_official_prices(html: str) -> tuple[date_cls | None, list[dict[str, Any]]]:
    """Parse le tableau officiel Euronext EMA -> (date_prix, liste de contrats)."""
    txt = re.sub(r"<[^>]+>", " ", html)
    txt = re.sub(r"\s+", " ", txt).strip()
    # date d'en-tête : "Prices - 29 May 2026"
    price_date = None
    m = re.search(r"Prices\s*-\s*(\d{1,2})\s+([A-Za-z]{3})\w*\s+(\d{4})", txt)
    if m:
        d, mon, y = int(m.group(1)), m.group(2)[:3].title(), int(m.group(3))
        if mon in MONTH_NUM:
            price_date = date_cls(y, MONTH_NUM[mon], d)
    # lignes : <Mon> <Year> puis 11 tokens (Bid Ask Last Time +/- Vol Open High Low Settl OI)
    rows: list[dict[str, Any]] = []
    pat = re.compile(
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(20\d{2})\s+"
        r"(\S+)\s+(\S+)\s+(\S+)\s+(\d{1,2}:\d{2}|-)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)")
    for mt in pat.finditer(txt):
        mon, yr, bid, ask, last, _time, _chg, vol, op, hi, lo, settl, oi = mt.groups()
        cm = MONTH_NUM[mon]
        rows.append({
            "contract_month": cm, "contract_year": int(yr), "month_code": MONTH_CODE[cm],
            "contract_code": f"EMA_{MONTH_CODE[cm]}{yr}",
            "bid": _num(bid), "ask": _num(ask), "last": _num(last),
            "volume": _num(vol), "open": _num(op), "high": _num(hi), "low": _num(lo),
            "settlement": _num(settl), "open_interest": _num(oi),
            "currency": "EUR", "unit": "EUR/t", "source": "euronext_official_ajax", "is_proxy": False,
        })
    return price_date, rows


def fetch_official_ema(timeout: int = 30) -> pd.DataFrame:
    """Snapshot officiel du jour. Lève NotImplementedError proprement si réseau/endpoint indisponible."""
    try:
        html = fetch_endpoint_html(timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        raise NotImplementedError(f"euronext officiel indisponible (réseau ?): {exc}") from exc
    price_date, rows = parse_official_prices(html)
    if not rows:
        raise NotImplementedError("euronext officiel : aucune ligne parsée (format changé ?)")
    df = pd.DataFrame(rows)
    df.insert(0, "price_date", pd.Timestamp(price_date) if price_date else pd.Timestamp("today").normalize())
    return df


def save_official_snapshot() -> dict[str, Any]:
    """Append-only du snapshot officiel du jour. Jamais de réécriture du passé."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "official_daily.parquet"
    try:
        df = fetch_official_ema()
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
            "n_contracts": int(len(df)), "n_added": int(n_added),
            "n_total": int(len(combined)), "path": str(path),
            "most_liquid": df.loc[df["open_interest"].idxmax(), "contract_code"]
            if df["open_interest"].notna().any() else None}
