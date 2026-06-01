# EMA / CBOT Relationship

> EMA historical prices are exploratory Barchart-derived data, not official Euronext settlement.

## Dataset

- Rows: 3082
- Period: 2010-01-04 -> 2025-07-25
- Price overlap: 3081

## Level And Basis

- Price correlation EMA vs CBOT EUR/t: 0.9409
- 1d return correlation: 0.3425
- Basis mean: 37.2297 EUR/t
- Basis std: 15.5229 EUR/t
- Basis range: -11.7072 -> 110.6579 EUR/t

## Lead-Lag

- Definition: corr(EMA adjusted return at t, CBOT EUR/t return at t+lag). Positive lag means EMA leads CBOT.
- Contemporaneous: lag 0 (same day), corr=0.3425, n=3079
- Best EMA leads: lag 1 (EMA leads CBOT), corr=0.0387, n=3078
- Best CBOT leads: lag -1 (CBOT leads EMA), corr=0.0423, n=3078
- Verdict: `mostly_contemporaneous`

## Rolling Correlation

- Window: 60 days
- Mean: 0.4116
- Median: 0.3941
- Range: -0.0025 -> 0.8755
- Share positive: 100.0%

## Granger

- Status: `OK`
- `ema_returns_to_cbot_returns`: min p=0.0144, best lag=1
- `cbot_returns_to_ema_returns`: min p=0.1605, best lag=2
- `basis_to_ema_returns`: min p=0.0735, best lag=1
- `basis_to_cbot_returns`: min p=0.0883, best lag=1

## Interpretation

- Granger and lead-lag diagnostics are exploratory and do not prove causality.
- Next step: Run basis mean-reversion study on basis z-score regimes.
