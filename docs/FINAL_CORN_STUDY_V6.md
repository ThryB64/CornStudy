# FINAL CORN STUDY V6

## Executive Summary

- Central thesis: CBOT remains the global maize engine; Euronext EMA signal is strongest in the EMA/CBOT European premium.
- CBOT status: `modest_but_real_global_context_signal`
- EMA absolute status: `NO_GO_AS_MAIN_TARGET`
- EMA premium status: `PRIMARY_RESEARCH_SIGNAL`
- Production verdict: `RESEARCH_ONLY_NOT_TRADING`

## Main V6 Discoveries

- Robust premium meta-model: `y_rel_outperform_h90` / `classic_plus_meta`, n=503, AUC=0.937, top20=0.970.
- Context sensor: `y_rel_outperform_when_basis_extreme_h90`, AUC=1.000, n=29 ; treated as narrow-context evidence.
- Best seasonal/roll policy: `seasonal_expert` / `top20_train_only`, coverage=0.135, BA=0.983, AUC=0.982.
- Best research-only spread backtest: `seasonal_expert` / `top40_no_roll`, trades=9, PnL=179.648 EUR/t, PF=100.160.
- Cross-market CBOT result: `y_cbot_up_h60` / `cbot_full_cross_market`, AUC=0.577, delta AUC=0.059.

## Scientific Interpretation

- EMA absolute direction remains a rejected main target.
- EMA/CBOT relative premium is the research core.
- Basis and seasonality are not auxiliary decoration; they are central economic structure.
- Cross-target OOF stacking improves selectivity and confidence, especially on H90 premium.
- Cross-market EMA→CBOT adds modest context to selected CBOT risk targets, but CBOT meta-signals do not improve EMA premium.

## Final Review

- Review verdict: `PASS_WITH_RESEARCH_ONLY_CAVEATS`

| Check | Pass |
|---|---:|
| `required_json_present` | `True` |
| `required_registry_present` | `True` |
| `required_docs_present` | `True` |
| `required_tests_present` | `True` |
| `meta_best_robust_support_ok` | `True` |
| `context_perfect_signal_not_main` | `True` |
| `backtest_research_only` | `True` |
| `ema_proxy_caveat_present` | `True` |
| `notebook_v6_blocked_by_agents_rule` | `True` |

## Caveats

- EMA historical data remains exploratory/proxy and must be validated on an official/licensed source.
- Backtests are research-only and not production/trading claims.
- The best seasonal backtest has a small number of non-overlapping trades.
- Notebook V6 remains blocked by AGENTS rules forbidding `notebooks/` access.

## Recommended Next Research

- Validate EMA history with official/licensed Euronext source.
- Re-run premium V6 on official data and true bid/ask/liquidity.
- Keep EMA/CBOT premium as main target; do not force EMA absolute direction.
- Use seasonal expert and confidence filters as research signals only.
- Extend EU fundamentals with true monthly MARS, FranceAgriMer, COMEXT and Ukraine flow data.