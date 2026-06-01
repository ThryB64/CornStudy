import json

import numpy as np
import pandas as pd
import yaml

from mais.features import _crop_progress_weekly_to_daily
from mais.features.phenology import build_phenology_features, evaluate_crop_condition_windows


def _weekly_crop() -> pd.DataFrame:
    dates = pd.date_range("2020-05-04", periods=12, freq="W-MON")
    return pd.DataFrame(
        {
            "Date": dates,
            "condition_gd_ex_pct": np.linspace(72, 60, len(dates)),
            "planted_pct": np.linspace(10, 100, len(dates)),
            "silking_pct": np.linspace(0, 80, len(dates)),
            "mature_pct": np.linspace(0, 10, len(dates)),
            "harvested_pct": np.linspace(0, 5, len(dates)),
        }
    )


def test_crop_condition_enabled(project_root):
    cfg = yaml.safe_load((project_root / "config" / "sources.yaml").read_text(encoding="utf-8"))
    source = next(item for item in cfg["sources"] if item["name"] == "usda_nass_crop_condition")
    assert source["enabled"] is True


def test_phenology_no_leakage():
    dates = pd.Series(pd.to_datetime(["2021-06-28", "2021-10-04", "2021-12-15"]))
    pheno = build_phenology_features(dates)
    assert pheno.loc[0, "pheno_silking_window"] == 1.0
    assert pheno.loc[1, "pheno_harvest_window"] == 1.0
    assert pd.isna(pheno.loc[2, "pheno_week_in_season"])
    assert set(pheno.columns) == {
        "Date",
        "pheno_silking_window",
        "pheno_dough_dent_window",
        "pheno_harvest_window",
        "pheno_growing_season",
        "pheno_week_in_season",
    }


def test_crop_condition_nan_off_season():
    daily = pd.Series(pd.bdate_range("2020-05-01", "2020-12-31"))
    result = _crop_progress_weekly_to_daily(daily, _weekly_crop())
    december = result[pd.to_datetime(result["Date"]).dt.month == 12]
    assert december["crop_ge_pct"].isna().all()
    assert result["crop_condition_available"].isin([0.0, 1.0]).all()


def test_crop_condition_ablation_documented(tmp_path):
    rng = np.random.default_rng(44)
    dates = pd.bdate_range("2010-01-04", periods=1800)
    df = pd.DataFrame({"Date": dates})
    df["baseline_signal"] = rng.normal(0, 1, len(df))
    df["crop_ge_pct_filled"] = 65 + rng.normal(0, 5, len(df))
    pheno = build_phenology_features(df["Date"])
    df = df.merge(pheno, on="Date", how="left")
    df["y_up_h40"] = (df["baseline_signal"] - 0.01 * df["crop_ge_pct_filled"] > -0.6).astype(int)
    out = tmp_path / "crop_condition_windows.json"
    payload = evaluate_crop_condition_windows(df, output_path=out)
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert payload["verdict"] in {"CONFIRMÉ", "PROMETTEUR", "NEUTRE", "REJETÉ", "INCONCLU"}
    assert {"jun_aug", "october", "off_season"}.issubset(loaded["windows"])


def test_ge_pct_range():
    daily = pd.Series(pd.bdate_range("2020-05-01", "2020-08-31"))
    result = _crop_progress_weekly_to_daily(daily, _weekly_crop())
    ge = result["crop_ge_pct"].dropna()
    assert ge.between(0, 100).all()
