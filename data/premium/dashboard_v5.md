# 📊 Dashboard indicateur premium v5 — 2026-09-25
_Généré 2026-09-25 10:26:32 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_STRONG** · basis 96.56 €/t · z 1.815 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **STRONG_SIGNAL** · score composite **2/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **PRIME_PHYSICALLY_JUSTIFIED** · nature **PRIME_PHYSICALLY_JUSTIFIED** · cycle **ACTIVE_EARLY**
- Objectif **z->0.5** · horizon ~51 j

## Signal actif (V124/V179)
- Entrée 2026-09-22 (z 1.229) · 3 j · statut **ACTIVE_EARLY**
- Compression réalisée **-4.94 €/t** · MFE 0.2 · MAE 4.94 · distance z→0.5 : 1.315

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 7.5 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.863 · substitution DATA_BLOCKED
- CBOT_SUPPORT HIGH · ADVERSE_RISK LOW · PHYSICAL_TENSION HIGH
- Météo US LOW · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **86** · prochain jalon **90** (validation proxy/officiel) · z rolling officiel True
- Validation V178 (40 j) : **PROXY_RESEARCH_ONLY** · paires proxy↔officiel 61
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 86/150', 'V168_MATIF': 'ACCUMULATING 85/150', 'V155_SUMMER': 'TRIGGERED 199/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ['prime adossée à une tension physique (backwardation) -> compression plus lente']

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
