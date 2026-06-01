# EMA H90 STRESS TEST

> Stress test strict de `relative_ema_outperformance_h90`.

## Verdict

- Statut : `H90_MAIN_GO_RESEARCH_ONLY`
- Production : `NO_PRODUCTION_BACKTEST`
- Strict non-overlap n : 26
- Strict non-overlap DA : 0.769
- Strict non-overlap AUC : 0.922
- Strict non-overlap balanced accuracy : 0.797
- Cout 5 EUR/t/leg positif : True
- Lecture : H90 survives strict non-overlap, crisis exclusion and simplified high costs, but remains research-only.

## Scenarios

| Scenario | n | DA | AUC | Balanced acc. | Top20 DA | Stability |
|---|---:|---:|---:|---:|---:|---:|
| all_oof | 2358 | 0.690 | 0.770 | 0.692 | 0.887 | 0.929 |
| strict_non_overlap | 26 | 0.769 | 0.922 | 0.797 | 1.000 | 0.692 |
| no_roll_proxy | 941 | 0.637 | 0.724 | 0.637 | 0.888 | 0.857 |
| no_crisis_2020_2022 | 1785 | 0.700 | 0.758 | 0.694 | 0.899 | 0.909 |
| strict_non_overlap_no_roll_proxy | 24 | 0.583 | 0.590 | 0.583 | 0.750 | 0.308 |
| leave_out_2020 | 2166 | 0.687 | 0.756 | 0.688 | 0.878 | 0.923 |
| leave_out_2021 | 2169 | 0.691 | 0.766 | 0.692 | 0.889 | 0.923 |
| leave_out_2022 | 2166 | 0.699 | 0.780 | 0.702 | 0.898 | 0.923 |

## Cout Stress H90 Combined Top40

| Cout/leg | n | Hit rate | PnL moyen | PnL total | PF | Pos years |
|---:|---:|---:|---:|---:|---:|---:|
| 1.0 | 21 | 0.810 | 12.50 | 262.58 | 10.358 | 0.923 |
| 2.0 | 21 | 0.714 | 10.50 | 220.58 | 7.087 | 0.923 |
| 3.0 | 21 | 0.714 | 8.50 | 178.58 | 4.702 | 0.846 |
| 5.0 | 21 | 0.571 | 4.50 | 94.58 | 2.217 | 0.462 |