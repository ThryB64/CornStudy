# EXT017 — Résultats : détection de régimes de marché

**Verdict : IMPROVE** (les régimes expliquent QUAND le signal marche ; filtre prometteur
mais risque d'overfitting post-hoc → à valider, pas à figer).

## Protocole
Régimes définis **sur info passée uniquement** (règles dans `regime_rules.csv`). On slice
les prédictions du meilleur modèle directionnel (market+wasde à H40, market+crop à H90 —
modèle GLOBAL, pas un modèle par régime, pour éviter le sur-apprentissage) et on mesure DA
/ balanced accuracy / Brier par régime, avec n par régime.

## Résultats marquants (DA, balanced accuracy)

**H40 (market+wasde)** — global DA 0.590 :
| Régime | DA | balanced | n |
|---|---|---|---|
| uptrend | **0.615** | **0.622** | 1748 |
| downtrend | 0.574 | 0.540 | 1942 |
| low_vol | 0.601 | 0.586 | 2209 |
| high_vol | 0.577 | 0.574 | 1788 |
| stocks tight | 0.609 | 0.605 | 2307 |
| stocks normal | 0.523 | 0.506 | 864 |
| crop normal | **0.664** | 0.652 | 1623 |

**H90 (market+crop)** — global DA 0.658 :
| Régime | DA | balanced | n |
|---|---|---|---|
| uptrend | 0.683 | **0.718** | 1748 |
| neutral_trend | **0.472** | 0.468 | 307 |
| low_vol | 0.676 | 0.660 | 2173 |
| high_vol | 0.636 | 0.627 | 1788 |
| stocks loose | **0.713** | 0.679 | 790 |
| stocks tight | 0.669 | 0.689 | 2307 |
| stocks normal | 0.578 | 0.577 | 864 |
| crop normal | 0.699 | 0.699 | 1623 |
| crop good | 0.593 | **0.491** | 1237 |

## Lecture honnête
1. **Le signal est nettement plus fort en faible volatilité et en tendance haussière**
   (H90 uptrend balanced 0.718). Cohérent avec la découverte interne V39-E4 (l'uptrend CBOT
   réduit le risque ADVERSE).
2. **Il s'effondre au pile/face dans les régimes "neutres/normaux"** : trend neutre (H90
   balanced 0.468), stocks normaux (0.58), et même crop *bonne* (balanced 0.491 ≈ hasard —
   quand la récolte s'annonce excellente, la direction est déjà price-in).
3. **L'edge se concentre aux EXTRÊMES de bilan** (stocks tight ou loose) et quand il y a une
   tendance : c'est là que les fondamentaux d'offre informent vraiment.
4. **Un filtre de régime** (agir surtout en uptrend + bilan extrême + faible vol)
   concentrerait l'edge, MAIS le découpage est post-hoc → **risque d'overfitting**. À
   valider en forward avant toute mise en production, pas à figer maintenant.

## Conclusion
**IMPROVE.** Les régimes n'ajoutent pas de bruit : ils **expliquent** la performance
hétérogène du signal directionnel — fort en tendance/faible-vol/bilan extrême, nul en
conditions neutres. Recommandation étape 6 : utiliser les régimes comme **conditionnement
du score de confiance** (haute confiance en uptrend/low-vol/bilan extrême ; s'abstenir en
neutre), en validant le gain en forward. Ne pas fitter un modèle par régime (échantillons
trop petits).
