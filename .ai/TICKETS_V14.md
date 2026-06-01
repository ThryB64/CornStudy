# Tickets — V14 Indicateur short-only, survival, robustesse proxy

Suite roadmap V13. Discipline : short basis-haut, sortie au niveau, abstention conforme, cost-aware,
validation. Module `src/mais/research/v14_short_indicator.py`, doc `docs/V14_SHORT_INDICATOR.md`.

## Tickets

- **V14-01** — `DONE` — Indicateur short-only assemblé. Découverte over-gating : gate strict = 0 signal ;
  gate relâché cost-aware = 5 trades hit 100%, +11.2 €/t/trade net coût 5 (vs +4.2 baseline). Verdict
  `SHORT_INDICATOR_SURVIVES_COST5`. Réserve n=5. Artefact `short_indicator.json`.
- **V14-02** — `DONE` — Survival reversion (Kaplan-Meier). Médiane 47j, P(revert≤90j)=0.74, saison apr-juin
  23j / jan-mars 53j → justifie plafond 90j + sortie saison-aware. Artefact `reversion_survival.json`.
- **V14-04** — `DONE` — Robustesse proxy. `PROXY_ROBUST` : edge survit à 10 €/t de bruit (hit 0.86→0.76).
  Artefact `proxy_robustness.json`.
- **V14-03** — `DONE` — Journal opérationnel (`scripts/run_premium_journal.py`, cron-ready, append-only).
  Premier run : 37 signaux, 5 trades mûrs. `data/reports/premium_journal.parquet`.

## Suite V15 (proposée)

- **V15-01** — sortie saison-aware (plafond court printemps / long hiver) + modèle de hazard saison×régime.
- **V15-02** — accumulation du journal forward (≥12 mois) pour un vrai track record.
- **V15-DATA** — `WAITING_DATA` — acquisition EMA officiel Euronext + comparaison proxy vs officiel.
