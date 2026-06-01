"""V7-16 — Microstructure et liquidité EMA."""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.registry.experiment_registry import register_experiment

_OUTPUT = ARTEFACTS_DIR / "v7" / "microstructure.json"


def _expandz(s: pd.Series) -> pd.Series:
    mu = s.expanding().mean()
    std = s.expanding().std()
    return ((s - mu) / std.replace(0, np.nan)).rename(s.name + "_z" if s.name else "z")


def build_microstructure_features(df: pd.DataFrame) -> pd.DataFrame:
    """Features de microstructure EMA : volume, OI, liquidité."""
    feats: dict[str, pd.Series] = {}

    if "ema_volume_total" in df.columns:
        vol = df["ema_volume_total"]
        feats["ema_volume_z60"] = _expandz(vol)
        low_liq = vol < vol.rolling(252, min_periods=30).quantile(0.10)
        feats["ema_low_liquidity"] = low_liq.astype(int)
        feats["ema_volume_ma20_ratio"] = (vol / vol.rolling(20, min_periods=5).mean()).clip(0, 10)

    if "ema_oi_total" in df.columns:
        oi = df["ema_oi_total"]
        feats["ema_oi_change_pct"] = oi.pct_change(20).replace([np.inf, -np.inf], np.nan)
        feats["ema_oi_z60"] = _expandz(oi)

    if "volume_oi_ratio_proxy" in df.columns:
        feats["ema_vol_oi_ratio"] = df["volume_oi_ratio_proxy"]

    if "ema_open_interest_available" in df.columns:
        feats["ema_oi_available"] = df["ema_open_interest_available"].astype(int)

    result = pd.DataFrame(feats, index=df.index)
    # anti-leakage : shift(1)
    return result.shift(1)


def compute_microstructure_report(df: pd.DataFrame) -> dict[str, Any]:
    """Analyse des patterns de liquidité EMA."""
    report: dict[str, Any] = {
        "version": "V7-16",
        "n_dates": len(df),
        "available_features": [],
    }

    if "ema_volume_total" in df.columns:
        vol = df["ema_volume_total"].dropna()
        n_low = int((vol < vol.quantile(0.10)).sum())
        report["available_features"].append("volume")
        report["volume"] = {
            "n_obs": len(vol),
            "mean": float(vol.mean()),
            "median": float(vol.median()),
            "std": float(vol.std()),
            "n_low_liquidity_days": n_low,
            "pct_low_liquidity": round(n_low / len(vol) * 100, 2) if len(vol) > 0 else 0,
        }

    if "ema_oi_total" in df.columns:
        oi = df["ema_oi_total"].dropna()
        report["available_features"].append("open_interest")
        report["open_interest"] = {
            "n_obs": len(oi),
            "mean": float(oi.mean()),
            "std": float(oi.std()),
        }

    # Corrélation liquidité vs basis
    if "ema_volume_total" in df.columns and "ema_cbot_basis" in df.columns:
        common = df[["ema_volume_total", "ema_cbot_basis"]].dropna()
        corr_vol_basis = float(common["ema_volume_total"].corr(common["ema_cbot_basis"]))
        report["corr_volume_vs_basis"] = round(corr_vol_basis, 4)
        report["available_features"].append("basis_liquidity_correlation")

    if "ema_volume_total" in df.columns and "ema_cbot_basis" in df.columns:
        # Comparer le spread basis en jours haute vs basse liquidité
        vol = df["ema_volume_total"]
        low_liq = vol < vol.rolling(252, min_periods=30).quantile(0.10)
        high_liq = vol > vol.rolling(252, min_periods=30).quantile(0.90)
        basis = df["ema_cbot_basis"].abs()
        basis_low = float(basis[low_liq].mean()) if low_liq.sum() > 0 else None
        basis_high = float(basis[high_liq].mean()) if high_liq.sum() > 0 else None
        report["abs_basis_low_liquidity"] = round(basis_low, 4) if basis_low else None
        report["abs_basis_high_liquidity"] = round(basis_high, 4) if basis_high else None

    report["n_high_risk_days"] = report.get("volume", {}).get("n_low_liquidity_days", 0)
    report["verdict"] = "MICROSTRUCTURE_ANALYZED"
    return report


def save_microstructure(df: pd.DataFrame) -> dict[str, Any]:
    result = compute_microstructure_report(df)
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    register_experiment(
        experiment_id="V7-16",
        target="microstructure_ema",
        horizon=0,
        model="liquidity_analysis",
        cv_protocol="none",
        embargo_days=0,
        n_oof=0,
        features=result.get("available_features", []),
        metrics={
            "n_dates": result["n_dates"],
            "n_high_risk_days": result.get("n_high_risk_days", 0),
            "corr_volume_vs_basis": result.get("corr_volume_vs_basis"),
        },
        p_value=None,
        verdict="DONE",
        artefact_paths=[str(_OUTPUT.relative_to(PROJECT_ROOT))],
        review_status="DONE",
    )
    return result
