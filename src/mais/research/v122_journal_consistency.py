"""V122 — Cohérence du journal officiel + politique de révision auditée.

Le journal V27 est append-only et REFUSE de réviser une date déjà loggée (`ALREADY_LOGGED`). Or un
settlement peut être révisé en intra-journée : le rapport quotidien (`latest.json`) recalcule alors un tier
différent de celui figé dans le journal (ex. 2026-06-01 loggé EXTREME z 2.039 puis recalculé STRONG z 1.88).
On obtient des couches qui se contredisent pour la même date.

Politique ici (sans modifier V27) :
  - `record_status` dérivé : une date == aujourd'hui est PROVISIONAL (révisable) ; une date passée est FINAL.
  - révision auditée : on ne révise QUE le jour courant (PROVISIONAL). Toute révision écrit une entrée dans
    `revision_log.jsonl` (old→new horodaté) et marque la ligne REVISED. Réviser une date FINAL est REFUSÉ
    (anti look-ahead : on ne réécrit jamais le passé settlé).
  - `consistency_check` compare le dernier jour du journal aux synthèses V101/V99 et au rapport quotidien.

Statut : RESEARCH_ONLY_NOT_TRADING. Baseline figée. Holdout verrouillé.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V122_DIR = ARTEFACTS_DIR / "v122"
V122_DIR.mkdir(parents=True, exist_ok=True)
JOURNAL_DIR = ROOT / "data" / "forward_journal"
JOURNAL_PARQUET = JOURNAL_DIR / "official_forward_journal.parquet"
REVISION_LOG = JOURNAL_DIR / "revision_log.jsonl"
DAILY_LATEST = ROOT / "reports" / "daily" / "latest.json"
V101_ARTEFACT = ARTEFACTS_DIR / "v101" / "official_synthesis_fix.json"
V99_ARTEFACT = ARTEFACTS_DIR / "v99" / "v99_synthesis_v2_latest.json"

REVISABLE_FIELDS = ("official_front_settlement", "cbot_cents_bu", "eurusd", "cbot_eur_t",
                    "basis_official_eur_t", "basis_z_used", "signal_tier")


def classify_record_status(price_date: Any, as_of: Any) -> str:
    """PROVISIONAL si la date est celle du jour courant (settlement encore révisable), FINAL sinon."""
    d = pd.Timestamp(price_date).normalize()
    today = pd.Timestamp(as_of).normalize()
    return "PROVISIONAL" if d >= today else "FINAL"


def detect_duplicates(j: pd.DataFrame) -> list[str]:
    """Vrai doublon = même date ET même record_status.

    Depuis V150, une date peut légitimement porter PROVISIONAL puis REVISED (upgrade append-only du
    soir) : ce n'est PAS un doublon, c'est la politique de révision. Sans colonne statut, on retombe
    sur la détection par date seule (journaux pré-V150).
    """
    if "price_date" not in j.columns or len(j) == 0:
        return []
    if "record_status" in j.columns:
        key = j["price_date"].astype(str) + "|" + j["record_status"].astype(str)
        dup_idx = key[key.duplicated(keep=False)].index
        return sorted(j.loc[dup_idx, "price_date"].astype(str).unique().tolist())
    s = j["price_date"].astype(str)
    return sorted(s[s.duplicated(keep=False)].unique().tolist())


def _append_revision_log(entry: dict[str, Any]) -> None:
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    with REVISION_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, default=str) + "\n")


def revise_same_day(record: dict[str, Any], as_of: Any, force: bool = False) -> dict[str, Any]:
    """DÉTECTE une révision intraday du jour courant (audit-only ; V27 est le seul writer du journal)."""
    if record.get("verdict") != "OFFICIAL_SIGNAL_COMPUTED":
        return {"status": "SKIP", "reason": record.get("verdict")}
    if not JOURNAL_PARQUET.exists():
        return {"status": "NO_JOURNAL"}
    j = pd.read_parquet(JOURNAL_PARQUET)
    pd_str = str(record["price_date"])
    mask = j["price_date"].astype(str) == pd_str
    if not mask.any():
        return {"status": "NOT_PRESENT", "price_date": pd_str,
                "note": "Date absente -> laisser V27 append-only l'ajouter normalement."}

    status = classify_record_status(record["price_date"], as_of)
    if status == "FINAL" and not force:
        return {"status": "REFUSED_FINAL", "price_date": pd_str,
                "note": "Date settlée (passée) immuable : on ne réécrit jamais le passé (anti look-ahead)."}

    # comparaison vs la ligne CANONIQUE du jour (REVISED > FINAL > SETTLING > PROVISIONAL)
    sub = j[mask]
    if "record_status" in sub.columns and len(sub) > 1:
        prio = {"REVISED": 3, "FINAL": 2, "SETTLING": 1, "PROVISIONAL": 0}
        sub = sub.assign(_prio=sub["record_status"].astype(str).map(prio).fillna(-1)).sort_values("_prio")
    idx = sub.index[-1]
    changes = {}
    for f in REVISABLE_FIELDS:
        old = j.at[idx, f] if f in j.columns else None
        new = record.get(f)
        if f in j.columns and pd.notna(new) and not _equal(old, new):
            changes[f] = {"old": _scalar(old), "new": _scalar(new)}

    if not changes:
        return {"status": "NO_CHANGE", "price_date": pd_str, "record_status": status,
                "signal_tier": _scalar(j.at[idx, "signal_tier"]) if "signal_tier" in j.columns else None}

    # CONSOLIDATION 2026-06-11 : V122 ne réécrit PLUS le journal. L'édition in-place (valeurs + statut
    # REVISED sur la ligne du matin) contredisait l'append-only V150 et a produit, le 06-10, un parquet
    # divergent du JSONL (2 lignes REVISED). V27 est le SEUL writer : l'upgrade effectif est la nouvelle
    # ligne REVISED du run du soir. Ici on DÉTECTE et on JOURNALISE pour l'audit, rien d'autre.
    entry = {"price_date": pd_str, "revised_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
             "as_of": str(pd.Timestamp(as_of).date()), "record_status": "CHANGES_DETECTED",
             "changes": changes,
             "note": "détection V122 (audit-only) ; upgrade append-only par V27 au run du soir"}
    _append_revision_log(entry)
    return {"status": "CHANGES_DETECTED_APPEND_ONLY", "price_date": pd_str, "changes": changes,
            "new_signal_tier": record.get("signal_tier"),
            "note": "journal NON modifié (V27 seul writer, append-only V150)"}


def _equal(a: Any, b: Any) -> bool:
    try:
        if isinstance(a, (int, float)) or isinstance(b, (int, float)):
            return abs(float(a) - float(b)) < 1e-9
    except (TypeError, ValueError):
        pass
    return str(a) == str(b)


def _scalar(v: Any) -> Any:
    if hasattr(v, "item"):
        try:
            return v.item()
        except (ValueError, AttributeError):
            return v
    return v


def _read_json(path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _layer_signal_from_daily() -> dict[str, Any] | None:
    d = _read_json(DAILY_LATEST)
    if not d:
        return None
    sig = (d.get("forward_journal") or {}).get("signal") or {}
    if not sig.get("price_date"):
        return None
    return {"layer": "daily_latest", "as_of": str(sig.get("price_date")),
            "signal_tier": sig.get("signal_tier")}


def consistency_check(as_of: Any | None = None) -> dict[str, Any]:
    """Le dernier jour du journal et les autres couches (V101/V99/daily) concordent-ils sur le tier ?"""
    if not JOURNAL_PARQUET.exists():
        return {"version": "V122-CONSISTENCY", "verdict": "NO_JOURNAL"}
    j = pd.read_parquet(JOURNAL_PARQUET).sort_values("price_date")
    if len(j) == 0:
        return {"version": "V122-CONSISTENCY", "verdict": "EMPTY_JOURNAL"}
    as_of = pd.Timestamp(as_of).normalize() if as_of is not None else pd.Timestamp(j["price_date"].iloc[-1]).normalize()
    ref_date = str(j["price_date"].iloc[-1])
    # référence = enregistrement CANONIQUE du dernier jour (REVISED > FINAL > SETTLING > PROVISIONAL)
    same_day = j[j["price_date"].astype(str) == ref_date]
    if "record_status" in same_day.columns and len(same_day) > 1:
        prio = {"REVISED": 3, "FINAL": 2, "SETTLING": 1, "PROVISIONAL": 0}
        same_day = same_day.assign(
            _prio=same_day["record_status"].astype(str).map(prio).fillna(-1)).sort_values("_prio")
    last = same_day.iloc[-1]
    ref_tier = _scalar(last.get("signal_tier"))

    layers = []
    v101 = _read_json(V101_ARTEFACT)
    if v101 and v101.get("verdict") == "OFFICIAL_SYNTHESIS_FIXED":
        layers.append({"layer": "v101", "as_of": str(v101.get("as_of")), "signal_tier": v101.get("signal_tier")})
    v99 = _read_json(V99_ARTEFACT)
    if v99 and v99.get("as_of"):
        layers.append({"layer": "v99", "as_of": str(v99.get("as_of")), "signal_tier": v99.get("signal_tier")})
    daily = _layer_signal_from_daily()
    if daily:
        layers.append(daily)

    # cohérence : pour chaque couche datée comme le journal, le tier doit matcher.
    # une couche plus ANCIENNE que la référence est "stale" (cf. V123 fraîcheur), pas une incohérence de tier.
    mismatches = []
    stale = []
    for ly in layers:
        if ly["as_of"] == ref_date:
            if ly["signal_tier"] != ref_tier:
                mismatches.append(ly)
        elif ly["as_of"] < ref_date:
            stale.append(ly)
    dups = detect_duplicates(j)
    consistent = (len(mismatches) == 0 and len(dups) == 0)

    out = {
        "version": "V122-CONSISTENCY",
        "as_of": str(as_of.date()),
        "reference_date": ref_date,
        "reference_signal_tier": ref_tier,
        "reference_record_status": classify_record_status(ref_date, as_of),
        "layers_checked": layers,
        "duplicate_dates": dups,
        "mismatched_layers": mismatches,
        "stale_layers": stale,
        "consistent": bool(consistent),
        "verdict": "LIVE_SIGNAL_CONSISTENT" if consistent else "LIVE_SIGNAL_INCONSISTENT",
        "n_revisions_logged": _n_revisions(),
        "interpretation": (
            f"Référence = dernier jour du journal officiel ({ref_date}, {ref_tier}, "
            f"{classify_record_status(ref_date, as_of)}). "
            + ("Toutes les couches datées concordent ; aucun doublon de date." if consistent
               else f"Incohérences : doublons {dups}, couches divergentes {[m['layer'] for m in mismatches]}.")),
        "note": "Révision auditée du jour courant uniquement (PROVISIONAL) ; passé FINAL immuable. "
                "CONTEXTE de cohérence, jamais un veto.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V122_DIR / "v122_consistency.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def _n_revisions() -> int:
    if not REVISION_LOG.exists():
        return 0
    try:
        return sum(1 for line in REVISION_LOG.read_text(encoding="utf-8").splitlines() if line.strip())
    except OSError:
        return 0


def run_v122(as_of: Any | None = None, revise_with: dict[str, Any] | None = None) -> dict[str, Any]:
    """Pipeline : (optionnel) réviser le jour courant à partir d'un signal recalculé, puis vérifier la cohérence."""
    revision = None
    if revise_with is not None:
        revision = revise_same_day(revise_with, as_of=as_of or revise_with.get("price_date"))
    check = consistency_check(as_of=as_of)
    check["revision"] = revision
    (V122_DIR / "v122_consistency.json").write_text(json.dumps(check, indent=2, default=str), encoding="utf-8")
    return check


def consistency_report_block(as_of: Any | None = None) -> str:
    s = consistency_check(as_of=as_of)
    if s.get("verdict") not in ("LIVE_SIGNAL_CONSISTENT", "LIVE_SIGNAL_INCONSISTENT"):
        return ""
    icon = "✅" if s["consistent"] else "⚠️"
    extra = "" if s["consistent"] else f" — divergences : doublons {s['duplicate_dates']}, " \
                                       f"couches {[m['layer'] for m in s['mismatched_layers']]}"
    return (
        "### Cohérence du signal live (V122 — politique de révision)\n"
        f"- Référence {s['reference_date']} · **{s['reference_signal_tier']}** "
        f"({s['reference_record_status']}) · couches vérifiées : "
        f"{', '.join(ly['layer'] for ly in s['layers_checked']) or 'aucune'}\n"
        f"- {icon} **{s['verdict']}**{extra} · révisions journalisées : {s['n_revisions_logged']}\n"
        "- Révision auditée du jour courant uniquement ; passé FINAL immuable. RESEARCH_ONLY_NOT_TRADING.\n"
    )
