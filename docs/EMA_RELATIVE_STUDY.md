# EMA RELATIVE STUDY

> Étude reproductible de la performance relative EMA/CBOT. Ce n'est pas une prédiction de direction EMA absolue.

## Verdict

- Verdict : RELATIVE_EMA_CBOT_SIGNAL_CONFIRMED
- Meilleur horizon : H90
- AUC daily meilleur horizon : 0.770
- Balanced accuracy : 0.692
- Top20 DA : 0.887

## Résultats daily

| Horizon | n | Base rate | DA | AUC | Balanced acc. | Top20 DA | Stabilité annuelle |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 2438 | 0.472 | 0.586 | 0.614 | 0.580 | 0.667 | 0.846 |
| 20 | 2428 | 0.482 | 0.626 | 0.663 | 0.621 | 0.732 | 0.846 |
| 40 | 2408 | 0.511 | 0.640 | 0.708 | 0.642 | 0.771 | 0.923 |
| 60 | 2388 | 0.496 | 0.648 | 0.724 | 0.647 | 0.803 | 0.769 |
| 90 | 2358 | 0.528 | 0.690 | 0.770 | 0.692 | 0.887 | 0.923 |

## Résultats weekly

| Horizon | n | DA | AUC | Balanced acc. | Top20 DA |
|---:|---:|---:|---:|---:|---:|
| 10 | 560 | 0.591 | 0.622 | 0.578 | 0.714 |
| 20 | 558 | 0.611 | 0.663 | 0.605 | 0.784 |
| 40 | 553 | 0.642 | 0.728 | 0.647 | 0.818 |
| 60 | 549 | 0.628 | 0.715 | 0.625 | 0.807 |
| 90 | 525 | 0.646 | 0.766 | 0.655 | 0.876 |

## Lecture

La cible relative retire le moteur mondial CBOT et isole mieux la prime européenne. C'est le cœur prédictif actuel de l'étude EMA.