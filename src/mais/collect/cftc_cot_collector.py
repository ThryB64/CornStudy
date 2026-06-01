"""CFTC Commitments of Traders weekly collector (Phase 1 NEW).

Public, no API key. Disaggregated report (TFF) is the most useful:
  https://www.cftc.gov/dea/newcot/f_disagg.txt

Released Friday 15:30 ET for the position as of Tuesday previous week.
Lag = 3 days (declared in sources.yaml).

Variables exported (after parsing):
  - cot_managed_money_long, _short, _net
  - cot_commercial_long, _short, _net
  - cot_producer_merchant_net
  - cot_swap_dealer_net
  - cot_open_interest

The historical archive is downloadable as zip per year:
  https://www.cftc.gov/files/dea/history/dea_fut_disagg_xls_{YYYY}.zip
"""

from __future__ import annotations

from pathlib import Path

from mais.utils import get_logger

log = get_logger("mais.collect.cot")


def download(out_dir: Path, src: dict) -> str:
    raise NotImplementedError(
        "CFTC COT collector to wire: see https://www.cftc.gov/dea/newcot/f_disagg.txt "
        "for live + history zip files. Filter on commodity_code='002602' (Corn No. 2 CBOT). "
        "Output CSV with columns: Date, cot_managed_money_long, cot_managed_money_short, "
        "cot_managed_money_net, cot_commercial_long, cot_commercial_short, cot_commercial_net, "
        "cot_swap_dealer_net, cot_open_interest."
    )
