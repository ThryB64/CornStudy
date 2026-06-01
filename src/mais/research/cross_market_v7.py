"""V7-05 — Relations croisées CBOT ↔ EMA."""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "cross_market_study.json"


def _oof_auc(x_df: pd.DataFrame, y: pd.Series, n_splits: int = 4) -> float | None:
    try:
        from lightgbm import LGBMClassifier
        from sklearn.metrics import roc_auc_score
    except ImportError:
        return None

    common = x_df.join(y.rename("target")).dropna()
    if len(common) < 100 or common["target"].nunique() < 2:
        return None

    x_c = common.drop(columns=["target"]).fillna(0)
    y_c = common["target"]
    tscv = TimeSeriesSplit(n_splits=n_splits)
    oof = np.full(len(x_c), np.nan)

    for tr_idx, te_idx in tscv.split(x_c):
        if len(tr_idx) < 30 or y_c.iloc[tr_idx].nunique() < 2:
            continue
        clf = LGBMClassifier(n_estimators=100, seed=42, verbose=-1, n_jobs=1)
        clf.fit(x_c.iloc[tr_idx], y_c.iloc[tr_idx])
        oof[te_idx] = clf.predict_proba(x_c.iloc[te_idx])[:, 1]

    valid = ~np.isnan(oof) & y_c.notna().values
    if valid.sum() < 30 or len(np.unique(y_c.values[valid])) < 2:
        return None
    from sklearn.metrics import roc_auc_score
    return round(float(roc_auc_score(y_c.values[valid], oof[valid])), 4)


def _get_feature_groups(df: pd.DataFrame) -> dict[str, list[str]]:
    exclude = {"y_", "Date", "date", "return_", "future_", "storage_", "prob_"}
    all_feat = [c for c in df.columns if not any(p in c for p in exclude)
                and df[c].dtype in [np.float64, float] and df[c].notna().mean() > 0.3]

    ema_feats = [c for c in all_feat if any(k in c for k in ["ema_", "basis_", "roll_risk"])][:20]
    cbot_feats = [c for c in all_feat if c not in ema_feats
                  and any(k in c for k in ["corn_", "cbot_", "wasde_", "cot_", "factor_", "eia_"])][:30]
    return {"ema": ema_feats, "cbot": cbot_feats}


def run_cross_market_study(df: pd.DataFrame) -> dict[str, Any]:
    groups = _get_feature_groups(df)
    ema_feats = groups["ema"]
    cbot_feats = groups["cbot"]

    y_cbot = next((df[c] for c in ["y_up_h20", "y_up_h60"] if c in df.columns), None)
    y_ema = next((df[c] for c in ["y_up_h20_ema", "y_up_h40_ema"] if c in df.columns), None)

    results: dict[str, Any] = {
        "n_ema_features": len(ema_feats),
        "n_cbot_features": len(cbot_feats),
    }

    if y_cbot is not None and cbot_feats:
        auc_base = _oof_auc(df[cbot_feats], y_cbot)
        auc_with_ema = _oof_auc(df[cbot_feats + ema_feats], y_cbot) if ema_feats else None
        results["cbot_model"] = {
            "auc_cbot_only": auc_base,
            "auc_cbot_plus_ema": auc_with_ema,
            "delta_ema_adds_to_cbot": round((auc_with_ema or 0) - (auc_base or 0), 4)
                if auc_base and auc_with_ema else None,
        }

    if y_ema is not None and ema_feats:
        auc_ema_base = _oof_auc(df[ema_feats], y_ema)
        auc_ema_plus_cbot = _oof_auc(df[ema_feats + cbot_feats], y_ema) if cbot_feats else None
        results["ema_model"] = {
            "auc_ema_only": auc_ema_base,
            "auc_ema_plus_cbot": auc_ema_plus_cbot,
            "delta_cbot_adds_to_ema": round((auc_ema_plus_cbot or 0) - (auc_ema_base or 0), 4)
                if auc_ema_base and auc_ema_plus_cbot else None,
        }

    d_ema = results.get("cbot_model", {}).get("delta_ema_adds_to_cbot") or 0
    d_cbot = results.get("ema_model", {}).get("delta_cbot_adds_to_ema") or 0
    verdict = (
        "BIDIRECTIONAL" if d_ema > 0.02 and d_cbot > 0.02
        else "EMA_ADDS_TO_CBOT" if d_ema > 0.02
        else "CBOT_ADDS_TO_EMA" if d_cbot > 0.02
        else "NONE"
    )

    results.update({"version": "V7-05", "verdict": verdict, "experiment_type": "PREDICTIVE_OOF"})
    return results


def save_cross_market_study(df: pd.DataFrame) -> dict[str, Any]:
    result = run_cross_market_study(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    register_experiment(
        experiment_id="V7-05",
        target="cross_market_cbot_ema",
        horizon=40,
        model="lgbm_oof_cross_market",
        cv_protocol="time_series_split_4",
        embargo_days=0,
        n_oof=0,
        features=["ema_features", "cbot_features"],
        metrics={
            "verdict": result["verdict"],
            "delta_ema_adds_to_cbot": result.get("cbot_model", {}).get("delta_ema_adds_to_cbot"),
            "delta_cbot_adds_to_ema": result.get("ema_model", {}).get("delta_cbot_adds_to_ema"),
        },
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
