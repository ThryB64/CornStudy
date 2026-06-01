# EMA HIERARCHICAL CBOT PREMIUM V5

> Diagnostic : EMA absolu = composante CBOT mondiale + composante prime europeenne.

## Verdict

- Meilleur modele : `cbot_only`
- Horizon : H40
- AUC : 0.559
- Balanced accuracy : 0.545
- Top20 DA : 0.482
- Lecture : The global CBOT component dominates absolute EMA direction in this diagnostic.

## Resultats

| Modele | H | n | DA | AUC | Bal. acc | dAUC vs direct | dBal vs direct | Top20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `direct_ema` | 40 | 2408 | 0.547 | 0.516 | 0.547 | 0.000 | 0.000 | 0.503 |
| `cbot_only` | 40 | 2408 | 0.545 | 0.559 | 0.545 | 0.042 | -0.002 | 0.482 |
| `premium_only` | 40 | 2408 | 0.509 | 0.500 | 0.509 | -0.016 | -0.038 | 0.422 |
| `hierarchical_fixed` | 40 | 2408 | 0.515 | 0.540 | 0.516 | 0.024 | -0.032 | 0.489 |
| `hierarchical_train_weighted` | 40 | 2408 | 0.498 | 0.500 | 0.498 | -0.017 | -0.049 | 0.524 |
| `direct_ema` | 90 | 2167 | 0.454 | 0.410 | 0.464 | 0.000 | 0.000 | 0.256 |
| `cbot_only` | 90 | 2167 | 0.521 | 0.482 | 0.534 | 0.072 | 0.071 | 0.360 |
| `premium_only` | 90 | 2167 | 0.500 | 0.491 | 0.508 | 0.081 | 0.044 | 0.418 |
| `hierarchical_fixed` | 90 | 2167 | 0.481 | 0.472 | 0.495 | 0.062 | 0.031 | 0.406 |
| `hierarchical_train_weighted` | 90 | 2167 | 0.494 | 0.532 | 0.507 | 0.122 | 0.043 | 0.510 |

## Limites

- La direction EMA absolue reste une cible diagnostic, pas le coeur de l'etude.
- La source EMA reste exploratoire/proxy.
- Les poids hierarchiques sont calibres uniquement sur train mais restent simples.