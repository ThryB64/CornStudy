# EMA RELATIVE ERROR ANALYSIS

> Analyse des erreurs du signal `relative_ema_outperformance_h40`.

## Verdict

- OOF : 2408
- Corrects : 1540
- Erreurs : 868
- Tag principal erreurs : roll_risk_proxy
- Tag principal failed top20 : roll_risk_proxy

## Tags erreurs

| Tag | Worst errors | Failed top20 | Top correct |
|---|---:|---:|---:|
| basis_extreme | 56 | 34 | 84 |
| crisis_period | 54 | 33 | 36 |
| large_relative_move | 1 | 1 | 35 |
| roll_risk_proxy | 86 | 50 | 84 |
| unknown | 6 | 0 | 2 |

## Lecture

Ces tags sont heuristiques. Ils servent à construire les filtres d'abstention, pas à attribuer causalement chaque erreur.