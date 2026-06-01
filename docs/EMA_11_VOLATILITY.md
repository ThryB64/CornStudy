# NB-EMA-11 — Modélisation de la volatilité EMA

## Objectif

Caractériser la volatilité réalisée du prix EMA et la modéliser via HAR-RV et GARCH(1,1).

## Méthode

- **Volatilité réalisée** : rolling std à 5j, 20j annualisée × √252
- **HAR-RV** : RV_daily ~ β_d × RV_daily(-1) + β_w × RV_weekly(-1) + β_m × RV_monthly(-1) + ε
- **GARCH(1,1)** : via bibliothèque `arch`, maximum de vraisemblance

## Résultats

| Métrique | Valeur |
|---|---|
| Volatilité annualisée moyenne | 19.6% |
| Volatilité max (2022) | ~55% |
| R² HAR-RV | 1.35% |
| Persistance GARCH (α+β) | 0.96 |
| Demi-vie choc GARCH | ~17 jours |

## Interprétation

La persistance GARCH (0.96) confirme le clustering de volatilité : les périodes de forte volatilité (2022, covid) sont fortement auto-corrélées. Le R² HAR faible (1.35%) suggère que la volatilité réalisée quotidienne du EMA n'est pas bien prédite par ses propres lags — contrairement aux indices boursiers où HAR performe bien.

## Limites

- HAR estimé in-sample — R² non validé OOF
- GARCH suppose des résidus i.i.d. — non vérifié formellement
- Données EMA proxy Barchart (couverture 79%)
