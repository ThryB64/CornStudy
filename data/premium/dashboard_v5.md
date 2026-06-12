# 📊 Dashboard indicateur premium v5 — 2026-06-12
_Généré 2026-06-12 09:46:03 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_EXTREME** · basis 75.92 €/t · z 2.038 (proxy_implied)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **EXTREME_SIGNAL** · score composite **3/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **COMPRESSION_HEALTHY** · nature **PRIME_PHYSICALLY_JUSTIFIED** · cycle **COMPRESSION_HEALTHY**
- Objectif **z->0.5** · horizon ~23 j

## Signal actif (V124/V179)
- Entrée 2026-05-29 (z 2.056) · 14 j · statut **HEALTHY**
- Compression réalisée **0.23 €/t** · MFE 3.56 · MAE 0.28 · distance z→0.5 : 1.538

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 9.75 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.943 · substitution DATA_BLOCKED
- CBOT_SUPPORT MEDIUM · ADVERSE_RISK MEDIUM · PHYSICAL_TENSION HIGH
- Météo US LOW · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **11** · prochain jalon **40** (z-score officiel rolling) · z rolling officiel False
- Validation V178 (40 j) : **ACCUMULATING_11_OF_40** · paires proxy↔officiel 3
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 11/150', 'V168_MATIF': 'ACCUMULATING 10/150', 'V155_SUMMER': 'ACCUMULATING 94/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ['prime adossée à une tension physique (backwardation) -> compression plus lente']

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
