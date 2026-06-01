"""V52 — Substitution EUROPÉENNE blé/maïs via le ratio MATIF (EBM / EMA), pas le ratio CBOT.

V36/V40 ont montré que le basis EU est porté par la substitution fourragère, et que c'est un phénomène
LOCAL (corr(ratio CBOT, basis) faible/inverse). Le bon ratio est donc probablement MATIF blé meunier /
MATIF maïs, tous deux en EUR/t. On collecte les settlements officiels (EBM + EMA) et on construit le ratio
européen. On le compare au ratio CBOT actuellement utilisé dans ADVERSE_RISK.

LIMITE HONNÊTE : l'endpoint officiel ne donne qu'un SNAPSHOT du jour (pas d'historique profond). La
VALIDATION historique du ratio MATIF sur les 42 trades (2014-2023) est donc `WAITING_DATA` : on l'accumule
en forward (journal append-only). Le ratio CBOT reste le proxy historique en attendant.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT
from mais.registry.holdout_lock import assert_no_holdout

V52_DIR = ARTEFACTS_DIR / "v52"
V52_DIR.mkdir(parents=True, exist_ok=True)
JOURNAL = ROOT / "data" / "official_forward" / "matif_ratio_journal.jsonl"


def _most_liquid(df: pd.DataFrame) -> pd.Series | None:
    s = df.dropna(subset=["settlement"])
    if len(s) == 0:
        return None
    if s["open_interest"].notna().any():
        return s.loc[s["open_interest"].idxmax()]
    return s.iloc[0]


def live_matif_ratio() -> dict[str, Any]:
    """Ratio MATIF blé/maïs du jour (most-liquid EBM / most-liquid EMA), EUR/t. SKIP propre si pas de réseau."""
    from mais.collect.euronext_milling_wheat import fetch_milling_wheat
    from mais.collect.euronext_official_live import fetch_official_ema
    try:
        wheat = fetch_milling_wheat()
        corn = fetch_official_ema()
    except NotImplementedError as exc:
        return {"status": "SKIP", "reason": str(exc)}
    w = _most_liquid(wheat)
    c = _most_liquid(corn)
    if w is None or c is None:
        return {"status": "SKIP", "reason": "settlements manquants"}
    ratio = round(float(w["settlement"]) / float(c["settlement"]), 4)
    return {
        "status": "OK",
        "price_date": str(pd.Timestamp(w["price_date"]).date()),
        "matif_wheat_contract": w["contract_code"], "matif_wheat_settle": float(w["settlement"]),
        "matif_corn_contract": c["contract_code"], "matif_corn_settle": float(c["settlement"]),
        "matif_wheat_corn_ratio": ratio,
    }


def append_matif_journal() -> dict[str, Any]:
    """Append-only du ratio MATIF du jour pour accumulation forward (clé = price_date)."""
    r = live_matif_ratio()
    if r.get("status") != "OK":
        return r
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if JOURNAL.exists():
        for line in JOURNAL.read_text(encoding="utf-8").splitlines():
            try:
                existing.add(json.loads(line).get("price_date"))
            except json.JSONDecodeError:
                continue
    if r["price_date"] in existing:
        return {**r, "appended": False, "reason": "déjà journalisé"}
    rec = {**r, "logged_at": datetime.now(timezone.utc).isoformat()}
    with JOURNAL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str) + "\n")
    return {**r, "appended": True}


def run_v52_matif(df: pd.DataFrame) -> dict[str, Any]:
    """Construit le ratio MATIF live, le compare au ratio CBOT, et formalise le gating historique."""
    assert_no_holdout(df)
    live = append_matif_journal()

    # ratio CBOT actuel (proxy historique utilisé par ADVERSE_RISK) — dernier point disponible
    wheat = pd.to_numeric(df.get("wheat_close"), errors="coerce")
    corn = pd.to_numeric(df.get("corn_close"), errors="coerce")
    cbot_ratio_series = (wheat / corn).dropna()
    cbot_ratio_last = round(float(cbot_ratio_series.iloc[-1]), 4) if len(cbot_ratio_series) else None

    n_journal = 0
    if JOURNAL.exists():
        n_journal = sum(1 for ln in JOURNAL.read_text(encoding="utf-8").splitlines() if ln.strip())

    historical_available = False  # endpoint = snapshot only
    if live.get("status") == "OK":
        verdict = ("MATIF_RATIO_LIVE_OK_HISTORICAL_WAITING_DATA"
                   if not historical_available else "MATIF_RATIO_FULL")
    else:
        verdict = "MATIF_RATIO_NETWORK_UNAVAILABLE"

    out = {
        "version": "V52-MATIF-SUBSTITUTION",
        "live_matif": live,
        "cbot_wheat_corn_ratio_last": cbot_ratio_last,
        "cbot_ratio_note": ("CBOT wheat/corn = cents-par-boisseau / cents-par-boisseau (boisseaux blé≠maïs) : "
                            "NON comparable en tonnes au ratio MATIF EUR/t. On compare les DYNAMIQUES (z-scores), "
                            "pas les niveaux bruts. Le ratio MATIF (EUR/t cohérent) est la mesure correcte."),
        "n_matif_journal_points": n_journal,
        "historical_matif_available": historical_available,
        "verdict": verdict,
        "interpretation": (
            "Le ratio MATIF blé/maïs (substitution EUROPÉENNE, EUR/t) est la bonne variable pour juger si une "
            "prime EMA haute est ÉCONOMIQUEMENT JUSTIFIÉE (V36/V40). Collecté en LIVE et journalisé en forward. "
            "L'endpoint officiel n'expose pas l'historique -> la validation sur les 42 trades attend "
            "l'accumulation forward ; d'ici là le ratio CBOT reste le proxy d'ADVERSE_RISK. Quand le journal "
            "MATIF sera assez long, brancher ce ratio dans ADVERSE_RISK v2 (V55) et comparer son pouvoir "
            "explicatif au ratio CBOT."),
        "next_step": ("Accumuler matif_ratio_journal.jsonl (GitHub Action) ; rebrancher dans V55 ADVERSE_RISK v2 "
                      "dès couverture suffisante."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V52_DIR / "v52_matif.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
