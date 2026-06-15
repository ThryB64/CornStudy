# 📊 Dashboard indicateur premium v5 — 2026-06-15
_Généré 2026-06-15 21:34:41 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 68.37 €/t · z 1.448 (proxy_implied)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **CONFIRMED_SIGNAL** · score composite **1/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **COMPRESSION_HEALTHY** · nature **PRIME_PHYSICALLY_JUSTIFIED** · cycle **COMPRESSION_HEALTHY**
- Objectif **z->0.5** · horizon ~23 j

## Signal actif (V124/V179)
- Entrée 2026-05-29 (z 2.056) · 17 j · statut **HEALTHY**
- Compression réalisée **7.78 €/t** · MFE 7.78 · MAE 0.28 · distance z→0.5 : 0.948

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 6.25 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.944 · substitution DATA_BLOCKED
- CBOT_SUPPORT LOW · ADVERSE_RISK HIGH · PHYSICAL_TENSION HIGH
- Météo US LOW · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **12** · prochain jalon **40** (z-score officiel rolling) · z rolling officiel False
- Validation V178 (40 j) : **ACCUMULATING_12_OF_40** · paires proxy↔officiel 4
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 12/150', 'V168_MATIF': 'ACCUMULATING 11/150', 'V155_SUMMER': 'ACCUMULATING 97/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_INCONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ['prime adossée à une tension physique (backwardation) -> compression plus lente', "ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer"]

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
