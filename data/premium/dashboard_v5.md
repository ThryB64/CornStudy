# 📊 Dashboard indicateur premium v5 — 2026-10-09
_Généré 2026-10-09 12:03:43 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 93.46 €/t · z 1.355 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **CONFIRMED_SIGNAL** · score composite **1/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **COMPRESSION_HEALTHY** · nature **PRIME_EXCESSIVE** · cycle **COMPRESSION_HEALTHY**
- Objectif **z->0.5** · horizon ~51 j

## Signal actif (V124/V179)
- Entrée 2026-10-06 (z 1.466) · 3 j · statut **HEALTHY**
- Compression réalisée **0.49 €/t** · MFE 0.49 · MAE 1.52 · distance z→0.5 : 0.855

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 3.0 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.908 · substitution DATA_BLOCKED
- CBOT_SUPPORT HIGH · ADVERSE_RISK HIGH · PHYSICAL_TENSION MEDIUM
- Météo US UNKNOWN (stale) · Météo EU LOW

## Officiel / proxy & jalons
- Jours officiels **96** · prochain jalon **180** (bilan forward) · z rolling officiel True
- Validation V178 (40 j) : **PROXY_RESEARCH_ONLY** · paires proxy↔officiel 61
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 96/150', 'V168_MATIF': 'ACCUMULATING 95/150', 'V155_SUMMER': 'TRIGGERED 213/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ["ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer"]

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
