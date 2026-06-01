# EMA CONTRACTS V2

> Source EMA exploratoire/proxy. La courbe multi-maturité reste partielle.

## Résultats clés

| Métrique | Valeur |
|---|---:|
| Rolls front | 68 |
| Gap moyen absolu | 9.83 €/t |
| Gap max absolu | 54.25 €/t |
| Fenêtres H20 avec roll | 39.5% |
| Fenêtres H40 avec roll | 78.1% |
| Fenêtres H60 avec roll | 98.9% |
| Dates avec >=2 contrats | 14.9% |

## Recommandation

- Série raw : prix absolu de marché.
- Série adjusted : rendements, momentum, volatilité et features techniques.
- Série no-roll : analyse de sensibilité uniquement, car H60 traverse presque toujours un roll.

## Conclusion

Les rolls sont un risque méthodologique majeur. Les résultats EMA doivent toujours préciser raw/adjusted/no-roll.