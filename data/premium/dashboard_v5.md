# 📊 Dashboard indicateur premium v5 — 2026-11-25
_Généré 2026-11-26 01:55:27 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 102.78 €/t · z 1.483 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **CONFIRMED_SIGNAL** · score composite **1/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **COMPRESSION_DELAYED** · nature **PRIME_PHYSICALLY_JUSTIFIED** · cycle **COMPRESSION_DELAYED**
- Objectif **z->0.5** · horizon ~51 j

## Signal actif (V124/V179)
- Entrée 2026-11-11 (z 1.05) · 14 j · statut **SLOW**
- Compression réalisée **-5.54 €/t** · MFE 0.0 · MAE 9.64 · distance z→0.5 : 0.983

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 5.0 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.888 · substitution DATA_BLOCKED
- CBOT_SUPPORT LOW · ADVERSE_RISK MEDIUM · PHYSICAL_TENSION HIGH
- Météo US LOW · Météo EU LOW

## Officiel / proxy & jalons
- Jours officiels **129** · prochain jalon **180** (bilan forward) · z rolling officiel True
- Validation V178 (40 j) : **PROXY_RESEARCH_ONLY** · paires proxy↔officiel 61
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 129/150', 'V168_MATIF': 'ACCUMULATING 128/150', 'V155_SUMMER': 'TRIGGERED 261/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ['prime adossée à une tension physique (backwardation) -> compression plus lente']

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
