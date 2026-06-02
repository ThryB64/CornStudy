"""V123 — Gate de fraîcheur et cohérence temporelle du contexte.

Le rapport empile des couches (signal, CBOT, courbe EMA, ratio MATIF, météo, COT) collectées à des dates
différentes. Une couche périmée ne doit pas être présentée comme fraîche. On lit le `as_of` de chaque couche
(artefacts/journaux déjà écrits par les collecteurs), on calcule le retard vs le signal officiel, et si une
couche dépasse le gate (5 jours), on la marque DISABLED (à ne pas afficher comme diagnostic frais).

Lecture seule, aucune donnée recalculée. Méta-information de fraîcheur, jamais un veto.
Statut : RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V123_DIR = ARTEFACTS_DIR / "v123"
V123_DIR.mkdir(parents=True, exist_ok=True)
JOURNAL_PARQUET = ROOT / "data" / "forward_journal" / "official_forward_journal.parquet"
MATIF_JOURNAL = ROOT / "data" / "official_forward" / "matif_ratio_journal.jsonl"
WEATHER_JOURNAL = ROOT / "data" / "official_forward" / "weather_forecast_journal.jsonl"
V107_ARTEFACT = ARTEFACTS_DIR / "v107" / "v107_context_refresh.json"
V109_ARTEFACT = ARTEFACTS_DIR / "v109" / "v109_curve_tension.json"
FRESHNESS_GATE_DAYS = 5
# gate par couche : le COT est hebdomadaire (Tuesday-of-record publié vendredi) -> ~7-10 j est normal.
LAYER_GATES = {"cbot": 5, "ema_curve": 5, "matif_ratio": 5, "weather": 5, "cot": 10}


def _read_json(path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _last_jsonl(path, key: str) -> str | None:
    if not path.exists():
        return None
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    for ln in reversed(lines):
        try:
            v = json.loads(ln).get(key)
        except ValueError:
            continue
        if v:
            return str(v)
    return None


def _signal_as_of() -> str | None:
    if not JOURNAL_PARQUET.exists():
        return None
    j = pd.read_parquet(JOURNAL_PARQUET)
    if len(j) == 0 or "price_date" not in j.columns:
        return None
    return str(pd.Timestamp(j.sort_values("price_date")["price_date"].iloc[-1]).date())


def collect_as_of() -> dict[str, str | None]:
    v107 = _read_json(V107_ARTEFACT) or {}
    v109 = _read_json(V109_ARTEFACT) or {}
    cot = (v107.get("cot_live") or {}).get("report_date") if isinstance(v107.get("cot_live"), dict) else None
    return {
        "signal_as_of": _signal_as_of(),
        "cbot_as_of": v107.get("market_data_date"),
        "ema_curve_as_of": v109.get("as_of_curve"),
        "matif_ratio_as_of": _last_jsonl(MATIF_JOURNAL, "price_date"),
        "weather_as_of": _last_jsonl(WEATHER_JOURNAL, "issue_date"),
        "cot_as_of": _parse_cot_date(cot),
    }


def _parse_cot_date(raw: str | None) -> str | None:
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%y%m%d", "%m/%d/%Y"):
        try:
            return str(pd.Timestamp(pd.to_datetime(raw, format=fmt)).date())
        except (ValueError, TypeError):
            continue
    try:
        return str(pd.Timestamp(pd.to_datetime(raw)).date())
    except (ValueError, TypeError):
        return None


def run_v123_freshness(gate_days: int = FRESHNESS_GATE_DAYS) -> dict[str, Any]:
    aso = collect_as_of()
    ref = aso.get("signal_as_of")
    if ref is None:
        return {"version": "V123-FRESHNESS", "verdict": "NO_SIGNAL_REFERENCE"}
    ref_ts = pd.Timestamp(ref)

    layers: dict[str, Any] = {}
    lags = []
    for name in ("cbot_as_of", "ema_curve_as_of", "matif_ratio_as_of", "weather_as_of", "cot_as_of"):
        val = aso[name]
        diag = name.replace("_as_of", "")
        if val is None:
            layers[diag] = {"as_of": None, "lag_days": None, "fresh": False, "action": "DISABLED_MISSING"}
            continue
        lag = int((ref_ts - pd.Timestamp(val)).days)
        layer_gate = LAYER_GATES.get(diag, gate_days)
        fresh = abs(lag) <= layer_gate
        lags.append(abs(lag))
        layers[diag] = {"as_of": val, "lag_days": lag, "fresh": bool(fresh),
                        "action": "ACTIVE" if fresh else "DISABLED_STALE"}

    context_lag_days = max(lags) if lags else None
    n_active = sum(1 for v in layers.values() if v["action"] == "ACTIVE")
    n_disabled = sum(1 for v in layers.values() if v["action"].startswith("DISABLED"))
    coherent = n_disabled == 0
    out = {
        "version": "V123-FRESHNESS",
        "signal_as_of": ref,
        "gate_days": gate_days,
        "layers": layers,
        "context_lag_days": context_lag_days,
        "n_active": n_active,
        "n_disabled": n_disabled,
        "verdict": "CONTEXT_COHERENT" if coherent else "CONTEXT_DEGRADED",
        "disabled_diagnostics": [k for k, v in layers.items() if v["action"].startswith("DISABLED")],
        "interpretation": (
            f"Signal de référence {ref}. Retard max du contexte {context_lag_days} j. "
            + (f"Toutes les couches sont dans leur gate -> contexte cohérent (base {gate_days} j, COT hebdo 10 j)."
               if coherent else
               f"Couches désactivées (périmées/manquantes) : {[k for k, v in layers.items() if v['action'].startswith('DISABLED')]}. "
               "Ne pas afficher ces diagnostics comme frais.")),
        "note": "Lecture des as_of des artefacts/journaux ; aucune donnée recalculée. Méta-fraîcheur, pas un veto.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V123_DIR / "v123_freshness.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def is_layer_active(diagnostic: str, gate_days: int = FRESHNESS_GATE_DAYS) -> bool:
    """Une couche (cbot/ema_curve/matif_ratio/weather/cot) est-elle fraîche assez pour être affichée ?"""
    s = run_v123_freshness(gate_days=gate_days)
    if s.get("verdict") == "NO_SIGNAL_REFERENCE":
        return False
    layer = s.get("layers", {}).get(diagnostic)
    return bool(layer and layer.get("action") == "ACTIVE")


def freshness_report_block() -> str:
    s = run_v123_freshness()
    if s.get("verdict") not in ("CONTEXT_COHERENT", "CONTEXT_DEGRADED"):
        return ""
    icon = "✅" if s["verdict"] == "CONTEXT_COHERENT" else "⚠️"
    rows = []
    for diag, v in s["layers"].items():
        mark = "·" if v["action"] == "ACTIVE" else "⛔"
        rows.append(f"{mark} {diag} {v['as_of']} (retard {v['lag_days']}j)")
    return (
        "### Fraîcheur du contexte (V123 — gate {}j)\n".format(s["gate_days"])
        + f"- Signal {s['signal_as_of']} · retard max contexte {s['context_lag_days']}j · "
        f"{s['n_active']} actives / {s['n_disabled']} désactivées\n"
        + f"- {', '.join(rows)}\n"
        + f"- {icon} **{s['verdict']}**. RESEARCH_ONLY_NOT_TRADING.\n"
    )
