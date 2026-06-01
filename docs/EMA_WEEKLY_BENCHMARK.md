# EMA WEEKLY BENCHMARK

> Benchmark vendredi→vendredi H4/H8/H12 semaines après correction des targets.

## Verdict

- Meilleur signal hebdomadaire : basis_reversion H12w
- Score meilleur signal : 76.4%
- EMA direct weekly : {'4': 'WEEKLY_GO', '8': 'WEEKLY_NO_GO', '12': 'WEEKLY_NO_GO'}

Weekly réduit le bruit quotidien, mais ne transforme pas automatiquement EMA direct en signal validé.

## Résultats généralisés

| Signal | Horizon | n | Score | IC95 | Verdict |
|---|---:|---:|---:|---|---|
| ema_direct_momentum | 4 | 679 | 54.6% | [51.1%; 58.3%] | WEEKLY_GO |
| relative_ema_outperformance_basis_z | 4 | 653 | 57.7% | [53.7%; 61.9%] | WEEKLY_GO |
| basis_reversion | 4 | 144 | 63.2% | [55.6%; 71.2%] | WEEKLY_GO |
| ema_vol_high_persistence | 4 | 619 | 73.8% | [70.4%; 77.6%] | WEEKLY_GO |
| ema_direct_momentum | 8 | 675 | 53.3% | [49.6%; 57.0%] | WEEKLY_NO_GO |
| relative_ema_outperformance_basis_z | 8 | 649 | 60.7% | [57.3%; 64.3%] | WEEKLY_GO |
| basis_reversion | 8 | 144 | 66.7% | [59.4%; 74.7%] | WEEKLY_GO |
| ema_vol_high_persistence | 8 | 615 | 72.5% | [69.3%; 76.1%] | WEEKLY_GO |
| ema_direct_momentum | 12 | 671 | 49.0% | [45.2%; 52.8%] | WEEKLY_NO_GO |
| relative_ema_outperformance_basis_z | 12 | 645 | 62.0% | [58.1%; 65.6%] | WEEKLY_GO |
| basis_reversion | 12 | 144 | 76.4% | [70.1%; 82.6%] | WEEKLY_GO |
| ema_vol_high_persistence | 12 | 611 | 71.5% | [67.9%; 74.9%] | WEEKLY_GO |