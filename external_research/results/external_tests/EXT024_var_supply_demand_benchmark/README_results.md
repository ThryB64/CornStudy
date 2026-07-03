# EXT024 — Résultats : benchmark supply-demand directionnel

**Verdict : IMPROVE (fort, KEEP-leaning pour Crop Condition à H90).**

## Question
Les deux signaux IMPROVE de l'étape 4 (WASDE état de bilan, Crop Condition), encodés
**stationnaires**, améliorent-ils la **direction** H40/H90 au-delà d'un modèle de marché
minimal ? (RMSE = secondaire). Classifieur : régression logistique L2, walk-forward
expandant, train-only, holdout 2024+ exclu. Métrique clé : DA et stabilité 2 sous-périodes.

## Résultats (logit L2)

| H | Spec | DA | DA−majorité | balanced | ROC-AUC | Brier | DA 1re | DA 2e |
|---|---|---|---|---|---|---|---|---|
| 40 | market_only | 0.555 | +0.045 | 0.554 | 0.579 | 0.247 | 0.519 | 0.591 |
| 40 | **market+wasde** | **0.590** | +0.080 | 0.588 | 0.587 | 0.258 | **0.591** | 0.590 |
| 40 | market+crop | 0.593 | +0.082 | 0.591 | 0.609 | 0.243 | 0.552 | 0.633 |
| 40 | market+wasde+crop | 0.586 | +0.076 | 0.585 | 0.566 | 0.271 | 0.552 | 0.620 |
| 40 | wasde+crop_only | 0.491 | −0.020 | 0.492 | 0.510 | 0.271 | 0.464 | 0.517 |
| 90 | market_only | 0.599 | +0.082 | 0.601 | 0.608 | 0.245 | 0.527 | 0.671 |
| 90 | market+wasde | 0.582 | +0.065 | 0.584 | 0.617 | 0.260 | 0.553 | 0.612 |
| 90 | **market+crop** | **0.658** | +0.140 | 0.661 | **0.713** | **0.222** | 0.619 | 0.697 |
| 90 | market+wasde+crop | 0.646 | +0.128 | 0.648 | 0.655 | 0.251 | 0.601 | 0.690 |
| 90 | wasde+crop_only | 0.614 | +0.097 | 0.613 | 0.636 | 0.242 | 0.577 | 0.652 |

Bootstrap DA (IC 95 %, blocs de 20 j) : H90 market_only [0.546, 0.658] vs market+crop
[0.605, 0.709] ; H40 market_only [0.507, 0.605] vs market+wasde [0.538, 0.643].

## Lecture honnête
1. **Le cadrage directionnel (classification) révèle le signal que le RMSE de l'étape 4
   masquait.** Le marché seul a déjà une skill directionnelle à H40/H90 (DA 0.55-0.60) mais
   **instable** (1re moitié faible : 0.519 à H40, 0.527 à H90).
2. **Crop Condition à H90 = meilleur résultat de l'étape 5** : DA 0.599→**0.658** (+5.9 pts),
   AUC 0.608→**0.713**, Brier **meilleur** (0.245→0.222), **stable** sur les deux moitiés
   (0.619/0.697). Confirme et renforce EXT019. C'est un vrai signal d'état d'offre lent.
3. **WASDE à H40** : DA 0.555→0.590 (+3.5 pts) et surtout **stabilise la 1re moitié**
   (0.519→0.591). Confirme EXT007.
4. **Parcimonie** : le modèle combiné (wasde+crop) ne bat PAS le meilleur signal seul
   (crop@H90, wasde@H40) — ajouter les deux introduit de la redondance. Garder UN signal
   par horizon.
5. **Les fondamentaux ne prédisent PAS seuls** : sans marché, DA 0.491 à H40 (inutile),
   0.614 à H90 (modeste). Ils sont **complémentaires** du momentum de marché, pas autonomes.
6. **Réserve** : les IC bootstrap market_only vs market+fondamental se chevauchent → le gain
   est net et stable mais pas formellement significatif contre le marché seul → **IMPROVE**,
   pas KEEP franc. Le saut d'AUC à H90 (+0.10) et la meilleure calibration penchent KEEP.

## Coefficients (H90, market+wasde+crop)
Plus gros poids : `s2u_pctile`, `s2u_z` (bilan WASDE), `cond_dev5y`, `cond_gd_ex_anom`
(condition), puis saisonnalité. Tous économiquement sensés (bilan tendu + bonne/mauvaise
condition + saison).

## Conclusion
**IMPROVE.** Oui, les deux signaux deviennent un indicateur **directionnel** crédible à
horizon long — surtout **Crop Condition à H90** (KEEP-leaning) et **WASDE à H40**. Mais
uniquement en cadrage direction/score, jamais sur le prix/RMSE, uniquement en complément
du momentum, et un seul signal par horizon (parcimonie). Suite : EXT015 (la sélection
train-only retient-elle ces variables ?), EXT017 (dans quels régimes ?), EXT050 (ensemble).
