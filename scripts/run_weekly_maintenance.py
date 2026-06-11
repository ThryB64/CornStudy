"""V181 — point d'entrée maintenance hebdomadaire.

Usage :
    python scripts/run_weekly_maintenance.py             # checks + tests critiques
    python scripts/run_weekly_maintenance.py --no-tests  # checks seulement (rapide)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-tests", action="store_true", help="sauter les tests critiques")
    args = parser.parse_args()
    from mais.ops.weekly_maintenance import run_v181_weekly
    out = run_v181_weekly(run_tests=not args.no_tests)
    print(json.dumps(out, indent=2, default=str))
    return 0 if out["verdict"] != "BROKEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
