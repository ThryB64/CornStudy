# Tickets — V13 Indicateur mean-reversion du basis

Suite roadmap V12. Discipline : basis, short basis-haut, sortie au niveau, abstention conforme, coûts,
validation stricte. Pas de meta-model, pas de H90, pas d'EMA brut, pas de bot.
Module `src/mais/research/v13_basis_reversion_indicator.py`, doc `docs/V13_BASIS_REVERSION_INDICATOR.md`.

## Tickets

- **V13-02** — `DONE` — Sorties dynamiques. H40 dominé ; z→0.5 meilleur profit/jour, z→0 meilleur PnL total,
  z→0 max90 meilleur compromis ; SL serré nuit. Artefact `dynamic_exits.json`.
- **V13-03** — `DONE` — Short basis-haut strict. `SHORT_RULE_ROBUST` : survit coût 5 hors crises (+115 €/t,
  n=30). Exit z→0 ≫ H40. Réserve : clustering. Artefact `short_rule_strict.json`.
- **V13-01** — `DONE` — Recalibration conforme. α=0.10 optimal (DA 0.875, couverture 0.83). Artefact
  `conformal_recalibration.json`.
- **V13-05** — `DONE` — Modèles de signe. Linéaire 2 vars meilleur (AUC 0.685) ; non-linéarité dégrade.
  Artefact `basis_change_sign_models.json`.
- **V13-06** — `DONE` — Long/short séparés. Asymétrie : compression 0.656 vs rebond 0.516. Artefact
  `long_short_separated.json`.
- **V13-07** — `DONE` — Journal append-only opérationnel (`append_premium_journal`, idempotent).
  Artefact `premium_journal.parquet`.

## Suite V14 (proposée)

- **V14-01** — indicateur **short-only** : abstention conforme α=0.10 + sortie z→0 (max 90j) + cost-aware.
- **V14-02** — modèle de durée (survival) du temps de reversion (Kaplan-Meier / Cox par saison).
- **V14-03** — brancher le journal en cron quotidien (`ops/daily.py`, append-only, éval à la sortie z).
- **V14-DATA** — `WAITING_DATA` — acquisition EMA officiel Euronext (déblocage principal).
