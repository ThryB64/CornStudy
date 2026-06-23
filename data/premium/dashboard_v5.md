# 📊 Dashboard indicateur premium v5 — 2026-06-23
_Généré 2026-06-23 20:36:58 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 66.86 €/t · z 1.329 (proxy_implied)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **CONFIRMED_SIGNAL** · score composite **1/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **COMPRESSION_HEALTHY** · nature **PRIME_EXCESSIVE** · cycle **COMPRESSION_HEALTHY**
- Objectif **z->0.5** · horizon ~23 j

## Signal actif (V124/V179)
- Entrée 2026-05-29 (z 2.056) · 25 j · statut **HEALTHY**
- Compression réalisée **9.29 €/t** · MFE 12.89 · MAE 1.47 · distance z→0.5 : 0.829

## Contexte marché
- Courbe EMA : NARROWING (spread front-next -2.75 €/t, CONTANGO)
- MATIF blé/maïs : 0.945 · substitution DATA_BLOCKED
- CBOT_SUPPORT LOW · ADVERSE_RISK HIGH · PHYSICAL_TENSION LOW
- Météo US MEDIUM · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **18** · prochain jalon **40** (z-score officiel rolling) · z rolling officiel False
- Validation V178 (40 j) : **ACCUMULATING_18_OF_40** · paires proxy↔officiel 10
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 18/150', 'V168_MATIF': 'ACCUMULATING 17/150', 'V155_SUMMER': 'ACCUMULATING 105/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ["ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer"]

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
