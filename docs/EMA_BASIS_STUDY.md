# EMA Basis Study

> EMA historical prices are exploratory Barchart-derived data, not official Euronext settlement.

## Dataset

- Rows: 3082
- Period: 2010-01-04 -> 2025-07-25
- Basis z-score window: 260 days

## Basis Distribution

- Mean: 37.2297 EUR/t
- Std: 15.5229 EUR/t
- P05/P50/P95: 8.4998 / 37.8577 / 62.5038 EUR/t
- High z>=2 share: 6.2%
- Low z<=-2 share: 5.1%

## Mean Reversion By Regime

- high H20: n=186, basis change mean=-7.6387, reversion=70.4%, EMA-CBOT return mean=-0.0622
- low H20: n=153, basis change mean=6.0641, reversion=68.0%, EMA-CBOT return mean=0.0725
- neutral H20: n=1832, basis change mean=0.6396, reversion=95.0%, EMA-CBOT return mean=-0.0032
- high H40: n=186, basis change mean=-8.9917, reversion=76.9%, EMA-CBOT return mean=-0.0927
- low H40: n=153, basis change mean=9.3673, reversion=79.1%, EMA-CBOT return mean=0.0825
- neutral H40: n=1812, basis change mean=0.2488, reversion=93.5%, EMA-CBOT return mean=-0.0088
- high H60: n=186, basis change mean=-12.7319, reversion=87.1%, EMA-CBOT return mean=-0.1054
- low H60: n=153, basis change mean=15.4751, reversion=83.7%, EMA-CBOT return mean=0.1372
- neutral H60: n=1792, basis change mean=-0.1386, reversion=92.0%, EMA-CBOT return mean=-0.0150

## Decision

- Verdict: `BASIS_MEAN_REVERSION_CONFIRMED`
- High and low basis extremes both tend to revert at the reference horizon.
