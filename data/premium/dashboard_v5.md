# 📊 Dashboard indicateur premium v5 — 2026-08-07
_Généré 2026-08-07 06:49:06 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 88.02 €/t · z 1.158 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · non confirmé (<1.2)** · qualité **BASELINE_SIGNAL** · score composite **1/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **PRIME_EXCESSIVE** · nature **PRIME_EXCESSIVE** · cycle **ACTIVE_EARLY**
- Objectif **z->0.5** · horizon ~47 j

## Signal actif (V124/V179)
- Entrée 2026-08-03 (z 1.197) · 4 j · statut **ACTIVE_EARLY**
- Compression réalisée **-0.76 €/t** · MFE 0.41 · MAE 6.02 · distance z→0.5 : 0.658

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 2.0 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.926 · substitution DATA_BLOCKED
- CBOT_SUPPORT HIGH · ADVERSE_RISK HIGH · PHYSICAL_TENSION MEDIUM
- Météo US MEDIUM · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **51** · prochain jalon **90** (validation proxy/officiel) · z rolling officiel True
- Validation V178 (40 j) : **PROXY_RESEARCH_ONLY** · paires proxy↔officiel 43
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 51/150', 'V168_MATIF': 'ACCUMULATING 50/150', 'V155_SUMMER': 'TRIGGERED 150/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ["ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer"]

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
