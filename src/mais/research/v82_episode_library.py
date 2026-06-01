"""V82 — Bibliothèque des épisodes de basis haut : les 42 trades vus comme ÉPISODES de marché complets.

On ne regarde plus les signaux comme des lignes de backtest, mais comme des épisodes documentés : dates clés
(entrée, pic de basis, sortie z→0.5, z→0), MFE/MAE, canal (V70), et tout le contexte d'entrée (tier,
ratio blé/maïs, CBOT_SUPPORT, ADVERSE_RISK, ENSO, production FR/UE, roll, crise) + une raison probable.
Objectif : comprendre les FAMILLES d'épisodes. Descriptif, baseline figée, aucun fit.

Statut : RESEARCH_ONLY_NOT_TRADING. Holdout 2024 jamais touché.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT
from mais.registry.holdout_lock import assert_no_holdout

V82_DIR = ARTEFACTS_DIR / "v82"
V82_DIR.mkdir(parents=True, exist_ok=True)
EPISODES_PARQUET = ROOT / "data" / "research" / "high_basis_episodes.parquet"
LIBRARY_MD = ROOT / "docs" / "HIGH_BASIS_EPISODE_LIBRARY.md"
MAX_HOLD = 90


def _rel(p) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def _episode_path_detail(df: pd.DataFrame, entry_date: str) -> dict[str, Any]:
    """MFE, date de pic de basis, dates d'atteinte z→0.5 / z→0 à partir de l'entrée."""
    ema = pd.to_numeric(df["ema_close"], errors="coerce").to_numpy()
    cbot = pd.to_numeric(df["cbot_eur_t"], errors="coerce").to_numpy()
    bz = pd.to_numeric(df["ema_cbot_basis_zscore_52w"], errors="coerce").to_numpy()
    basis = pd.to_numeric(df.get("ema_cbot_basis"), errors="coerce").to_numpy()
    dates = df.index
    d = pd.Timestamp(entry_date)
    if d not in df.index:
        return {}
    i = df.index.get_loc(d)
    e0, c0 = ema[i], cbot[i]
    mfe, peak_basis, peak_date = 0.0, basis[i] if not np.isnan(basis[i]) else -1e9, None
    z05_date, z0_date = None, None
    for t in range(1, MAX_HOLD + 1):
        j = i + t
        if j >= len(ema) or np.isnan(ema[j]) or np.isnan(cbot[j]):
            continue
        pnl = -1.0 * ((ema[j] / e0 - 1) - (cbot[j] / c0 - 1)) * e0
        mfe = max(mfe, pnl)
        if not np.isnan(basis[j]) and basis[j] > peak_basis:
            peak_basis, peak_date = basis[j], dates[j]
        if z05_date is None and not np.isnan(bz[j]) and bz[j] <= 0.5:
            z05_date = dates[j]
        if z0_date is None and not np.isnan(bz[j]) and bz[j] <= 0.0:
            z0_date = dates[j]
    return {
        "mfe": round(float(mfe), 2),
        "peak_basis_date": str(peak_date.date()) if peak_date is not None else None,
        "exit_z05_date": str(z05_date.date()) if z05_date is not None else None,
        "exit_z0_date": str(z0_date.date()) if z0_date is not None else None,
    }


def _safe_series(fn, df, col):
    try:
        return fn(df)[col]
    except Exception:  # noqa: BLE001
        return pd.Series(np.nan, index=df.index)


def _probable_reason(row) -> str:
    r = []
    if row.get("path") == "ADVERSE":
        if row.get("cbot_support") == "LOW":
            r.append("échec : CBOT non porteur")
        if float(row.get("entry_z", 99)) < 1.5:
            r.append("échec : prime seulement modérée")
        if int(row.get("roll_month", 0)) == 1:
            r.append("échec : mois de roll")
        return " ; ".join(r) if r else "échec : indéterminé"
    if row.get("path") == "CBOT_DRIVEN":
        return "compression par rattrapage CBOT"
    if row.get("path") == "EMA_DRIVEN":
        return "compression par repli EMA"
    return "compression mixte"


def build_episodes(df: pd.DataFrame, with_network: bool = True) -> pd.DataFrame:
    from mais.research.v17_research_indicator import build_trades_detailed
    from mais.research.v32_adverse_path_research import build_adverse_frame
    from mais.research.v38_adverse_risk import _wheat_corn_ratio_z, compute_adverse_risk
    from mais.research.v41_cbot_support import compute_cbot_support

    t = build_trades_detailed(df)
    if len(t) == 0:
        return t
    adv = build_adverse_frame(df)
    if len(adv):
        t = t.merge(adv[["entry_date", "path", "adverse"]], on="entry_date", how="left")

    entry = pd.to_datetime(t["entry_date"])
    t["cbot_support"] = compute_cbot_support(df)["cbot_support"].reindex(entry).to_numpy()
    t["adverse_risk"] = compute_adverse_risk(df)["adverse_risk"].reindex(entry).to_numpy()
    t["wheat_corn_z"] = _wheat_corn_ratio_z(df).reindex(entry).to_numpy()

    # production EU / FR (annuel, lag1) — optionnel réseau
    if with_network:
        prod_eu = _safe_series(lambda d: __import__(
            "mais.research.v71_eu_production_balance", fromlist=["_eu_production_aligned"]
        )._eu_production_aligned(d.index), df, "ec_mars_prod_anomaly_eu_lag1")
        t["eu_prod_anomaly"] = pd.to_numeric(prod_eu, errors="coerce").reindex(entry).to_numpy()
        # ENSO
        try:
            from mais.research.v79_enso_regime import enso_features, fetch_oni
            ef = enso_features(df.index, fetch_oni(try_network=True))
            t["enso_regime"] = ef["enso_regime"].reindex(entry).to_numpy() if "enso_regime" in ef else None
        except Exception:  # noqa: BLE001
            t["enso_regime"] = None
    else:
        t["eu_prod_anomaly"] = np.nan
        t["enso_regime"] = None

    # détails de chemin par épisode
    det = t["entry_date"].apply(lambda d: _episode_path_detail(df, d)).apply(pd.Series)
    t = pd.concat([t, det], axis=1)
    t["probable_reason"] = t.apply(_probable_reason, axis=1)
    return t


def run_v82_episodes(df: pd.DataFrame, with_network: bool = True) -> dict[str, Any]:
    assert_no_holdout(df)
    ep = build_episodes(df, with_network=with_network)
    if len(ep) < 15:
        return {"version": "V82-EPISODE-LIBRARY", "verdict": "TOO_FEW", "n": int(len(ep))}

    EPISODES_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    ep.to_parquet(EPISODES_PARQUET, index=False)

    by_path = ep["path"].value_counts().to_dict() if "path" in ep else {}
    families = {}
    for p in ("CBOT_DRIVEN", "EMA_DRIVEN", "BOTH", "ADVERSE"):
        sub = ep[ep["path"] == p] if "path" in ep else ep.iloc[0:0]
        if len(sub):
            families[p] = {
                "n": int(len(sub)),
                "mean_pnl": round(float(sub["pnl_z0_max90_sl20"].mean()), 2),
                "mean_mfe": round(float(sub["mfe"].mean()), 2) if "mfe" in sub else None,
                "mean_duration": round(float(sub["duration_days"].mean()), 1),
                "win_rate": round(float(sub["win"].mean()), 3),
                "dominant_cbot_support": (sub["cbot_support"].mode().iloc[0]
                                          if sub["cbot_support"].notna().any() else None),
            }

    # rédige une bibliothèque markdown lisible
    lines = ["# Bibliothèque des épisodes de basis haut (V82)",
             "", "Les 42 signaux short-premium vus comme ÉPISODES de marché. Descriptif, anti-leakage, "
             "baseline figée. `RESEARCH_ONLY_NOT_TRADING`.", "",
             f"{len(ep)} épisodes. Répartition par canal : {by_path}.", "",
             "## Familles d'épisodes (par canal de compression)", ""]
    for p, b in families.items():
        lines.append(f"- **{p}** : n={b['n']}, win={b['win_rate']}, PnL={b['mean_pnl']}, MFE={b['mean_mfe']}, "
                     f"durée={b['mean_duration']} j, CBOT_SUPPORT dominant={b['dominant_cbot_support']}")
    lines += ["", "## Épisodes (extrait)", "",
              "| entrée | tier | z | path | CBOT_SUP | ADV_RISK | ENSO | durée | MFE | PnL | raison |",
              "|---|---|---:|---|---|---|---|---:|---:|---:|---|"]
    for _, e in ep.sort_values("entry_date").iterrows():
        lines.append(
            f"| {e['entry_date']} | {e.get('tier')} | {round(float(e['entry_z']),2)} | {e.get('path')} | "
            f"{e.get('cbot_support')} | {e.get('adverse_risk')} | {e.get('enso_regime')} | "
            f"{int(e['duration_days'])} | {e.get('mfe')} | {round(float(e['pnl_z0_max90_sl20']),1)} | "
            f"{e['probable_reason']} |")
    LIBRARY_MD.write_text("\n".join(lines), encoding="utf-8")

    out = {
        "version": "V82-EPISODE-LIBRARY",
        "n_episodes": int(len(ep)),
        "by_path": by_path,
        "families": families,
        "episodes_parquet": _rel(EPISODES_PARQUET),
        "library_md": _rel(LIBRARY_MD),
        "verdict": "EPISODE_LIBRARY_BUILT",
        "interpretation": (
            "Les épisodes se regroupent par canal : CBOT_DRIVEN (rattrapage, les plus profitables), EMA_DRIVEN "
            "(repli EMA), BOTH, et ADVERSE (échecs, CBOT non porteur / prime modérée). La bibliothèque sert de "
            "base à l'analyse qualitative et au choix d'objectif/horizon — pas un backtest réoptimisé."),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V82_DIR / "v82_episodes.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
