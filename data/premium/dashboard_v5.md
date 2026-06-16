# 📊 Dashboard indicateur premium v5 — 2026-06-16
_Généré 2026-06-16 10:28:43 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 63.26 €/t · z 1.048 (proxy_implied)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · non confirmé (<1.2)** · qualité **BASELINE_SIGNAL** · score composite **0/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **COMPRESSION_HEALTHY** · nature **PRIME_EXCESSIVE** · cycle **COMPRESSION_HEALTHY**
- Objectif **z->0.5** · horizon ~23 j

## Signal actif (V124/V179)
- Entrée 2026-05-29 (z 2.056) · 18 j · statut **HEALTHY**
- Compression réalisée **12.89 €/t** · MFE 12.89 · MAE 0.28 · distance z→0.5 : 0.548

## Contexte marché
- Courbe EMA : NARROWING (spread front-next -4.75 €/t, CONTANGO)
- MATIF blé/maïs : 0.983 · substitution DATA_BLOCKED
- CBOT_SUPPORT LOW · ADVERSE_RISK HIGH · PHYSICAL_TENSION LOW
- Météo US MEDIUM · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **13** · prochain jalon **40** (z-score officiel rolling) · z rolling officiel False
- Validation V178 (40 j) : **ACCUMULATING_13_OF_40** · paires proxy↔officiel 5
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 13/150', 'V168_MATIF': 'ACCUMULATING 12/150', 'V155_SUMMER': 'ACCUMULATING 98/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ["ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer"]

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
