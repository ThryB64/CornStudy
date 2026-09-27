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


def test_fas_dated_at_release_with_shutdown_backlog_and_my_boundary():
    from mais.collect import fas_export_sales_collector as fas
    rows = [
        {"weekEndingDate": "2026-09-03", "countryCode": 5700, "marketYear": 2026,
         "currentMYNetSales": 5, "currentMYTotalCommitment": 87},
        {"weekEndingDate": "2026-09-03", "countryCode": 5700, "marketYear": 2027,
         "currentMYNetSales": 7, "currentMYTotalCommitment": 16},
        {"weekEndingDate": "2025-10-02", "countryCode": 1220, "marketYear": 2026,
         "currentMYNetSales": 1, "currentMYTotalCommitment": 2},
    ]
    out = fas.build_weekly(rows).set_index("Date")
    assert out.loc[pd.Timestamp("2026-09-10"), "export_sales_accumulated_mt"] == 16
    assert out.loc[pd.Timestamp("2026-09-10"), "export_china_sales_mt"] == 7
    assert pd.Timestamp("2026-01-08") in out.index


def test_nass_versions_dated_at_publication():
    from mais.collect import nass_annual
    bulk = pd.Timestamp("2012-01-01")
    assert nass_annual.release_date(2005, "YEAR - MAR ACREAGE", bulk) == pd.Timestamp("2005-03-31")
    assert nass_annual.release_date(2025, "YEAR", pd.Timestamp("2026-01-12 12:00")) == pd.Timestamp("2026-01-12")
    assert nass_annual.release_date(2000, "YEAR", bulk) == pd.Timestamp("2001-09-30")
    assert nass_annual.release_date(2026, "YEAR", pd.Timestamp("2026-09-11")) is None


def test_conab_survey_release_month():
    from mais.collect import conab_brazil
    assert conab_brazil.release_date("2025/26", 1) == pd.Timestamp("2025-10-16")
    assert conab_brazil.release_date("2025/26", 12) == pd.Timestamp("2026-09-16")


def test_brazil_exports_available_next_month():
    from mais.collect import brazil_exports
    rows = [{"year": "2026", "monthNumber": "08", "metricKG": "4653100189", "metricFOB": "1002656682"}]
    out = brazil_exports.build_monthly(rows)
    assert out["Date"].iloc[0] == pd.Timestamp("2026-09-10")
    assert round(out["br_corn_fob_usd_t"].iloc[0], 1) == 215.5


def test_wasde_world_parses_old_and_new_layouts(tmp_path):
    from mais.collect import wasde_world
    old = ("                          World Corn Supply and Use 1/\r\n"
           "                      :                 2010/11 (Projected)\r\n"
           "World 3/              :\r\n"
           "             May      :  147.04  835.03   86.12  492.70  827.87   88.53  154.21\r\n"
           "   EU-27 6/       May :    4.43   57.00    2.50   43.50   58.25    1.25    4.43\r\n")
    new = ("                          World Corn Supply and Use  1/\n"
           "                                  2026/27 Proj.\n"
           "    European Union  6/  \n"
           "                     Aug    5.95   50.20   23.50   53.00   73.00    1.60    5.05\n"
           "                     Sep    5.95   50.60   23.50   53.40   73.40    1.60    5.05\n")
    (tmp_path / "wasde1005.txt").write_text(old)
    (tmp_path / "wasde2609.txt").write_text(new)
    r_old = {r["country"]: r for r in wasde_world._parse_wasde_file(tmp_path / "wasde1005.txt")}
    r_new = {r["country"]: r for r in wasde_world._parse_wasde_file(tmp_path / "wasde2609.txt")}
    assert r_old["world"]["production"] == 835.03 and r_old["eu"]["crop_year"] == 2011
    assert r_new["eu"]["production"] == 50.6 and r_new["eu"]["crop_year"] == 2027
