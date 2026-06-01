from __future__ import annotations

import pandas as pd

from mais.research.roll_audit import (
    audit_rolls,
    check_targets_cross_rolls,
    write_roll_audit_report,
)


def _front_raw() -> pd.DataFrame:
    dates = pd.bdate_range("2026-01-01", periods=6)
    return pd.DataFrame(
        {
            "date": dates,
            "series_name": "front_raw",
            "price": [100.0, 101.0, 110.0, 111.0, 112.0, 113.0],
            "contract_code": [
                "EMA_H2026",
                "EMA_H2026",
                "EMA_M2026",
                "EMA_M2026",
                "EMA_M2026",
                "EMA_M2026",
            ],
            "roll_event": [False, False, True, False, False, False],
            "prev_contract_code": [None, "EMA_H2026", "EMA_H2026", "EMA_M2026", "EMA_M2026", "EMA_M2026"],
            "roll_price_old": [None, None, 105.0, None, None, None],
            "roll_adjustment": [0.0, 0.0, 5.0, 0.0, 0.0, 0.0],
        }
    )


def _front_adjusted() -> pd.DataFrame:
    raw = _front_raw().copy()
    raw["series_name"] = "front_adjusted"
    raw["cum_roll_adjustment"] = raw["roll_adjustment"].cumsum()
    raw["adjusted_price"] = raw["price"] - raw["cum_roll_adjustment"]
    return raw


def test_audit_rolls_detects_gap_and_invariant() -> None:
    payload = audit_rolls(_front_raw(), _front_adjusted())

    assert payload["total_rolls"] == 1
    assert payload["average_roll_gap_abs_eur_t"] == 5.0
    assert payload["max_roll_gap_abs_eur_t"] == 5.0
    assert payload["adjustment_invariant"]["ok"] is True
    assert payload["verdict"] == "OK"


def test_audit_rolls_flags_adjustment_mismatch() -> None:
    adjusted = _front_adjusted()
    adjusted.loc[2, "adjusted_price"] = adjusted.loc[2, "adjusted_price"] + 1.0

    payload = audit_rolls(_front_raw(), adjusted)

    assert payload["adjustment_invariant"]["ok"] is False
    assert payload["verdict"] == "FAIL"


def test_check_targets_cross_rolls_finds_potential_raw_windows() -> None:
    targets = pd.DataFrame({
        "Date": pd.bdate_range("2026-01-01", periods=6),
        "y_ema_up_h3": [0, 1, 0, 1, 0, 1],
    })
    roll_log = pd.DataFrame({"date": [pd.Timestamp("2026-01-05")]})

    violations = check_targets_cross_rolls(targets, roll_log, target_columns=["y_ema_up_h3"])

    assert violations
    assert violations[0]["date"] == "2026-01-01"
    assert violations[0]["first_roll_date"] == "2026-01-05"
    assert violations[0]["target_col"] == "y_ema_up_h3"


def test_generic_cbot_targets_are_not_audited_by_default() -> None:
    targets = pd.DataFrame({
        "Date": pd.bdate_range("2026-01-01", periods=6),
        "y_up_h3": [0, 1, 0, 1, 0, 1],
    })
    roll_log = pd.DataFrame({"date": [pd.Timestamp("2026-01-05")]})

    assert check_targets_cross_rolls(targets, roll_log) == []


def test_write_roll_audit_report(tmp_path) -> None:
    output = tmp_path / "roll_audit_report.txt"
    payload = write_roll_audit_report(_front_raw(), _front_adjusted(), output_path=output)

    text = output.read_text(encoding="utf-8")
    assert payload["verdict"] == "OK"
    assert "ROLL AUDIT REPORT" in text
    assert "Total rolls detected: 1" in text
    assert "EMA_H2026 -> EMA_M2026" in text
    assert "gap=5.000 EUR/t" in text
    assert "PENDING_NO_EMA_TARGETS" in text
