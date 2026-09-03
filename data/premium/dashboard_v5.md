# 📊 Dashboard indicateur premium v5 — 2026-09-03
_Généré 2026-09-03 10:02:27 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_STRONG** · basis 97.1 €/t · z 1.925 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **STRONG_SIGNAL** · score composite **2/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **PRIME_PHYSICALLY_JUSTIFIED** · nature **PRIME_PHYSICALLY_JUSTIFIED** · cycle **ACTIVE_EARLY**
- Objectif **z->0.5** · horizon ~51 j

## Signal actif (V124/V179)
- Entrée 2026-09-02 (z 1.28) · 1 j · statut **ACTIVE_EARLY**
- Compression réalisée **-5.38 €/t** · MFE 0.0 · MAE 5.38 · distance z→0.5 : 1.425

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 5.25 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.926 · substitution DATA_BLOCKED
- CBOT_SUPPORT HIGH · ADVERSE_RISK MEDIUM · PHYSICAL_TENSION HIGH
- Météo US MEDIUM · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **70** · prochain jalon **90** (validation proxy/officiel) · z rolling officiel True
- Validation V178 (40 j) : **PROXY_RESEARCH_ONLY** · paires proxy↔officiel 61
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 70/150', 'V168_MATIF': 'ACCUMULATING 69/150', 'V155_SUMMER': 'TRIGGERED 177/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ['prime adossée à une tension physique (backwardation) -> compression plus lente']

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
