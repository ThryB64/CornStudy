# V17 — Indicateur research de prime EMA/CBOT (consolidation)

**Date** : 2026-05-31
**Statut** : `RESEARCH_ONLY_NOT_TRADING`
**Module** : `src/mais/research/v17_research_indicator.py` · runner `run_v17.py` · tests (6 PASS)
**Artefacts** : `artefacts/v17/` (walk_forward_final, trade_fiches[.parquet/_summary], failure_analysis, daily_report.md)
**Données** : hors holdout 2024. Holdout verrouillé, jamais touché.

Consolidation de V13-V16 : **aucun nouveau modèle**. On transforme la règle validée (short basis-haut,
sortie au retour du basis, stop large) en **indicateur research quotidien explicable**, on le valide une
dernière fois proprement, et on documente chaque trade.

---

## V17-01 — Indicateur à paliers

Signal par date, à partir de basis_z, avec warnings (pas de veto dur — leçon V15) :

| Palier | Condition | n (historique) |
|---|---|---:|
| NO_SIGNAL | basis_z < 1 | 5387 |
| SHORT_PREMIUM_MODERATE | 1 ≤ z < 1.5 | 154 |
| SHORT_PREMIUM_STRONG | 1.5 ≤ z < 2 | 110 |
| SHORT_PREMIUM_EXTREME | z ≥ 2 | 92 |
| UNCERTAIN_ROLL / _VOL / _DATA | warning actif | 181 / 16 / 0 |

Chaque signal expose : basis & basis_z, objectif prudent (z→0.5) et complet (z→0), stop indicatif −20,
horizon médian (saison), risque de non-reversion (low/medium/**high si z>2**), contexte CBOT (vs tendance),
coût estimé/leg (dynamique), qualité data.

**Signal live (2025-07-25)** : basis_z **1.703** → palier STRONG, mais **rétrogradé en `UNCERTAIN_ROLL`**
(juillet = mois de roll), coût estimé **7 €/t/leg** (roll + faible liquidité), contexte **below_trend**.
L'indicateur affiche donc honnêtement *signal fort mais conditions défavorables* — il n'incite pas à agir.

## V17-04 — Walk-forward final ultra-propre

Un seul trade ouvert à la fois, entrée z>1, sortie z→0 (max 90j), **stop −20**, **coût dynamique** :

| Métrique | Valeur |
|---|---:|
| n trades | 32 |
| hit rate | **0.656** |
| net PnL (coût dynamique) | **+138 €/t** |
| mean net / trade | +4.3 €/t |
| max drawdown | −39.7 €/t |
| années positives | **9 / 14** |
| verdict | `WALKFORWARD_ROBUST` |

**Lecture honnête** : avec stop −20 + coût dynamique, le hit tombe à **0.656** (vs 0.90 sans stop en V15) —
le stop coupe certains trades qui auraient fini par se compresser. Mais le résultat reste **positif et
robuste** (9/14 années +, net +138). C'est la version la plus conservatrice et crédible à ce jour.

## V17-05 — Fiches des 42 trades + paliers

| Palier | n | win rate | PnL moyen €/t |
|---|---:|---:|---:|
| MODERATE (z 1-1.5) | 29 | 0.79 | 7.3 |
| STRONG (z 1.5-2) | 4 | **1.00** | 14.5 |
| EXTREME (z > 2) | 9 | 0.78 | **29.9** |

Win rate global 0.81. Confirme la structure en paliers : **EXTREME paie le plus** (29.9), STRONG le plus
fiable (n=4), MODERATE modeste. Fiches complètes exportées (`trade_fiches.parquet`).

## V17-06 — Analyse des 8 trades perdants : insights qualitatifs

| Profil des pertes (n=8) | valeur |
|---|---:|
| z d'entrée moyen | 1.62 |
| part en haute volatilité | **0.50** |
| part en mois de roll | 0.375 |
| part en contexte below_trend | **0.875** |
| part stoppées (−20) | **0.50** |

**Découverte cruciale — l'exit prudent z→0.5 aurait sauvé plusieurs pertes.** Plusieurs trades perdants en
sortie z→0+stop auraient été **gagnants en sortie z→0.5** :
- 2010-05-24 : z→0 **−22.8** (stoppé) vs **z→0.5 +23.2**
- 2013-07-16 : z→0 **−1.7** vs **z→0.5 +30.3**
- 2018-06-15 : z→0 **−22.0** (stoppé) vs **z→0.5 +5.1**

Le basis a temporairement empiré (spike) avant de se compresser : le stop −20 ou le plafond 90j a coupé
trop tôt, alors que le retour partiel (z→0.5) était déjà atteint plus tôt.

**Warnings (pas vetoes)** : les pertes se concentrent en **haute volatilité**, **mois de roll**, et surtout
**CBOT sous sa tendance** (87.5% des pertes). Ce ne sont pas des vetoes durs (cf. V15) mais des **drapeaux de
prudence** : en below_trend + haute vol + roll, préférer l'objectif prudent z→0.5 et réduire la taille.

## V17-02 — Rapport quotidien

`generate_daily_report` produit un rapport Markdown clair (prix CBOT/EMA, basis, z-score, signal, objectifs,
stop, horizon, risque, contexte, coût, qualité data, réserve research-only). Exemple : `daily_report.md`.

## V17-03 — Journal forward

Le journal append-only est opérationnel (`scripts/run_premium_journal.py`, V14-03), à brancher en cron pour
accumuler un track record forward.

---

## Synthèse V17

| Élément | Résultat |
|---|---|
| Indicateur à paliers | MODERATE/STRONG/EXTREME + warnings UNCERTAIN, explicable. |
| Signal live (2025-07) | STRONG mais UNCERTAIN_ROLL (honnête : conditions défavorables). |
| Walk-forward (stop+coût dyn) | hit 0.656, net +138, 9/14 ans +, DD −39.7 → ROBUSTE mais sobre. |
| Paliers | EXTREME paie le plus (29.9), STRONG le plus fiable. |
| Insight pertes | **z→0.5 prudent** sauve plusieurs pertes ; prudence en below_trend/vol/roll. |

## Recommandation pour l'indicateur

> **Objectif prudent (z→0.5)** par défaut, surtout pour MODERATE et en contexte défavorable (below_trend,
> haute vol, roll). **Objectif complet (z→0, max 90j, stop −20)** pour STRONG/EXTREME en contexte favorable.
> Afficher toujours le palier, les warnings, le coût estimé et le risque de non-reversion.

## Limites et suite

- 42 trades (32 en strict) → échantillon modeste, forward réel requis.
- exit z→0 optimiste ; stop −20 réduit le hit (tradeoff assumé).
- Prix EMA proxy.
- **Suite V18** (données) : EMA officiel Euronext, courbe multi-échéances, données physiques EU — seul vrai
  levier restant. **V19** : paper trading forward 6-12 mois via le journal. Pas de bot réel.

---

*V17 — 2026-05-31. La règle est devenue un indicateur research explicable, validé sobrement, avec fiches*
*trades et warnings. L'exit prudent z→0.5 ressort comme protection clé. Statut research-only maintenu.*
