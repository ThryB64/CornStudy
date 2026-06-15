# 📊 Dashboard indicateur premium v5 — 2026-06-15
_Généré 2026-06-15 11:33:22 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_STRONG** · basis 74.42 €/t · z 1.921 (proxy_implied)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **STRONG_SIGNAL** · score composite **2/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **COMPRESSION_HEALTHY** · nature **PRIME_PHYSICALLY_JUSTIFIED** · cycle **COMPRESSION_HEALTHY**
- Objectif **z->0.5** · horizon ~23 j

## Signal actif (V124/V179)
- Entrée 2026-05-29 (z 2.056) · 17 j · statut **HEALTHY**
- Compression réalisée **1.73 €/t** · MFE 3.99 · MAE 0.28 · distance z→0.5 : 1.421

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 8.75 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.944 · substitution DATA_BLOCKED
- CBOT_SUPPORT LOW · ADVERSE_RISK MEDIUM · PHYSICAL_TENSION HIGH
- Météo US UNKNOWN (stale) · Météo EU HIGH

## Officiel / proxy & jalons
- Jours officiels **12** · prochain jalon **40** (z-score officiel rolling) · z rolling officiel False
- Validation V178 (40 j) : **ACCUMULATING_12_OF_40** · paires proxy↔officiel 4
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 12/150', 'V168_MATIF': 'ACCUMULATING 11/150', 'V155_SUMMER': 'ACCUMULATING 97/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ['prime adossée à une tension physique (backwardation) -> compression plus lente']

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
