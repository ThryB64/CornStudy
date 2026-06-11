"""V152-SYNC — Audit de cohérence de la source unique premium.

Vérifie que tous les consommateurs live racontent LA MÊME vérité :
head (`premium_daily_head.json`) = couche V132 = dashboard v4 = lifecycle = monthly = journal officiel
= bloc `premium_head` embarqué dans `reports/daily/latest.json`.

Verdicts par check : PASS / WARN / FAIL / SKIP. Aucune science ici — uniquement la plomberie de vérité.
RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
import re
from typing import Any

from mais.paths import ARTEFACTS_DIR, DATA_DIR, PROJECT_ROOT

AUDIT_DIR = ARTEFACTS_DIR / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

HEAD_PATH = DATA_DIR / "premium" / "premium_daily_head.json"
DASHBOARD_PATH = DATA_DIR / "premium" / "dashboard_v4.md"
LIFECYCLE_PATH = DATA_DIR / "premium" / "lifecycle.md"
V132_PATH = ARTEFACTS_DIR / "v132" / "indicator_v3_latest.json"
DAILY_LATEST = PROJECT_ROOT / "reports" / "daily" / "latest.json"
MONTHLY_LATEST = PROJECT_ROOT / "reports" / "monthly" / "latest.md"

_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _read_json(path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _md_header_date(path) -> str | None:
    try:
        first = path.read_text(encoding="utf-8").splitlines()[0]
    except (OSError, IndexError):
        return None
    m = _DATE_RE.search(first)
    return m.group(1) if m else None


def run_single_source_audit() -> dict[str, Any]:
    head = _read_json(HEAD_PATH)
    checks: dict[str, dict[str, Any]] = {}

    if head.get("verdict") != "PREMIUM_HEAD_BUILT":
        out = {"audit": "single_source", "overall": "FAIL",
               "reason": "head absent ou non construit", "checks": {}}
        (AUDIT_DIR / "single_source_report.json").write_text(
            json.dumps(out, indent=2, default=str), encoding="utf-8")
        return out
    head_as_of = str(head.get("as_of"))

    # 1) head dérive bien de la synthèse V132 (même date)
    v132 = _read_json(V132_PATH)
    checks["head_matches_v132"] = {
        "verdict": "PASS" if str(v132.get("as_of")) == head_as_of else "FAIL",
        "head_as_of": head_as_of, "v132_as_of": v132.get("as_of"),
    }

    # 2) head non périmé vs journal officiel (sa propre session_truth)
    st = head.get("session_truth") or {}
    last_journal = str(st.get("last_date"))
    checks["head_not_stale_vs_journal"] = {
        "verdict": "PASS" if last_journal == head_as_of else "FAIL",
        "journal_last_date": last_journal, "head_as_of": head_as_of,
        "note": "le head doit refléter le dernier jour journalisé",
    }
    checks["head_has_session_truth"] = {
        "verdict": "PASS" if st.get("last_record_status") else "FAIL",
        "last_record_status": st.get("last_record_status"),
        "session_warning": head.get("session_warning"),
    }

    # 3) dashboard v4 : même date que le head + déclare lire le head
    dash_date = _md_header_date(DASHBOARD_PATH)
    try:
        dash_txt = DASHBOARD_PATH.read_text(encoding="utf-8")
    except OSError:
        dash_txt = ""
    checks["dashboard_reads_head_only"] = {
        "verdict": ("PASS" if dash_date == head_as_of and "premium_daily_head.json" in dash_txt
                    else "FAIL"),
        "dashboard_date": dash_date, "head_as_of": head_as_of,
        "declares_head_source": "premium_daily_head.json" in dash_txt,
    }

    # 4) lifecycle : même date que le head
    life_date = _md_header_date(LIFECYCLE_PATH)
    checks["lifecycle_in_sync"] = {
        "verdict": "PASS" if life_date == head_as_of else "FAIL",
        "lifecycle_date": life_date, "head_as_of": head_as_of,
    }

    # 5) monthly : régénéré chaque jour depuis V152-SYNC ; WARN seulement (transition tolérée)
    monthly_date = _md_header_date(MONTHLY_LATEST)
    checks["monthly_in_sync"] = {
        "verdict": "PASS" if monthly_date == head_as_of else "WARN",
        "monthly_date": monthly_date, "head_as_of": head_as_of,
        "note": "WARN tant que le run quotidien V133 n'a pas tourné après la mise en place V152",
    }

    # 6) latest.json embarque le même head (CI et fichier commité racontent la même chose)
    latest = _read_json(DAILY_LATEST)
    embedded = latest.get("premium_head") or {}
    emb_as_of = str(embedded.get("as_of"))
    if emb_as_of == head_as_of:
        v = "PASS"
    elif emb_as_of < head_as_of:
        v = "WARN"   # head régénéré localement après le dernier run CI : pas un mensonge, juste plus frais
    else:
        v = "FAIL"   # le fichier head est PLUS VIEUX que le dernier run : artefact stale servi comme vérité
    checks["latest_embeds_same_head"] = {
        "verdict": v, "latest_premium_head_as_of": embedded.get("as_of"), "head_as_of": head_as_of,
    }

    verdicts = [c["verdict"] for c in checks.values()]
    overall = "FAIL" if "FAIL" in verdicts else ("WARN" if "WARN" in verdicts else "PASS")
    out = {"audit": "single_source", "overall": overall, "head_as_of": head_as_of,
           "checks": checks, "status": "RESEARCH_ONLY_NOT_TRADING"}
    (AUDIT_DIR / "single_source_report.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out
