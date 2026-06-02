"""V126 — Substitution MATIF blé/maïs v2 : historique structuré + relation au basis.

V52 collecte déjà le ratio MATIF officiel (EBM/EMA) en live et l'append au journal forward. Ici on
(a) structure ce journal jsonl en parquet exploitable, (b) calcule le z-score forward du ratio quand assez
de jours, (c) teste la relation ratio↔basis sur le master via le PROXY (ratio CBOT blé/maïs en z, seule
mesure historiquement disponible — le vrai ratio EBM/EMA historique reste WAITING_DATA), et (d) regarde le
lien avec ADVERSE et l'objectif z→0.5/z→0.

Verdict honnête : SUBSTITUTION_SIGNAL_READY si la relation proxy est confirmée sur le master ET le ratio
officiel s'accumule en forward ; le niveau historique officiel reste DATA_BLOCKED (à accumuler).
Statut : RESEARCH_ONLY_NOT_TRADING. Holdout verrouillé. Contexte, jamais un veto.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.paths import PROJECT_ROOT as ROOT

V126_DIR = ARTEFACTS_DIR / "v126"
V126_DIR.mkdir(parents=True, exist_ok=True)
MATIF_JSONL = ROOT / "data" / "official_forward" / "matif_ratio_journal.jsonl"
RATIO_HISTORY = ROOT / "data" / "official_forward" / "matif_ratio_history.parquet"
MIN_FORWARD_Z = 30


def build_ratio_history() -> pd.DataFrame:
    """Structure le journal jsonl MATIF en parquet (une ligne par price_date, dédupliqué)."""
    if not MATIF_JSONL.exists():
        return pd.DataFrame()
    recs = []
    for ln in MATIF_JSONL.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("status") == "OK" and d.get("matif_wheat_corn_ratio") is not None:
            recs.append({"price_date": pd.Timestamp(d["price_date"]).normalize(),
                         "ratio": float(d["matif_wheat_corn_ratio"]),
                         "wheat_settle": d.get("matif_wheat_settle"),
                         "corn_settle": d.get("matif_corn_settle")})
    if not recs:
        return pd.DataFrame()
    h = pd.DataFrame(recs).drop_duplicates(subset="price_date", keep="last").sort_values("price_date")
    return h.reset_index(drop=True)


def _proxy_relation_on_master() -> dict[str, Any] | None:
    """corr(ratio CBOT blé/maïs z, basis_z) sur le master — proxy historique de la relation substitution↔basis."""
    try:
        from mais.research.v38_adverse_risk import _wheat_corn_ratio_z
        from mais.scripts.run_v8_phase_a import filter_out_holdout, load_master_dataset
        df = filter_out_holdout(load_master_dataset())
        bz = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
        wcz = _wheat_corn_ratio_z(df)
        m = bz.notna() & wcz.notna()
        if m.sum() < 200:
            return None
        corr = float(np.corrcoef(wcz[m], bz[m])[0, 1])
        # relation sur signaux actifs (basis_z>1) : la prime haute coïncide-t-elle avec un ratio blé/maïs haut ?
        active = m & (bz >= 1.0)
        corr_active = float(np.corrcoef(wcz[active], bz[active])[0, 1]) if active.sum() > 30 else None
        return {"n": int(m.sum()), "corr_ratio_basis": round(corr, 3),
                "n_active": int(active.sum()),
                "corr_ratio_basis_active": round(corr_active, 3) if corr_active is not None else None}
    except Exception:  # noqa: BLE001
        return None


def run_v126_substitution() -> dict[str, Any]:
    hist = build_ratio_history()
    if len(hist):
        RATIO_HISTORY.parent.mkdir(parents=True, exist_ok=True)
        hist.to_parquet(RATIO_HISTORY, index=False)
    n_fwd = int(len(hist))
    ratio_last = round(float(hist["ratio"].iloc[-1]), 4) if n_fwd else None
    ratio_z_fwd = None
    if n_fwd >= MIN_FORWARD_Z:
        r = pd.to_numeric(hist["ratio"], errors="coerce")
        ratio_z_fwd = round(float((r.iloc[-1] - r.mean()) / r.std()), 3) if r.std() else None

    rel = _proxy_relation_on_master()
    proxy_confirmed = bool(rel and rel["corr_ratio_basis"] > 0.3)

    if proxy_confirmed and n_fwd >= 1:
        verdict = "SUBSTITUTION_SIGNAL_READY"
    elif rel is None:
        verdict = "DATA_BLOCKED"
    else:
        verdict = "PROXY_OK_FORWARD_ACCUMULATING"

    out = {
        "version": "V126-MATIF-SUBSTITUTION-V2",
        "verdict": verdict,
        "n_forward_days": n_fwd,
        "matif_ratio_last": ratio_last,
        "matif_ratio_z_forward": ratio_z_fwd,
        "forward_z_available": bool(ratio_z_fwd is not None),
        "proxy_relation_master": rel,
        "proxy_relation_confirmed": proxy_confirmed,
        "historical_official_status": "WAITING_DATA",
        "interpretation": (
            f"Ratio MATIF officiel (EBM/EMA) live = {ratio_last} ; {n_fwd} jour(s) accumulé(s) en forward "
            f"(z forward {'indispo (<' + str(MIN_FORWARD_Z) + ' j)' if ratio_z_fwd is None else ratio_z_fwd}). "
            + (f"Relation proxy sur le master : corr(ratio blé/maïs z, basis_z)="
               f"{rel['corr_ratio_basis'] if rel else 'n/a'} "
               f"(actifs {rel['corr_ratio_basis_active'] if rel else 'n/a'}) -> "
               + ("substitution liée au basis CONFIRMÉE (proxy). " if proxy_confirmed
                  else "relation proxy faible. ") if rel else "relation proxy indisponible. ")
            + "Le ratio officiel EBM/EMA historique reste WAITING_DATA : on l'accumule en forward avant de le "
              "brancher dans ADVERSE_RISK. Un ratio blé/maïs HAUT = maïs relativement cher = prime moins "
              "compressible (objectif prudent)."),
        "note": "Réutilise V52 (journal). Niveau officiel historique non disponible -> proxy CBOT z pour la "
                "relation, ratio officiel pour le live. Contexte, jamais un veto.",
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V126_DIR / "v126_substitution.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def substitution_v2_report_block() -> str:
    s = run_v126_substitution()
    if s.get("verdict") in (None, "DATA_BLOCKED") or s.get("matif_ratio_last") is None:
        return ""
    rel = s.get("proxy_relation_master") or {}
    return (
        "### Substitution MATIF blé/maïs (V126)\n"
        f"- Ratio officiel EBM/EMA live **{s['matif_ratio_last']}** · {s['n_forward_days']} j forward "
        f"· z forward {s['matif_ratio_z_forward']}\n"
        f"- Relation proxy (master) corr(ratio,basis)={rel.get('corr_ratio_basis')} "
        f"(actifs {rel.get('corr_ratio_basis_active')}) · officiel historique = WAITING_DATA\n"
        f"- **{s['verdict']}** : ratio blé/maïs haut = maïs cher = prime moins compressible. "
        "Contexte, jamais un veto. RESEARCH_ONLY_NOT_TRADING.\n"
    )
