# 📊 Dashboard indicateur premium v5 — 2026-11-23
_Généré 2026-11-23 16:20:43 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_STRONG** · basis 103.31 €/t · z 1.564 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **STRONG_SIGNAL** · score composite **1/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **COMPRESSION_DELAYED** · nature **PRIME_PHYSICALLY_JUSTIFIED** · cycle **COMPRESSION_DELAYED**
- Objectif **z->0.5** · horizon ~51 j

## Signal actif (V124/V179)
- Entrée 2026-11-11 (z 1.05) · 12 j · statut **SLOW**
- Compression réalisée **-6.07 €/t** · MFE 0.0 · MAE 6.83 · distance z→0.5 : 1.064

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 5.25 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.878 · substitution DATA_BLOCKED
- CBOT_SUPPORT LOW · ADVERSE_RISK LOW · PHYSICAL_TENSION HIGH
- Météo US LOW · Météo EU LOW

## Officiel / proxy & jalons
- Jours officiels **127** · prochain jalon **180** (bilan forward) · z rolling officiel True
- Validation V178 (40 j) : **PROXY_RESEARCH_ONLY** · paires proxy↔officiel 61
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 127/150', 'V168_MATIF': 'ACCUMULATING 126/150', 'V155_SUMMER': 'TRIGGERED 258/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ['prime adossée à une tension physique (backwardation) -> compression plus lente']

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
