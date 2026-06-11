# ÉTUDE MAÏS — RAPPORT MAÎTRE : LA PRIME EMA/CBOT

_Version 1.0 · 2026-06-11 · RESEARCH_ONLY_NOT_TRADING_
_Ce document est la synthèse canonique de l'étude. En cas de divergence avec un document antérieur,
ce rapport et les verdicts canoniques qu'il cite priment. Chaque chiffre renvoie à un artefact._

## 1. Question de recherche

Le prix brut du maïs (CBOT ou Euronext) est difficilement prédictible directement (DA ≈ 0.45-0.56 sur
les benchmarks honnêtes). La question devenue centrale : **la prime du maïs Euronext sur le CBOT
converti en EUR/t (le « basis ») est-elle expliquable, et sa compression est-elle anticipable ?**
Objectif : un indicateur research analytique, explicable et auditable — pas un système de trading.

## 2. Données

| Source | Couverture | Statut |
|---|---|---|
| Settlements officiels Euronext EMA (journal forward sessionisé) | 2026-05-29 → aujourd'hui (10+ j, append-only, REVISED>FINAL>PROVISIONAL) | OFFICIEL |
| Proxy Barchart EMA (historique) | 2010 → 2025-07 | EXPLORATOIRE (interdit en benchmark, PROXY_FORBIDDEN) |
| CBOT corn (+ blé, soja, avoine, énergie, DXY) | 2000 → 2025-07 (master) + live | OK ; conversion EUR/t auditée (err max 0.008 €/t) |
| FX | yfinance + **taux BCE horodaté 14:15 CET** (archive committée) | écart règles ≤ 0.19 €/t (V174) |
| Courbe EMA officielle, ratio MATIF blé/maïs | journaux forward (10 j) | ACCUMULATING |
| Météo previous-runs (révisions lead-fixe, 17 zones US+EU) | 2026-03-11 → aujourd'hui, append quotidien CI | INFRA PRÊTE |
| COMEXT prix unitaires d'import (UA/BR/extra-UE) | 2015 → 2026-02, lag publication 60 j | OK (explicatif) |
| COT CFTC, WASDE, Crop Progress, drought, éthanol | historiques | OK |
| Quote proxy forward du front officiel | depuis 2026-06-10 (1 paire/jour) | ACCUMULATING (V144 à ~40 paires) |

## 3. Construction du basis

