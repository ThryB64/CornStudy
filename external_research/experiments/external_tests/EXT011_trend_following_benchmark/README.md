# EXT011 — Trend-following benchmark

Règles figées ex ante (momentum 20/60/120, MA 50/200, EWMAC 16/64) sur CBOT continu.
Évalué en direction H40/H90 et en stratégie (Sharpe/maxDD/hit/turnover), causal.
`run_EXT011.py` produit `trend_signals.csv`, `trend_backtest_metrics.csv`, `metrics_EXT011.csv`.

Verdict : **REJECT** — le maïs ne tend pas (DA < 0.5, Sharpe ≤ 0.20 avec drawdowns énormes).
Negative control utile : l'edge directionnel d'EXT024 n'est PAS du momentum déguisé.
