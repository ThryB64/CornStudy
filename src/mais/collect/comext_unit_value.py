"""V161-DATA — COMEXT prix unitaires d'import maïs UE (CIF implicite, gratuit).

Source : API dissémination COMEXT (host dédié, DS-045409 « EU trade since 1988 »). Pour chaque mois et
partenaire (Ukraine, Brésil, total extra-UE), on récupère VALUE_IN_EUROS et QUANTITY_IN_100KG du code
CN 1005 (maïs), flow=1 (import UE27). Prix unitaire €/t = valeur / tonnes : c'est un coût d'import CIF
implicite (fret inclus) — le matériau de la parité d'import physique.

Anti-leakage : COMEXT publie ~6-8 semaines après la fin du mois -> en aval, une valeur du mois M n'est
utilisable qu'à partir de fin M + PUBLICATION_LAG_DAYS. Archive committée. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime
from typing import Any

import pandas as pd

from mais.paths import PROJECT_ROOT as ROOT

COMEXT_URL = (
    "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/DS-045409"
    "?format=JSON&freq=M&reporter=EU27_2020&product=1005&flow=1"
    "&indicators=VALUE_IN_EUROS&indicators=QUANTITY_IN_100KG&sinceTimePeriod={since}{partners}"
)
DEFAULT_PARTNERS = ("UA", "BR", "EXT_EU27_2020")
ARCHIVE_PATH = ROOT / "data" / "official_forward" / "comext_maize_unit_value.parquet"
PUBLICATION_LAG_DAYS = 60  # disponibilité honnête : fin de mois + ~2 mois


def decode_jsonstat(d: dict) -> pd.DataFrame:
    """JSON-stat -> long df (partner, indicator, month, value). Décodage par index linéaire."""
    ids = d["id"]
    sizes = d["size"]
    cats = {dim: list(d["dimension"][dim]["category"]["index"].keys()) for dim in ids}
    strides = [1] * len(sizes)
    for i in range(len(sizes) - 2, -1, -1):
        strides[i] = strides[i + 1] * sizes[i + 1]
    rows = []
    for lin_str, val in d.get("value", {}).items():
        lin = int(lin_str)
        coord = {dim: cats[dim][(lin // strides[k]) % sizes[k]] for k, dim in enumerate(ids)}
        rows.append({"partner": coord.get("partner"), "indicator": coord.get("indicators"),
                     "month": coord.get("time"), "value": float(val)})
    return pd.DataFrame(rows)


def fetch_comext_unit_values(partners=DEFAULT_PARTNERS, since: str = "2015-01",
                             write: bool = True) -> dict[str, Any]:
    url = COMEXT_URL.format(since=since, partners="".join(f"&partner={p}" for p in partners))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "mais-research/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
            d = json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"verdict": "WAITING_DATA", "reason": f"{type(e).__name__}"}
    long = decode_jsonstat(d)
    if long.empty:
        return {"verdict": "WAITING_DATA", "reason": "réponse vide"}
    wide = long.pivot_table(index=["month", "partner"], columns="indicator",
                            values="value", aggfunc="first").reset_index()
    wide = wide.rename(columns={"VALUE_IN_EUROS": "value_eur", "QUANTITY_IN_100KG": "qty_100kg"})
    wide["qty_t"] = pd.to_numeric(wide.get("qty_100kg"), errors="coerce") / 10.0
    wide["unit_value_eur_t"] = pd.to_numeric(wide.get("value_eur"), errors="coerce") / wide["qty_t"]
    wide = wide[(wide["qty_t"] > 1000)]  # mois quasi vides -> prix unitaire non significatif
    out_df = wide[["month", "partner", "value_eur", "qty_t", "unit_value_eur_t"]].dropna()
    if write:
        ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
        if ARCHIVE_PATH.exists():
            old = pd.read_parquet(ARCHIVE_PATH)
            out_df = pd.concat([old, out_df], ignore_index=True).drop_duplicates(
                subset=["month", "partner"], keep="last")
        out_df = out_df.sort_values(["month", "partner"]).reset_index(drop=True)
        out_df.to_parquet(ARCHIVE_PATH, index=False)
    return {"verdict": "COMEXT_UNIT_VALUES_COLLECTED", "n_rows": int(len(out_df)),
            "partners": sorted(out_df["partner"].unique().tolist()),
            "first": str(out_df["month"].min()), "last": str(out_df["month"].max()),
            "collected_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}


def load_comext_unit_values() -> pd.DataFrame:
    return pd.read_parquet(ARCHIVE_PATH) if ARCHIVE_PATH.exists() else pd.DataFrame()
