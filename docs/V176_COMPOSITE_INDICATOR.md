# V176 — INDICATEUR COMPOSITE DE LA PRIME EMA/CBOT

_2026-06-11 · RESEARCH_ONLY_NOT_TRADING · baseline z>1 INTOUCHÉE · holdout 2024 exclu_

## Ce que c'est

La synthèse opérationnelle de tout ce que l'étude a démontré : un **score composite règle-basé (aucun
fit)** qui stratifie la QUALITÉ d'un signal baseline au moment où il se déclenche. Ce n'est pas un
nouveau seuil d'entrée — l'entrée candidate reste z>1 — c'est une lecture « ce signal-là a-t-il les
caractéristiques des signaux qui ont historiquement bien fini ? ».

| Composante | Valeur | Découverte source |
|---|---|---|
| `intensity` | 0/1/2 (paliers 1.5/2.0 de la baseline) | V130 (demi-vie rétrécit avec l'extrême), V173 (EXTREME survit à 8 €/t/jambe) |
| `confirmed` | +1 si z ≥ 1.2 | V131 (marginaux z<1.2 : 6.09 vs 14.14 €/t) |
| `cbot_support` | +1 si momentum CBOT 60 j > 0 | V10-E (DA 0.69 uptrend), V39-E4 (ADVERSE ÷2, PnL ×2), V173 |
| `summer` | +1 si juin-août | V167 (pic des départs, compression 1.45z), V173 |
| `subst_risk` | −1 si blé/maïs z > 1 | V36/V41 (corr ratio↔basis +0.59 : substitution = prime justifiée), VNEXT (wheat_corn_z meilleur flag ADVERSE 0.653) |

**SCORE = intensity + confirmed + cbot_support + summer + subst_risk ∈ [−1, 5]**

## Les essais : 8 variantes pré-déclarées, mêmes règles de sortie partout

Simulation V17 inchangée (1 trade à la fois, sortie z→0 max 90 j, stop −20), coût 3 €/t/jambe +
slippage 0.5 (hypothèse primaire V173), 2010→2025 hors holdout. **Chaque variante = un essai compté
dans la déflation.**

| Variante | n | trades/an | mois couverts | hit | net moyen | Sharpe/trade | hors-été : n, net, hit |
|---|---|---|---|---|---|---|---|
| baseline_all_z1 (réf.) | 31 | 2.00 | 9 | 0.61 | +5.25 | 0.27 | 14, +2.91, 0.64 |
| **confirmed_z12 ★** | **25** | **1.62** | **10** | **0.72** | **+7.28** | **0.35** | **11, +5.96, 0.73** |
| support_and_confirmed | 10 | 0.65 | 6 | 0.60 | +5.77 | 0.24 | 5, +1.34, 0.40 |
| score_ge1 | 29 | 1.87 | 9 | 0.62 | +6.11 | 0.31 | 12, +4.27, 0.67 |
| score_ge2 | 23 | 1.49 | 8 | 0.70 | +8.38 | 0.41 | 8, +9.41, 0.63 |
| score_ge3 | 18 | 1.16 | 8 | 0.72 | +10.33 | 0.43 | 6, +14.47, 0.83 |
| score_noseason_ge2 | 20 | 1.29 | 9 | 0.65 | +9.50 | 0.42 | 9, +10.87, 0.67 |
| extreme_only | 11 | 0.71 | 5 | 0.73 | +15.66 | 0.67 | 6, +12.22, 0.67 |

### Lecture des essais

1. **Le score stratifie comme prévu** : net moyen et hit montent de façon monotone avec le seuil de
   score (5.25 → 6.11 → 8.38 → 10.33) — chaque composante validée individuellement contribue dans le
   bon sens une fois combinée. C'est la confirmation croisée du corpus V130/V131/V10-E/V167/V41.
2. **Le dilemme fréquence/qualité est réel** : les variantes les plus rentables par trade (EXTREME,
   score≥3) tombent sous 1.2 signal/an et 5-8 mois de couverture — exactement ce que l'exigence
   year-round interdit de recommander seul.
3. **Réponse à la question « plusieurs fois par an, pas qu'en été »** : la variante recommandée par les
   critères PRÉ-DÉCLARÉS (net>0, hit≥0.55, ≥1.5 trades/an, ≥6 mois, net hors-été>0) est
   **`confirmed_z12`** : ~1.6 signal/an, **10 mois civils couverts sur 12**, hit 0.72, et **hors été :
   11 trades, net +5.96, hit 0.73** — le signal n'est PAS un artefact saisonnier. Le score complet
   sert ensuite de gradient de qualité PAR-DESSUS ce qualificatif (un signal qualifié avec score 4
   a historiquement ~2× le net d'un score 1).

## Honnêteté statistique (pack V172 appliqué)

- **DSR de la variante recommandée** : 0.75 (déflaté par les 8 essais de la famille), **0.57 sous 50
  essais** → **ne survit PAS au seuil 0.95**. Comme pour la baseline (V172 : DSR 0.11), l'edge par
  trade est réel en moyenne mais trop petit/peu fréquent pour être statistiquement irréfutable après
  correction de multiplicité sur 25 trades.
- **PBO (années × 8 variantes) = 0.92 → OVERFIT_LIKELY pour la SÉLECTION ANNUELLE de variante** : avec
  ~1-2 trades/an, la « meilleure variante de l'année » est du bruit. Conséquence opérationnelle :
  **on fige UNE lecture ex-ante** (confirmed_z12 + gradient de score) et on ne change jamais de
  variante en cours de route. C'est exactement ce que le PBO de V172 (0.26 sur la famille de seuils z)
  autorisait : la sélection de SEUIL est robuste, la sélection de VARIANTE fine ne l'est pas.
- Le z reste **proxy_implied** (2010-2025). La revalidation forward officielle est automatique :
  la lecture live tourne chaque jour dans le CI et les jalons V147 (10/40/90 j) s'appliquent.

## Lecture live (quotidienne, CI)

`run_v176_live()` (étape 15septies du daily) combine : basis_z du head (V151), composantes CBOT live
(V107 : uptrend/momentum, corn_cheap_vs_wheat), mois courant. **Aujourd'hui (2026-06-11) : z 1.872 →
score 2/5** (STRONG +1, confirmé +1, été +1, support CBOT 0, malus substitution −1), qualifié
`confirmed_z12`. Artefact : `artefacts/v176/v176_live.json` + bloc dans `reports/daily/latest.json`.
Le head et la machine d'état V139 ne sont pas modifiés : V176 est une couche de stratification.

## Statut et limites

- **INDICATOR_ANALYTIC / RESEARCH_ONLY_NOT_TRADING.** Pas un système de trading ; le mur des coûts
  (V173 : mort à 5 €/t/jambe global) reste la contrainte n°1.
- 25-31 trades en 15 ans : toutes les conclusions sont des stratifications descriptives, pas des
  garanties. Les drapeaux DSR/PBO ci-dessus sont conservés tels quels.
- Composante substitution calculée sur blé CBOT (le MATIF officiel n'a que 8 jours) ; basculera sur
  V126 quand l'historique officiel suffira.
- Tests : `tests/test_v176_composite_indicator.py` (causalité sans futur, paliers baseline respectés,
  monotonie filtres, éligibilité hors-été, fallback live). Artefacts : `artefacts/v176/`.
