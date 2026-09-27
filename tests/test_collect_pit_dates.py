"""Datage point-in-time des collecteurs fondamentaux (correctif anti-leakage 2026-09-27)."""
import pandas as pd

from mais.collect import cftc_cot_collector, drought_monitor_collector, enso, usda_wasde_collector


def test_cot_dated_at_friday_release_and_shutdown_backlog():
    asof = pd.Series(pd.to_datetime(["2026-09-22", "2025-10-07", "2025-12-23", "2025-12-30"]))
    rel = cftc_cot_collector.release_date(asof)
    assert rel.iloc[0] == pd.Timestamp("2026-09-25")
    assert rel.iloc[1] == pd.Timestamp("2025-12-29")
    assert rel.iloc[2] == pd.Timestamp("2025-12-29")
    assert rel.iloc[3] == pd.Timestamp("2026-01-02")


def test_cot_backlog_keeps_only_latest_report_per_release_date():
    raw = pd.DataFrame({"report_date_as_yyyy_mm_dd": ["2025-10-07", "2025-10-14"],
                        **{k: ["100", "200"] for k in cftc_cot_collector.FIELDS}})
    out = cftc_cot_collector.build_cot(raw)
    assert len(out) == 1 and out["cot_open_interest"].iloc[0] == 200


def test_enso_season_available_after_season_end():
    text = "SEAS YR TOTAL ANOM\n DJF 2026 26.0 -0.5\n JJA 2026 29.09 1.80\n"
    out = enso.parse_oni_ascii(text)
    djf = out.loc[out["enso_oni_index"] == -0.5, "Date"].iloc[0]
    assert djf == pd.Timestamp("2026-03-10")
    assert out["Date"].max() == pd.Timestamp("2026-09-10")


def test_drought_cumulative_to_exclusive_and_release_lag():
    csv = pd.DataFrame({"MapDate": [20260922], "D0": [40.0], "D1": [20.0], "D2": [10.0],
                        "D3": [5.0], "D4": [1.0]})
    out = drought_monitor_collector._parse_records({"19": csv})
    row = out.iloc[0]
    assert row["Date"] == pd.Timestamp("2026-09-24")
    assert [row[f"corn_area_d{i}"] for i in range(5)] == [20.0, 10.0, 5.0, 4.0, 1.0]


def test_wasde_effective_after_release(tmp_path, monkeypatch):
    monkeypatch.setattr(usda_wasde_collector, "TXT_DIR", tmp_path)
    monkeypatch.setattr(usda_wasde_collector, "RELEASES_CSV", tmp_path / "release_dates.csv")
    monkeypatch.setattr(usda_wasde_collector, "LEGACY_CSV", tmp_path / "legacy_reports.csv")
    pd.DataFrame({"yymm": ["2609"], "file": ["wasde0926"], "url": ["x"],
                  "release_date": ["2026-09-11"]}).to_csv(tmp_path / "release_dates.csv", index=False)
    pd.DataFrame({"yymm": ["2608"], "production": [16013.0], "ending_stocks": [1653.0],
                  "use_total": [16000.0], "exports": [3000.0], "domestic_total": [13000.0],
                  "supply_total": [17653.0], "avg_farm_price": [4.1], "stocks_to_use_ratio": [10.3]}
                 ).to_csv(tmp_path / "legacy_reports.csv", index=False)
    sessions = pd.bdate_range("2026-08-01", "2026-09-30")
    out = usda_wasde_collector.build_interim(sessions)
    # rapport d'août sans date connue → repli au 14 → effectif le 17/08 (lundi)
    assert out["Date"].min() == pd.Timestamp("2026-08-17")
    assert out.loc[out["Date"] == pd.Timestamp("2026-09-01"), "wasde_production"].iloc[0] == 16013.0
