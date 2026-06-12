# 📊 Dashboard indicateur premium v5 — 2026-06-12
_Généré 2026-06-12 20:37:36 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_STRONG** · basis 72.16 €/t · z 1.744 (proxy_implied)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **STRONG_SIGNAL** · score composite **2/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **COMPRESSION_HEALTHY** · nature **PRIME_PHYSICALLY_JUSTIFIED** · cycle **COMPRESSION_HEALTHY**
- Objectif **z->0.5** · horizon ~23 j

## Signal actif (V124/V179)
- Entrée 2026-05-29 (z 2.056) · 14 j · statut **HEALTHY**
- Compression réalisée **3.99 €/t** · MFE 3.99 · MAE 0.28 · distance z→0.5 : 1.244

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 8.75 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.943 · substitution DATA_BLOCKED
- CBOT_SUPPORT LOW · ADVERSE_RISK MEDIUM · PHYSICAL_TENSION HIGH
- Météo US LOW · Météo EU MEDIUM

## Officiel / proxy & jalons
- Jours officiels **11** · prochain jalon **40** (z-score officiel rolling) · z rolling officiel False
- Validation V178 (40 j) : **ACCUMULATING_11_OF_40** · paires proxy↔officiel 3
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 11/150', 'V168_MATIF': 'ACCUMULATING 10/150', 'V155_SUMMER': 'ACCUMULATING 94/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_INCONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ['prime adossée à une tension physique (backwardation) -> compression plus lente']

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
