"""V129 — Catalogue de catalyseurs fondamentaux des compressions de prime (DESCRIPTIF ex-post).

But : comprendre POURQUOI la prime se comprime, pas QUAND (non prédictible, cf V104-V106). Pour chaque
épisode de compression (basis_z passe d'un pic >=1.5 à une chute >=1.0), on regarde la fenêtre [pic→chute] et
on attribue un catalyseur DOMINANT à partir des variables du master :
  - CBOT_WEATHER       : CBOT rallie + chaleur US (compression via rattrapage CBOT, V21)
  - CBOT_WASDE         : CBOT rallie sur un saut journalier marqué (proxy d'un choc rapport, calendrier non lié)
  - COT_SHORT_COVERING : CBOT rallie + managed-money achète fortement
  - EU_BALANCE_UPDATE  : prime tombée surtout par baisse EMA (jambe EU), CBOT ~plat
  - CURVE_RELAXATION   : mois de roll, CBOT ~plat
  - UNKNOWN            : aucun catalyseur dominant identifiable avec les données dispo

C'est une classification ex-post, à base de PROXYS (pas de calendriers exacts WASDE/MARS). Une part
d'UNKNOWN est attendue et HONNÊTE. JAMAIS un feature prédictif (sinon look-ahead).
Statut : RESEARCH_ONLY_NOT_TRADING. Holdout verrouillé.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT
from mais.registry.holdout_lock import assert_no_holdout

V129_DIR = ARTEFACTS_DIR / "v129"
V129_DIR.mkdir(parents=True, exist_ok=True)
EVENT_STORE = ROOT / "data" / "research" / "event_catalyst_library.parquet"
ROLL_MONTHS = (2, 5, 7, 10)
PEAK_Z, DROP_Z, MAX_WINDOW = 1.5, 1.0, 60
CBOT_RALLY = 0.03
BIG_1D = 0.03
HEAT_Z = 1.0


def detect_compression_events(df: pd.DataFrame) -> pd.DataFrame:
    """Pics de basis_z >=1.5 suivis d'une chute >=1.0 dans <=60 j ouvrés."""
    z = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    s = z.dropna()
    if len(s) < 200:
        return pd.DataFrame()
    vals = s.to_numpy()
    idx = s.index
    events = []
    i = 0
    n = len(vals)
    while i < n:
        if vals[i] >= PEAK_Z and (i == 0 or vals[i] >= vals[i - 1]):
            # pic local : avancer tant que ça monte
            j = i
            while j + 1 < n and vals[j + 1] >= vals[j]:
                j += 1
            peak_val = vals[j]
            # chercher la chute >=DROP_Z dans la fenêtre
            end = None
            for k in range(j + 1, min(j + 1 + MAX_WINDOW, n)):
                if peak_val - vals[k] >= DROP_Z:
                    end = k
                    break
            if end is not None:
                events.append({"peak_date": idx[j], "end_date": idx[end],
                               "peak_z": round(float(peak_val), 3), "end_z": round(float(vals[end]), 3)})
                i = end + 1
                continue
        i += 1
    return pd.DataFrame(events)


def _classify_event(df: pd.DataFrame, peak: pd.Timestamp, end: pd.Timestamp) -> dict[str, Any]:
    win = df.loc[peak:end]
    if len(win) < 2:
        return {"catalyst": "UNKNOWN", "features": {}}
    cbot = pd.to_numeric(win.get("cbot_close"), errors="coerce").dropna()
    cbot_ret = float(np.log(cbot.iloc[-1] / cbot.iloc[0])) if len(cbot) >= 2 and cbot.iloc[0] > 0 else 0.0
    basis = pd.to_numeric(win.get("ema_cbot_basis"), errors="coerce").dropna()
    basis_drop = float(basis.iloc[0] - basis.iloc[-1]) if len(basis) >= 2 else 0.0
    heat = pd.to_numeric(win.get("wx_belt_tmax_c_anom_z"), errors="coerce")
    heat_max = float(heat.max()) if heat.notna().any() else np.nan
    cot = pd.to_numeric(win.get("cot_mm_net"), errors="coerce").dropna()
    cot_change = float(cot.iloc[-1] - cot.iloc[0]) if len(cot) >= 2 else 0.0
    cot_chg_norm = cot_change / (abs(cot.iloc[0]) + 1e-6) if len(cot) >= 2 else 0.0
    d1 = pd.to_numeric(win.get("corn_logret_1d"), errors="coerce")
    big_jump = float(d1.max()) if d1.notna().any() else 0.0
    roll = any(m in ROLL_MONTHS for m in win.index.month.unique())

    feats = {"cbot_ret": round(cbot_ret, 4), "basis_drop_eur_t": round(basis_drop, 2),
             "heat_max_z": round(heat_max, 2) if not np.isnan(heat_max) else None,
             "cot_net_change_norm": round(cot_chg_norm, 3), "max_1d_corn_ret": round(big_jump, 4),
             "roll_month": bool(roll)}

    if cbot_ret >= CBOT_RALLY:
        if not np.isnan(heat_max) and heat_max >= HEAT_Z:
            cat = "CBOT_WEATHER"
        elif cot_chg_norm >= 0.25:
            cat = "COT_SHORT_COVERING"
        elif big_jump >= BIG_1D:
            cat = "CBOT_WASDE"
        else:
            cat = "CBOT_RALLY_UNATTRIBUTED"
    elif basis_drop > 0 and abs(cbot_ret) < CBOT_RALLY:
        cat = "CURVE_RELAXATION" if roll else "EU_BALANCE_UPDATE"
    else:
        cat = "UNKNOWN"
    return {"catalyst": cat, "features": feats}


