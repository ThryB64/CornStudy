"""V79 — Régime climatique ENSO (El Niño / La Niña) → CBOT et basis EMA/CBOT.

Extension CLIMAT de V51 : la météo quotidienne est anticipée, mais ENSO est un régime LENT et persistant
(plusieurs mois) potentiellement moins entièrement pricé à long horizon. La Niña (ONI < −0.5) est liée à des
sécheresses US/Amérique du Sud (haussier maïs), El Niño plutôt à l'inverse. On teste si le régime ENSO connu
à J (anti-leakage : décalé de 2 mois pour la centralisation + publication) précède des rendements CBOT
multi-horizons, et s'il touche le basis (attendu non : prime locale).

Source : NOAA CPC ONI (fichier ASCII, rapide). Anti-leakage : ONI centré ≥2 mois avant, ffill, shift(1) j.
Descriptif, aucun fit, baseline figée inchangée. `RESEARCH_ONLY_NOT_TRADING`. Holdout verrouillé.
"""
from __future__ import annotations

import io
import json
import urllib.request
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.registry.holdout_lock import assert_no_holdout

V79_DIR = ARTEFACTS_DIR / "v79"
V79_DIR.mkdir(parents=True, exist_ok=True)
ONI_ASCII = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
SEASON_TO_MONTH = {s: i + 1 for i, s in enumerate(
    ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"])}
PUB_LAG_MONTHS = 2  # centralisation 3 mois + publication -> connu ~2 mois après le mois central


def fetch_oni(try_network: bool = True, timeout: int = 30) -> pd.DataFrame:
    """ONI mensuel (Date centrée, anomalie). Vide proprement si pas de réseau."""
    if not try_network:
        return pd.DataFrame()
    try:
        req = urllib.request.Request(ONI_ASCII, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            txt = r.read().decode("utf-8", errors="replace")
        raw = pd.read_csv(io.StringIO(txt), sep=r"\s+")
    except Exception:  # noqa: BLE001
        return pd.DataFrame()
    if not {"SEAS", "YR", "ANOM"}.issubset(raw.columns):
        return pd.DataFrame()
    rows = []
    for _, r in raw.iterrows():
        m = SEASON_TO_MONTH.get(str(r["SEAS"]).strip())
        yr = pd.to_numeric(r["YR"], errors="coerce")
        anom = pd.to_numeric(r["ANOM"], errors="coerce")
        if m and not pd.isna(yr) and not pd.isna(anom):
            rows.append({"Date": pd.Timestamp(int(yr), m, 1), "oni": float(anom)})
    return pd.DataFrame(rows).sort_values("Date").reset_index(drop=True)


def enso_features(index: pd.DatetimeIndex, oni: pd.DataFrame) -> pd.DataFrame:
    """Features ENSO causales alignées sur index (régime, lag, accumulation), anti-leakage 2 mois + shift(1)."""
    if oni is None or len(oni) == 0:
        return pd.DataFrame(index=index)
    o = oni.copy()
    # décalage de publication/centralisation : la valeur centrée au mois M n'est connue que ~2 mois après
    o["known_date"] = o["Date"] + pd.DateOffset(months=PUB_LAG_MONTHS)
    o = o.sort_values("known_date")
    base = pd.DataFrame({"known_date": index}).sort_values("known_date")
    merged = pd.merge_asof(base, o[["known_date", "oni"]], on="known_date", direction="backward")
    merged.index = index
    oni_s = merged["oni"]
    regime = np.where(oni_s >= 0.5, "EL_NINO", np.where(oni_s <= -0.5, "LA_NINA", "NEUTRAL"))
    out = pd.DataFrame({
        "oni": oni_s,
        "enso_regime": regime,
        "la_nina_flag": (oni_s <= -0.5).astype(int),
        "el_nino_flag": (oni_s >= 0.5).astype(int),
    }, index=index)
    return out.shift(1)  # sécurité anti-leakage supplémentaire (1 jour)


def run_v79_enso(df: pd.DataFrame, try_network: bool = True) -> dict[str, Any]:
    assert_no_holdout(df)
    oni = fetch_oni(try_network=try_network)
    feats = enso_features(df.index, oni)
    if "oni" not in feats.columns or feats["oni"].notna().sum() < 500:
        return {"version": "V79-ENSO-REGIME", "verdict": "NO_DATA_ENSO"}

    cbot = pd.to_numeric(df.get("cbot_eur_t"), errors="coerce")
    oni_s = feats["oni"]
    regime = feats["enso_regime"]

    # 1) ONI connu à J vs rendement CBOT forward multi-horizon (La Niña haussier -> corr NÉGATIVE attendue)
    fwd = {}
    for h in (20, 60, 120):
        r = cbot.shift(-h) / cbot - 1.0
        m = oni_s.notna() & r.notna()
        if m.sum() > 300 and oni_s[m].std() > 0:
            fwd[h] = round(float(np.corrcoef(oni_s[m], r[m])[0, 1]), 3)

    # 2) rendement CBOT forward 60j par régime
    r60 = cbot.shift(-60) / cbot - 1.0
    by_regime = {}
    for g in ("LA_NINA", "NEUTRAL", "EL_NINO"):
        mm = (regime == g) & r60.notna()
        if mm.sum() > 60:
            by_regime[g] = {"n_days": int(mm.sum()), "mean_fwd_ret_60d": round(float(r60[mm].mean()), 4)}

    # 3) basis par régime (attendu : peu de lien -> prime locale)
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce")
    basis_by_regime = {}
    for g in ("LA_NINA", "NEUTRAL", "EL_NINO"):
        mm = (regime == g) & basis.notna()
        if mm.sum() > 60:
            basis_by_regime[g] = round(float(basis[mm].mean()), 2)

    la = by_regime.get("LA_NINA", {}).get("mean_fwd_ret_60d")
    el = by_regime.get("EL_NINO", {}).get("mean_fwd_ret_60d")
    la_nina_bullish = bool(la is not None and el is not None and la > el)
    best_abs_corr = max((abs(v) for v in fwd.values()), default=0.0)
    material = best_abs_corr >= 0.1

    # ROBUSTESSE : la La Niña 2020-2022 chevauche le bull COVID/Ukraine -> confond majeur.
    # On recalcule le lien HORS années de crise (2020-2022).
    crisis = pd.Series(np.isin(df.index.year, (2020, 2021, 2022)), index=df.index)
    la_mask = (regime == "LA_NINA") & r60.notna() & (~crisis)
    el_mask = (regime == "EL_NINO") & r60.notna() & (~crisis)
    la_excl = round(float(r60[la_mask].mean()), 4) if la_mask.sum() > 40 else None
    el_excl = round(float(r60[el_mask].mean()), 4) if el_mask.sum() > 40 else None
    robust_ex_crisis = bool(la_excl is not None and el_excl is not None and la_excl > el_excl)
    confounded = bool(la_nina_bullish and not robust_ex_crisis)

    if la_nina_bullish and material and robust_ex_crisis:
        verdict = "ENSO_LA_NINA_BULLISH_ROBUST_EX_CRISIS_WATCHLIST"
    elif confounded:
        verdict = "ENSO_LA_NINA_SIGNAL_CONFOUNDED_BY_2020_2022_BULL"
    elif material:
        verdict = "ENSO_WEAK_DIRECTIONAL_LINK_WATCHLIST"
    else:
        verdict = "ENSO_LARGELY_PRICED_NO_ROBUST_EDGE"

    out = {
        "version": "V79-ENSO-REGIME",
        "n_days": int(oni_s.notna().sum()),
        "corr_oni_vs_fwd_cbot": fwd,
        "cbot_fwd60_by_regime": by_regime,
        "basis_by_regime": basis_by_regime,
        "la_nina_more_bullish_than_el_nino": la_nina_bullish,
        "cbot_fwd60_la_nina_ex_crisis": la_excl,
        "cbot_fwd60_el_nino_ex_crisis": el_excl,
        "robust_excluding_2020_2022": robust_ex_crisis,
        "confounded_by_crisis": confounded,
        "verdict": verdict,
        "interpretation": (
            f"corr(ONI connu à J, rendement CBOT) = {fwd} (négatif attendu : La Niña = ONI bas = haussier). "
            f"Rendement CBOT 60j La Niña {la} vs El Niño {el}. MAIS la La Niña 2020-2022 chevauche le bull "
            f"COVID/Ukraine : HORS crise, La Niña {la_excl} vs El Niño {el_excl} -> robuste={robust_ex_crisis}. "
            "Si le lien s'effondre hors crise, c'est un CONFOND, pas un edge climatique. ENSO est lent et "
            "forecastable (donc en partie pricé) ; au mieux un CONTEXTE macro-climatique, jamais un veto. Le "
            "basis par régime confirme que l'effet (s'il existe) passe par le CBOT mondial, pas la prime EU."),
        "caveat": "ONI décalé 2 mois + shift(1) (anti-leakage). Régime persistant -> peu d'épisodes "
                  "indépendants (~12), puissance effective ≪ n_days. Confond crise majeur. Descriptif, aucun fit.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V79_DIR / "v79_enso.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
