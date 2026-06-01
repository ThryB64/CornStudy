# Review phase V60→V78 (synthèse critique)

Bilan honnête de la phase. `RESEARCH_ONLY_NOT_TRADING`, baseline figée, holdout verrouillé. Chaque verdict
distingue : **améliore l'indicateur** / **explicatif seulement** / **rejeté** / **data-gated** / **à suivre forward**.

---

## 1. Ce qui AMÉLIORE réellement l'indicateur (GO / ADD)

| Module | Apport | Preuve |
|---|---|---|
| **V56** TARGET_RECOMMENDATION | Objectif z→0.5/z→0 contextuel | −7.2 j d'exposition à PnL égal (`RISK_EFFICIENT`) |
| **V72** survival time-to-reversion | **Horizon probable** : 22 j→z0.5, 42 j→z0 ; HIGH support 29 j | KM par régime, cohérent V56/V57 |
| **V57** magnitude buckets | Classes de compression croissantes avec CBOT_SUPPORT | MFE 18→44 €/t |
| **V64** ADVERSE_RISK v2 | **Couche d'explication** par composant du risque | sépare en binaire, branché daily report |

Ces briques restent des **diagnostics/objectifs**, jamais des vetos ; la règle figée est intacte.

## 2. Ce qui est EXPLICATIF seulement (KEEP_AS_EXPLANATION)

- **V52** ratio MATIF blé/maïs : vraie variable de substitution EU (live 0.914) — explique le NIVEAU du basis,
  pas un timing. Rebranchement dans ADVERSE_RISK différé (historique forward).
- **V54** PHYSICAL_TENSION : score courbe live-usable, validation historique forward.
- **V58** casebook enrichi : 71 % des pertes auraient été flaggées « prudent ».
- **V51** météo extrêmes : queue réelle (+2.4 %/10 j) mais **anticipée** ; persistance > intensité.
- **V73** carte causale : 13 arêtes, statut empirique — cadre les tests futurs.

## 3. Ce qui est REJETÉ (NO_GO — négatifs documentés, précieux)

- **V65** CBOT rebound engine : direction CBOT non prédictible OOF (AUC ≤ 0.537) → **garder CBOT_SUPPORT
  règle-basé**, ne pas modéliser (cohérent V8-META overfit).
- **V64-bis** ADVERSE_RISK v2 comme SCORE : empiler des composants (roll/crise/vol) **dilue** la séparation
  (gap 0.087 < v1 0.189) → garder v1 pour le tier. Leçon anti-overfitting.
- **V60** (du tour précédent) météo US → driver du basis : NEUTRAL, basis plutôt plus bas → **prime locale**.

## 4. Ce qui est BLOQUÉ par la donnée (DATA-GATED — framework prêt)

- **V60-intraday** : intraday CBOT gratuit ~1 mois seulement. Probe : bruit d'alignement close↔settle-time
  ≈ **0.22 % (~0.43 €/t)** — matériel mais modeste. Backtest 2014+ impossible → WATCHLIST forward.
- **V61/V71/V74** : MATIF historique, fondamentaux EU (FranceAgriMer/EC MARS/COMEXT/Ukraine), options/IV.
- Météo EU réalisée ; archive de révisions de prévision (Open-Meteo historical time-out).

## 5. Ce qu'il faut SUIVRE en forward (FORWARD)

- Journaux append-only (GitHub Action) : signal officiel V27, ratio MATIF V52, météo (pic + persistance) V45.
- V75 rapport mensuel ; V76 proxy vs officiel à 40/90 j ; V78 décision après 3–6 mois.
- Révisions de prévision météo (la seule météo *non anticipée*, donc potentiellement tradeable).

## 6. Ce qu'il ne faut PAS utiliser en trading réel

- Aucun module n'est un signal tradeable : statut `RESEARCH_ONLY_NOT_TRADING` maintenu.
- Les bornes « réalisées » (météo, intraday) sont explicatives, pas exploitables a posteriori.
- Pas de veto issu d'un warning ; pas de modèle CBOT direction ; pas d'optimisation sur 42 trades.

## 7. Réponse d'étape à la grande question

> Quand un basis haut est-il anomalie compressible vs prime justifiée ?

État actuel de la réponse opérationnelle (diagnostics, pas vetos) :
- **Anomalie compressible** (objectif complet z→0, horizon ~29–42 j) : **CBOT porteur** (V41/V65-contexte),
  prime forte (z≥1.5), pas de substitution/tension justifiant la prime.
- **Prime justifiée** (objectif prudent z→0.5, ou warning) : CBOT non porteur, prime modérée (z∈[1,1.5)),
  ratio MATIF blé/maïs élevé, tension physique (backwardation), contexte roll/crise.

Le **CBOT porteur** est le discriminant central (compression plus forte, plus complète, plus rapide). La
prime EU est **locale** (ni macro ni météo US). La météo n'aide que via un **avantage de prévision** sur le
CBOT. La suite est surtout une affaire d'**accumulation forward** et de **données EU/officielles**, pas de
nouveaux modèles.