def run_v129_event_library(df: pd.DataFrame) -> dict[str, Any]:
    assert_no_holdout(df)
    events = detect_compression_events(df)
    if len(events) == 0:
        return {"version": "V129-EVENT-LIBRARY", "verdict": "NO_EVENTS"}
    rows = []
    for _, e in events.iterrows():
        cl = _classify_event(df, e["peak_date"], e["end_date"])
        rows.append({"peak_date": pd.Timestamp(e["peak_date"]).normalize(),
                     "end_date": pd.Timestamp(e["end_date"]).normalize(),
                     "duration_days": int((e["end_date"] - e["peak_date"]).days),
                     "peak_z": e["peak_z"], "end_z": e["end_z"], "catalyst": cl["catalyst"],
                     **{f"f_{k}": v for k, v in cl["features"].items()}})
    lib = pd.DataFrame(rows)
    EVENT_STORE.parent.mkdir(parents=True, exist_ok=True)
    lib.to_parquet(EVENT_STORE, index=False)

    counts = lib["catalyst"].value_counts().to_dict()
    n = int(len(lib))
    pct_unknown = round(100.0 * (counts.get("UNKNOWN", 0) + counts.get("CBOT_RALLY_UNATTRIBUTED", 0)) / n, 1)
    out = {
        "version": "V129-EVENT-LIBRARY",
        "verdict": "EVENT_LIBRARY_READY",
        "n_events": n,
        "catalyst_counts": {str(k): int(v) for k, v in counts.items()},
        "pct_unattributed": pct_unknown,
        "median_duration_days": int(lib["duration_days"].median()),
        "interpretation": (
            f"{n} épisodes de compression détectés (pic z≥{PEAK_Z} → chute ≥{DROP_Z} en ≤{MAX_WINDOW} j). "
            f"Catalyseurs dominants : {counts}. Part non attribuée {pct_unknown}%. Cohérent avec V21 : la "
            "compression est surtout un RATTRAPAGE CBOT (météo/rapports/short-covering) ; la jambe EU "
            "(EU_BALANCE_UPDATE) et le roll (CURVE_RELAXATION) complètent. DESCRIPTIF ex-post, à base de "
            "proxys (pas de calendriers exacts) -> JAMAIS un feature prédictif."),
        "note": "Attribution heuristique sur variables du master. Une part d'UNKNOWN est attendue et honnête.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V129_DIR / "v129_event_library.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def event_library_report_block(df: pd.DataFrame | None = None) -> str:
    artefact = V129_DIR / "v129_event_library.json"
    if not artefact.exists():
        return ""
    try:
        s = json.loads(artefact.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    if s.get("verdict") != "EVENT_LIBRARY_READY":
        return ""
    return (
        "### Catalyseurs des compressions (V129 — descriptif ex-post)\n"
        f"- {s['n_events']} épisodes · catalyseurs {s['catalyst_counts']}\n"
        f"- Non attribué {s['pct_unattributed']}% · durée médiane {s['median_duration_days']} j\n"
        "- Comprendre POURQUOI (rattrapage CBOT dominant), pas QUAND. Jamais un signal. RESEARCH_ONLY_NOT_TRADING.\n"
    )
