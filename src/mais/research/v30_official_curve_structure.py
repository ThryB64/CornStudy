"""V30 — Structure de courbe EMA OFFICIELLE (contango / backwardation) sur données réelles.

Le collecteur officiel (V26) fournit plusieurs échéances avec settlement + open interest. On caractérise
la VRAIE courbe Euronext : spreads inter-échéances, pente nearby, contango/backwardation, contrat le plus
liquide. Hypothèse (cf. baseline figée / V16) :
  basis haut + BACKWARDATION nearby = tension physique réelle -> prime se normalise plus lentement ;
  basis haut + CONTANGO          = portage normal       -> prime plus probablement compressible.

Cette piste était bloquée par le manque de données multi-échéances ; débloquée par la source officielle.
Snapshot du jour seulement (s'enrichit forward avec le journal V27).

Statut : RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V30_DIR = ARTEFACTS_DIR / "v30"
V30_DIR.mkdir(parents=True, exist_ok=True)
OFFICIAL_PARQUET = ROOT / "data" / "raw" / "euronext_ema_official" / "official_daily.parquet"


def _liquid_curve(snap: pd.DataFrame) -> pd.DataFrame:
    """Garde les échéances réellement cotées (OI>0 ou volume>0) et ordonne par maturité."""
    s = snap.dropna(subset=["settlement"]).copy()
    oi = pd.to_numeric(s["open_interest"], errors="coerce").fillna(0.0)
    vol = pd.to_numeric(s.get("volume"), errors="coerce").fillna(0.0)
    s = s[(oi > 0) | (vol > 0)]
    if s.empty:
        return s
    s["maturity"] = s["contract_year"].astype(int) * 12 + s["contract_month"].astype(int)
    return s.sort_values("maturity").reset_index(drop=True)


def compute_curve_structure(price_date: str | None = None) -> dict[str, Any]:
    """Structure de courbe officielle pour la date la plus récente (ou `price_date` donné)."""
    if not OFFICIAL_PARQUET.exists():
        return {"version": "V30-OFFICIAL-CURVE", "verdict": "NO_OFFICIAL_DATA"}
    df = pd.read_parquet(OFFICIAL_PARQUET)
    df["price_date"] = pd.to_datetime(df["price_date"]).dt.date.astype(str)
    target = price_date or sorted(df["price_date"].unique())[-1]
    snap = df[df["price_date"] == target]
    curve = _liquid_curve(snap)
    if len(curve) < 2:
        return {"version": "V30-OFFICIAL-CURVE", "verdict": "TOO_FEW_LIQUID", "price_date": target,
                "n_liquid": int(len(curve))}

    settl = curve["settlement"].astype(float).tolist()
    codes = curve["contract_code"].tolist()
    oi = pd.to_numeric(curve["open_interest"], errors="coerce").fillna(0.0)
    spreads = [round(settl[i] - settl[i + 1], 2) for i in range(len(settl) - 1)]
    # front liquide = plus grand OI
    liquid_pos = int(oi.values.argmax())
    front_second_spread = round(settl[0] - settl[1], 2)
    # nearby slope : >0 => nearby plus cher que déféré => backwardation
    nearby_shape = ("BACKWARDATION" if front_second_spread > 0.5
                    else "CONTANGO" if front_second_spread < -0.5 else "FLAT")
    n_back = sum(1 for s in spreads if s > 0.5)
    n_cont = sum(1 for s in spreads if s < -0.5)
    overall = ("MOSTLY_BACKWARDATION" if n_back > n_cont
               else "MOSTLY_CONTANGO" if n_cont > n_back else "MIXED")
    out = {
        "version": "V30-OFFICIAL-CURVE",
        "price_date": target,
        "n_liquid_contracts": int(len(curve)),
        "contracts": codes,
        "settlements": settl,
        "open_interest": [int(v) for v in oi.tolist()],
        "consecutive_spreads": spreads,
        "front_contract": codes[0],
        "most_liquid_contract": codes[liquid_pos],
        "front_second_spread_eur_t": front_second_spread,
        "nearby_shape": nearby_shape,
        "overall_shape": overall,
        "verdict": "OFFICIAL_CURVE_CHARACTERISED",
        "interpretation": (
            f"Courbe nearby {nearby_shape} (front−second {front_second_spread:+.2f} €/t), "
            f"structure globale {overall}. " + (
                "Backwardation nearby = tension physique old-crop -> un basis haut peut se normaliser "
                "plus lentement (compression prudente)." if nearby_shape == "BACKWARDATION"
                else "Contango = portage normal -> un basis haut est plus probablement compressible."
                if nearby_shape == "CONTANGO" else "Courbe nearby plate.")
        ),
    }
    (V30_DIR / "official_curve_structure.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def curve_context_for_journal(price_date: str | None = None) -> dict[str, Any]:
    """Contexte compact (shape) à joindre au journal forward V27."""
    cs = compute_curve_structure(price_date)
    if cs.get("verdict") != "OFFICIAL_CURVE_CHARACTERISED":
        return {"curve_shape": None, "curve_verdict": cs.get("verdict")}
    return {"curve_shape": cs["nearby_shape"], "curve_overall": cs["overall_shape"],
            "front_second_spread_eur_t": cs["front_second_spread_eur_t"],
            "most_liquid_contract": cs["most_liquid_contract"]}


def run_v30() -> dict[str, Any]:
    out = compute_curve_structure()
    (V30_DIR / "v30_summary.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
