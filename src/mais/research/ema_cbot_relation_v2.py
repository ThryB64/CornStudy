"""NB2-02 — Transmission EMA/CBOT v2 avec rolling correlations et Granger OOF."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET, PROJECT_ROOT
from mais.research.ema_cbot_cointegration import build_cbot_cointegration
from mais.research.ema_granger_validation import build_granger_validation

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_cbot_relation_v2.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_CBOT_RELATION_V2.md"


def _load_aligned() -> pd.DataFrame:
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    cols = ["Date", "ema_front_price", "cbot_eur_t", "ema_cbot_basis"]
    df = feats.loc[feats["ema_front_price"].notna() & feats["cbot_eur_t"].notna(), cols].copy()
    df = df.sort_values("Date").reset_index(drop=True)
    df["ema_ret"] = df["ema_front_price"].pct_change()
    df["cbot_ret"] = df["cbot_eur_t"].pct_change()
    return df


def _rolling_corr(df: pd.DataFrame, window: int, a: str, b: str) -> dict:
    corr = df[a].rolling(window).corr(df[b]).dropna()
    return {
        "window": int(window),
        "n": int(len(corr)),
        "mean": float(corr.mean()),
        "median": float(corr.median()),
        "min": float(corr.min()),
        "max": float(corr.max()),
        "pct_gt_0_8": float((corr > 0.8).mean()),
        "pct_lt_0_5": float((corr < 0.5).mean()),
    }


def _lead_lag(df: pd.DataFrame) -> list[dict]:
    rows = []
    base = df[["ema_ret", "cbot_ret"]].dropna().reset_index(drop=True)
    for lag in range(-5, 6):
        if lag < 0:
            corr = base["ema_ret"].corr(base["cbot_ret"].shift(-lag))
            interpretation = "CBOT leads EMA" if corr == corr else "insufficient"
        elif lag > 0:
            corr = base["ema_ret"].shift(lag).corr(base["cbot_ret"])
            interpretation = "EMA leads CBOT" if corr == corr else "insufficient"
        else:
            corr = base["ema_ret"].corr(base["cbot_ret"])
            interpretation = "contemporaneous"
        rows.append({"lag": lag, "corr": float(corr), "interpretation": interpretation})
    return rows


def _rolling_beta(df: pd.DataFrame, window: int = 260) -> dict:
    sub = df[["Date", "ema_ret", "cbot_ret"]].dropna().reset_index(drop=True)
    betas = []
    for i in range(window, len(sub) + 1):
        win = sub.iloc[i - window:i]
        x = win["cbot_ret"].values
        y = win["ema_ret"].values
        if np.nanstd(x) == 0:
            continue
        beta = float(np.cov(x, y)[0, 1] / np.var(x))
        betas.append(beta)
    return {
        "window": window,
        "n_windows": len(betas),
        "mean_beta_cbot_to_ema": float(np.nanmean(betas)) if betas else float("nan"),
        "std_beta_cbot_to_ema": float(np.nanstd(betas)) if betas else float("nan"),
        "min_beta_cbot_to_ema": float(np.nanmin(betas)) if betas else float("nan"),
        "max_beta_cbot_to_ema": float(np.nanmax(betas)) if betas else float("nan"),
    }


def _rolling_r2_decomposition(df: pd.DataFrame, window: int = 260) -> dict:
    sub = df[["ema_ret", "cbot_ret", "ema_cbot_basis"]].dropna().copy()
    sub["basis_chg"] = sub["ema_cbot_basis"].diff()
    sub = sub.dropna().reset_index(drop=True)
    r2_vals = []
    for i in range(window, len(sub) + 1):
        win = sub.iloc[i - window:i]
        y = win["ema_ret"].values
        x = win[["cbot_ret", "basis_chg"]].values
        xc = np.column_stack([np.ones(len(x)), x])
        coefs, _, _, _ = np.linalg.lstsq(xc, y, rcond=None)
        pred = xc @ coefs
        ss_res = float(np.sum((y - pred) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r2_vals.append(1 - ss_res / ss_tot if ss_tot else np.nan)
    return {
        "window": window,
        "n_windows": len(r2_vals),
        "mean_r2": float(np.nanmean(r2_vals)) if r2_vals else float("nan"),
        "min_r2": float(np.nanmin(r2_vals)) if r2_vals else float("nan"),
        "max_r2": float(np.nanmax(r2_vals)) if r2_vals else float("nan"),
    }


def build_cbot_relation_v2() -> dict:
    df = _load_aligned()
    coint = build_cbot_cointegration()
    granger_oof = build_granger_validation()
    lead_lag = _lead_lag(df)
    best_lag = max(lead_lag, key=lambda row: abs(row["corr"]) if row["corr"] == row["corr"] else -1)
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "n_obs": int(len(df)),
        "period_start": str(df["Date"].min().date()),
        "period_end": str(df["Date"].max().date()),
        "static": coint.get("static_correlation", {}),
        "cointegration": {
            "engle_granger": coint.get("engle_granger", {}),
            "vecm": coint.get("vecm", {}),
        },
        "rolling_corr_price_60d": _rolling_corr(df, 60, "ema_front_price", "cbot_eur_t"),
        "rolling_corr_price_260d": _rolling_corr(df, 260, "ema_front_price", "cbot_eur_t"),
        "rolling_corr_returns_60d": _rolling_corr(df.dropna(), 60, "ema_ret", "cbot_ret"),
        "rolling_corr_returns_260d": _rolling_corr(df.dropna(), 260, "ema_ret", "cbot_ret"),
        "lead_lag_returns": lead_lag,
        "best_abs_lead_lag": best_lag,
        "rolling_beta_260d": _rolling_beta(df),
        "rolling_r2_decomposition_260d": _rolling_r2_decomposition(df),
        "granger": {
            "in_sample_cbot_to_ema": coint.get("granger_cbot_to_ema", {}),
            "in_sample_ema_to_cbot": coint.get("granger_ema_to_cbot", {}),
            "ema_to_cbot_oof_validation": granger_oof.get("summary", {}),
            "mandatory_wording": "Granger EMA→CBOT IN-SAMPLE : significatif mais NON CONFIRMÉ en validation robuste OOF. La relation est surtout contemporaine.",
        },
        "key_findings": {
            "corr_price_levels": coint.get("key_findings", {}).get("corr_price_levels"),
            "corr_daily_returns": coint.get("key_findings", {}).get("corr_daily_returns"),
            "vecm_half_life_days": coint.get("key_findings", {}).get("vecm_half_life_days"),
            "granger_ema_to_cbot_oof_verdict": granger_oof.get("summary", {}).get("overall_verdict"),
            "relation_label": "forte, structurelle et surtout contemporaine",
        },
    }


def _json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return str(obj.date())
    if isinstance(obj, bool):
        return bool(obj)
    raise TypeError(f"Not serialisable: {type(obj)}")


def _write_markdown(data: dict, path: Path) -> None:
    k = data["key_findings"]
    lines = [
        "# EMA CBOT RELATION V2",
        "",
        "> Source EMA exploratoire/proxy. Résultats expérimentaux.",
        "",
        "## Verdict",
        "",
        "- EMA et CBOT sont fortement liés et cointégrés.",
        "- La relation est surtout structurelle et contemporaine.",
        "- Granger EMA→CBOT est significatif in-sample mais NON CONFIRMÉ en validation robuste OOF.",
        "",
        "## Métriques clés",
        "",
        "| Métrique | Valeur |",
        "|---|---:|",
        f"| Corrélation niveaux | {k['corr_price_levels']:.3f} |",
        f"| Corrélation retours journaliers | {k['corr_daily_returns']:.3f} |",
        f"| Demi-vie VECM | {k['vecm_half_life_days']:.1f} jours |",
        f"| Granger EMA→CBOT OOF | {k['granger_ema_to_cbot_oof_verdict']} |",
        "",
        "## Wording obligatoire",
        "",
        data["granger"]["mandatory_wording"],
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_cbot_relation_v2(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_cbot_relation_v2()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_cbot_relation_v2()
    print(f"CBOT relation v2 saved -> {out}")
