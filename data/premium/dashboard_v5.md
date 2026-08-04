# 📊 Dashboard indicateur premium v5 — 2026-08-04
_Généré 2026-08-04 08:04:51 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 86.85 €/t · z 1.125 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · non confirmé (<1.2)** · qualité **BASELINE_SIGNAL** · score composite **1/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **COMPRESSION_HEALTHY** · nature **PRIME_EXCESSIVE** · cycle **COMPRESSION_HEALTHY**
- Objectif **z->0.5** · horizon ~47 j

## Signal actif (V124/V179)
- Entrée 2026-08-03 (z 1.197) · 1 j · statut **HEALTHY**
- Compression réalisée **0.41 €/t** · MFE 0.41 · MAE 0.0 · distance z→0.5 : 0.625

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 1.75 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.933 · substitution DATA_BLOCKED
- CBOT_SUPPORT HIGH · ADVERSE_RISK HIGH · PHYSICAL_TENSION MEDIUM
- Météo US HIGH · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **48** · prochain jalon **90** (validation proxy/officiel) · z rolling officiel True
- Validation V178 (40 j) : **PROXY_RESEARCH_ONLY** · paires proxy↔officiel 40
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 48/150', 'V168_MATIF': 'ACCUMULATING 47/150', 'V155_SUMMER': 'ACCUMULATING 147/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ["ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer"]

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
