"""Runner V8 Phase A + V8-META-REVALIDATION.

Étape 1 : V8-INFRA-HOLDOUT — écrit holdout_lock.json
Étape 2 : V8-INFRA-REGISTRY — merge V6 CSV + V7 JSONL → registry_unified
Étape 3 : V8-FRAGILE-FLAGS-AUDIT — scan V0–V7 artefacts
Étape 4 : V8-META-REVALIDATION — exécute revalidation complète
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

ARTEFACTS = ROOT / "artefacts"
V8 = ARTEFACTS / "v8"
V8.mkdir(parents=True, exist_ok=True)


def load_master_dataset() -> pd.DataFrame:
    """Charge features + market + EMA continuous + targets CBOT + targets EMA.

    Construit la base utilisée par tous les modules V8.
    """
    df = pd.read_parquet(ROOT / "data/processed/features.parquet")
    if "Date" in df.columns:
        df = df.set_index("Date")
    df.index = pd.to_datetime(df.index)

    mk = pd.read_parquet(ROOT / "data/interim/market.parquet")
    if "Date" in mk.columns:
        mk = mk.set_index("Date")
    mk.index = pd.to_datetime(mk.index)
    for col in ["corn_close", "wheat_close", "soy_close", "oats_close", "oil_close",
                "gas_close", "usd_index_close", "corn_volume"]:
        if col in mk.columns and col not in df.columns:
            df[col] = mk[col]
    if "corn_close" in df.columns:
        df["cbot_close"] = df["corn_close"]

    ema_raw_path = ROOT / "data/processed/euronext/ema_front_continuous_raw.parquet"
    if ema_raw_path.exists():
        ema_raw = pd.read_parquet(ema_raw_path)
        if "date" in ema_raw.columns:
            ema_raw["date"] = pd.to_datetime(ema_raw["date"])
            ema_raw = ema_raw.set_index("date")
        ema_close = ema_raw["price"].rename("ema_close") if "price" in ema_raw.columns else None
        if ema_close is not None:
            df["ema_close"] = ema_close

    if "cbot_eur_t" in df.columns and "cbot_close_eur" not in df.columns:
        df["cbot_close_eur"] = df["cbot_eur_t"]

    # V25-01 (audit V24) : utiliser le VRAI taux EUR/USD (eu_cross_assets) plutôt qu'une dérivation.
    # L'ancienne dérivation (corn_close*36.744/cbot_eur_t ~ 93×taux réel) était un transform linéaire
    # -> inoffensif comme feature standardisée, mais mal étiqueté. On charge le vrai taux si dispo.
    if "eurusd" not in df.columns:
        fx_path = ROOT / "data/raw/eu_cross_assets/eu_cross_assets.csv"
        fx_real = None
        if fx_path.exists():
            try:
                fxd = pd.read_csv(fx_path)
                if "Date" in fxd.columns and "eurusd_rate" in fxd.columns:
                    fxd["Date"] = pd.to_datetime(fxd["Date"])
                    fx_real = fxd.set_index("Date")["eurusd_rate"]
            except Exception:
                fx_real = None
        if fx_real is not None:
            df["eurusd"] = fx_real.reindex(df.index)
        elif "cbot_close" in df.columns and "cbot_eur_t" in df.columns:
            # fallback dérivé (étiqueté comme tel via eurusd_is_derived)
            eurusd_derived = (df["cbot_close"] * 36.744) / df["cbot_eur_t"]
            df["eurusd"] = eurusd_derived.replace([np.inf, -np.inf], np.nan)
            df["eurusd_is_derived"] = True

    # CBOT targets
    cbot_t = pd.read_parquet(ROOT / "data/processed/targets.parquet")
    if "Date" in cbot_t.columns:
        cbot_t = cbot_t.set_index("Date")
    cbot_t.index = pd.to_datetime(cbot_t.index)
    new_cols = [c for c in cbot_t.columns if c not in df.columns]
    df = df.join(cbot_t[new_cols], how="left")

    # Aliases pour les versions h{H} demandées par V8
    if "y_up_h20" not in df.columns and "y_up_h20" in cbot_t.columns:
        df["y_up_h20"] = cbot_t["y_up_h20"]
    if "y_up_h40" not in df.columns and "y_up_h40" in cbot_t.columns:
        df["y_up_h40"] = cbot_t["y_up_h40"]

    # EMA targets
    ema_t_path = ROOT / "data/processed/euronext/ema_targets.parquet"
    if ema_t_path.exists():
        ema_t = pd.read_parquet(ema_t_path)
        if "Date" in ema_t.columns:
            ema_t = ema_t.set_index("Date")
        ema_t.index = pd.to_datetime(ema_t.index)
        new_ema_cols = [c for c in ema_t.columns if c not in df.columns]
        df = df.join(ema_t[new_ema_cols], how="left")

    return df


def filter_out_holdout(df: pd.DataFrame, holdout=("2024-01-01", "2024-12-31")) -> pd.DataFrame:
    """Retire le holdout 2024 du dataset. Le holdout est gardé hors training/research."""
    start, end = pd.Timestamp(holdout[0]), pd.Timestamp(holdout[1])
    mask = (df.index < start) | (df.index > end)
    return df.loc[mask].copy()


# ---------------------------------------------------------------------------
# V8-INFRA-HOLDOUT
# ---------------------------------------------------------------------------

def run_v8_infra_holdout():
    from mais.registry.holdout_lock import read_lock, write_lock
    dataset_path = ROOT / "data/processed/features.parquet"
    payload = write_lock(dataset_path, human_signature="claude-v8-setup-2026-05-30")
    lock = read_lock()
    print(f"  V8-INFRA-HOLDOUT: lock written at {lock['lock_date']}")
    print(f"  holdout_range={lock['holdout_range']}")
    print(f"  dataset_sha256={lock['dataset_sha256'][:16]}...")
    return payload


# ---------------------------------------------------------------------------
# V8-INFRA-REGISTRY
# ---------------------------------------------------------------------------

def run_v8_infra_registry():
    """Merge V6 CSV + V7 JSONL → experiments_unified.jsonl."""
    v6_csv = ARTEFACTS / "experiments" / "experiment_registry_v6.csv"
    v7_jsonl = ARTEFACTS / "registry" / "experiments.jsonl"
    out = ARTEFACTS / "registry" / "experiments_unified.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)

    entries = []

    if v6_csv.exists():
        v6 = pd.read_csv(v6_csv)
        for _, row in v6.iterrows():
            e = row.to_dict()
            e["registry_source"] = "v6_csv"
            e["dataset_version"] = e.get("dataset_version", "v6_legacy")
            entries.append(e)

    if v7_jsonl.exists():
        with open(v7_jsonl) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    e["registry_source"] = "v7_jsonl"
                    entries.append(e)
                except json.JSONDecodeError:
                    continue

    # Déduplication par (experiment_id, dataset_version, registry_source) — dernière entrée gagne
    seen: dict[tuple, dict] = {}
    for e in entries:
        key = (e.get("experiment_id", "unknown"),
               e.get("dataset_version", "unknown"),
               e.get("registry_source", "unknown"))
        seen[key] = e

    with open(out, "w") as f:
        for e in seen.values():
            f.write(json.dumps(e, default=str) + "\n")

    n_v6 = sum(1 for e in seen.values() if e.get("registry_source") == "v6_csv")
    n_v7 = sum(1 for e in seen.values() if e.get("registry_source") == "v7_jsonl")
    print(f"  V8-INFRA-REGISTRY: merged {len(seen)} entries ({n_v6} V6 + {n_v7} V7)")

    summary = {
        "version": "V8-INFRA-REGISTRY",
        "n_unified_entries": len(seen),
        "n_from_v6_csv": n_v6,
        "n_from_v7_jsonl": n_v7,
        "output_path": str(out.relative_to(ROOT)),
    }
    (V8 / "infra_registry_merge.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary


# ---------------------------------------------------------------------------
# V8-FRAGILE-FLAGS-AUDIT
# ---------------------------------------------------------------------------

def run_v8_fragile_flags_audit():
    """Scan tous les artefacts V6/V7 et flag FRAGILE si critères réunis."""
    flagged = []
    v6_dir = ARTEFACTS / "v6"
    v7_dir = ARTEFACTS / "v7"

    def check_payload(name: str, data, src: str):
        results = []
        # patterns courants : data["results"] = [...] ou data["fold_results"] = [...]
        candidates: list[dict] = []
        if isinstance(data, dict):
            if "results" in data and isinstance(data["results"], list):
                candidates.extend([r for r in data["results"] if isinstance(r, dict)])
            if "fold_results" in data and isinstance(data["fold_results"], list):
                candidates.extend([r for r in data["fold_results"] if isinstance(r, dict)])
            # Le payload top-level lui-même
            candidates.append(data)
        for r in candidates:
            n = r.get("n") or r.get("n_oof") or r.get("n_test") or r.get("n_obs")
            auc = r.get("auc") or r.get("AUC") or r.get("global_auc")
            top20 = r.get("top20_da") or r.get("top20")
            da = r.get("da") or r.get("DA")
            if (isinstance(n, (int, float)) and isinstance(auc, (int, float))
                    and ((n < 100 and auc >= 0.85) or (n < 200 and auc >= 0.90))):
                results.append({"target": r.get("target", "?"),
                                "n": n, "auc": round(auc, 4),
                                "fragile_reason": "auc_high_n_low"})
            if (isinstance(n, (int, float)) and isinstance(top20, (int, float))
                    and n < 100 and top20 >= 0.90):
                results.append({"target": r.get("target", "?"),
                                "n": n, "top20": round(top20, 4),
                                "fragile_reason": "top20_high_n_low"})
            if (isinstance(n, (int, float)) and isinstance(da, (int, float))
                    and n < 200 and da >= 0.90):
                results.append({"target": r.get("target", "?"),
                                "n": n, "da": round(da, 4),
                                "fragile_reason": "da_high_n_low"})
        if results:
            flagged.append({"artefact": name, "source": src, "fragile_entries": results})

    for d in (v6_dir, v7_dir):
        if not d.exists():
            continue
        for p in d.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            check_payload(p.name, data, str(p.relative_to(ROOT)))

    summary = {
        "version": "V8-FRAGILE-FLAGS-AUDIT",
        "n_artefacts_scanned": sum(1 for _ in (v6_dir.glob("*.json"))) + sum(1 for _ in v7_dir.glob("*.json")),
        "n_artefacts_with_fragile_entries": len(flagged),
        "flagged": flagged,
    }
    (V8 / "fragile_flags_audit.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"  V8-FRAGILE-FLAGS-AUDIT: {len(flagged)} artefacts contiennent des résultats FRAGILE")
    for f in flagged[:5]:
        print(f"    {f['artefact']}: {len(f['fragile_entries'])} fragile entries")
    return summary


# ---------------------------------------------------------------------------
# V8-META-REVALIDATION
# ---------------------------------------------------------------------------

def run_v8_meta_revalidation(df: pd.DataFrame, fast: bool = False):
    from mais.meta.meta_revalidation_v8 import save_meta_revalidation
    result = save_meta_revalidation(df, fast=fast)
    print(f"  V8-META-REVALIDATION: global_verdict={result.get('global_verdict')}")
    for tgt, payload in result.get("results_by_target", {}).items():
        summary = payload.get("summary", {})
        print(f"    {tgt}: verdict={payload['verdict']} | "
              f"median_auc={summary.get('median_auc')} | "
              f"n_combos×proto={summary.get('n_valid_combinations_protocols')}")
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("V8 PHASE A + V8-META-REVALIDATION")
    print("=" * 60)

    print("\n[1/4] V8-INFRA-HOLDOUT")
    run_v8_infra_holdout()

    print("\n[2/4] V8-INFRA-REGISTRY")
    run_v8_infra_registry()

    print("\n[3/4] V8-FRAGILE-FLAGS-AUDIT")
    run_v8_fragile_flags_audit()

    print("\n[4/4] V8-META-REVALIDATION (fast=False, full)")
    print("  Loading master dataset...")
    df = load_master_dataset()
    print(f"  master shape pre-holdout-filter: {df.shape}")
    df_no_hold = filter_out_holdout(df)
    print(f"  master shape post-holdout-filter (2024 excluded): {df_no_hold.shape}")
    run_v8_meta_revalidation(df_no_hold, fast=False)

    print("\nDONE V8 Phase A + META-REVALIDATION")
    print(f"  artefacts in {V8}")
