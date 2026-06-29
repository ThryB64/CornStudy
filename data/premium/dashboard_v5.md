# 📊 Dashboard indicateur premium v5 — 2026-06-29
_Généré 2026-06-29 20:26:25 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_EXTREME** · basis 77.83 €/t · z 2.188 (proxy_implied)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **EXTREME_SIGNAL** · score composite **3/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **COMPRESSION_DELAYED** · nature **PRIME_EXCESSIVE** · cycle **COMPRESSION_DELAYED**
- Objectif **z->0.5** · horizon ~23 j

## Signal actif (V124/V179)
- Entrée 2026-05-29 (z 2.056) · 31 j · statut **DELAYED**
- Compression réalisée **-1.68 €/t** · MFE 12.89 · MAE 5.4 · distance z→0.5 : 1.688

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 2.0 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.917 · substitution DATA_BLOCKED
- CBOT_SUPPORT LOW · ADVERSE_RISK MEDIUM · PHYSICAL_TENSION MEDIUM
- Météo US MEDIUM · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **22** · prochain jalon **40** (z-score officiel rolling) · z rolling officiel False
- Validation V178 (40 j) : **ACCUMULATING_22_OF_40** · paires proxy↔officiel 14
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 22/150', 'V168_MATIF': 'ACCUMULATING 21/150', 'V155_SUMMER': 'ACCUMULATING 111/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_INCONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ['santé du signal DELAYED (signature lente/adverse)']

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
