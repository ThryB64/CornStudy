# V15 — Réalisme de l'indicateur short basis-haut

**Date** : 2026-05-31
**Statut** : `RESEARCH_ONLY_NOT_TRADING`
**Module** : `src/mais/research/v15_short_realism.py` · runner `run_v15.py` · tests (5 PASS)
**Artefacts** : `artefacts/v15/` (season_aware_exits, censored_archaeology, drawdown_study, partial_exits, position_sizing, dynamic_cost, strict_portfolio)
**Données** : hors holdout 2024. Holdout verrouillé, jamais touché.

Suite V14, ciblée et disciplinée : on n'ajoute aucun modèle, on rend la règle short basis-haut
(`basis_z > 1`, validée robuste hors crise en V13) plus **réaliste, saison-aware et moins optimiste**.
Plusieurs résultats sont des « ça n'aide pas » — c'est la discipline assumée.

---

## V15-01 — Sortie saison-aware : n'améliore pas le z→0 uniforme

| Sortie | hit | mean PnL €/t | net coût 3 | profit/jour | détention méd. |
|---|---:|---:|---:|---:|---:|
| H40 | 0.79 | 10.5 | +188 | 0.376 | 28 |
| z→0.5 | 0.88 | 12.6 | +278 | **0.384** | 33 |
| **z→0** | 0.86 | **15.9** | **+417** | 0.268 | 59 |
| z→0 max90 | 0.86 | 14.6 | +361 | 0.322 | 45 |
| season_aware | 0.79 | 13.6 | +319 | 0.299 | 46 |

**Résultat honnête** : la sortie **saison-aware ne bat pas** le simple **z→0** (+319 vs +417 net coût 3).
Les deux sorties uniformes dominent : **z→0 pour le PnL total**, **z→0.5 pour l'efficacité capital**
(profit/jour 0.384, détention 33j). On garde simple : pas de plafond saisonnier.

## V15-02 — Archéologie des trades censurés : pas de veto dur

9 trades sur 42 ne reviennent pas à 0 en 120j. Profil des échecs vs réussites :

| | censurés (n=9) | réussites (n=33) |
|---|---:|---:|
| z d'entrée moyen | **1.83** | 1.57 |
| part z > 2 | **0.33** | 0.18 |
| part en crise | 0.33 | 0.27 |
| part mois de roll | 0.22 | 0.39 |

**Découverte** : les échecs ont un **z d'entrée plus extrême** (deux fois plus souvent z>2) et un peu plus
de crise — mais l'écart **n'est pas assez net pour un veto dur**. Verdict : **ne pas sur-filtrer**. Nuance
importante reliée à V15-05 : z>2 paie gros quand il revient, mais revient moins souvent (risque asymétrique).

## V15-03 — Drawdown avant reversion : stop rationnel ≈ −20/−25 €/t

MAE (max adverse excursion) avant sortie z→0 max90 : **p50 −9.1, p75 −14.3, p90 −19.7, p95 −23.3,
pire −29.4 €/t**.

| Stop-loss | hit | net coût 5 €/t |
|---|---:|---:|
| −10 | 0.50 | **−287** (détruit) |
| −15 | 0.71 | −49 |
| **−20** | 0.81 | **+119** |
| −25 | 0.83 | +153 |

**Découverte** : un stop serré (−10) **détruit l'edge** (le bruit déclenche le stop, le trade a besoin de
respirer). Le **stop rationnel est ≈ −20/−25 €/t** (niveau p90-p95 du MAE), qui préserve l'edge à coût 5.
Confirme et quantifie V13.

## V15-04 — Sorties partielles : pas de gain clair

| Stratégie | hit | net coût 3 | profit/jour | MAE moyen |
|---|---:|---:|---:|---:|
| full z→0.5 | 0.88 | +278 | **0.384** | −8.6 |
| full z→0 max90 | 0.86 | +361 | 0.322 | −9.6 |
| partielle 50% z→0.5 + 50% z→0 max90 | 0.88 | +295 | 0.287 | −9.6 |
| partielle + SL −20 | 0.83 | +234 | 0.273 | −9.4 |

**Résultat honnête** : la sortie partielle **n'améliore ni le profit/jour ni le MAE** par rapport aux
sorties pures. z→0.5 reste le meilleur en efficacité, z→0 en total. On n'ajoute pas cette complexité.

