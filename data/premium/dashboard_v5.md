# 📊 Dashboard indicateur premium v5 — 2026-06-11
_Généré 2026-06-11 20:45:48 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_EXTREME** · basis 75.53 €/t · z 2.008 (proxy_implied)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **EXTREME_SIGNAL** · score composite **3/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **COMPRESSION_HEALTHY** · nature **PRIME_PHYSICALLY_JUSTIFIED** · cycle **COMPRESSION_HEALTHY**
- Objectif **z->0.5** · horizon ~23 j

## Signal actif (V124/V179)
- Entrée 2026-05-29 (z 2.056) · 13 j · statut **HEALTHY**
- Compression réalisée **0.62 €/t** · MFE 3.56 · MAE 0.28 · distance z→0.5 : 1.508

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 9.75 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.939 · substitution DATA_BLOCKED
- CBOT_SUPPORT MEDIUM · ADVERSE_RISK MEDIUM · PHYSICAL_TENSION HIGH
- Météo US MEDIUM · Météo EU LOW

## Officiel / proxy & jalons
- Jours officiels **10** · prochain jalon **40** (z-score officiel rolling) · z rolling officiel False
- Validation V178 (40 j) : **ACCUMULATING_10_OF_40** · paires proxy↔officiel 2
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 10/150', 'V168_MATIF': 'ACCUMULATING 9/150', 'V155_SUMMER': 'ACCUMULATING 93/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_INCONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ['prime adossée à une tension physique (backwardation) -> compression plus lente']

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
