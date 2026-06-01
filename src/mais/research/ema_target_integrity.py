"""FIX-EMA-01 — Audit intégrité des targets EMA futures."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, PROJECT_ROOT
from mais.research.ema_direction_benchmarks_v2 import _load_dataset

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_target_integrity.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_TARGET_INTEGRITY.md"

_TARGET_HORIZONS = {
    "y_up_h20_ema_raw": 20,
    "y_up_h40_ema_raw": 40,
    "y_ema_outperforms_cbot_h20": 20,
    "y_ema_outperforms_cbot_h40": 40,
    "basis_reversion_h20": 20,
    "ema_vol_high_h20": 20,
    "eu_residual_shock_up_h20": 20,
    "eu_residual_shock_down_h20": 20,
}


def _tail_audit(df: pd.DataFrame, target: str, horizon: int) -> dict:
    if target not in df.columns:
        return {"target": target, "horizon": horizon, "status": "missing"}
    tail = df[target].tail(horizon)
    return {
        "target": target,
        "horizon": horizon,
        "n_rows": int(df[target].notna().sum()),
        "base_rate": float(df[target].dropna().mean()) if df[target].notna().any() else float("nan"),
        "tail_nan_count": int(tail.isna().sum()),
        "tail_non_null_count": int(tail.notna().sum()),
        "tail_integrity_ok": bool(tail.isna().all()),
        "unexpected_tail_values": [float(x) for x in tail.dropna().tolist()],
    }


def build_target_integrity_audit() -> dict:
    df = _load_dataset()
    audits = [_tail_audit(df, target, horizon) for target, horizon in _TARGET_HORIZONS.items()]
    bad = [row for row in audits if row.get("tail_integrity_ok") is False]
    return {
        "source_quality": "exploratoire_barchart_proxy",
        "targets_checked": audits,
        "n_targets_checked": len(audits),
        "n_failed": len(bad),
        "failed_targets": [row["target"] for row in bad],
        "verdict": "TARGET_INTEGRITY_PASS" if not bad else "TARGET_INTEGRITY_FAIL",
        "rule": "Futures inconnus en fin de série doivent rester NaN, jamais devenir 0 via NaN > 0.",
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
    lines = [
        "# EMA TARGET INTEGRITY",
        "",
        "> Audit FIX-EMA-01 : les cibles futures inconnues doivent rester NaN.",
        "",
        f"**Verdict :** {data['verdict']}",
        "",
        "| Target | Horizon | Non-null | Base rate | Tail NaN | Verdict |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in data["targets_checked"]:
        base_rate = row.get("base_rate")
        base_text = "N/A" if base_rate != base_rate else f"{base_rate:.1%}"
        lines.append(
            f"| {row['target']} | {row['horizon']} | {row.get('n_rows', 0)} | "
            f"{base_text} | {row.get('tail_nan_count', 0)} | "
            f"{'PASS' if row.get('tail_integrity_ok') else 'FAIL'} |"
        )
    lines += [
        "",
        "## Règle",
        "",
        data["rule"],
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_target_integrity_audit(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_target_integrity_audit()
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    _write_markdown(data, _DOC_OUTPUT)
    return path


if __name__ == "__main__":
    out = save_target_integrity_audit()
    print(f"Target integrity audit saved -> {out}")