`basis = EMA_front − CBOT_front × conversion EUR/t` (39.3679 bu/t, FX du jour ; règle BCE horodatée
recommandée, V174). `basis_z` = z-score 52 semaines. **Le z reste proxy_implied** : l'historique officiel
est court ; les niveaux officiels ont validé les niveaux proxy (basis officiel ≈ 99e percentile proxy à
l'ouverture du journal). Anti-leakage : shift(1) + z expandants partout ; labels sans lookahead testés.

## 4. Baseline (FIGÉE — ne se change pas)

- `basis_z > 1` → SHORT_PREMIUM (signal research) ; 1.5 → STRONG ; 2.0 → EXTREME.
- Objectif prudent z→0.5 ; objectif complet z→0.
- **Niveaux de QUALITÉ autour de la baseline (ils ne la remplacent jamais)** : 1<z<1.2 = BASELINE_SIGNAL
  marginal (V131 : attendre confirmation) ; z≥1.2 = CONFIRMED_SIGNAL ; + score composite V176 (−1..5).
- Sous le seuil : NORMAL < WATCHLIST (0.5) < PRE_SIGNAL (0.75) — surveillance, jamais déclenchement.

## 5. Ce qui est démontré (historique 2010-2025, holdout 2024 exclu)

1. **Cointégration EMA/CBOT** (Johansen rang ≥1 ; EG p=7.3e-7). Demi-vie du déséquilibre **~12-15 j** ;
   part de correction par jambe **régime-dépendante** (52/48 sur 15 ans, EMA dominante en fenêtre
   récente, épisodes CBOT-driven) — verdict unique : `docs/VECM_CANONICAL_VERDICT.md`.
2. **Mean-reversion du basis** : 63 épisodes (event study 2.0), z médian 1.33 → 0.34 à +90 j ; la
   demi-vie rétrécit avec l'extrême (MODERATE 8.3 j / STRONG 4.9 j / EXTREME 3.3 j, V130) ; mais
   l'horizon de trade réalisé est ~28 j (V138 : niveau ≠ trajectoire).
3. **La prime est LOCALE** (triple confirmation) : ni la macro (V16, R² OOF −0.25), ni la parité
   d'import COMEXT (V161, corr 0.089), ne l'expliquent ; la substitution blé/maïs européenne la
   SOUTIENT (corr +0.59, V36/V41) — ratio haut = prime justifiée = compression plus lente/ADVERSE-prone.
4. **Stratification de qualité (V176, 8 variantes pré-déclarées)** : le net moyen par trade monte de
   façon monotone avec le score composite (+5.25 → +10.33 €/t à coût 3+0.5/jambe ; hit 0.61 → 0.72).
   Variante year-round recommandée : `confirmed_z12` (z≥1.2) — 1.62 signal/an, 10 mois civils couverts,
   hors-été net +5.96 (hit 0.73).
5. **Mur des coûts (V173)** : l'edge meurt à ~5 €/t/jambe globalement ; survit à 8 €/t en EXTREME, en
   été (jul-août) et en uptrend CBOT ; meurt à 1-3 €/t en MODERATE / avril-juin / downtrend.
6. **Tension physique** : backwardation forte = prime davantage justifiée, compression plus lente
   (machine d'état : PRIME_PHYSICALLY_JUSTIFIED).

## 6. Robustesse (le signal survit-il à la falsification ?)

| Test | Résultat | Artefact |
|---|---|---|
| Placebos élargis (14 spreads témoins, même moteur) | **Basis EMA rang 1/15** (Sharpe/trade 0.94 vs 0.55 max témoin) → spécifique | v171_extended.json |
| Signal décalé 30 j | Sharpe −0.13 (le timing du z est porteur) | idem |
| Sens inversé | −0.94 (symétrie propre) | idem |
| Entrées aléatoires (500 tirages, même n) | p(random ≥ réel) = **0.000** | idem |
| Deflated Sharpe (50 essais) | **0.11-0.57 : NE survit PAS** — edge réel mais petit | v172, v176 |
| PBO sélection de seuil z | 0.26 ROBUSTE | v172 |
| PBO sélection annuelle de variante composite | 0.92 → INTERDIT (lecture unique figée ex-ante) | v176 |
| SPA / White | p ≈ 0.06-0.07, borderline | v172 |

**Lecture honnête : l'edge est SPÉCIFIQUE et DIRECTIONNEL, sa sélection de seuil est robuste, mais sa
TAILLE ne survit pas à la correction de multiplicité sur ~30 trades.** D'où le statut analytique.

## 7. Ce qui est REJETÉ (ne pas rouvrir sans donnée nouvelle)

Timing ex-ante du départ de compression (3 angles : V153 START AUC OOF **0.515** — canonique de
l'artefact, vs IN_PROGRESS 0.789 qui RECONNAÎT la compression en cours ; V164 HMM triangule le label
mais pas la prédiction ; V175 aucun discriminant d'escalade) · inversion saisonnière V8 (falsifiée OOF) ·
H90 (V10) · filtre régime forward (V11) · fair-value macro (V16) · parité d'import comme ancre (V161) ·
météo RÉALISÉE → CBOT (V45, price-in) · COT seul OOS (VNEXT) · hazard timing (V106) · meta-model V6
(overfit/leakage, V8) · demi-vie analytique = horizon trade (V138).

## 8. Forward officiel (la preuve en cours)

- **Jalon 10 jours officiels ATTEINT** (2026-06-11). Prochain : 40 j (≈ fin juillet) → z officiel
  rolling + modèle de biais proxy↔officiel V144 (quote proxy quotidienne du même contrat depuis 06-10,
  1re paire : 216.5 = 216.5). Puis 90 j (bilan), 6-12 mois (validation).
- Validations forward courbe/MATIF (V141/V142) : gate 40 j, ACCUMULATING.
- Météo : re-test V155 quand l'archive couvre juillet-août (n≥150). Avant ces jalons, AUCUNE conclusion
  forte sur l'officiel.

## 9. L'indicateur final (état au 2026-06-11)

Architecture : journal officiel sessionisé → couches autoritatives (V122 cohérence role-aware, V123
fraîcheur, V124 santé, V132 synthèse) → **head unique** (`premium_daily_head.json`, commité par le CI)
→ machine d'état V139 (+ **qualité V176**) → dashboard v4 / lifecycle / monthly. Audit single_source
7 checks PASS quotidien.

Snapshot live : **SHORT_PREMIUM_STRONG, z 1.872, basis 73.79 €/t (proxy_implied), qualité
STRONG_SIGNAL, score composite 2/5, nature PRIME_PHYSICALLY_JUSTIFIED, cycle COMPRESSION_HEALTHY
(+2.36 €/t réalisés), objectif z→0.5, horizon ~23 j, cohérence LIVE_SIGNAL_CONSISTENT.**

## 10. Limites

z proxy_implied jusqu'à 40+ j officiels · ~30-42 trades historiques (toutes conclusions =
stratifications descriptives) · DSR ne survit pas (taille d'edge) · coûts réels ≥5 €/t tuent l'edge
hors strates fortes · composante substitution sur blé CBOT (MATIF officiel trop court) · attribution
des catalyseurs ex-post · pas de validation trading réel (hors périmètre).

## 11. Suite (ordre)

1. Laisser mûrir le forward (tout est automatique : CI quotidien, jalons, V144, V141/V142).
2. Re-test météo V155 à l'été. 3. Envoi des e-mails d'acquisition (action utilisateur,
`docs/ACQUISITION_PACKAGE.md`). 4. À 40 j officiels : V144 + z officiel rolling + revalidation V176 sur
données officielles. 5. N'ajouter une expérience QUE si elle apporte une information nouvelle (règle de
consolidation du 2026-06-11).
