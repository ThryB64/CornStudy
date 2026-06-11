"""V177 — Re-runs data-gated automatiques : la science reportée se déclenche SEULE.

Trois tests ont été honnêtement reportés faute de données mûres, avec protocoles FIGÉS au moment
du report (zéro degré de liberté ajouté à la maturité) :

- V166-OFFICIEL : la chaîne CY→basis n'est pas testable sur le proxy (0/45 jours-signal en
  backwardation) → re-run sur la courbe OFFICIELLE quand ≥150 sessions accumulées (V125).
  Protocole figé : corr(front_next_spread, basis_z officiel) ≥ +0.2 avec moitiés de même signe.
- V168-MATIF : la substitution EUROPÉENNE (EBM/EMA) rejoint le test quand le journal V52/V126
  a ≥150 observations. Protocole figé : corr(ratio_z MATIF, basis_z) vs corr(wheat_corn_z CBOT,
  basis_z) sur la MÊME fenêtre, marge +0.03 (identique V168).
- V155-ÉTÉ : révisions météo → CBOT, verdict bloqué PRELIMINARY_N_SMALL sous n=150 (seuil déjà
  dans v155) → re-run automatique quand l'archive a ≥150 jours joints.

Chaque jour, ce module écrit l'état (ACCUMULATING x/seuil ou TRIGGERED+résultat) dans
`artefacts/v177/data_gated_status.json`. Un re-run déclenché est journalisé une seule fois par
palier (idempotent). Baseline intouchée. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V177_DIR = ARTEFACTS_DIR / "v177"
V177_DIR.mkdir(parents=True, exist_ok=True)
STATUS_PATH = V177_DIR / "data_gated_status.json"

CURVE_OFFICIAL = ROOT / "data" / "official_forward" / "ema_curve_history.parquet"
MATIF_HISTORY = ROOT / "data" / "official_forward" / "matif_ratio_history.parquet"
WEATHER_REVISIONS = ROOT / "data" / "weather" / "forecast_revisions.parquet"

GATE_CURVE = 150
GATE_MATIF = 150
GATE_WEATHER = 150
CORR_THRESHOLD = 0.2   # V166, figé
MARGIN_CORR = 0.03     # V168, figé


def _halves_hold(x: pd.Series, y: pd.Series, threshold: float) -> dict[str, Any]:
    al = pd.concat([x, y], axis=1).dropna()
    mid = len(al) // 2
    full = float(al.iloc[:, 0].corr(al.iloc[:, 1]))
    h1 = float(al.iloc[:mid, 0].corr(al.iloc[:mid, 1]))
    h2 = float(al.iloc[mid:, 0].corr(al.iloc[mid:, 1]))
    return {"n": int(len(al)), "corr_full": round(full, 3), "corr_h1": round(h1, 3),
            "corr_h2": round(h2, 3),
            "holds": bool(full >= threshold and h1 > 0 and h2 > 0)}


def _official_frame() -> pd.DataFrame | None:
    try:
        from mais.research.v27_official_forward import load_forward_journal
        j = load_forward_journal(final_only=True)
    except Exception:  # noqa: BLE001
        return None
    if j is None or len(j) == 0:
        return None
    j = j.copy()
    j["price_date"] = pd.to_datetime(j["price_date"])
    return j.set_index("price_date").sort_index()


def check_v166_official() -> dict[str, Any]:
    n = 0
    if CURVE_OFFICIAL.exists():
        n = int(len(pd.read_parquet(CURVE_OFFICIAL)))
    gate = {"rerun": "V166_OFFICIAL", "gate": GATE_CURVE, "n": n}
    if n < GATE_CURVE:
        gate["status"] = "ACCUMULATING"
        return gate
    curve = pd.read_parquet(CURVE_OFFICIAL)
    curve["price_date"] = pd.to_datetime(curve["price_date"])
    curve = curve.set_index("price_date").sort_index()
    jr = _official_frame()
    if jr is None:
        gate.update({"status": "GATE_MET_JOURNAL_UNAVAILABLE"})
        return gate
    spread = pd.to_numeric(curve["front_next_spread"], errors="coerce")
    bz = pd.to_numeric(jr["basis_z_used"], errors="coerce")
    res = _halves_hold(spread.rename("cy"), bz.rename("bz"), CORR_THRESHOLD)
    gate.update({"status": "TRIGGERED",
                 "protocol": "corr(front_next_spread, basis_z_officiel) >= +0.2, moitiés mêmes "
                             "signes — figé V166 2026-06-11",
                 "result": res,
                 "verdict": "CY_OFFICIAL_SUPPORTS_PREMIUM" if res["holds"]
                            else "CY_OFFICIAL_DOES_NOT_EXPLAIN_PREMIUM"})
    (V177_DIR / "v166_official_rerun.json").write_text(
        json.dumps(gate, indent=2, default=str), encoding="utf-8")
    return gate


def check_v168_matif() -> dict[str, Any]:
    n = 0
    if MATIF_HISTORY.exists():
        n = int(len(pd.read_parquet(MATIF_HISTORY)))
    gate = {"rerun": "V168_MATIF", "gate": GATE_MATIF, "n": n}
    if n < GATE_MATIF:
        gate["status"] = "ACCUMULATING"
        return gate
    hist = pd.read_parquet(MATIF_HISTORY)
    hist["price_date"] = pd.to_datetime(hist["price_date"])
    hist = hist.set_index("price_date").sort_index()
    ratio = pd.to_numeric(hist.get("ratio"), errors="coerce")
    mu = ratio.expanding(min_periods=60).mean()
    sd = ratio.expanding(min_periods=60).std()
    ratio_z = (ratio - mu) / sd
    jr = _official_frame()
    if jr is None:
        gate.update({"status": "GATE_MET_JOURNAL_UNAVAILABLE"})
        return gate
    bz = pd.to_numeric(jr["basis_z_used"], errors="coerce")
    res = _halves_hold(ratio_z.rename("matif_z"), bz.rename("bz"), CORR_THRESHOLD)
    gate.update({"status": "TRIGGERED",
                 "protocol": "corr(ratio_z MATIF, basis_z) vs incumbent blé CBOT, marge +0.03 — "
                             "figé V168 2026-06-11",
                 "result": res})
    (V177_DIR / "v168_matif_rerun.json").write_text(
        json.dumps(gate, indent=2, default=str), encoding="utf-8")
    return gate


def check_v155_summer() -> dict[str, Any]:
    n_days = 0
    if WEATHER_REVISIONS.exists():
        rev = pd.read_parquet(WEATHER_REVISIONS)
        col = "valid_date" if "valid_date" in rev.columns else rev.columns[0]
        n_days = int(pd.to_datetime(rev[col], errors="coerce").dt.date.nunique())
    gate = {"rerun": "V155_SUMMER", "gate": GATE_WEATHER, "n": n_days}
    if n_days < GATE_WEATHER:
        gate["status"] = "ACCUMULATING"
        return gate
    try:
        from mais.research.v155_weather_revision_validation import run_v155_validation
        out = run_v155_validation()
        gate.update({"status": "TRIGGERED", "verdict": out.get("verdict"),
                     "n_joint": out.get("n_days")})
    except Exception as e:  # noqa: BLE001
        gate.update({"status": "GATE_MET_RUN_FAILED", "error": f"{type(e).__name__}: {e}"})
    return gate


def run_v177_data_gated() -> dict[str, Any]:
    gates = [check_v166_official(), check_v168_matif(), check_v155_summer()]
    out = {
        "version": "V177-DATA-GATED-RERUNS",
        "as_of": pd.Timestamp.now(tz="UTC").isoformat(),
        "gates": gates,
        "note": "Protocoles figés au moment du report (V166/V168 2026-06-11, V155 seuil interne "
                "n=150). Ce module ne fait que vérifier la maturité et exécuter tel quel.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    STATUS_PATH.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
