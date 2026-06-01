import json

import numpy as np
import pandas as pd
import yaml

from mais.collect.fas_exports import download, empty_fas_weekly
from mais.features import _fas_weekly_to_daily
from mais.features.fas_features import build_fas_features, evaluate_fas_ablation


def _weekly_fas(n: int = 120) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.date_range("2018-09-06", periods=n, freq="W-THU")
    sales = rng.normal(950_000, 120_000, n).clip(min=10_000)
    china = sales * rng.uniform(0.05, 0.35, n)
    return pd.DataFrame(
        {
            "Date": dates,
            "export_sales_mt": sales,
            "export_china_sales_mt": china,
            "usda_export_forecast_mt": 48_000_000.0,
        }
    )


def test_fas_no_leakage():
    weekly = _weekly_fas(8)
    daily = pd.Series(pd.bdate_range("2018-09-06", "2018-10-31"))
    result = build_fas_features(weekly, daily)
    first_available = result["export_sales_weekly_mt"].first_valid_index()
    assert first_available is not None
    assert pd.to_datetime(result.loc[first_available, "Date"]) > weekly["Date"].min()


def test_fas_coverage_documented(project_root):
    cfg = yaml.safe_load((project_root / "config" / "sources.yaml").read_text(encoding="utf-8"))
    source = next(item for item in cfg["sources"] if item["name"] == "usda_fas_export_sales")
    assert source["enabled"] is True
    assert source["api_key_env"] == "FAS_API_KEY"


def test_fas_fallback_no_crash(tmp_path, monkeypatch):
    monkeypatch.delenv("FAS_API_KEY", raising=False)
    result = download(tmp_path, {"api_key_env": "FAS_API_KEY", "commodity": "CORN", "write_interim": False})
    assert "empty fallback" in result
    assert (tmp_path / "fas_export_sales.csv").exists()
    assert set(empty_fas_weekly().columns).issuperset({"Date", "export_sales_mt"})


def test_fas_delta_auc_documented(tmp_path):
    weekly = _weekly_fas(260)
    daily = pd.Series(pd.bdate_range("2018-09-06", periods=1300))
    fas = _fas_weekly_to_daily(daily, weekly)
    rng = np.random.default_rng(7)
    df = fas.copy()
    df["baseline_signal"] = rng.normal(0, 1, len(df))
    score = df["baseline_signal"] + df["export_momentum_4w"].fillna(0) / 500_000
    df["y_up_h40"] = (score > score.median()).astype(int)
    out = tmp_path / "fas_ablation.json"
    payload = evaluate_fas_ablation(df, output_path=out)
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert payload["verdict"] in {"CONFIRMÉ", "PROMETTEUR", "NEUTRE", "REJETÉ", "INCONCLU"}
    assert {"global", "sept_jan", "off_season"}.issubset(loaded["windows"])


def test_fas_feature_columns_present():
    result = build_fas_features(_weekly_fas(), pd.Series(pd.bdate_range("2018-09-06", periods=120)))
    expected = {
        "export_sales_weekly_mt",
        "export_sales_accumulated_mt",
        "export_pace_vs_usda_forecast",
        "export_pace_vs_5y_avg",
        "export_sales_weekly_zscore",
        "export_china_pct_total",
        "export_momentum_4w",
        "export_vs_same_week_last_year",
    }
    assert expected.issubset(result.columns)
