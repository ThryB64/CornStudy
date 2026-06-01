# Validation endpoint Euronext EMA

Date de validation : 2026-05-19

## Verdict

Endpoint quotidien valide pour les contrats actifs EMA :

```text
https://live.euronext.com/en/ajax/getPricesFutures/commodities-futures/EMA/DPAR
```

Cet endpoint est appelé par le JavaScript officiel de la page Euronext :

```text
/modules/custom/awl_derivatives/js/awl-derivatives-prices.js
```

La page produit de référence est :

```text
https://live.euronext.com/en/product/commodity-futures/EMA-DPAR
```

## Structure

L'endpoint retourne un fragment HTML contenant la table `future-prices-table`.

Champs disponibles :

- `Delivery`
- `Bid`
- `Ask`
- `Last`
- `Time`
- `+/-`
- `Day Vol.`
- `Open`
- `High`
- `Low`
- `Settl.`
- `O.I`

Mapping retenu :

| Euronext | Pipeline |
|---|---|
| `Delivery` | `delivery` + `contract_code` |
| `Day Vol.` | `day_volume` |
| `Settl.` | `settlement` |
| `O.I` | `open_interest` |

## Contrats EMA

La page `EMA-DPAR` correspond bien au produit Corn / Mais Euronext Paris.

Mapping mois validé :

| Libellé | Code |
|---|---|
| Jan | `F` |
| Mar | `H` |
| Jun | `M` |
| Aug | `Q` |
| Nov | `X` |

Exemples :

```text
Jun 2026 -> EMA_M2026
Aug 2026 -> EMA_Q2026
Nov 2026 -> EMA_X2026
Mar 2027 -> EMA_H2027
Jan 2027 -> EMA_F2027
```

## Endpoints rejetés

Les endpoints candidats initiaux ne sont pas retenus pour EMA :

```text
https://live.euronext.com/en/pd_ajax/fixings?d=EMA-DPAR&p=0
```

Résultat observé : 404.

```text
https://live.euronext.com/en/pd/data/quote?d=EMA-DPAR&t=commodity-futures
```

Résultat observé : JSON vide (`aaData: []`).

## Limites

L'endpoint validé expose les contrats actifs du jour. Il ne fournit pas le backfill historique 2014-2025.

Conséquence :

- `DATA-EMA-01` peut utiliser cet endpoint pour la collecte quotidienne.
- `DATA-EMA-02` doit encore implémenter le backfill via fichier manuel profond, source payante, ou endpoint historique distinct s'il est découvert via navigateur.

## Procédure si l'URL change

1. Ouvrir `https://live.euronext.com/en/product/commodity-futures/EMA-DPAR`.
2. Ouvrir DevTools > Network.
3. Filtrer sur `getPricesFutures`, `prices`, `EMA` ou `DPAR`.
4. Vérifier que la réponse contient `future-prices-table`.
5. Relancer :

```bash
venv/bin/python -m mais.collect.euronext_endpoint_probe
```

6. Comparer les contrats et les settlements avec la page affichée.

Throttle recommandé pour `DATA-EMA-01` : au moins 2 secondes entre appels, même si la collecte quotidienne ne nécessite normalement qu'un seul appel.
