# 📊 Dashboard indicateur premium v5 — 2026-09-24
_Généré 2026-09-24 10:23:15 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 91.42 €/t · z 1.169 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · non confirmé (<1.2)** · qualité **BASELINE_SIGNAL** · score composite **0/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **COMPRESSION_HEALTHY** · nature **PRIME_PHYSICALLY_JUSTIFIED** · cycle **COMPRESSION_HEALTHY**
- Objectif **z->0.5** · horizon ~51 j

## Signal actif (V124/V179)
- Entrée 2026-09-22 (z 1.229) · 2 j · statut **HEALTHY**
- Compression réalisée **0.2 €/t** · MFE 0.2 · MAE 1.78 · distance z→0.5 : 0.669

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 5.5 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.875 · substitution DATA_BLOCKED
- CBOT_SUPPORT HIGH · ADVERSE_RISK HIGH · PHYSICAL_TENSION HIGH
- Météo US LOW · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **85** · prochain jalon **90** (validation proxy/officiel) · z rolling officiel True
- Validation V178 (40 j) : **PROXY_RESEARCH_ONLY** · paires proxy↔officiel 61
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 85/150', 'V168_MATIF': 'ACCUMULATING 84/150', 'V155_SUMMER': 'TRIGGERED 198/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ['prime adossée à une tension physique (backwardation) -> compression plus lente', "ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer"]

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
