# Tickets — V15 Réalisme de l'indicateur short basis-haut

Suite roadmap V14. Discipline : aucun nouveau modèle ; affiner sortie/risque/coûts/forward de la règle
short basis-haut. Module `src/mais/research/v15_short_realism.py`, doc `docs/V15_SHORT_REALISM.md`.

## Tickets

- **V15-01** — `DONE` — Sortie saison-aware. N'améliore PAS le z→0 uniforme (+319 vs +417). Garder simple.
  Artefact `season_aware_exits.json`.
- **V15-02** — `DONE` — Archéologie censurés. 9/42 échecs, z d'entrée plus extrême (z>2) mais pas de veto
  dur → ne pas sur-filtrer. Artefact `censored_archaeology.json`.
- **V15-03** — `DONE` — Drawdown. MAE p90 −19.7/p95 −23.3 ; stop rationnel ≈ −20/−25 (−10 détruit).
  Artefact `drawdown_study.json`.
- **V15-04** — `DONE` — Sorties partielles. Pas de gain clair vs z→0/z→0.5 purs. Artefact `partial_exits.json`.
- **V15-05** — `DONE` — Position sizing. Edge concentré sur z>2 (29.9 vs 9.9 €/t/trade). Artefact
  `position_sizing.json`.
- **V15-06** — `DONE` — Coût dynamique. Règle survit (+309 net). Artefact `dynamic_cost.json`.
- **V15-07** — `DONE` — Portfolio strict 1-trade-à-la-fois. 29 trades, hit 0.90, +116 net coût 5, DD −27.
  Artefact `strict_portfolio.json`.
- **V15-08** — paper-trading forward : opérationnel via `scripts/run_premium_journal.py` (V14-03), à
  accumuler dans le temps (cron).

## Suite V16 (explication économique du basis)

- **V16-01** — fair value du basis (`basis_mispricing = basis − basis_fair`) ; mieux que basis_z ?
- **V16-02** — structure de courbe EMA (contango/backwardation, roll yield, OI) → basis durable vs compressible.
- **V16-03** — données EU/Ukraine/énergie, uniquement si elles expliquent le basis et sa reversion.
- **V16-DATA** — `WAITING_DATA` — EMA officiel Euronext.
