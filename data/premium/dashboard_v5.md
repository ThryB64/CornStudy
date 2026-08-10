# 📊 Dashboard indicateur premium v5 — 2026-08-10
_Généré 2026-08-10 06:54:13 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 89.93 €/t · z 1.363 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **CONFIRMED_SIGNAL** · score composite **2/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **PRIME_EXCESSIVE** · nature **PRIME_EXCESSIVE** · cycle **ACTIVE_EARLY**
- Objectif **z->0.5** · horizon ~47 j

## Signal actif (V124/V179)
- Entrée 2026-08-03 (z 1.197) · 7 j · statut **ACTIVE_EARLY**
- Compression réalisée **-2.67 €/t** · MFE 0.41 · MAE 6.02 · distance z→0.5 : 0.863

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 2.25 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.934 · substitution DATA_BLOCKED
- CBOT_SUPPORT HIGH · ADVERSE_RISK HIGH · PHYSICAL_TENSION MEDIUM
- Météo US HIGH · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **52** · prochain jalon **90** (validation proxy/officiel) · z rolling officiel True
- Validation V178 (40 j) : **PROXY_RESEARCH_ONLY** · paires proxy↔officiel 44
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 52/150', 'V168_MATIF': 'ACCUMULATING 51/150', 'V155_SUMMER': 'TRIGGERED 153/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ["ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer"]

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
