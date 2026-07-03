# EMA ABSTENTION FILTERS

> Filtres d'abstention sur `relative_ema_outperformance_h40`.

## Verdict

- Baseline DA : 0.639
- Baseline balanced accuracy : 0.642
- Meilleur filtre : basis_extreme_only
- Balanced accuracy meilleur filtre : 0.761
- Coverage meilleur filtre : 0.231
- Lecture : Abstention materially improves balanced accuracy, but must be checked in backtest.

## Filtres

| Filtre | n | Coverage | DA | AUC | Balanced acc. | Top20 DA | Δ BAcc |
|---|---:|---:|---:|---:|---:|---:|---:|
| all_signals | 2409 | 1.000 | 0.639 | 0.708 | 0.642 | 0.771 | 0.000 |
| top20_confidence | 482 | 0.200 | 0.772 | 0.796 | 0.732 | 0.885 | 0.090 |
| top40_confidence | 964 | 0.400 | 0.727 | 0.750 | 0.702 | 0.880 | 0.060 |
| no_roll_risk_proxy | 961 | 0.399 | 0.641 | 0.695 | 0.619 | 0.766 | -0.023 |
| no_crisis_years | 1803 | 0.748 | 0.627 | 0.690 | 0.630 | 0.817 | -0.012 |
| no_roll_no_crisis | 718 | 0.298 | 0.628 | 0.676 | 0.619 | 0.783 | -0.023 |
| basis_extreme_only | 556 | 0.231 | 0.768 | 0.789 | 0.761 | 0.874 | 0.119 |
| top40_no_roll_no_crisis | 176 | 0.073 | 0.761 | 0.771 | 0.682 | 1.000 | 0.040 |