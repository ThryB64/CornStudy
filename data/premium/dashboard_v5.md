# 📊 Dashboard indicateur premium v5 — 2026-06-22
_Généré 2026-06-22 11:16:21 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_STRONG** · basis 70.47 €/t · z 1.612 (proxy_implied)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **STRONG_SIGNAL** · score composite **2/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **COMPRESSION_HEALTHY** · nature **PRIME_EXCESSIVE** · cycle **COMPRESSION_HEALTHY**
- Objectif **z->0.5** · horizon ~23 j

## Signal actif (V124/V179)
- Entrée 2026-05-29 (z 2.056) · 24 j · statut **HEALTHY**
- Compression réalisée **5.68 €/t** · MFE 12.89 · MAE 0.28 · distance z→0.5 : 1.112

## Contexte marché
- Courbe EMA : NARROWING (spread front-next -2.75 €/t, CONTANGO)
- MATIF blé/maïs : 0.945 · substitution DATA_BLOCKED
- CBOT_SUPPORT LOW · ADVERSE_RISK MEDIUM · PHYSICAL_TENSION LOW
- Météo US UNKNOWN (stale) · Météo EU MEDIUM

## Officiel / proxy & jalons
- Jours officiels **17** · prochain jalon **40** (z-score officiel rolling) · z rolling officiel False
- Validation V178 (40 j) : **ACCUMULATING_17_OF_40** · paires proxy↔officiel 9
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 17/150', 'V168_MATIF': 'ACCUMULATING 16/150', 'V155_SUMMER': 'ACCUMULATING 104/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_DEGRADED · scope_clean True
- Diagnostics bloqués : ['cot']
- Warnings : ["diagnostics périmés (non frais) : ['cot']"]

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
