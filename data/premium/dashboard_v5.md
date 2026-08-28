# 📊 Dashboard indicateur premium v5 — 2026-08-28
_Généré 2026-08-28 17:37:57 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 89.93 €/t · z 1.083 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · non confirmé (<1.2)** · qualité **BASELINE_SIGNAL** · score composite **1/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **PRIME_PHYSICALLY_JUSTIFIED** · nature **PRIME_PHYSICALLY_JUSTIFIED** · cycle **ACTIVE_EARLY**
- Objectif **z->0.5** · horizon ~47 j

## Signal actif (V124/V179)
- Entrée 2026-08-28 (z 1.083) · 0 j · statut **ACTIVE_EARLY**
- Compression réalisée **0.0 €/t** · MFE 0.0 · MAE 0.0 · distance z→0.5 : 0.583

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 5.75 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.925 · substitution DATA_BLOCKED
- CBOT_SUPPORT HIGH · ADVERSE_RISK HIGH · PHYSICAL_TENSION HIGH
- Météo US UNKNOWN (stale) · Météo EU LOW

## Officiel / proxy & jalons
- Jours officiels **66** · prochain jalon **90** (validation proxy/officiel) · z rolling officiel True
- Validation V178 (40 j) : **PROXY_RESEARCH_ONLY** · paires proxy↔officiel 58
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 66/150', 'V168_MATIF': 'ACCUMULATING 65/150', 'V155_SUMMER': 'TRIGGERED 171/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ['prime adossée à une tension physique (backwardation) -> compression plus lente', "ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer"]

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
