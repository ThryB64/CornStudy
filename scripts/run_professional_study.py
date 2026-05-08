#!/usr/bin/env python3
"""Build the professional corn price study artefacts and Markdown report."""

from __future__ import annotations

from mais.study import build_professional_study


if __name__ == "__main__":
    result = build_professional_study()
    print(f"Wrote {result.report_path}")
    print(result.summary["artefacts"])
