# V21-IND — Intégration : contexte CBOT + chemin de compression (découverte majeure)

**Date** : 2026-05-31 · **Statut** : `RESEARCH_ONLY_NOT_TRADING`
**Module** : `src/mais/research/v21_indicator_integration.py` · runner `run_v21.py` · tests (5 PASS)
**Artefacts** : `artefacts/v21/compression_path.json`, `integrated_indicator.json`
**Données** : hors holdout 2024 ; holdout verrouillé. Règle basis **inchangée**.

On relie les découvertes CBOT (V19) à l'indicateur de prime (V17) sans modifier la règle, et on répond à la
question clé : **comment** la prime se compresse-t-elle (baisse EMA vs hausse CBOT) ?

---

## Découverte majeure — La compression vient surtout d'une HAUSSE du CBOT, pas d'une baisse de l'EMA

Décomposition du PnL des 39 trades short basis-haut en deux jambes :
`ema_leg = −(rendement EMA)` (positif si EMA baisse) · `cbot_leg = +(rendement CBOT)` (positif si CBOT monte).

| Chemin de compression | n | part |
|---|---:|---:|
| **CBOT_DRIVEN** (CBOT monte) | 14 | **36%** |
| **BOTH** (EMA baisse ET CBOT monte) | 13 | **33%** |
| EMA_DRIVEN (EMA baisse) | 8 | 21% |
| ADVERSE (perte) | 4 | 10% |

- **jambe CBOT moyenne : +0.064** · **jambe EMA moyenne : +0.011** → le CBOT contribue **~6× plus** au gain.
- **~69% des compressions impliquent une hausse du CBOT** (CBOT_DRIVEN + BOTH).

**Reframing profond du signal** : le « short premium » est, en grande partie, un pari que **le CBOT
(sous-évalué relativement à l'Europe) va se redresser** — pas que l'EMA va chuter. Un basis EMA/CBOT élevé
signale souvent un **CBOT temporairement déprimé** vs le prix européen, et c'est le **prix mondial qui
mean-reverte à la hausse**. Économiquement cohérent (l'Europe = marché de prime sur le mondial).

**Conséquences** :
1. Le nom « short premium » est trompeur : c'est surtout du **« long CBOT relatif »**.
2. Relie à V19 : les **rallyes CBOT sont durs à prévoir** (AUC 0.58) → explique une partie de la difficulté
   et du drawdown des trades (la jambe gagnante dépend d'un mouvement CBOT haussier non garanti).
3. Pour l'exécution : garder le **spread** (short EMA / long CBOT) reste prudent (couverture), mais il faut
   assumer que le moteur du gain est majoritairement la **jambe CBOT longue**.

## Indicateur intégré (prime + contexte CBOT)

`compute_integrated_indicator` joint le signal de prime V17 et un **contexte CBOT causal** (observable au
jour J, aucune prédiction → aucun leakage) :

- Labels contexte : `CBOT_UPTREND` (2310 j), `CBOT_NEUTRAL` (1859), `CBOT_BULLISH_WEATHER` (1382),
  `CBOT_RISK_OFF` (389) ; `drawdown_risk` ∈ {low, medium, high} (élevé en below_trend + high vol, cf. V19).
- `compression_path_hint` : si `CBOT_BULLISH_WEATHER` → compression possible **via hausse CBOT** (gain même
  sans baisse EMA) ; si `CBOT_RISK_OFF` → compression possible **via baisse EMA**.

**Snapshot live (2025-07-25)** : premium `UNCERTAIN_ROLL` (z=1.703), contexte `CBOT_NEUTRAL`,
drawdown_risk `medium`, objectifs z→0.5 / z→0. Le contexte est affiché **à côté** du signal, sans le modifier.

## Discipline

- La **règle basis reste figée** (short basis-haut, sortie z→0/0.5, warnings). Le contexte CBOT est une
  **information**, pas un filtre.
- Le contexte est **causal** (pas de modèle prédictif embarqué → pas de leakage).

## Suite

- **Météo prévue** : collecteur `openmeteo_forecast_collector.py` prêt (Forecast + Historical Forecast API,
  format long anti-leakage). Réseau requis → `WAITING_DATA`. Une fois l'archive collectée, brancher
  `weather_forecast.build_forecast_features` et re-tester direction CBOT / drawdown / compression.
- **V22** : paper trading forward via le journal ; comparaison backtest vs forward.

---

*V21-IND — 2026-05-31. Découverte clé : la prime se compresse surtout par HAUSSE du CBOT (jambe CBOT 6× la*
*jambe EMA, 69% via CBOT-up). Le « short premium » est surtout un « long CBOT relatif ». Contexte CBOT*
*intégré sans toucher la règle basis. Research-only.*
