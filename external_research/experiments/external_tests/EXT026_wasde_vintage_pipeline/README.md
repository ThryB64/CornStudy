# EXT026 — WASDE vintage pipeline

Hypothèse : un pipeline WASDE daté publication réelle (valeurs telles que publiées, jamais révisées) est constructible et fiable — prérequis de EXT007/EXT008/EXT024/EXT038/EXT043.

- `run_ext026.py` : audit anti-fuite de `data/interim/wasde.parquet` (dates de changement vs publications réelles) + construction de `wasde_vintage_dataset.csv` depuis l'archive interne (210 txt USDA Cornell + parse `csv/wasde/wasde_txt.csv`), dates hiérarchisées links_table > usda_calendar > fallback jour-12, `available_from = publication + 1 jour ouvré`.
- `validate_ext026.py` : validation de 3 rapports historiques (été/automne/hiver) contre les textes bruts.

`fdfoneill/wasdeparser` cloné dans `external_research/github_repos/` (MIT) — outil de contre-vérification.

Résultats : `external_research/results/external_tests/EXT026_wasde_vintage_pipeline/` — **verdict KEEP**, avec **fuite de ~8 jours détectée dans la série quotidienne interne actuelle** (143/160 rapports) — correction proposée par ticket projet séparé (voir `README_results.md`).
