"""V181 — Maintenance hebdomadaire research : le système est-il en bonne santé pour accumuler ?

Phase de validation forward = pas de nouvelle exploration ; le travail hebdomadaire est de
VÉRIFIER que tout accumule proprement : CI quotidien, journal officiel, head à jour, couches
fraîches, archives météo/MATIF/courbe qui grossissent, tests critiques verts, prochains jalons.

Chaque check rend OK / WARN / FAIL + détail. Verdict global : OK si aucun FAIL et <=2 WARN,
DEGRADED si WARN>2, BROKEN si FAIL. Sorties : artefact JSON + reports/weekly/maintenance_latest.md.
Lecture seule (les tests critiques tournent en sous-processus). RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V181_DIR = ARTEFACTS_DIR / "v181"
V181_DIR.mkdir(parents=True, exist_ok=True)
WEEKLY_DIR = ROOT / "reports" / "weekly"

DAILY_LATEST = ROOT / "reports" / "daily" / "latest.json"
HEAD = ROOT / "data" / "premium" / "premium_daily_head.json"
JOURNAL = ROOT / "data" / "forward_journal" / "official_forward_journal.parquet"
WEATHER = ROOT / "data" / "weather" / "forecast_revisions.parquet"
MATIF = ROOT / "data" / "official_forward" / "matif_ratio_history.parquet"
CURVE = ROOT / "data" / "official_forward" / "ema_curve_history.parquet"
SINGLE_SOURCE = ARTEFACTS_DIR / "audit" / "single_source_report.json"

CRITICAL_TESTS = ["tests/test_state_machine.py", "tests/test_single_source_v152.py",
                  "tests/test_v27_official_forward.py",
                  "tests/test_v178_official_validation.py", "tests/test_v177_data_gated_reruns.py"]
MAX_HEAD_AGE_DAYS = 4   # tolère un week-end + férié
MAX_DAILY_AGE_DAYS = 4


def _check(name: str, status: str, detail: str) -> dict[str, str]:
    return {"check": name, "status": status, "detail": detail}


def _age_days(date_str: str | None) -> int | None:
    if not date_str:
        return None
    try:
        d = pd.Timestamp(str(date_str)[:10])
        return int((pd.Timestamp.now().normalize() - d.normalize()).days)
    except Exception:  # noqa: BLE001
        return None


def _read_json(path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _parquet_growth(path, date_col: str) -> tuple[int, int | None]:
    """(n_rows, jours depuis la dernière date) — None si fichier absent."""
    if not path.exists():
        return 0, None
    df = pd.read_parquet(path)
    if date_col not in df.columns or df.empty:
        return int(len(df)), None
    last = pd.to_datetime(df[date_col], errors="coerce").max()
    return int(len(df)), int((pd.Timestamp.now().normalize() - last.normalize()).days)


def check_ci() -> dict[str, str]:
    daily = _read_json(DAILY_LATEST)
    if not daily:
        return _check("ci_daily", "FAIL", "reports/daily/latest.json absent")
    age = _age_days(daily.get("as_of"))
    result = daily.get("result")
    if age is not None and age > MAX_DAILY_AGE_DAYS:
        return _check("ci_daily", "FAIL", f"dernier daily vieux de {age} j (result={result})")
    if result not in ("OK", "NEEDS_RETRY"):
        return _check("ci_daily", "WARN", f"daily result={result} (age {age} j)")
    return _check("ci_daily", "OK", f"daily {daily.get('as_of')} result={result}")


def check_head() -> dict[str, str]:
    head = _read_json(HEAD)
    if not head:
        return _check("premium_head", "FAIL", "head absent")
    age = _age_days(head.get("as_of"))
    cons = (head.get("consistency") or {}).get("verdict")
    if age is None or age > MAX_HEAD_AGE_DAYS:
        return _check("premium_head", "FAIL", f"head as_of {head.get('as_of')} (âge {age} j)")
    if cons != "LIVE_SIGNAL_CONSISTENT":
        return _check("premium_head", "WARN", f"cohérence {cons}")
    return _check("premium_head", "OK", f"as_of {head.get('as_of')}, {cons}")


def check_stale_layers() -> dict[str, str]:
    ss = _read_json(SINGLE_SOURCE)
    if not ss:
        return _check("single_source", "WARN", "audit single_source absent")
    overall = ss.get("overall")
    return _check("single_source", "OK" if overall == "PASS" else "FAIL",
                  f"audit single_source {overall}")


def check_accumulations() -> list[dict[str, str]]:
    out = []
    for name, path, col, max_age in (("official_journal", JOURNAL, "price_date", 4),
                                     ("ema_curve", CURVE, "price_date", 4),
                                     ("matif_ratio", MATIF, "price_date", 6),
                                     ("weather_archive", WEATHER, "valid_date", 4)):
        n, age = _parquet_growth(path, col)
        if n == 0:
            out.append(_check(name, "FAIL", "fichier absent ou vide"))
        elif age is not None and age > max_age:
            out.append(_check(name, "WARN", f"{n} lignes mais dernière date vieille de {age} j"))
        else:
            out.append(_check(name, "OK", f"{n} lignes, dernière date il y a {age} j"))
    return out


def check_critical_tests(run: bool = True) -> dict[str, str]:
    if not run:
        return _check("critical_tests", "WARN", "non exécutés (run_tests=False)")
    existing = [t for t in CRITICAL_TESTS if (ROOT / t).exists()]
    if not existing:
        return _check("critical_tests", "WARN", "aucun test critique trouvé")
    proc = subprocess.run([sys.executable, "-m", "pytest", "-x", "-q", *existing],
                          capture_output=True, text=True, cwd=ROOT, timeout=600)
    ok = proc.returncode == 0
    tail = (proc.stdout or proc.stderr).strip().splitlines()[-1:]
    return _check("critical_tests", "OK" if ok else "FAIL",
                  f"{len(existing)} fichiers : {' '.join(tail)}")


def next_milestones() -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        from mais.premium.forward_milestones import run_v147_milestones
        ms = run_v147_milestones()
        out["official"] = {"n_days": ms.get("n_official_days"),
                           "next": ms.get("next_milestone"), "meaning": ms.get("next_meaning")}
    except Exception:  # noqa: BLE001
        out["official"] = None
    v177 = _read_json(ARTEFACTS_DIR / "v177" / "data_gated_status.json")
    out["data_gated"] = {g.get("rerun"): f"{g.get('n')}/{g.get('gate')}"
                         for g in v177.get("gates", [])} or None
    v178 = _read_json(ARTEFACTS_DIR / "v178" / "v178_official_validation.json")
    out["v178_validation"] = v178.get("verdict")
    return out


def run_v181_weekly(run_tests: bool = True) -> dict[str, Any]:
    checks = [check_ci(), check_head(), check_stale_layers(), *check_accumulations(),
              check_critical_tests(run=run_tests)]
    n_fail = sum(1 for c in checks if c["status"] == "FAIL")
    n_warn = sum(1 for c in checks if c["status"] == "WARN")
    verdict = "BROKEN" if n_fail else ("DEGRADED" if n_warn > 2 else "OK")
    out = {
        "version": "V181-WEEKLY-MAINTENANCE",
        "verdict": verdict, "n_fail": n_fail, "n_warn": n_warn,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "next_milestones": next_milestones(),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V181_DIR / "weekly_maintenance.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8")
    _write_markdown(out)
    return out


def _write_markdown(out: dict[str, Any]) -> None:
    WEEKLY_DIR.mkdir(parents=True, exist_ok=True)
    icon = {"OK": "✅", "WARN": "⚠️", "FAIL": "❌"}
    lines = [f"# 🔧 Maintenance hebdomadaire — {out['generated_at'][:10]}",
             f"**Verdict : {out['verdict']}** ({out['n_fail']} FAIL, {out['n_warn']} WARN)", "",
             "| Check | Statut | Détail |", "|---|---|---|"]
    lines += [f"| {c['check']} | {icon.get(c['status'], '?')} {c['status']} | {c['detail']} |"
              for c in out["checks"]]
    ms = out["next_milestones"]
    lines += ["", "## Prochains jalons",
              f"- Officiel : {ms.get('official')}",
              f"- Data-gated (V177) : {ms.get('data_gated')}",
              f"- Validation proxy V178 : {ms.get('v178_validation')}", "",
              "RESEARCH_ONLY_NOT_TRADING."]
    (WEEKLY_DIR / "maintenance_latest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
