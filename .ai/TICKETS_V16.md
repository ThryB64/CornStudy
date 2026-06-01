# Tickets — V16 Explication économique du basis

Suite roadmap V15. Discipline : tester des explications économiques du basis, pas un modèle opaque.
Module `src/mais/research/v16_basis_explanation.py`, doc `docs/V16_BASIS_EXPLANATION.md`.

## Tickets

- **V16-01** — `DONE` — Fair value du basis. `BASIS_Z_REMAINS_BEST` : fair value R² OOF −0.25 (la macro
  n'explique pas le basis), mispricing ne bat pas basis_z (AUC 0.636 vs 0.670, +16 vs +193 coût 5).
  Artefact `basis_fair_value.json`.
- **V16-02** — `DONE` — Structure de courbe. `CURVE_STRUCTURE_EXPLORATORY` : vraies features EMA trop rares
  (n=4 basis-haut+contango) ; proxy tendance : reversion plus forte si CBOT au-dessus tendance (n=19, hit 1.0,
  exploratoire). Artefact `curve_structure.json`.
- **V16-03** — `DONE` — Drivers du basis. R² OOF −0.25 : le basis est une prime locale idiosyncratique non
  expliquée par FX/énergie/saison. Données EU spécifiques = WAITING_DATA. Artefact `basis_drivers.json`.

## Conclusion V16

La macro mondiale n'explique pas le basis → la mean-reversion statistique de basis_z (V13-V15) est la bonne
approche, pas un modèle fondamental. La fair-value fondamentale est rejetée honnêtement.

## Suite V17 (proposée)

- **V17-DATA** — `WAITING_DATA` — EMA officiel Euronext + EC MARS + FranceAgriMer + Eurostat + Ukraine + TTF ;
  re-tester fair value et structure de courbe avec ces données.
- **V17-01** — accumulation du journal forward V14 (≥12 mois) + rapport research final consolidé de l'indicateur.
