#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p data/reports logs

venv/bin/python - <<'PY' >> logs/weekly_report.log 2>&1
from pathlib import Path
from mais.ops.weekly_report import WeeklyReportInput, generate_weekly_report

report = WeeklyReportInput(
    date="latest",
    current_price_cents=0.0,
    market_reading="A ACTUALISER",
    probability_up=0.50,
    p_correct=0.50,
    market_clarity="FAIBLE",
    downside_risk_score=0.50,
    upside_opportunity_score=0.50,
)
generate_weekly_report(report, output_path=Path("data/reports/weekly_report_latest.md"))
PY
