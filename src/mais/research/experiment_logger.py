"""Experiment logger — track every test in EXPERIMENT_INDEX.md.

Usage
-----
    from mais.research.experiment_logger import ExperimentLogger

    log = ExperimentLogger()
    exp_id = log.new(
        title="ARIMA on log-returns h20",
        hypothesis="Returns have autocorrelation exploitable by ARIMA",
        method="ARIMA(1,0,1) walk-forward, 10 folds",
        result="RMSE=0.071, baseline=0.071 → no gain",
        decision="failed",
        notes="DA slightly negative, seasonal naive wins",
    )
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

NOTEBOOK_ROOT = Path(__file__).resolve().parents[3] / "notebooks" / "corn_study"
INDEX_FILE = NOTEBOOK_ROOT / "EXPERIMENT_INDEX.md"

VALID_DECISIONS = {"successful", "neutral", "failed"}

HEADER = """# Experiment Index — Corn Study

Each row is one experiment. Decision = where the notebook lives.

| ID | Date | Title | Hypothesis | Result | Decision |
|---|---|---|---|---|---|
"""


class ExperimentLogger:
    def __init__(self, index_path: Path | None = None) -> None:
        self.index_path = index_path or INDEX_FILE
        if not self.index_path.exists():
            self.index_path.write_text(HEADER, encoding="utf-8")

    def _next_id(self) -> str:
        text = self.index_path.read_text(encoding="utf-8")
        ids = re.findall(r"\| (EXP-\d+) \|", text)
        if not ids:
            return "EXP-001"
        last = max(int(i.replace("EXP-", "")) for i in ids)
        return f"EXP-{last+1:03d}"

    def new(
        self,
        title: str,
        hypothesis: str,
        method: str,
        result: str,
        decision: str,
        notes: str = "",
    ) -> str:
        if decision not in VALID_DECISIONS:
            raise ValueError(f"decision must be one of {VALID_DECISIONS}")

        exp_id = self._next_id()
        date_str = datetime.now().strftime("%Y-%m-%d")

        # Append table row
        row = f"| {exp_id} | {date_str} | {title} | {hypothesis[:60]} | {result[:80]} | **{decision}** |\n"
        with open(self.index_path, "a", encoding="utf-8") as f:
            f.write(row)

        # Append detail block
        detail = f"""
---

## {exp_id} — {title}

**Date :** {date_str}
**Décision :** `{decision}`

**Hypothèse :**
{hypothesis}

**Méthode :**
{method}

**Résultat :**
{result}

**Notes :**
{notes or '—'}
"""
        with open(self.index_path, "a", encoding="utf-8") as f:
            f.write(detail)

        return exp_id

    def get_all(self) -> list[dict]:
        text = self.index_path.read_text(encoding="utf-8")
        rows = []
        for match in re.finditer(
            r"\| (EXP-\d+) \| (\d{4}-\d{2}-\d{2}) \| (.+?) \| (.+?) \| (.+?) \| \*\*(\w+)\*\* \|",
            text,
        ):
            rows.append({
                "id": match.group(1),
                "date": match.group(2),
                "title": match.group(3).strip(),
                "hypothesis": match.group(4).strip(),
                "result": match.group(5).strip(),
                "decision": match.group(6),
            })
        return rows

    def summary(self) -> dict[str, int]:
        all_exp = self.get_all()
        out: dict[str, int] = {"successful": 0, "neutral": 0, "failed": 0}
        for e in all_exp:
            d = e["decision"]
            if d in out:
                out[d] += 1
        out["total"] = len(all_exp)
        return out
