# EMA ROLL TARGET AFTER FIX

> Benchmark raw / adjusted / no-roll après correction de l'intégrité des targets futures.

## Verdict

- Verdict : ROLL_TARGET_NOT_EXPLAINED
- Raison : Roll-aware targets do not materially improve the primary EMA benchmark.
- Meilleure amélioration DA vs raw : -0.1%

H60 no-roll peut être structurellement indisponible car presque toutes les fenêtres H60 traversent un roll.

## Audit tail NaN

| Target | Horizon | Non-null | Tail non-null | Verdict |
|---|---:|---:|---:|---|
| y_up_h20_ema_raw | 20 | 3357 | 0 | PASS |
| y_up_h20_ema_adjusted | 20 | 3357 | 0 | PASS |
| y_up_h20_ema_no_roll | 20 | 2023 | 0 | PASS |
| y_up_h40_ema_raw | 40 | 3337 | 0 | PASS |
| y_up_h40_ema_adjusted | 40 | 3337 | 0 | PASS |
| y_up_h40_ema_no_roll | 40 | 699 | 0 | PASS |
| y_up_h60_ema_raw | 60 | 3317 | 0 | PASS |
| y_up_h60_ema_adjusted | 60 | 3317 | 0 | PASS |
| y_up_h60_ema_no_roll | 60 | 0 | 0 | PASS |

## Résultats primaires

| Horizon | Variante | Statut | n OOF | DA | AUC | Top20 DA |
|---:|---|---|---:|---:|---:|---:|
| 20 | raw | OK | 1575 | 46.7% | 0.503 | 60.3% |
| 20 | adjusted | OK | 1575 | 44.7% | 0.444 | 48.9% |
| 20 | no_roll | OK | 949 | 44.6% | 0.438 | 43.7% |
| 40 | raw | OK | 1575 | 40.9% | 0.433 | 46.7% |
| 40 | adjusted | OK | 1575 | 40.4% | 0.375 | 47.0% |
| 40 | no_roll | OK | 334 | 32.0% | 0.286 | 22.4% |
| 60 | raw | OK | 1575 | 45.5% | 0.490 | 54.3% |
| 60 | adjusted | OK | 1575 | 45.3% | 0.382 | 47.6% |
| 60 | no_roll | SKIPPED | 0 | N/A | N/A | N/A |