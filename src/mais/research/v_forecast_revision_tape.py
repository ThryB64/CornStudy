"""VN-C4 — Forecast revision tape : la RÉVISION de prévision, pas le niveau moyen.

V45 a montré que le stress RÉALISÉ ne prédit pas le CBOT. Le vrai signal candidat est la RÉVISION : entre
deux émissions successives, de combien le nombre de jours >32°C (lead 3) ou le cumul de pluie a-t-il bougé ?
On construit ici la série de révisions à partir du journal des émissions successives (V127, append-only), par
région. Le backfill HISTORIQUE multi-lead passe par l'Open-Meteo Previous-Runs API (séries lead-fixe 1-7 j
depuis 2024) — best-effort, documenté ; tant qu'il n'est pas collecté, la tape vit en FORWARD.

Anti-leakage : chaque révision est datée de l'émission courante (Δ vs émission précédente), jamais réindexée.
Lecture seule du journal. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V_DIR = ARTEFACTS_DIR / "forecast_revision_tape"
V_DIR.mkdir(parents=True, exist_ok=True)
WX_JOURNAL = ROOT / "data" / "official_forward" / "weather_extremes_journal.jsonl"
TAPE = ROOT / "data" / "official_forward" / "forecast_revision_tape.parquet"


def _load_emissions(region: str) -> pd.DataFrame:
    if not WX_JOURNAL.exists():
        return pd.DataFrame()
    recs = []
    for ln in WX_JOURNAL.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("region") == region and d.get("status") == "OK":
            recs.append(d)
    if not recs:
        return pd.DataFrame()
    df = pd.DataFrame(recs).drop_duplicates(subset="issue_date", keep="last")
    return df.sort_values("issue_date").reset_index(drop=True)


def build_revision_tape(region: str = "us") -> pd.DataFrame:
    em = _load_emissions(region)
    if len(em) < 2:
        return pd.DataFrame()
    for c in ("heat_days_gt32", "heat_days_gt35", "precip_total_mm", "stress_score"):
        if c not in em.columns:
            em[c] = pd.NA
    em["d_heat32"] = pd.to_numeric(em["heat_days_gt32"], errors="coerce").diff()
    em["d_heat35"] = pd.to_numeric(em["heat_days_gt35"], errors="coerce").diff()
    em["d_precip"] = pd.to_numeric(em["precip_total_mm"], errors="coerce").diff()
    em["d_score"] = pd.to_numeric(em["stress_score"], errors="coerce").diff()
    em["region"] = region
    return em.dropna(subset=["d_score"]).reset_index(drop=True)


def run_v_revision_tape() -> dict[str, Any]:
    tapes = {r: build_revision_tape(r) for r in ("us", "eu")}
    frames = [t for t in tapes.values() if len(t)]
    n = sum(len(t) for t in frames)
    if n == 0:
        return {"version": "FORECAST-REVISION-TAPE", "verdict": "FORWARD_ONLY_ACCUMULATING",
                "n_revisions": 0,
                "note": "Au moins 2 émissions par région requises (V127 s'accumule). Backfill historique "
                        "multi-lead = Open-Meteo Previous-Runs (best-effort, à collecter).",
                "status": "RESEARCH_ONLY_NOT_TRADING"}
    allt = pd.concat(frames, ignore_index=True)
    TAPE.parent.mkdir(parents=True, exist_ok=True)
    allt.to_parquet(TAPE, index=False)
    last = {r: (None if len(t) == 0 else {"issue_date": str(t["issue_date"].iloc[-1]),
                                          "d_heat32": float(t["d_heat32"].iloc[-1]),
                                          "d_score": float(t["d_score"].iloc[-1])})
            for r, t in tapes.items()}
    out = {
        "version": "FORECAST-REVISION-TAPE",
        "verdict": "REVISION_TAPE_READY",
        "n_revisions": int(n),
        "by_region_last": last,
        "interpretation": (
            f"{n} révisions inter-émissions journalisées. La révision (Δ jours>32°C, Δscore) est le signal "
            "candidat LEADING (vs le niveau réalisé, price-in selon V45). Relation révision→CBOT à tester "
            "quand la tape sera assez longue (forward). Backfill historique = Previous-Runs API."),
        "note": "Construit depuis le journal d'émissions V127 (append-only). Anti-leakage par construction.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V_DIR / "forecast_revision_tape.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
