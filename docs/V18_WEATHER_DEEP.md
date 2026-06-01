# V18-WEATHER-DEEP — La météo comme « basis justifié par stress » (théorie du stockage)

**Date** : 2026-05-31 · **Statut** : `RESEARCH_ONLY_NOT_TRADING`
**Module** : `src/mais/research/v18_weather_deep.py` · runner `run_v18_weather.py` · tests (3 PASS)
**Artefacts** : `artefacts/v18/weather_deep_trades.json`, `weather_justification.json`
**Données** : hors holdout 2024. Holdout verrouillé.

Approfondissement de la seule famille WATCHLIST de V18-LIT. Hypothèse (théorie du stockage) : un basis
élevé **soutenu par un vrai stress de rendement** (chaleur 38°C, déficit de pluie, sécheresse, mauvaise
condition de culture) reflète une **tension physique durable**, donc **se compresse moins**.

Indice de stress = z-score expandant composite : `heat_38c + rain_deficit + drought − crop_condition`.

---

## Résultat 1 (population) — Le stress réduit fortement la compression : CONFIRME la théorie du stockage

Sur les jours à basis élevé (basis_z>1), taux de compression du basis à H40 :

| Régime météo | taux de compression (basis_change < 0) |
|---|---:|
| **Stress élevé** (z > 0.5) | **0.333** |
| Stress faible (z ≤ 0.5) | **0.682** |

- Corrélation stress × basis_change : **+0.145** (plus de stress → basis monte/reste).

**Découverte mécaniste forte** : un basis élevé en **stress météo se compresse deux fois moins** (33% vs
68%). C'est l'explication économique du gain WATCHLIST (+0.016 AUC) de V18-LIT : **le stress physique
« justifie » la prime** (théorie du stockage / convenience yield) → elle est durable, pas une simple anomalie.

## Résultat 2 (trade) — Pas d'impact exploitable confirmé : `WEATHER_NEUTRAL`

Sur les 42 trades short basis-haut réels (sortie z→0 max90, stop −20) :

| Entrée | n | win rate | PnL moyen €/t | part censurée/stoppée | MAE moyen |
|---|---:|---:|---:|---:|---:|
| Stress élevé | 6 | 0.833 | 11.9 | 0.167 | −11.5 |
| Stress faible | 36 | 0.806 | 13.0 | 0.306 | −9.0 |

Contre l'intuition, les trades en stress élevé **n'ont pas perdu davantage** (win 0.83 vs 0.81). Mais
**n=6 est trop petit** pour conclure, et la **sortie dynamique** (z→0 / max90 / stop) capture des reversions
**partielles** même quand la compression complète n'a pas lieu — ce qui masque l'effet population au niveau
trade.

Verdict : **`WEATHER_NEUTRAL`** au niveau trade.

---

## Décision (discipline maintenue)

- Le signal **population** (33% vs 68% de compression) est **réel et important** : meilleure confirmation
  mécaniste de la théorie du stockage de toute l'étude.
- Mais il **ne se traduit pas (encore) en perte exploitable** au niveau trade (n=6 trop petit).
- **On n'ajoute PAS** de warning dur `UNCERTAIN_WEATHER` dans l'indicateur (ne pas sur-filtrer sur n=6, cf.
  leçon V15). La météo reste un **contexte documenté** (à afficher dans le rapport, sans modifier le signal).
- **WATCHLIST maintenu** : à re-tester avec plus de données (EU MARS, condition de culture EU, plus de trades).

## Implication économique (à intégrer au récit, pas au code)

> La compression d'un basis élevé dépend de **pourquoi** il est élevé. Un basis gonflé par un **stress
> physique réel** (sécheresse, chaleur) est **durable** (compression 33%). Un basis élevé **sans stress**
> est une **anomalie qui se normalise** (compression 68%). C'est exactement la distinction
> contango/surprix vs backwardation/tension de la théorie du stockage — ici via la météo plutôt que la courbe.

## Suite

- `V18-WEATHER` reste **WATCHLIST**. Re-test prioritaire quand : (a) données condition de culture EU / EC MARS
  disponibles, (b) plus de trades à stress élevé (échantillon).
- L'indicateur V17 reste **inchangé** (basis_z + saison + sortie z→0/0.5 + warnings roll/vol/data).
- Le rapport quotidien pourra **afficher** le niveau de stress météo comme contexte (information, pas filtre).

---

*V18-WEATHER-DEEP — 2026-05-31. Le stress météo divise par ~2 le taux de compression d'un basis élevé*
*(33% vs 68%) : confirmation mécaniste de la théorie du stockage. Mais effet trade non confirmé (n=6) →*
*contexte documenté, pas un warning. Discipline maintenue, research-only.*
