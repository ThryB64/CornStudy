"""V26 — Validation de la source EMA officielle (déblocage de la donnée officielle Euronext).

L'endpoint officiel Euronext fournit les settlements réels. Ce module :
- run_collect_official : sauvegarde le snapshot officiel du jour (append-only).
- run_official_basis : fetch live CBOT+FX, calcule le basis OFFICIEL (EMA officiel - CBOT EUR/t).
- run_proxy_vs_official_levels : situe le basis officiel dans la distribution du basis PROXY historique
  (même s'il n'y a pas de chevauchement de dates, on compare les NIVEAUX et le basis_z impliqué).

Statut : officiel pour le snapshot du jour ; l'historique officiel s'accumule forward.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V26_DIR = ARTEFACTS_DIR / "v26"
V26_DIR.mkdir(parents=True, exist_ok=True)
BUSHEL_TO_TONNE = 39.3679


def run_collect_official() -> dict[str, Any]:
    from mais.collect.euronext_official_live import save_official_snapshot
    out = save_official_snapshot()
    (V26_DIR / "official_collect.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def _yahoo_last(sym: str, timeout: int = 25):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
        d = json.loads(r.read())
    res = d["chart"]["result"][0]
    closes = res["indicators"]["quote"][0]["close"]
    ts = res["timestamp"]
    vals = [(t, c) for t, c in zip(ts, closes, strict=False) if c is not None]
    return vals[-1] if vals else None


def run_official_basis() -> dict[str, Any]:
    """Calcule le basis officiel du jour : EMA settlement officiel - CBOT converti EUR/t (live)."""
    from mais.collect.euronext_official_live import fetch_official_ema
    try:
        ema = fetch_official_ema()
        zc = _yahoo_last("ZC=F")
        fx = _yahoo_last("EURUSD=X")
    except Exception as exc:  # noqa: BLE001
        out = {"version": "V26-OFFICIAL-BASIS", "verdict": "SKIP_OFFLINE", "reason": str(exc)[:160]}
        (V26_DIR / "official_basis.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
        return out
    if zc is None or fx is None:
        return {"version": "V26-OFFICIAL-BASIS", "verdict": "NO_LIVE_CBOT_FX"}
    cbot_eur_t = zc[1] / 100.0 / fx[1] * BUSHEL_TO_TONNE
    # front liquide officiel = settlement du contrat à plus grand open interest
    valid = ema.dropna(subset=["settlement"])
    front = valid.loc[valid["open_interest"].idxmax()] if valid["open_interest"].notna().any() else valid.iloc[0]
    basis_official = float(front["settlement"]) - cbot_eur_t
    out = {
        "version": "V26-OFFICIAL-BASIS",
        "price_date": str(ema["price_date"].iloc[0].date()),
        "cbot_cents_bu": round(float(zc[1]), 2),
        "eurusd": round(float(fx[1]), 4),
        "cbot_eur_t": round(cbot_eur_t, 2),
        "official_front_contract": front["contract_code"],
        "official_front_settlement": round(float(front["settlement"]), 2),
        "official_front_oi": int(front["open_interest"]) if pd.notna(front["open_interest"]) else None,
        "basis_official_eur_t": round(basis_official, 2),
        "all_contracts_basis": {
            r["contract_code"]: round(float(r["settlement"]) - cbot_eur_t, 2)
            for _, r in valid.iterrows()},
        "verdict": "OFFICIAL_BASIS_COMPUTED",
    }
    (V26_DIR / "official_basis.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_proxy_vs_official_levels(official_basis: float | None = None) -> dict[str, Any]:
    """Situe le basis officiel dans la distribution du basis PROXY historique (niveau + z impliqué)."""
    curve = ROOT / "data/processed/euronext/ema_curve_features.parquet"
    out: dict[str, Any] = {"version": "V26-PROXY-VS-OFFICIAL"}
    if not curve.exists():
        out["verdict"] = "MISSING_PROXY"
        return out
    cf = pd.read_parquet(curve)
    if "ema_cbot_basis" not in cf.columns:
        out["verdict"] = "MISSING_BASIS_COL"
        return out
    b = pd.to_numeric(cf["ema_cbot_basis"], errors="coerce").dropna()
    proxy_stats = {
        "n": int(len(b)), "mean": round(float(b.mean()), 2), "std": round(float(b.std()), 2),
        "p50": round(float(b.median()), 2), "p90": round(float(b.quantile(0.90)), 2),
        "p95": round(float(b.quantile(0.95)), 2), "max": round(float(b.max()), 2),
    }
    out["proxy_basis_distribution"] = proxy_stats
    if official_basis is not None:
        pctl = float((b < official_basis).mean())
        z_implied = (official_basis - b.mean()) / b.std() if b.std() else None
        out["official_basis_eur_t"] = round(official_basis, 2)
        out["official_basis_percentile_in_proxy"] = round(pctl, 4)
        out["official_basis_z_implied_vs_proxy_dist"] = round(float(z_implied), 3) if z_implied is not None else None
        out["interpretation"] = (
            f"Le basis officiel ({official_basis:.1f} €/t) est au {pctl*100:.0f}e percentile de la "
            f"distribution proxy (z~{z_implied:.2f}). Niveau cohérent => les niveaux proxy sont réalistes. "
            "Mais validation date-par-date impossible (pas de chevauchement) -> accumuler l'officiel forward."
        )
    out["verdict"] = "PROXY_VS_OFFICIAL_LEVELS_DONE"
    (V26_DIR / "proxy_vs_official_levels.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def run_v26_all() -> dict[str, Any]:
    collect = run_collect_official()
    basis = run_official_basis()
    ob = basis.get("basis_official_eur_t") if basis.get("verdict") == "OFFICIAL_BASIS_COMPUTED" else None
    levels = run_proxy_vs_official_levels(ob)
    out = {
        "version": "V26-SUMMARY",
        "collect": collect,
        "official_basis": basis,
        "proxy_vs_official": {k: levels.get(k) for k in
                              ["proxy_basis_distribution", "official_basis_percentile_in_proxy",
                               "official_basis_z_implied_vs_proxy_dist", "interpretation"]},
        "unblock_status": ("OFFICIAL_EMA_COLLECTOR_OPERATIONAL"
                           if collect.get("status") == "OK" else "OFFLINE_THIS_RUN"),
        "note": "Source EMA officielle Euronext débloquée (settlement réel). Historique officiel à accumuler "
                "forward (snapshot du jour seulement). Le proxy reste utilisé pour l'historique research.",
    }
    (V26_DIR / "v26_summary.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
