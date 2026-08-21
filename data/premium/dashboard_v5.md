# 📊 Dashboard indicateur premium v5 — 2026-08-21
_Généré 2026-08-21 06:01:07 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_STRONG** · basis 93.94 €/t · z 1.619 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **STRONG_SIGNAL** · score composite **3/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **PRIME_PHYSICALLY_JUSTIFIED** · nature **PRIME_PHYSICALLY_JUSTIFIED** · cycle **ACTIVE_EARLY**
- Objectif **z->0.5** · horizon ~47 j

## Signal actif (V124/V179)
- Entrée 2026-08-18 (z 1.185) · 3 j · statut **ACTIVE_EARLY**
- Compression réalisée **-4.04 €/t** · MFE 1.06 · MAE 4.04 · distance z→0.5 : 1.119

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 5.0 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.917 · substitution DATA_BLOCKED
- CBOT_SUPPORT HIGH · ADVERSE_RISK MEDIUM · PHYSICAL_TENSION HIGH
- Météo US HIGH · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **61** · prochain jalon **90** (validation proxy/officiel) · z rolling officiel True
- Validation V178 (40 j) : **PROXY_RESEARCH_ONLY** · paires proxy↔officiel 53
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 61/150', 'V168_MATIF': 'ACCUMULATING 60/150', 'V155_SUMMER': 'TRIGGERED 164/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ['prime adossée à une tension physique (backwardation) -> compression plus lente']

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
