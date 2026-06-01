# Tickets — V17 Indicateur research de prime (consolidation)

Suite roadmap V16. Discipline : AUCUN nouveau modèle ; consolider, valider, expliquer, suivre en live.
Module `src/mais/research/v17_research_indicator.py`, doc `docs/V17_RESEARCH_INDICATOR.md`.

## Tickets

- **V17-01** — `DONE` — Indicateur à paliers (MODERATE/STRONG/EXTREME + UNCERTAIN data/roll/vol). Signal live
  2025-07-25 : STRONG (z=1.70) rétrogradé UNCERTAIN_ROLL, coût 7 €/t, below_trend. `compute_indicator_v17`.
- **V17-02** — `DONE` — Rapport quotidien Markdown (`generate_daily_report`, `daily_report.md`).
- **V17-03** — `DONE` — Journal forward append-only (via `scripts/run_premium_journal.py`, V14-03).
- **V17-04** — `DONE` — Walk-forward final (1 trade/fois, stop −20, coût dynamique). `WALKFORWARD_ROBUST` :
  32 trades, hit 0.656, net +138, 9/14 ans +, DD −39.7. Artefact `walk_forward_final.json`.
- **V17-05** — `DONE` — Fiches des 42 trades. Win 0.81 ; EXTREME PnL 29.9, STRONG win 1.0, MODERATE 7.3.
  Artefacts `trade_fiches.parquet` + `trade_fiches_summary.json`.
- **V17-06** — `DONE` — Analyse des échecs. Pertes en haute vol/roll/below_trend ; insight clé : **z→0.5
  prudent** sauve plusieurs pertes (2010 +23, 2013 +30 vs négatif en z→0). Warnings, pas vetoes.
  Artefact `failure_analysis.json`.

## Recommandation indicateur

Objectif prudent z→0.5 par défaut (surtout MODERATE / contexte défavorable) ; objectif complet z→0 max90
stop −20 pour STRONG/EXTREME en contexte favorable. Toujours afficher palier, warnings, coût, risque.

## Suite (données = seul vrai levier)

- **V18-01** `WAITING_DATA` — EMA officiel Euronext + comparaison proxy.
- **V18-02** `WAITING_DATA` — courbe EMA multi-échéances (contango/backwardation).
- **V18-03** `WAITING_DATA` — données physiques EU (FranceAgriMer, MARS, COMEXT, Ukraine, TTF, fret, météo).
- **V19-01** — paper trading forward 6-12 mois via le journal.
