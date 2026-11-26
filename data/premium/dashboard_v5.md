# 📊 Dashboard indicateur premium v5 — 2026-11-26
_Généré 2026-11-26 15:36:20 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_EXTREME** · basis 108.79 €/t · z 2.035 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **EXTREME_SIGNAL** · score composite **3/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **COMPRESSION_DELAYED** · nature **PRIME_PHYSICALLY_JUSTIFIED** · cycle **COMPRESSION_DELAYED**
- Objectif **z->0.5** · horizon ~51 j

## Signal actif (V124/V179)
- Entrée 2026-11-11 (z 1.05) · 15 j · statut **SLOW**
- Compression réalisée **-11.55 €/t** · MFE 0.0 · MAE 11.55 · distance z→0.5 : 1.535

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 5.0 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.885 · substitution DATA_BLOCKED
- CBOT_SUPPORT LOW · ADVERSE_RISK LOW · PHYSICAL_TENSION HIGH
- Météo US LOW · Météo EU MEDIUM

## Officiel / proxy & jalons
- Jours officiels **130** · prochain jalon **180** (bilan forward) · z rolling officiel True
- Validation V178 (40 j) : **PROXY_RESEARCH_ONLY** · paires proxy↔officiel 61
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 130/150', 'V168_MATIF': 'ACCUMULATING 129/150', 'V155_SUMMER': 'TRIGGERED 261/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ['prime adossée à une tension physique (backwardation) -> compression plus lente']

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
