# EMA 06 — Étude du Résidu EU (Chocs Européens Spécifiques)

> Source exploratoire (Barchart proxy). Résultats expérimentaux.

## Résultats clés

| Métrique | Valeur |
|---|---|
| Chocs extrêmes (≥3σ) | 49 événements (1.64% des jours) |
| Chocs extrêmes (≥2σ) | 149 événements |
| DA persistance signe lag-1 | 49.4% (aléatoire) |
| ADF résidu | Stationnaire |
| Std résidu | 0.407% |

## Chocs les plus importants (négatifs)

| Date | Résidu | z-score |
|---|---|---|
| 2022-07-18 | -4.27% | -10.5σ |
| 2022-07-15 | -3.60% | -8.8σ |

Le pic de juillet 2022 correspond à la détente des prix agricoles européens après la tension initiale liée à la guerre en Ukraine.

## Interprétation

**49 chocs identifiés** à 3σ sur 15 ans de données — soit environ 3 chocs/an de magnitude notable. Ces chocs représentent des mouvements d'EMA non expliqués par CBOT ni par le basis. Ce sont les vrais chocs "européens spécifiques".

**Le résidu est stationnaire** (ADF p << 0.05) et **non autocorrélé en signe** (DA ≈ 50%) — il ne contient pas de signal directionnel exploitable à court terme.

## Artefact produit

`artefacts/ema_study/ema_residual_study.json`
