"""V178 — Validation officielle 40 jours : proxy vs officiel sur les paires accumulées.

Complète V144 (z rolling stagé) avec la comparaison PAIRE À PAIRE : chaque jour, le collecteur
V144-DATA quote sur Barchart LE MÊME contrat que le front officiel ; ce module mesure l'écart
proxy↔officiel sur le prix EMA, le basis, le basis_z et le tier de signal.

Gate : n_official_days >= 40 (jalon V147). Sous le gate : ACCUMULATING, avec stats PRÉLIMINAIRES
si >=5 paires (informatif, jamais un verdict). Seuils de verdict PRÉ-DÉCLARÉS et FIGÉS au
2026-06-11, AVANT d'avoir vu les 40 jours :

  PROXY_VALIDATED      : MAE prix <= 2.0 €/t ET |biais| <= 1.0 €/t ET tier agreement >= 0.90
  PROXY_INVALID        : MAE prix > 5.0 €/t OU tier agreement < 0.70
  PROXY_RESEARCH_ONLY  : tout le reste (le proxy reste utilisable en research, pas en lecture z)

Baseline z>1 intouchée ; le head n'est jamais modifié ici. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V178_DIR = ARTEFACTS_DIR / "v178"
V178_DIR.mkdir(parents=True, exist_ok=True)
PROXY_QUOTES = ROOT / "data" / "official_forward" / "proxy_quote_journal.parquet"

GATE_DAYS = 40
MIN_PAIRS_PRELIM = 5
# seuils figés 2026-06-11 (avant données)
MAE_VALIDATED, BIAS_VALIDATED, TIER_VALIDATED = 2.0, 1.0, 0.90
MAE_INVALID, TIER_INVALID = 5.0, 0.70
TIER_EDGES = [(2.0, "EXTREME"), (1.5, "STRONG"), (1.0, "MODERATE")]


def tier_from_z(z: float | None) -> str | None:
    if z is None or not np.isfinite(z):
        return None
    for edge, name in TIER_EDGES:
        if z >= edge:
            return name
    return "NO_SIGNAL"


_STATUS_RANK = {"REVISED": 3, "FINAL": 2}


def _load_official() -> pd.DataFrame | None:
    """Une ligne CANONIQUE par date (REVISED > FINAL > PROVISIONAL), comme le jalon V147."""
    try:
        from mais.research.v27_official_forward import load_forward_journal
        j = load_forward_journal(final_only=False)
    except Exception:  # noqa: BLE001
        return None
    if j is None or len(j) == 0:
        return None
    j = j.copy()
    j["price_date"] = pd.to_datetime(j["price_date"]).dt.strftime("%Y-%m-%d")
    j["_rank"] = j.get("record_status", pd.Series(index=j.index)).map(_STATUS_RANK).fillna(1)
    sort_cols = ["price_date", "_rank"] + (["logged_at"] if "logged_at" in j.columns else [])
    j = j.sort_values(sort_cols).drop_duplicates(subset="price_date", keep="last")
    return j.drop(columns="_rank").reset_index(drop=True)


def build_pairs(official: pd.DataFrame, quotes: pd.DataFrame) -> pd.DataFrame:
    """Apparie par price_date + contrat ; calcule erreurs prix/basis/z/tier côte à côte."""
    q = quotes.copy()
    q["price_date"] = pd.to_datetime(q["price_date"]).dt.strftime("%Y-%m-%d")
    pairs = official.merge(q, left_on=["price_date", "official_front_contract"],
                           right_on=["price_date", "contract"], how="inner")
    if pairs.empty:
        return pairs
    pairs["official_price"] = pd.to_numeric(pairs["official_front_settlement"], errors="coerce")
    pairs["proxy_price"] = pd.to_numeric(pairs["proxy_last_price"], errors="coerce")
    pairs["price_err"] = pairs["proxy_price"] - pairs["official_price"]
    cbot = pd.to_numeric(pairs["cbot_eur_t"], errors="coerce")
    pairs["official_basis"] = pd.to_numeric(pairs["basis_official_eur_t"], errors="coerce")
    pairs["proxy_basis"] = pairs["proxy_price"] - cbot
    pairs["basis_err"] = pairs["proxy_basis"] - pairs["official_basis"]
    # z : mêmes mu/sigma (stats proxy trailing, comme le z_used du journal) appliqués aux DEUX
    # basis -> l'écart de z reflète uniquement l'écart de prix, pas un choix de fenêtre
    mu = sigma = None
    try:
        from mais.research.v27_official_forward import proxy_trailing_stats
        stats = proxy_trailing_stats()
        if stats and stats.get("std"):
            mu, sigma = float(stats["mean"]), float(stats["std"])
    except Exception:  # noqa: BLE001
        pass
    if sigma:
        pairs["z_official"] = (pairs["official_basis"] - mu) / sigma
        pairs["z_proxy"] = (pairs["proxy_basis"] - mu) / sigma
    else:
        pairs["z_official"] = pd.to_numeric(pairs["basis_z_used"], errors="coerce")
        pairs["z_proxy"] = np.nan
    pairs["tier_official"] = pairs["z_official"].map(tier_from_z)
    pairs["tier_proxy"] = pairs["z_proxy"].map(tier_from_z)
    return pairs


def _metrics(pairs: pd.DataFrame) -> dict[str, Any]:
    if pairs.empty or "price_err" not in pairs.columns:
        return {"n_pairs": 0, "price": None, "basis": None, "basis_z": None,
                "tier_agreement": None}
    err = pairs["price_err"].dropna()
    berr = pairs["basis_err"].dropna()
    tiers = pairs[["tier_official", "tier_proxy"]].dropna()
    agree = float((tiers["tier_official"] == tiers["tier_proxy"]).mean()) if len(tiers) else None
    zdiff = (pairs["z_proxy"] - pairs["z_official"]).dropna()
    return {
        "n_pairs": int(len(pairs)),
        "price": {"mae": round(float(err.abs().mean()), 3), "rmse": round(float(np.sqrt((err ** 2).mean())), 3),
                  "bias": round(float(err.mean()), 3)} if len(err) else None,
        "basis": {"mae": round(float(berr.abs().mean()), 3),
                  "rmse": round(float(np.sqrt((berr ** 2).mean())), 3),
                  "bias": round(float(berr.mean()), 3)} if len(berr) else None,
        "basis_z": {"mean_abs_diff": round(float(zdiff.abs().mean()), 4),
                    "max_abs_diff": round(float(zdiff.abs().max()), 4)} if len(zdiff) else None,
        "tier_agreement": round(agree, 3) if agree is not None else None,
    }


def _verdict(m: dict[str, Any]) -> str:
    if not m or m.get("price") is None or m.get("tier_agreement") is None:
        return "PROXY_RESEARCH_ONLY"
    mae, bias = m["price"]["mae"], abs(m["price"]["bias"])
    agree = m["tier_agreement"]
    if mae > MAE_INVALID or agree < TIER_INVALID:
        return "PROXY_INVALID"
    if mae <= MAE_VALIDATED and bias <= BIAS_VALIDATED and agree >= TIER_VALIDATED:
        return "PROXY_VALIDATED"
    return "PROXY_RESEARCH_ONLY"


def run_v178_validation() -> dict[str, Any]:
    official = _load_official()
    if official is None:
        return {"version": "V178-OFFICIAL-VALIDATION", "verdict": "NO_JOURNAL"}
    n_days = int(official["price_date"].nunique())
    quotes = pd.read_parquet(PROXY_QUOTES) if PROXY_QUOTES.exists() else pd.DataFrame()
    pairs = build_pairs(official, quotes) if len(quotes) else pd.DataFrame()
    gated = n_days >= GATE_DAYS

    out: dict[str, Any] = {
        "version": "V178-OFFICIAL-VALIDATION",
        "gate_days": GATE_DAYS, "n_official_days": n_days, "n_pairs": int(len(pairs)),
        "n_final_or_revised": int(official.get("record_status", pd.Series(dtype=str))
                                  .isin(["FINAL", "REVISED"]).sum()),
        "thresholds_frozen_2026_06_11": {
            "validated": {"mae_price_eur_t": MAE_VALIDATED, "abs_bias_eur_t": BIAS_VALIDATED,
                          "tier_agreement": TIER_VALIDATED},
            "invalid": {"mae_price_eur_t_gt": MAE_INVALID, "tier_agreement_lt": TIER_INVALID},
        },
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    if not gated:
        out["verdict"] = f"ACCUMULATING_{n_days}_OF_{GATE_DAYS}"
        if len(pairs) >= MIN_PAIRS_PRELIM:
            out["preliminary_metrics_not_a_verdict"] = _metrics(pairs)
    else:
        m = _metrics(pairs)
        out["metrics"] = m
        out["verdict"] = _verdict(m)
        out["interpretation"] = (
            f"{n_days} jours officiels, {m['n_pairs']} paires proxy↔officiel. "
            f"Prix : MAE {m['price']['mae'] if m['price'] else None} €/t, biais "
            f"{m['price']['bias'] if m['price'] else None} €/t ; tier agreement "
            f"{m['tier_agreement']}. Verdict (seuils figés ex-ante) : {out['verdict']}."
            + (" Aucune paire exploitable -> research only par défaut." if m["n_pairs"] == 0 else ""))
    (V178_DIR / "v178_official_validation.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
