# 📊 Dashboard indicateur premium v5 — 2026-06-18
_Généré 2026-06-18 21:06:19 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 68.51 €/t · z 1.459 (proxy_implied)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **CONFIRMED_SIGNAL** · score composite **1/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **COMPRESSION_HEALTHY** · nature **PRIME_EXCESSIVE** · cycle **COMPRESSION_HEALTHY**
- Objectif **z->0.5** · horizon ~23 j

## Signal actif (V124/V179)
- Entrée 2026-05-29 (z 2.056) · 20 j · statut **HEALTHY**
- Compression réalisée **7.64 €/t** · MFE 12.89 · MAE 0.28 · distance z→0.5 : 0.959

## Contexte marché
- Courbe EMA : NARROWING (spread front-next -3.0 €/t, CONTANGO)
- MATIF blé/maïs : 0.969 · substitution DATA_BLOCKED
- CBOT_SUPPORT LOW · ADVERSE_RISK HIGH · PHYSICAL_TENSION LOW
- Météo US MEDIUM · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **15** · prochain jalon **40** (z-score officiel rolling) · z rolling officiel False
- Validation V178 (40 j) : **ACCUMULATING_15_OF_40** · paires proxy↔officiel 7
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 15/150', 'V168_MATIF': 'ACCUMULATING 14/150', 'V155_SUMMER': 'ACCUMULATING 100/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ["ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer"]

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
