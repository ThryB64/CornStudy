"""EXT026 — Validation du parse vintage sur 3 rapports historiques.

Pour un rapport d'ete (2023-07), d'automne (2023-11) et d'hiver/stocks
(2024-01): verifier que les valeurs parsees (csv/wasde/wasde_txt.csv)
apparaissent bien dans le texte brut USDA correspondant (data/wasde_raw/).
Ecrit wasde_validation_report.md.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
RESULTS = ROOT / "external_research" / "results" / "external_tests" / \
    "EXT026_wasde_vintage_pipeline"

REPORTS = {"wasde2307.txt": "été 2023-07",
           "wasde2311.txt": "automne 2023-11",
           "wasde2401.txt": "hiver/stocks 2024-01"}

CHECK_VARS = ["production", "beginning_stocks", "ending_stocks", "exports",
              "use_total", "domestic_total", "feed_and_residual",
              "avg_farm_price"]


def fmt_variants(x: float) -> list[str]:
    """Formats plausibles d'une valeur WASDE dans le texte brut."""
    out = []
    if x == int(x):
        i = int(x)
        out += [f"{i:,}", str(i)]
        out += [f"{i / 1000:,.1f}".rstrip("0").rstrip(".")]  # parfois en milliards
    out += [f"{x:.2f}", f"{x:.1f}", f"{x:,.1f}", f"{x:,.2f}"]
    return list(dict.fromkeys(out))


def corn_excerpt(raw: str, n_lines: int = 40) -> str:
    lines = raw.splitlines()
    for i, line in enumerate(lines):
        if re.search(r"CORN", line, re.IGNORECASE) and \
           re.search(r"FEED|CORN AND|U\.?S\.?", line, re.IGNORECASE):
            return "\n".join(lines[i:i + n_lines])
    for i, line in enumerate(lines):
        if "CORN" in line.upper():
            return "\n".join(lines[i:i + n_lines])
    return "(section corn non trouvee)"


def main() -> None:
    parsed = pd.read_csv(ROOT / "csv" / "wasde" / "wasde_txt.csv")
    md = ["# Validation du parse WASDE vintage — 3 rapports historiques",
          "",
          "Méthode : chaque valeur parsée doit apparaître textuellement dans le",
          "fichier brut USDA (formats avec/sans séparateur de milliers testés).",
          "Les valeurs vérifiées sont celles publiées À L'ÉPOQUE (vintage), pas",
          "les valeurs révisées ultérieures.", ""]
    summary = []
    for fname, label in REPORTS.items():
        raw_path = ROOT / "data" / "wasde_raw" / fname
        md.append(f"## {fname} ({label})")
        md.append("")
        if not raw_path.exists():
            md += [f"❌ fichier brut absent : {raw_path}", ""]
            summary.append((fname, "MISSING_RAW", 0, 0))
            continue
        raw = raw_path.read_text(errors="replace")
        row = parsed[parsed["filename"] == fname]
        if row.empty:
            md += ["❌ rapport absent du parse wasde_txt.csv", ""]
            summary.append((fname, "MISSING_PARSE", 0, 0))
            continue
        row = row.iloc[0]
        ok = tot = 0
        md.append("| variable | valeur parsée | trouvée dans le brut |")
        md.append("|---|---|---|")
        for v in CHECK_VARS:
            val = row.get(v)
            if pd.isna(val):
                md.append(f"| {v} | (NaN) | — |")
                continue
            tot += 1
            found = any(s in raw for s in fmt_variants(float(val)))
            ok += int(found)
            md.append(f"| {v} | {val} | {'✅' if found else '❌'} |")
        md += ["", f"**Score : {ok}/{tot} valeurs retrouvées dans le brut.**", "",
               "Extrait de la section corn du brut :", "", "```",
               corn_excerpt(raw, 25), "```", ""]
        summary.append((fname, "OK", ok, tot))

    md.append("## Synthèse")
    md.append("")
    for fname, status, ok, tot in summary:
        md.append(f"- {fname} : {status}, {ok}/{tot}")
    all_ok = all(s == "OK" and ok == tot and tot > 0 for fname, s, ok, tot in summary)
    partial = any(s == "OK" and ok > 0 for _, s, ok, _ in summary)
    verdict = "VALIDATED" if all_ok else ("PARTIAL" if partial else "FAILED")
    md += ["", f"**Verdict de validation : {verdict}**", ""]
    (RESULTS / "wasde_validation_report.md").write_text("\n".join(md))
    print(f"validation: {verdict}")
    for s in summary:
        print(s)


if __name__ == "__main__":
    main()
