from __future__ import annotations

import pandas as pd

from mais.research.ema_data_audit import (
    RECOMMENDED_CURVE_LABEL,
    SOURCE_QUALITY_NOTE,
    render_markdown,
    run_ema_data_audit,
    summarize_curve_daily,
    summarize_curve_features,
    summarize_targets,
)


def test_summarize_curve_daily_distribution() -> None:
    curve = pd.DataFrame(
        {
            "date": [
                "2024-01-01",
                "2024-01-01",
                "2024-01-02",
                "2024-01-03",
                "2024-01-03",
                "2024-01-03",
            ],
            "contract_code": ["A", "B", "A", "A", "B", "C"],
        }
    )

    summary = summarize_curve_daily(curve)

    assert summary["unique_dates"] == 3
    assert summary["contract_count_distribution"] == {"1": 1, "2": 1, "3": 1}
    assert summary["dates_ge_2_contracts_pct"] == 2 / 3


def test_sparse_curve_rates_are_reported_as_sparse() -> None:
    features = pd.DataFrame(
        {
            "Date": pd.bdate_range("2024-01-01", periods=10),
            "ema_spread_f0_f1": [1.0] + [None] * 9,
            "ema_curve_slope_3": [None] * 10,
        }
    )

    summary = summarize_curve_features(features)

    assert summary["curve_label_recommendation"] == RECOMMENDED_CURVE_LABEL
    assert summary["sparse_curve_feature_non_null_rates"]["ema_spread_f0_f1"] == 0.1
    assert "ema_spread_f0_f1" in summary["sparse_below_20pct"]


def test_target_roll_cross_rates() -> None:
    targets = pd.DataFrame(
        {
            "Date": pd.bdate_range("2024-01-01", periods=4),
            "y_up_h20_ema_raw": [1.0, 0.0, None, None],
            "y_up_h20_ema_adjusted": [1.0, 0.0, None, None],
            "y_up_h20_ema_no_roll": [1.0, None, None, None],
            "target_crosses_roll_h20": [0.0, 1.0, None, None],
        }
    )

    summary = summarize_targets(targets)

    assert summary["by_horizon"]["20"]["cross_roll_rate"] == 0.5
    assert summary["by_horizon"]["20"]["raw_non_null"] == 2
    assert summary["by_horizon"]["20"]["no_roll_non_null"] == 1


def test_run_ema_data_audit_writes_json_and_markdown(tmp_path) -> None:
    dates = pd.bdate_range("2024-01-01", periods=8)
    contracts = pd.DataFrame(
        {
            "date": [dates[0], dates[0], dates[1]],
            "contract_code": ["EMA_H2024", "EMA_M2024", "EMA_F2024"],
            "source": ["barchart_proxy_exploratory", "euronext_ajax_prices", "barchart_proxy_exploratory"],
            "source_quality": ["exploratory", "official", "exploratory"],
            "month_code": ["H", "M", "F"],
            "import_verdict": ["usable", "usable", "legacy_or_ambiguous"],
            "price": [200.0, 202.0, 198.0],
        }
    )
    curve = contracts[["date", "contract_code", "price"]]
    front = pd.DataFrame(
        {
            "date": dates,
            "contract_code": ["EMA_H2024"] * 4 + ["EMA_M2024"] * 4,
            "price": range(200, 208),
            "roll_event": [False, False, False, False, True, False, False, False],
            "roll_adjustment": [0.0, 0.0, 0.0, 0.0, 5.0, 0.0, 0.0, 0.0],
        }
    )
    adjusted = front.assign(adjusted_price=front["price"] - front["roll_adjustment"].cumsum())
    curve_features = pd.DataFrame(
        {
            "Date": dates,
            "ema_spread_f0_f1": [None, 1.0, None, None, None, None, None, None],
            "ema_curve_slope_3": [None] * 8,
        }
    )
    targets = pd.DataFrame(
        {
            "Date": dates,
            "y_up_h20_ema_raw": [1.0, 0.0] + [None] * 6,
            "y_up_h20_ema_adjusted": [1.0, 0.0] + [None] * 6,
            "y_up_h20_ema_no_roll": [1.0, None] + [None] * 6,
            "target_crosses_roll_h20": [0.0, 1.0] + [None] * 6,
        }
    )
    paths = {}
    for name, frame in {
        "contracts": contracts,
        "curve": curve,
        "front": front,
        "adjusted": adjusted,
        "liquid": front,
        "harvest": front,
        "features": curve_features,
        "targets": targets,
    }.items():
        path = tmp_path / f"{name}.parquet"
        frame.to_parquet(path, index=False)
        paths[name] = path

    payload = run_ema_data_audit(
        contract_daily_path=paths["contracts"],
        curve_daily_path=paths["curve"],
        front_raw_path=paths["front"],
        front_adjusted_path=paths["adjusted"],
        liquid_raw_path=paths["liquid"],
        harvest_nov_path=paths["harvest"],
        curve_features_path=paths["features"],
        ema_targets_path=paths["targets"],
        output_json_path=tmp_path / "audit.json",
        output_markdown_path=tmp_path / "audit.md",
    )

    assert payload["source_quality_note"] == SOURCE_QUALITY_NOTE
    assert (tmp_path / "audit.json").exists()
    assert (tmp_path / "audit.md").exists()
    assert payload["contract_daily"]["legacy_f_usable_rows"] == 0
    assert payload["continuous_series"]["front_raw"]["rolls"]["n_rolls"] == 1


def test_render_markdown_contains_guardrails() -> None:
    payload = {
        "source_quality_note": SOURCE_QUALITY_NOTE,
        "recommended_curve_label": RECOMMENDED_CURVE_LABEL,
        "contract_daily": {
            "rows": 0,
            "date_start": None,
            "date_end": None,
            "unique_dates": 0,
            "unique_contracts": 0,
            "source_counts": {},
            "usable_month_counts": {},
            "legacy_f_usable_rows": 0,
        },
        "continuous_series": {
            "front_raw": {"rows": 0, "date_start": None, "date_end": None, "rolls": {}},
            "front_adjusted": {"rows": 0, "date_start": None, "date_end": None},
            "liquid_raw": {"rows": 0, "date_start": None, "date_end": None},
            "harvest_nov": {"rows": 0, "date_start": None, "date_end": None},
        },
        "curve_daily": {
            "rows": 0,
            "unique_dates": 0,
            "avg_contracts_per_date": None,
            "contract_count_distribution": {},
            "dates_ge_2_contracts_pct": None,
            "dates_ge_3_contracts_pct": None,
        },
        "curve_features": {"sparse_curve_feature_non_null_rates": {}},
        "targets": {"by_horizon": {}},
    }

    markdown = render_markdown(payload)

    assert SOURCE_QUALITY_NOTE in markdown
    assert RECOMMENDED_CURVE_LABEL in markdown
