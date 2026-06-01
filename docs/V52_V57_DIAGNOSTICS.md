# V52 / V54 / V56 / V57 — Diagnostics enrichis de la prime EMA/CBOT

Session 2026-06-01. Quatre incréments disciplinés, **baseline figée inchangée** (short basis-haut), aucun fit
sur les 42 trades, anti-leakage. `RESEARCH_ONLY_NOT_TRADING`. Holdout 2024 jamais touché.

Runner : `venv/bin/python -m mais.scripts.run_v52_v57`. Blocs LIVE branchés dans `generate_daily_report`.

## V56 — Objectif recommandé z→0.5 vs z→0 (la plus concrète)
Formalise V47 en une **règle de recommandation** (contexte, jamais un veto) :

> prudent **z→0.5** si `CBOT_SUPPORT==LOW` **ou** `ADVERSE_RISK==HIGH` **ou** `PHYSICAL_TENSION==HIGH` ;
> complet **z→0** sinon.

Validation à conditions égales (stop −20, max 90 j) sur 42 signaux :

| | reco | toujours z→0 | toujours z→0.5 |
|---|---:|---:|---:|
| PnL moyen €/t | **12.42** | 12.83 | 10.31 |
| jours d'exposition moyens | **35.3** | 42.5 | — |
| profit/jour | 0.781 | 0.593 | 0.813 |

- Sur les **18 signaux notés « complet »** : z→0 gagne vraiment (17.99 vs 13.07 €/t pour z→0.5 ici).
- Sur les **24 signaux notés « prudent »** : z→0 n'ajoute presque rien (8.96 vs 8.24) pour ~17 j de plus.

→ `TARGET_RULE_RISK_EFFICIENT` : la règle capte ~tout le PnL du complet en **économisant 7.2 j**
d'exposition moyenne. Amélioration nette de la DÉCISION sans toucher le signal.

## V57 — Classes de magnitude de compression
On prédit des **classes** (V44 : l'amplitude exacte est imprévisible), via MFE (max favorable excursion)
et atteinte des cibles, sur 42 signaux. Résultat clé : la magnitude **croît monotone avec CBOT_SUPPORT**.

| CBOT_SUPPORT | n | MFE médiane €/t | P(MFE>20) | atteint z→0.5 <40j | atteint z→0 <90j |
|---|---:|---:|---:|---:|---:|
| LOW | 23 | 17.98 | 0.435 | 0.739 | 0.696 |
| MEDIUM | 11 | 27.02 | 0.727 | 0.545 | 0.727 |
| HIGH | 8 | **43.66** | 0.625 | 0.875 | 0.875 |

→ `MAGNITUDE_AS_CLASSES_CONTEXT_DEPENDENT`. La **forte compression se concentre sur CBOT soutenu**,
confirmation indépendante de la logique V56 (objectif complet réservé au CBOT porteur). Global : MFE médiane
22.6 €/t, P(MFE>5)=0.90, atteinte z→0(<90j)=0.74.

## V54 — Score de tension physique (courbe EMA)
Score RÈGLE-BASÉ 0..2 = backwardation + front cher (spread front-second > médiane expandante). HIGH = prime
adossée à une tension physique → compression plus lente, objectif prudent. **Limite honnête** : la courbe
EMA proxy/officielle ne couvre qu'une fenêtre récente (~330 j, contango dominant) qui ne recouvre pas les 42
trades → `PHYSICAL_TENSION_SCORE_BUILT_VALIDATION_WAITING_DATA`. Le score est **utilisable en LIVE** et
alimente V56 ; sa validation historique attend l'accumulation de la courbe officielle.

## V52 — Substitution EUROPÉENNE blé/maïs (ratio MATIF EBM/EMA)
Collecteur officiel **EBM (blé meunier MATIF)** ajouté (`euronext_milling_wheat.py`), même endpoint que l'EMA.
Le ratio MATIF blé/maïs (EUR/t cohérent) est la **bonne** variable de substitution européenne (V36/V40),
là où le ratio CBOT est un proxy local médiocre.

- Live 2026-06-01 : EBM_U2026 207.5 / EMA_Q2026 227.0 → **ratio MATIF = 0.914** (blé EU *moins cher* que
  le maïs EU → ne soutient PAS économiquement une prime maïs haute).
- Ratio CBOT wheat/corn = 1.285, mais en **cents/boisseau** (boisseaux blé≠maïs) : non comparable en tonnes ;
  on comparera les **dynamiques (z-scores)**, pas les niveaux bruts.

**Limite honnête** : l'endpoint officiel n'expose qu'un snapshot du jour → `MATIF_RATIO_LIVE_OK_HISTORICAL_WAITING_DATA`.
Le ratio est **journalisé en forward** (`data/official_forward/matif_ratio_journal.jsonl`, branché dans le
collecteur quotidien / GitHub Action). Dès couverture suffisante, le rebrancher dans **ADVERSE_RISK v2 (V55)**
et comparer son pouvoir explicatif au ratio CBOT.

## Synthèse
La thèse se renforce et se cohérencifie : le **CBOT porteur** est le facteur pivot — il prédit à la fois une
compression plus FORTE (V57), plus COMPLÈTE/rapide (atteinte z→0), et justifie l'objectif **complet** (V56).
À l'inverse, CBOT faible / prime modérée / tension physique → objectif **prudent**. La substitution se mesure
désormais avec la vraie variable européenne (MATIF, V52), en attente d'historique. Aucune de ces briques n'est
un veto : ce sont des diagnostics de CONTEXTE autour d'un signal figé.

Tests : `test_v52` (3), `test_v54` (3), `test_v56` (3), `test_v57` (2) — tous PASS. Ruff clean.
