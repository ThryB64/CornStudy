# TARGET LABS V6

> Cibles auxiliaires EMA premium et CBOT pour alimenter le stacking V6.

## Verdict

- Cibles testees : 55
- Cibles OOF evaluables : 53
- Meilleure cible EMA : `y_rel_outperform_when_basis_extreme_h40` AUC 0.968
- Meilleure cible CBOT : `y_cbot_drawdown_5pct_h20` AUC 0.750
- Lecture : Best EMA target remains premium/relative (y_rel_outperform_when_basis_extreme_h40); best CBOT target is y_cbot_drawdown_5pct_h20. Use these as auxiliary experts for V6 stacking.

## Resultats

| Market | Target | Verdict | n OOF | AUC | Bal. acc | Top20 | Rare |
|---|---|---|---:|---:|---:|---:|---|
| ema | `y_rel_outperform_h10` | WATCHLIST | 714 | 0.625 | 0.605 | 0.613 | False |
| ema | `y_rel_large_outperform_h10` | WATCHLIST | 714 | 0.643 | 0.614 | 0.711 | False |
| ema | `y_rel_large_underperform_h10` | WATCHLIST | 714 | 0.600 | 0.568 | 0.563 | False |
| ema | `y_rel_outperform_after_cbot_weak_h10` | NO_GO | 352 | 0.554 | 0.553 | 0.643 | False |
| ema | `y_rel_outperform_when_basis_extreme_h10` | PROMISING | 91 | 0.834 | 0.741 | 0.944 | False |
| ema | `y_rel_outperform_h20` | PROMISING | 704 | 0.742 | 0.647 | 0.900 | False |
| ema | `y_rel_large_outperform_h20` | PROMISING | 704 | 0.756 | 0.653 | 0.907 | False |
| ema | `y_rel_large_underperform_h20` | PROMISING | 704 | 0.728 | 0.624 | 0.886 | False |
| ema | `y_rel_outperform_after_cbot_weak_h20` | WATCHLIST | 332 | 0.646 | 0.618 | 0.773 | False |
| ema | `y_rel_outperform_when_basis_extreme_h20` | PROMISING | 91 | 0.877 | 0.783 | 1.000 | False |
| ema | `y_rel_outperform_h40` | PROMISING | 680 | 0.768 | 0.711 | 0.809 | False |
| ema | `y_rel_large_outperform_h40` | PROMISING | 680 | 0.813 | 0.734 | 0.882 | False |
| ema | `y_rel_large_underperform_h40` | PROMISING | 680 | 0.756 | 0.700 | 0.831 | False |
| ema | `y_rel_outperform_after_cbot_weak_h40` | WATCHLIST | 332 | 0.693 | 0.652 | 0.742 | False |
| ema | `y_rel_outperform_when_basis_extreme_h40` | PROMISING | 91 | 0.968 | 0.908 | 1.000 | False |
| ema | `y_rel_outperform_h60` | PROMISING | 680 | 0.778 | 0.747 | 0.890 | False |
| ema | `y_rel_large_outperform_h60` | PROMISING | 680 | 0.804 | 0.770 | 0.897 | False |
| ema | `y_rel_large_underperform_h60` | PROMISING | 680 | 0.762 | 0.727 | 0.868 | False |
| ema | `y_rel_outperform_after_cbot_weak_h60` | WATCHLIST | 332 | 0.659 | 0.594 | 0.894 | False |
| ema | `y_rel_outperform_when_basis_extreme_h60` | PROMISING | 91 | 0.768 | 0.725 | 0.500 | False |
| ema | `y_rel_outperform_h90` | PROMISING | 680 | 0.828 | 0.763 | 0.890 | False |
| ema | `y_rel_large_outperform_h90` | PROMISING | 680 | 0.864 | 0.787 | 0.926 | False |
| ema | `y_rel_large_underperform_h90` | PROMISING | 680 | 0.827 | 0.781 | 0.860 | False |
| ema | `y_rel_outperform_after_cbot_weak_h90` | PROMISING | 332 | 0.749 | 0.695 | 0.864 | False |
| ema | `y_rel_outperform_when_basis_extreme_h90` | SKIPPED | 59 | N/A | N/A | N/A | False |
| ema | `y_rel_outperform_h120` | PROMISING | 680 | 0.921 | 0.810 | 0.978 | False |
| ema | `y_rel_large_outperform_h120` | PROMISING | 680 | 0.910 | 0.795 | 0.985 | False |
| ema | `y_rel_large_underperform_h120` | PROMISING | 680 | 0.871 | 0.794 | 0.897 | False |
| ema | `y_rel_outperform_after_cbot_weak_h120` | PROMISING | 299 | 0.731 | 0.652 | 0.864 | False |
| ema | `y_rel_outperform_when_basis_extreme_h120` | SKIPPED | 59 | N/A | N/A | N/A | False |
| cbot | `y_cbot_up_h10` | WATCHLIST | 657 | 0.605 | 0.566 | 0.725 | False |
| cbot | `y_cbot_large_up_3pct_h10` | NO_GO | 657 | 0.507 | 0.490 | 0.534 | False |
| cbot | `y_cbot_large_down_3pct_h10` | WATCHLIST | 657 | 0.649 | 0.579 | 0.733 | False |
| cbot | `y_cbot_rally_5pct_h10` | NO_GO | 624 | 0.510 | 0.493 | 0.629 | False |
| cbot | `y_cbot_drawdown_5pct_h10` | WATCHLIST | 657 | 0.651 | 0.604 | 0.718 | False |
| cbot | `y_cbot_up_h20` | WATCHLIST | 544 | 0.697 | 0.628 | 0.833 | False |
| cbot | `y_cbot_large_up_3pct_h20` | WATCHLIST | 544 | 0.678 | 0.588 | 0.843 | False |
| cbot | `y_cbot_large_down_3pct_h20` | PROMISING | 544 | 0.700 | 0.625 | 0.843 | False |
| cbot | `y_cbot_rally_5pct_h20` | WATCHLIST | 544 | 0.636 | 0.594 | 0.778 | False |
| cbot | `y_cbot_drawdown_5pct_h20` | PROMISING | 544 | 0.750 | 0.693 | 0.889 | False |
| cbot | `y_cbot_up_h40` | WATCHLIST | 478 | 0.659 | 0.623 | 0.979 | False |
| cbot | `y_cbot_large_up_3pct_h40` | WATCHLIST | 478 | 0.679 | 0.627 | 0.947 | False |
| cbot | `y_cbot_large_down_3pct_h40` | WATCHLIST | 478 | 0.665 | 0.650 | 0.905 | False |
| cbot | `y_cbot_rally_5pct_h40` | WATCHLIST | 478 | 0.683 | 0.630 | 0.842 | False |
| cbot | `y_cbot_drawdown_5pct_h40` | WATCHLIST | 419 | 0.687 | 0.622 | 0.940 | False |
| cbot | `y_cbot_up_h60` | WATCHLIST | 488 | 0.645 | 0.575 | 0.866 | False |
| cbot | `y_cbot_large_up_3pct_h60` | NO_GO | 488 | 0.589 | 0.539 | 0.835 | False |
| cbot | `y_cbot_large_down_3pct_h60` | PROMISING | 488 | 0.705 | 0.664 | 0.825 | False |
| cbot | `y_cbot_rally_5pct_h60` | NO_GO | 433 | 0.541 | 0.511 | 0.698 | False |
| cbot | `y_cbot_drawdown_5pct_h60` | PROMISING | 430 | 0.718 | 0.653 | 0.919 | False |
| cbot | `y_cbot_up_h90` | WATCHLIST | 509 | 0.650 | 0.626 | 0.782 | False |
| cbot | `y_cbot_large_up_3pct_h90` | NO_GO | 452 | 0.580 | 0.545 | 0.633 | False |
| cbot | `y_cbot_large_down_3pct_h90` | PROMISING | 450 | 0.716 | 0.653 | 0.956 | False |
| cbot | `y_cbot_rally_5pct_h90` | NO_GO | 452 | 0.558 | 0.486 | 0.678 | False |
| cbot | `y_cbot_drawdown_5pct_h90` | WATCHLIST | 450 | 0.698 | 0.648 | 0.944 | False |