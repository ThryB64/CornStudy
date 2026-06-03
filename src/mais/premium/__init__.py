"""Périmètre PREMIUM — l'indicateur de prime EMA/CBOT, séparé du legacy farmer/cash.

Single source of truth : `premium_daily_head.json` (build_premium_head). Tout ce qui n'est pas ici
(ops/daily.py, decision/, farmer_backtest, SELL_NOW) est LEGACY et hors périmètre premium.
RESEARCH_ONLY_NOT_TRADING.
"""
