# NB-EMA-09 — Étude d'événements sur résidus EMA

## Objectif

Analyser le comportement du prix EMA autour des chocs extrêmes (résidus > 2σ), mesurer la persistance et la réversion.

## Méthode

- Chocs identifiés sur la série de résidus OLS (EMA ~ CBOT + basis_chg) générée par NB-EMA-05
- Seuil : |résidu_z| > 2σ
- Fenêtre événementielle : -20j à +40j
- Métriques : CAR moyen, médiane, t-test, classification par type (positif / négatif)

## Résultats

| Métrique | Valeur |
|---|---|
| Nombre d'événements (2σ) | 73 |
| Chocs positifs | ~36 |
| Chocs négatifs | ~37 |
| CAR post +20j (chocs positifs) | -1.04% |
| CAR post +20j (chocs négatifs) | +0.94% |
| Réversion détectée | **OUI** |

## Interprétation

Les chocs positifs sont suivis d'une légère réversion à horizon 20j (−1%), et les chocs négatifs d'un rebond (+0.9%). Ce pattern de mean-reversion est cohérent avec la dynamique de cointégration EMA/CBOT.

La magnitude est faible : la réversion n'est pas exploitable directement sans modèle de signal plus précis.

## Limites

- Analyse in-sample uniquement
- Contamination possible par événements fondamentaux (WASDE, guerre Ukraine 2022)
- Pas de correction pour la multiplicité des tests
