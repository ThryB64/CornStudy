"""Build the meta-database from per-model OOF predictions."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from mais.paths import META_DB_PARQUET, PREDICTIONS_DIR
from mais.utils import get_logger, read_parquet, write_parquet

log = get_logger("mais.meta.db")


def build_meta_database(target: str = "y_logret_h20",
                        date_col: str = "Date") -> pd.DataFrame:
    """Read all <model>.parquet files for a target, build a wide table:

    ``Date | y_true | pred_<model1> | pred_<model2> | ... | fold``
    """
    pred_dir = PREDICTIONS_DIR / target
    if not pred_dir.is_dir():
        raise FileNotFoundError(f"No predictions directory: {pred_dir}")

    files = sorted(pred_dir.glob("*.parquet"))
    if not files:
        raise RuntimeError(f"No model predictions in {pred_dir}")

    base = None
    for f in files:
        df = read_parquet(f)
        model_name = f.stem
        df = df.rename(columns={"y_pred": f"pred_{model_name}"})
        keep = [date_col, "y_true", f"pred_{model_name}", "fold"]
        keep = [c for c in keep if c in df.columns]
        df = df[keep]
        if base is None:
            base = df
        else:
            base = base.merge(df.drop(columns=["y_true", "fold"], errors="ignore"),
                               on=date_col, how="outer")

    base = base.sort_values(date_col).reset_index(drop=True)
    write_parquet(base, META_DB_PARQUET)
    log.info("meta_database_built", target=target, models=len(files),
              rows=len(base), out=str(META_DB_PARQUET))
    return base
