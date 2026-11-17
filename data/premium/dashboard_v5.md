# 📊 Dashboard indicateur premium v5 — 2026-11-16
_Généré 2026-11-17 01:57:42 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 100.52 €/t · z 1.346 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **CONFIRMED_SIGNAL** · score composite **0/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **PRIME_EXCESSIVE** · nature **PRIME_EXCESSIVE** · cycle **ACTIVE_EARLY**
- Objectif **z->0.5** · horizon ~51 j

## Signal actif (V124/V179)
- Entrée 2026-11-11 (z 1.05) · 5 j · statut **ACTIVE_EARLY**
- Compression réalisée **-3.28 €/t** · MFE 0.0 · MAE 3.28 · distance z→0.5 : 0.846

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 3.5 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.888 · substitution DATA_BLOCKED
- CBOT_SUPPORT LOW · ADVERSE_RISK HIGH · PHYSICAL_TENSION MEDIUM
- Météo US LOW · Météo EU LOW

## Officiel / proxy & jalons
- Jours officiels **122** · prochain jalon **180** (bilan forward) · z rolling officiel True
- Validation V178 (40 j) : **PROXY_RESEARCH_ONLY** · paires proxy↔officiel 61
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 122/150', 'V168_MATIF': 'ACCUMULATING 121/150', 'V155_SUMMER': 'TRIGGERED 252/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ["ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer"]

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
