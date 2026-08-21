# 📊 Dashboard indicateur premium v5 — 2026-08-21
_Généré 2026-08-21 19:08:52 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 89.75 €/t · z 1.076 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · non confirmé (<1.2)** · qualité **BASELINE_SIGNAL** · score composite **1/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **COMPRESSION_HEALTHY** · nature **PRIME_EXCESSIVE** · cycle **COMPRESSION_HEALTHY**
- Objectif **z->0.5** · horizon ~47 j

## Signal actif (V124/V179)
- Entrée 2026-08-18 (z 1.185) · 3 j · statut **HEALTHY**
- Compression réalisée **0.15 €/t** · MFE 1.06 · MAE 4.04 · distance z→0.5 : 0.576

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 4.75 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.917 · substitution DATA_BLOCKED
- CBOT_SUPPORT HIGH · ADVERSE_RISK HIGH · PHYSICAL_TENSION MEDIUM
- Météo US MEDIUM · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **61** · prochain jalon **90** (validation proxy/officiel) · z rolling officiel True
- Validation V178 (40 j) : **PROXY_RESEARCH_ONLY** · paires proxy↔officiel 53
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 61/150', 'V168_MATIF': 'ACCUMULATING 60/150', 'V155_SUMMER': 'TRIGGERED 164/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_INCONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ["ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer"]

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