## V15-05 — Position sizing : l'edge est concentré sur les anomalies extrêmes

| Bucket basis_z d'entrée | n | hit | mean PnL €/t | net coût 5 |
|---|---:|---:|---:|---:|
| 1 – 1.5 | 29 | 0.86 | 9.9 | **−4** |
| 1.5 – 2 | 4 | — | — | — |
| **> 2** | 9 | 0.78 | **29.9** | **+179** |

**Découverte majeure** : le **PnL est très concentré sur les entrées z > 2** (29.9 €/t/trade contre 9.9
pour z 1-1.5, qui est à peine rentable à coût 5). L'essentiel de la profitabilité de la règle vient des
**anomalies de prime extrêmes**. Combiné à V15-02 (z>2 plus souvent censuré), le profil est : **z>2 = haut
rendement + risque de non-reversion plus élevé** → justifie un plafond de détention long et un stop ~−20.

## V15-06 — Coût dynamique : la règle survit

Coût par leg = 1 €/t + 2 si OI faible + 2 si vol haute + 2 si mois de roll.
- Net PnL **coût dynamique : +309 €/t** (vs +361 à coût plat 3). **survives_dynamic_cost = True**.

**Découverte** : l'edge **survit à un modèle de coût réaliste** (plus cher en liquidité faible / vol haute /
roll). Plus crédible qu'un coût plat. Réserve : approximation, pas de bid-ask réel.

## V15-07 — Portfolio strict un-trade-à-la-fois : le track réaliste tient

| Comptage | n trades | hit | net coût 5 €/t | max DD coût 3 |
|---|---:|---:|---:|---:|
| **strict (1 trade ouvert)** | 29 | **0.90** | **+116** | −27 |
| non-overlap 40j | 42 | 0.86 | +193 | — |
| events indépendants | 541 | 0.86 | +3732 (surestimé) | — |

**Découverte** : le portfolio **strict un-trade-à-la-fois** (le plus réaliste) donne **29 trades, hit 0.90,
+116 €/t net coût 5, max drawdown −27**. Il reste solidement positif. Les « 541 events indépendants »
**surestiment massivement** le nombre de trades exploitables — à ne jamais utiliser pour un track record.

---

## Synthèse V15

| Question | Réponse |
|---|---|
| Sortie saison-aware utile ? | **Non** — z→0 (PnL) / z→0.5 (efficacité) restent meilleurs. |
| Veto sur les échecs ? | **Pas de veto dur** — z>2 un peu plus risqué, mais ne pas sur-filtrer. |
| Stop rationnel ? | **≈ −20/−25 €/t** (p90-p95 MAE). −10 détruit. |
| Sortie partielle utile ? | **Non** — pas de gain clair. |
| Où est l'edge ? | **Concentré sur z > 2** (29.9 vs 9.9 €/t/trade). |
| Survit aux coûts réalistes ? | **Oui** (+309 net coût dynamique). |
| Track réaliste (1 trade à la fois) ? | **+116 net coût 5, hit 0.90, n=29, DD −27**. |

## Profil de risque consolidé de la règle short basis-haut

> Entrée `basis_z > 1` (idéalement renforcée sur z > 2 où l'edge se concentre), sortie au retour du basis
> (z→0, plafond 90j), stop −20/−25 €/t. En portfolio strict : ~29 trades sur ~17 ans, hit 0.90, +116 €/t
> net de coût 5, drawdown max −27 €/t. Survit aux coûts dynamiques. **Rare mais robuste.**

## Limites et suite V16

- Données EMA proxy → acquisition officielle = déblocage n°1.
- Edge concentré sur z>2 → peu de trades extrêmes (n=9) → fragile, forward requis.
- exit z→0 optimiste, `basis_z` issu du proxy.
- **V16** (explication économique du basis) : fair value du basis (`basis_mispricing = basis − basis_fair`),
  structure de courbe EMA (contango/backwardation → tension durable vs surprix compressible), données
  EU/Ukraine/énergie **uniquement si elles expliquent le basis et sa reversion**.

---

*V15 — 2026-05-31. On a rendu la règle réaliste : stop −20, edge concentré sur z>2, survit au coût*
*dynamique et au portfolio strict. Plusieurs raffinements rejetés honnêtement (saison-aware, partiel).*
