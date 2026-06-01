"""V60-intraday — Basis CBOT aligné sur l'heure de settlement Euronext (réduction du bruit de désynchro).

V44/V46 : le basis quotidien EMA(settlement ~18:30 CET) − CBOT(close) souffre d'une désynchronisation horaire.
On teste l'ampleur de ce bruit en comparant le CBOT de CLÔTURE au CBOT À L'HEURE du settlement Euronext
(≈16:30 UTC l'été). Si le décalage CBOT close↔settle-time est significatif, une partie du bruit du basis est
ARTIFICIELLE et corrigeable en alignant les données (sans aucun modèle).

LIMITE HONNÊTE : l'intraday CBOT gratuit (Yahoo ZC=F) ne couvre que ~1–2 mois récents. On NE peut PAS
reconstruire le basis aligné sur 2014–2023. Ce module quantifie donc l'AMPLEUR du désalignement sur la
fenêtre récente (borne de bruit) et fournit le framework ; la validation historique reste data-gated
(WATCHLIST), à accumuler en forward.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché. Baseline figée inchangée.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR

V60I_DIR = ARTEFACTS_DIR / "v60_intraday"
V60I_DIR.mkdir(parents=True, exist_ok=True)
SETTLE_HOUR_UTC = 16  # ≈ 18:30 CET (settlement Euronext, été) -> barre horaire la plus proche


def align_gap_stats(intraday: pd.DataFrame, settle_hour_utc: int = SETTLE_HOUR_UTC) -> dict[str, Any]:
    """intraday : index datetime UTC, colonne 'close'. Compare CBOT(close du jour) vs CBOT(heure settle)."""
    if intraday is None or len(intraday) == 0 or "close" not in intraday.columns:
        return {"verdict": "NO_INTRADAY"}
    s = intraday["close"].dropna()
    if len(s) < 30:
        return {"verdict": "TOO_FEW_BARS", "n": int(len(s))}
    idx = pd.to_datetime(s.index, utc=True)
    s = pd.Series(s.to_numpy(), index=idx)
    day = s.index.date
    frame = pd.DataFrame({"close": s.to_numpy(), "hour": s.index.hour, "day": day})
    rows = []
    for d, g in frame.groupby("day"):
        last = g.iloc[-1]["close"]  # clôture du jour (dernière barre)
        at = g[g["hour"] <= settle_hour_utc]
        settle_val = at.iloc[-1]["close"] if len(at) else np.nan
        if not np.isnan(settle_val) and last:
            rows.append({"day": str(d), "close": float(last), "at_settle": float(settle_val),
                         "rel_gap": float(last / settle_val - 1.0)})
    if len(rows) < 20:
        return {"verdict": "TOO_FEW_DAYS", "n": int(len(rows))}
    gd = pd.DataFrame(rows)
    rel = gd["rel_gap"]
    return {
        "verdict": "ALIGNMENT_GAP_MEASURED",
        "n_days": int(len(gd)),
        "settle_hour_utc": settle_hour_utc,
        "mean_rel_gap": round(float(rel.mean()), 5),
        "mean_abs_rel_gap": round(float(rel.abs().mean()), 5),
        "std_rel_gap": round(float(rel.std()), 5),
        "approx_eur_t_noise_at_200": round(float(rel.abs().mean() * 200.0), 3),
    }


def fetch_cbot_intraday(try_network: bool = True, interval: str = "60m", rng: str = "1mo") -> pd.DataFrame:
    """Intraday ZC=F via Yahoo (UTC). Lève/retourne vide proprement si pas de réseau."""
    if not try_network:
        return pd.DataFrame()
    import urllib.request
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/ZC=F?interval={interval}&range={rng}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        res = d["chart"]["result"][0]
        ts = res["timestamp"]
        close = res["indicators"]["quote"][0]["close"]
        idx = pd.to_datetime(ts, unit="s", utc=True)
        return pd.DataFrame({"close": close}, index=idx).dropna()
    except Exception:  # noqa: BLE001
        return pd.DataFrame()


def run_v60_intraday(try_network: bool = True) -> dict[str, Any]:
    intraday = fetch_cbot_intraday(try_network=try_network)
    stats = align_gap_stats(intraday)
    if stats.get("verdict") != "ALIGNMENT_GAP_MEASURED":
        out = {"version": "V60-INTRADAY-BASIS", "probe": stats,
               "verdict": "WATCHLIST_DATA_GATED",
               "note": "Intraday CBOT gratuit indisponible/insuffisant ; framework prêt, à accumuler forward.",
               "status": "RESEARCH_ONLY_NOT_TRADING"}
    else:
        material = stats["mean_abs_rel_gap"] >= 0.002  # >0.2% => désalignement matériel
        out = {
            "version": "V60-INTRADAY-BASIS",
            "probe": stats,
            "alignment_material": bool(material),
            "verdict": ("ALIGNMENT_MATERIAL_WATCHLIST_HISTORICAL_GATED" if material
                        else "ALIGNMENT_SMALL_ON_RECENT_WINDOW"),
            "interpretation": (
                f"Sur {stats['n_days']} jours récents, écart moyen |CBOT close − CBOT settle-time| = "
                f"{stats['mean_abs_rel_gap']:.3%} (~{stats['approx_eur_t_noise_at_200']} €/t à 200 €/t). "
                "C'est une borne du bruit de désynchro intégré au basis quotidien. L'historique intraday "
                "n'étant pas disponible gratuitement, la reconstruction du basis aligné 2014+ reste data-gated "
                "(WATCHLIST) ; on accumule en forward et on mesurera l'effet sur demi-vie/ADVERSE quand "
                "l'échantillon sera suffisant."),
            "note": "Borne de bruit sur fenêtre récente (Yahoo ~1 mois). Pas de backtest historique possible.",
            "status": "RESEARCH_ONLY_NOT_TRADING",
        }
    (V60I_DIR / "v60_intraday.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
