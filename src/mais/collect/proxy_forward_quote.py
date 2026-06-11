"""V144-DATA — Quote proxy Barchart quotidienne du contrat front EMA officiel.

Le modèle de biais proxy<->officiel (V144) était bloqué : le proxy historique s'arrête en 2025-07 et le
journal officiel commence en 2026-05 -> AUCUN overlap. Ce collecteur le CRÉE en forward : chaque jour,
on quote sur Barchart LE MÊME contrat que le front officiel du journal, et on archive. Après ~40 jours,
`official_proxy_validation.py` (V144) aura ses paires.

Le lastPrice Barchart est un prix retardé/de fin de page, pas le settlement DSP : c'est EXACTEMENT le
biais que V144 doit modéliser. Source exploratoire, jamais mélangée à l'officiel. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from mais.collect.barchart_ema_probe import build_barchart_symbol, fetch_barchart_html
from mais.paths import PROJECT_ROOT as ROOT

JOURNAL_JSONL = ROOT / "data" / "official_forward" / "proxy_quote_journal.jsonl"
JOURNAL_PARQUET = ROOT / "data" / "official_forward" / "proxy_quote_journal.parquet"

_PRICE_RE = re.compile(r'"lastPrice"\s*:\s*"?([0-9]+(?:\.[0-9]+)?)')
_SETTLE_RE = re.compile(r'"previousSettlement"\s*:\s*"?([0-9]+(?:\.[0-9]+)?)')


def official_contract_to_symbol(contract: str) -> str | None:
    """'EMA_Q2026' -> symbole Barchart 'XBQ26'."""
    m = re.fullmatch(r"EMA_([FHKMNQUVXZ])(\d{4})", str(contract))
    if not m:
        return None
    return build_barchart_symbol(m.group(1), int(m.group(2)))


def parse_quote(html: str) -> dict[str, float | None]:
    last = _PRICE_RE.search(html)
    settle = _SETTLE_RE.search(html)
    return {"last_price": float(last.group(1)) if last else None,
            "previous_settlement": float(settle.group(1)) if settle else None}


def append_proxy_quote(front_contract: str, price_date: str,
                       fetch=fetch_barchart_html) -> dict[str, Any]:
    """Quote le front officiel et l'append (dédup par price_date+contrat, append-only)."""
    sym = official_contract_to_symbol(front_contract)
    if sym is None:
        return {"verdict": "SKIP", "reason": f"contrat non mappable: {front_contract}"}
    try:
        code, html = fetch(sym)
    except Exception as e:  # noqa: BLE001
        return {"verdict": "WAITING_DATA", "reason": f"{type(e).__name__}"}
    if code != 200:
        return {"verdict": "WAITING_DATA", "reason": f"http {code}"}
    q = parse_quote(html)
    if q["last_price"] is None:
        return {"verdict": "WAITING_DATA", "reason": "lastPrice introuvable"}
    rec = {"price_date": price_date, "contract": front_contract, "barchart_symbol": sym,
           "proxy_last_price": q["last_price"], "proxy_previous_settlement": q["previous_settlement"],
           "collected_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
           "source": "barchart_proxy_exploratory"}
    JOURNAL_JSONL.parent.mkdir(parents=True, exist_ok=True)
    existing = load_proxy_quotes()
    dup = (not existing.empty
           and ((existing["price_date"] == price_date) & (existing["contract"] == front_contract)).any())
    if dup:
        return {"verdict": "ALREADY_LOGGED", "price_date": price_date, "contract": front_contract}
    with JOURNAL_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    df = pd.concat([existing, pd.DataFrame([rec])], ignore_index=True)
    df.to_parquet(JOURNAL_PARQUET, index=False)
    return {"verdict": "PROXY_QUOTE_LOGGED", **{k: rec[k] for k in
            ("price_date", "contract", "proxy_last_price", "proxy_previous_settlement")},
            "n_overlap_days": int(df["price_date"].nunique())}


def load_proxy_quotes() -> pd.DataFrame:
    if not JOURNAL_JSONL.exists():
        return pd.DataFrame()
    recs = [json.loads(ln) for ln in JOURNAL_JSONL.read_text(encoding="utf-8").splitlines()
            if ln.strip()]
    return pd.DataFrame(recs)


def run_proxy_forward_quote() -> dict[str, Any]:
    """Étape daily : quote le front officiel le plus récent du journal."""
    from mais.research import v27_official_forward as v27
    try:
        j = v27.load_forward_journal(final_only=False)
    except Exception as e:  # noqa: BLE001
        return {"verdict": "SKIP", "reason": f"journal illisible: {type(e).__name__}"}
    if j is None or j.empty:
        return {"verdict": "SKIP", "reason": "journal vide"}
    last = j.sort_values("price_date").iloc[-1]
    return append_proxy_quote(str(last["official_front_contract"]), str(last["price_date"]))
