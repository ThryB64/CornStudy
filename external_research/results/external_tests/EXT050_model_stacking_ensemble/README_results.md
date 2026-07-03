# EXT050 (ex-EXT028) — Résultats : stacking ensemble (méta-modèle)

**Verdict : REJECT** (le stacking sur-apprend ; moyenne simple et meilleur modèle seul font
mieux). Renommé `EXT028` → `EXT050` à l'étape 5 bis (collision : EXT028 satellite + EXT029
corn-crush déjà réservés au catalogue). Chiffres ci-dessous = **après correction target_date**.

## Protocole
Méta-modèle = régression logistique sur les probabilités OOS des 3 membres (market_only,
market+wasde, market+crop), entraîné walk-forward sur le passé seulement. Comparé à la
moyenne simple et aux membres. Pas d'optimisation globale, pas de holdout.

## Résultats (corrigés)

| H | Modèle | DA | balanced | AUC | Brier | DA 1re | DA 2e |
|---|---|---|---|---|---|---|---|
| 40 | stack | 0.574 | 0.571 | 0.551 | 0.252 | **0.484** | 0.664 |
| 40 | simple_avg | 0.591 | 0.589 | 0.601 | 0.244 | 0.556 | 0.625 |
| 40 | market+wasde | **0.598** | 0.596 | 0.591 | 0.253 | 0.573 | 0.624 |
| 90 | stack | 0.606 | 0.606 | 0.640 | 0.237 | **0.500** | 0.711 |
| 90 | simple_avg | 0.615 | 0.616 | 0.685 | 0.226 | 0.570 | 0.660 |
| 90 | market+crop | **0.665** | 0.666 | **0.735** | **0.215** | 0.614 | 0.716 |

## Lecture
- Le **stacking est le pire** : DA inférieure aux membres et à la moyenne simple, et surtout
  **instable** (1re moitié ≤ 0.5 aux deux horizons : 0.484 / 0.500). Avec un edge faible et
  peu d'observations effectives (refits annuels), le méta-modèle apprend des poids qui ne
  généralisent pas.
- La **moyenne simple** est correcte mais reste sous le meilleur membre seul.
- **`market+crop` seul reste le meilleur à H90** (0.665, AUC 0.735, Brier 0.215).

## Conclusion
**REJECT.** Empiler n'aide pas ici — au contraire, le stacking sur-apprend. Message net de
l'étape 5 : avec un signal directionnel faible mais réel, **la parcimonie gagne**. Garder
le modèle simple par horizon (crop@H90, wasde@H40) + éventuellement un BMA robuste
(EXT014) ; ne pas ajouter de méta-modèle.
