# V11-07 — Design du paper-trading research (sans exécution réelle)

**Statut** : DESIGN seulement. `RESEARCH_ONLY_NOT_TRADING`. Aucun ordre réel, aucun broker connecté.

Objectif : définir un **journal quotidien de recherche** qui enregistre, chaque jour ouvré, ce que
l'indicateur V11 aurait signalé, afin d'accumuler un track record **out-of-sample réel dans le temps**
(le seul vrai test honnête restant, hors holdout 2024). Ce n'est pas du trading : c'est de l'observation
forward enregistrée.

## 1. Ce qu'on enregistre chaque jour

Source du signal : `mais.indicator.structural_indicator_v9.run_indicator_v9` (modèle 2 vars promu V11).

```
date
signal            ∈ {LONG_PREMIUM, SHORT_PREMIUM, ABSTAIN}
confidence        ∈ [0, 1]  (P calibrée Isotonic)
drivers           list[str]
veto_reasons      list[str]
horizon           40
basis_z           valeur du jour
month_cos         valeur du jour
cbot_eur_t        prix CBOT en EUR/t
ema_close         prix EMA (proxy — marqué exploratory)
expected_eval_date  date + 40 jours ouvrés (évaluation différée)
statut            RESEARCH_ONLY_NOT_TRADING
data_source_flag  "barchart_proxy_exploratory"
```

## 2. Évaluation différée (à J+40)

Quand `expected_eval_date` est atteinte, on calcule **a posteriori** :
- `realized_spread_return` = rendement EMA − rendement CBOT sur 40j.
- `correct` = (signal LONG et spread>0) ou (signal SHORT et spread<0).
- `gross_pnl_eur_t`, puis `net_pnl` à coûts {1, 2, 3, 5} €/t/leg.

On agrège un track record glissant : hit rate, DA, net PnL par coût, coverage, drawdown.

## 3. Règles de discipline du journal

1. **Aucune ré-écriture** : une ligne écrite un jour J ne se modifie jamais (append-only, anti-lookahead).
2. **Vetoes respectés** : si DQ/liquidité/WASDE/roll veto → `ABSTAIN` enregistré tel quel.
3. **Pas de re-fit quotidien du modèle** sur des données incluant le futur : le modèle est figé
   (paramètres appris jusqu'à la veille), ré-entraîné au plus une fois par trimestre, daté.
4. **Holdout 2024 jamais utilisé** comme entraînement.
5. **Marquage proxy** : tant que la source EMA est `barchart_proxy_exploratory`, tout le journal porte le
   flag et reste research-only.

## 4. Critères de promotion (futurs, non atteints aujourd'hui)

Le journal ne pourra justifier une étape supérieure que si, sur **≥ 12 mois de track record forward réel** :
- DA des signaux actifs ≥ 0.60,
- net PnL positif à **coût ≥ 3 €/t/leg**,
- calibration maintenue (ECE ≤ 0.10),
- ET source EMA officielle validée (V11-DATA).

Tant que ces critères ne sont pas réunis : aucune exécution réelle, aucun bot.

## 5. Implémentation suggérée (V12)

- Étendre `ops/daily.py` avec un `append_premium_journal()` écrivant une ligne/jour dans
  `data/reports/premium_journal.parquet` (append-only).
- Tâche cron quotidienne (jours ouvrés) après la collecte.
- Fonction `evaluate_matured_journal()` qui calcule le PnL des lignes arrivées à J+40.
- Rapport hebdomadaire `docs`-style du track record.

---

*Design uniquement. Aucune position réelle. Le paper-trading research est l'étape de validation forward la*
*plus honnête, mais il requiert d'abord une source EMA officielle pour sortir du statut exploratoire.*
