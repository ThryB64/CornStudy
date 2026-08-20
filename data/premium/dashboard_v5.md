# 📊 Dashboard indicateur premium v5 — 2026-08-20
_Généré 2026-08-20 19:11:35 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_STRONG** · basis 93.35 €/t · z 1.57 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **STRONG_SIGNAL** · score composite **3/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **PRIME_PHYSICALLY_JUSTIFIED** · nature **PRIME_PHYSICALLY_JUSTIFIED** · cycle **ACTIVE_EARLY**
- Objectif **z->0.5** · horizon ~47 j

## Signal actif (V124/V179)
- Entrée 2026-08-18 (z 1.185) · 2 j · statut **ACTIVE_EARLY**
- Compression réalisée **-3.45 €/t** · MFE 1.06 · MAE 3.45 · distance z→0.5 : 1.07

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 5.0 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.918 · substitution DATA_BLOCKED
- CBOT_SUPPORT HIGH · ADVERSE_RISK MEDIUM · PHYSICAL_TENSION HIGH
- Météo US UNKNOWN (stale) · Météo EU LOW

## Officiel / proxy & jalons
- Jours officiels **60** · prochain jalon **90** (validation proxy/officiel) · z rolling officiel True
- Validation V178 (40 j) : **PROXY_RESEARCH_ONLY** · paires proxy↔officiel 52
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 60/150', 'V168_MATIF': 'ACCUMULATING 59/150', 'V155_SUMMER': 'TRIGGERED 163/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_INCONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ['prime adossée à une tension physique (backwardation) -> compression plus lente']

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
