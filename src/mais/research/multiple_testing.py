"""V7-29 — Correction multiple testing (Benjamini-Hochberg) + holdout lock."""

from __future__ import annotations

import json
from typing import Any

import numpy as np

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import load_registry, register_experiment

_HOLDOUT_LOCK = PROJECT_ROOT / "artefacts" / "holdout_lock.json"
_BH_OUTPUT = ARTEFACTS_DIR / "v7" / "bh_corrections.json"
_BH_ALPHA = 0.05


def _load_holdout_lock() -> dict:
    if _HOLDOUT_LOCK.exists():
        return json.loads(_HOLDOUT_LOCK.read_text(encoding="utf-8"))
    return {"used": False, "used_by": None, "used_at": None}


def _write_holdout_lock(used_by: str, timestamp: str) -> None:
    lock = {"used": True, "used_by": used_by, "used_at": timestamp}
    _HOLDOUT_LOCK.parent.mkdir(parents=True, exist_ok=True)
    _HOLDOUT_LOCK.write_text(json.dumps(lock, indent=2), encoding="utf-8")


def is_holdout_available() -> bool:
    lock = _load_holdout_lock()
    return not lock.get("used", False)


def consume_holdout(experiment_id: str) -> dict:
    """Verrou holdout 2024 — utilisable UNE SEULE FOIS (V7-28 uniquement)."""
    if not is_holdout_available():
        lock = _load_holdout_lock()
        raise RuntimeError(
            f"Holdout 2024 déjà consommé par {lock['used_by']} le {lock['used_at']}. "
            "Non réutilisable."
        )
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).isoformat()
    _write_holdout_lock(experiment_id, ts)
    return {"status": "CONSUMED", "experiment_id": experiment_id, "timestamp": ts}


def bh_correction(p_values: list[float], alpha: float = _BH_ALPHA) -> dict[str, Any]:
    """Benjamini-Hochberg FDR correction.

    Returns per-hypothesis results plus which hypotheses survive BH threshold.
    """
    m = len(p_values)
    if m == 0:
        return {"m": 0, "alpha": alpha, "results": [], "n_rejected": 0}
    order = np.argsort(p_values)
    sorted_p = np.array(p_values)[order]
    thresholds = (np.arange(1, m + 1) / m) * alpha
    below = sorted_p <= thresholds
    k_star = 0 if not below.any() else int(np.where(below)[0].max()) + 1

    rejected_set = set(order[:k_star].tolist())
    results = []
    for i, (orig_idx, p, thr) in enumerate(zip(order, sorted_p, thresholds, strict=True)):
        results.append({
            "original_index": int(orig_idx),
            "p_value": float(p),
            "bh_rank": i + 1,
            "bh_threshold": float(thr),
            "rejected": orig_idx in rejected_set,
            "q_bh": float(p * m / (i + 1)),
        })
    results.sort(key=lambda r: r["original_index"])
    return {
        "m": m,
        "alpha": alpha,
        "k_star": k_star,
        "n_rejected": k_star,
        "results": results,
    }


def run_bh_on_registry(alpha: float = _BH_ALPHA) -> dict[str, Any]:
    """Applique BH à tous les experiments avec p_value non-None dans le registre."""
    experiments = load_registry()
    testable = [
        e for e in experiments
        if e.get("p_value") is not None and e["p_value"] != "None"
    ]
    if not testable:
        return {
            "n_testable": 0,
            "alpha": alpha,
            "bh_results": [],
            "global_verdict": "NO_TESTS",
        }
    p_values = [float(e["p_value"]) for e in testable]
    bh = bh_correction(p_values, alpha=alpha)

    bh_results = []
    for entry, bh_res in zip(testable, bh["results"], strict=True):
        bh_results.append({
            "experiment_id": entry["experiment_id"],
            "target": entry.get("target"),
            "p_value": bh_res["p_value"],
            "q_bh": bh_res["q_bh"],
            "bh_threshold": bh_res["bh_threshold"],
            "rejected_h0": bh_res["rejected"],
            "go_research": bh_res["rejected"] and bh_res["q_bh"] < alpha,
        })

    n_go = sum(1 for r in bh_results if r["go_research"])
    return {
        "n_testable": len(testable),
        "n_rejected": bh["n_rejected"],
        "n_go_research": n_go,
        "alpha": alpha,
        "bh_results": bh_results,
        "global_verdict": "SOME_SIGNIFICANT" if n_go > 0 else "NONE_SIGNIFICANT",
    }


def save_bh_corrections() -> dict[str, Any]:
    """Produit, sauvegarde et enregistre les corrections BH."""
    result = run_bh_on_registry()
    _BH_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _BH_OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    register_experiment(
        experiment_id="V7-29",
        target="bh_multiple_testing_correction",
        horizon=0,
        model="bh_fdr",
        cv_protocol="none",
        embargo_days=0,
        n_oof=0,
        features=[],
        metrics={
            "n_testable": result["n_testable"],
            "n_rejected": result["n_rejected"],
            "alpha": _BH_ALPHA,
        },
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_BH_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
