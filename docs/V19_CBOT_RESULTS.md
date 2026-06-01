# V19-CBOT — Pousser le CBOT : risques, interactions, météo (réalisée) + infra forecast

**Date** : 2026-05-31 · **Statut** : `RESEARCH_ONLY_NOT_TRADING`
**Modules** : `src/mais/research/v19_cbot_lab.py`, `src/mais/features/weather_forecast.py`
**Runner** : `run_v19_cbot.py` · tests (7 PASS) · artefacts `artefacts/v19/`
**Plan** : `docs/PLAN_V19_CBOT_WEATHER.md`. Données hors holdout 2024 ; holdout verrouillé.

On a poussé le CBOT comme moteur mondial — pas du « up/down » brut, mais les **risques** (drawdown/rally/
vol), les **interactions** (COT×météo, WASDE×météo) et la **météo** — et on a posé l'**infrastructure météo
prévisionnelle** avec garde anti-leakage (archive réelle = WAITING_DATA).

---

## Découverte 1 — Asymétrie de prédictibilité : baisses ≫ hausses

AUC OOF (logistique, baseline technique de prix seule) :

| Cible de risque CBOT | base rate | AUC (technique) |
|---|---:|---:|
| drawdown 3% h10 | 0.39 | 0.625 |
| drawdown 5% h20 | 0.34 | 0.657 |
| **drawdown 8% h40** | 0.32 | **0.725** |
| rally 3% h10 | 0.43 | 0.586 |
| rally 5% h20 | 0.40 | 0.575 |
| rally 8% h40 | 0.39 | 0.587 |
| vol_spike h10 | 0.18 | 0.616 |
| up_h20 (direction) | 0.52 | 0.529 |

**Le CBOT est un marché « risk-off prévisible »** : les **grandes baisses sont nettement prévisibles**
(0.725 à h40, et d'autant plus que l'horizon est long), alors que les **rallyes ne le sont pas** (~0.58) et
que la **direction brute** est quasi pile/face (0.53). C'est l'extension quantifiée de la trouvaille V8
(`y_down_gt_5pct_h20` était la meilleure cible CBOT). **Implication indicateur** : un module CBOT doit
fournir un **risque de drawdown** (utile, robuste), pas une prédiction de hausse.

## Découverte 2 — La météo (réalisée) améliore la direction CBOT (+0.07) → ADD

Delta AUC en ajoutant chaque famille à la baseline technique :

| Cible | weather | cot | wasde | weather+interactions |
|---|---:|---:|---:|---:|
| **up_h20** | **+0.071 (ADD)** | +0.009 | −0.010 | **+0.057** |
| drawdown 5% h20 | +0.012 (WATCH) | +0.001 | −0.041 | +0.013 |
| drawdown 8% h40 | +0.013 (WATCH) | +0.014 (WATCH) | −0.050 | −0.004 |
| rally 5% h20 | −0.176 | −0.110 | −0.059 | −0.192 |
| vol_spike h10 | −0.109 | −0.039 | −0.029 | −0.111 |

**La météo (stress réalisé : chaleur 38°C, déficit pluie, GDD, sécheresse) améliore la DIRECTION CBOT à
h20 de +0.071** (0.529 → 0.600) — seul `ADD_TO_CBOT_MODEL`. Le stress porte une info **bullish
fondamentale** que les techniques de prix ne captent pas. Elle aide aussi (modestement) le drawdown
(+0.013, WATCHLIST). En revanche elle **détruit** la prédiction de rally (−0.18) : à ne pas y mettre.

> **Motive fortement la météo PRÉVUE** : si le **réalisé** aide déjà +0.07 sur la direction, l'**anticipé**
> (forecasts + révisions, connus à l'avance donc exploitables) pourrait aider davantage. C'est la priorité
> data suivante (V19-WX, WAITING_DATA archive).

## Découverte 3 — COT × météo (short-covering) : `NO_GO` honnête

L'hypothèse « météo bullish × fonds très short → rally (short covering) » **ne se confirme pas** OOF :
rally 5% h20 delta −0.006, rally 8% h40 −0.007, drawdown 5% h20 +0.0003. Plausible économiquement, mais
les données (COT 2900 obs) ne la soutiennent pas. Rejet honnête.

## Découverte 4 — WASDE : pas de valeur OOF (confirme V18-LIT)

Les surprises WASDE dégradent presque toutes les cibles (deltas négatifs). Confirme V18-LIT : les annonces
US déplacent le prix ponctuellement mais n'améliorent pas la prédiction OOF des risques.

## Infrastructure météo prévisionnelle (posée, anti-leakage)

`src/mais/features/weather_forecast.py` :
- Schéma d'archive long : `issue_date | valid_date | lead_time | zone | variable | value | [member]`.
- `assert_forecast_no_leakage` : vérifie `valid = issue + lead`, `lead ≥ 0`, `issue ≤ as_of` (run futur interdit).
- `build_forecast_features` : agrégat pondéré par zone (poids production US/EU), **anomalies** vs normales,
  **révisions** (run du jour − précédent), **incertitude d'ensemble** (dispersion membres), **stress
  phénologique** (pollinisation juin-août).
- 4 tests anti-leakage PASS (dont détection de valid_date incohérent et de run futur).

**Statut** : l'archive réelle (Open-Meteo Historical Forecast / GFS / GEFS) n'est pas collectée →
`WAITING_DATA`. Le code et les tests tournent sur archive synthétique.

---

## Synthèse V19-CBOT

| Question | Réponse |
|---|---|
| Le CBOT est-il prévisible ? | **Oui pour les baisses** (drawdown 8% h40 AUC 0.725), **non pour les hausses/direction**. |
| La météo aide-t-elle le CBOT ? | **Oui, la direction (+0.07)** et le drawdown (+0.013) ; **non les rallyes**. |
| Short-covering (COT×météo) ? | **Non** confirmé OOF. |
| WASDE ? | **Pas de valeur OOF**. |
| Météo prévue ? | Infra + anti-leakage posés ; archive `WAITING_DATA` (priorité). |

## Décisions

- `ADD_TO_CBOT_MODEL` : météo (réalisée) → direction CBOT h20. À intégrer dans un **module contexte CBOT**
  (pas dans l'indicateur basis, qui reste figé).
- `WATCHLIST` : météo → drawdown ; COT → drawdown 8% h40.
- `KEEP_AS_EXPLANATION` : asymétrie drawdown/rally (risk model).
- `NO_GO` : COT×météo short-covering, WASDE, météo→rally.
- `WAITING_DATA` : archive météo prévue (US + EU), courbe CBOT old/new crop.

## Suite

- **V19-WX (WAITING_DATA)** : collecter l'archive de prévisions (Open-Meteo Historical Forecast) → calculer
  anomalies/révisions/incertitude réelles → re-tester sur direction CBOT et drawdown (l'anticipé devrait
  battre le réalisé). Anti-leakage déjà en place.
- **V21-IND** : module **contexte CBOT** (risque de drawdown + biais météo directionnel) affiché à côté du
  signal de prime — **sans** modifier la règle basis (un short premium gagne aussi si le CBOT monte vite).

---

*V19-CBOT — 2026-05-31. Le CBOT prédit ses baisses, pas ses hausses ; la météo réalisée améliore sa*
*direction (+0.07). Infra météo prévue posée (anti-leakage). Research-only, indicateur basis inchangé.*
