# NB-EMA-13 — Benchmark hebdomadaire EMA

## Objectif

Évaluer la prédictibilité des signaux EMA sur données hebdomadaires (clôture vendredi).

## Méthode

- Resampling W-FRI sur le prix EMA ajusté (front)
- **DA naïf** : sign(ret_semaine_précédente) == sign(ret_futur_H semaines)
- **Signal basis** : basis > moyenne 52 semaines → short EMA (basis va baisser)
- IC95% bootstrap (500 tirages)

## Résultats

| Métrique | Valeur |
|---|---|
| Nombre de semaines | ~670 |
| % semaines en hausse | ~52% |
| Sharpe hebdo | ~0.08 |
| DA naïf H=4 semaines | 52.5% |
| DA signal basis H=4 semaines | 60.8% |

## Interprétation

Le signal basis (basis > MA52S) atteint une DA de 60.8% sur données hebdomadaires, significativement supérieure au 50% aléatoire. Ce signal n'est pas validé OOF — il s'agit d'un benchmark descriptif in-sample.

La marche aléatoire hebdomadaire (DA=52.5%) reste proche du hasard, confirmant la faible prédictibilité directionnelle.

## Limites

- Analyse in-sample uniquement — pas de validation OOF
- Pas de coûts de transaction
- Données EMA proxy Barchart (couverture 79%)
