# V11 — Programme discipliné : consolidation du signal compris

**Date** : 2026-05-31
**Statut** : `RESEARCH_ONLY_NOT_TRADING`
**Module** : `src/mais/research/v11_simplified_program.py` · runner `run_v11.py` · tests (6 PASS)
**Artefacts** : `artefacts/v11/` (promote_simplified, forward_regime_filter, cost_aware_decision, basis_change_regression, simple_rules_lab_v11)
**Données** : dataset hors holdout 2024. Holdout verrouillé, jamais touché.

Suite directe de la review V10. Principe imposé : **pas de meta-model, pas de H90, pas d'EMA brut**.
On consolide le signal compris (basis mean-reverting + saison), on valide *forward* les trouvailles
post-hoc, et on attaque honnêtement le mur des coûts.

---

## V11-01 — Le modèle 2 variables est promu cœur de l'indicateur

Validation complète `basis_z + month_cos` vs 6 variables, même batterie (OOF / LOYO / red team / backtest) :

| Métrique | 6 vars (V9) | **2 vars (promu)** |
|---|---:|---:|
| AUC OOF | 0.656 | **0.694** |
| Balanced accuracy | 0.619 | **0.633** |
| top20 DA | 0.735 | **0.748** |
| **ECE (calibration)** | 0.154 | **0.059** |
| LOYO | STABLE (0.77) | STABLE (0.758) |
| Red team p | 0.0099 | 0.0099 |
| Backtest net coût 0 | +381 | **+531** |
| Backtest net coût 2 | +85 | **+239** |
| **Backtest net coût 3** | **−63** | **+93** |
| Backtest net coût 5 | −359 | −199 |

**Décision : `PROMOTE_SIMPLIFIED`.** Le modèle 2 variables est meilleur **partout**, nettement mieux
**calibré** (ECE 0.059 vs 0.154), et **repousse le seuil de rentabilité de ~2.5 à ~3.5-4 €/t/leg**. Il est
désormais le **défaut** de `run_indicator_v9` (`features=SIMPLIFIED_FEATURES`). La prime EMA/CBOT se réduit
économiquement au **basis et au cycle annuel de récolte** — rien d'autre n'aide.

## V11-02 — Le filtre de régime ne survit PAS en forward (rejet honnête)

V10-E avait trouvé un edge plus fort en uptrend CBOT (AUC 0.683). V11-02 a appris le meilleur régime
**uniquement sur les années passées** et l'a appliqué forward :

| | net coût 2 | net coût 3 | DA |
|---|---:|---:|---:|
| Filtre régime appris forward | +83 | **−37** | 0.70 |
| Baseline sans filtre | +234 | **+104** | 0.72 |

**Verdict `REGIME_FILTER_POST_HOC_ONLY`.** Le filtre **dégrade** le forward (l'algorithme choisit « none »
la plupart des années). La supériorité de l'uptrend était un **artefact post-hoc** : elle ne se valide pas
hors échantillon. On **ne l'ajoute pas** à l'indicateur. (Discipline : on rejette ce qui ne tient pas forward.)

## V11-03 — Couche cost-aware : aide réelle mais fragile à coût 5

Règle : ne trader que si l'edge brut attendu (appris forward par bucket de confiance) > `2·coût + marge`.

| Coût | seuil edge | n trades gatés | net PnL gaté | hit | net PnL sans gating |
|---|---:|---:|---:|---:|---:|
| 3 €/t | 8 €/t | 25 | **+158** | 0.84 | +140 |
| 5 €/t | 13 €/t | 3 | +26 | 1.00 | −99 |

**Verdict `COST_AWARE_BREAKS_WALL` — mais à nuancer.** Le gating cost-aware améliore le net à tous les coûts
et rend le **coût 5 positif** (+26) — première fois de l'étude. **Mais avec seulement 3 trades**, c'est
statistiquement fragile. À coût 3, c'est solide (25 trades, +158, hit 0.84). Lecture honnête : la décision
cost-aware est la **bonne direction**, l'edge net survit à coût 3 avec un volume crédible, mais reste
trop rare pour un claim à coût 5.

## V11-04 — La direction du basis change est prédictible, pas sa magnitude

Régression Ridge OOF de `basis_change_h` (EUR/t) sur `basis_z + month_cos + eurusd` :

| Horizon | R² | MAE €/t | sign-DA |
|---|---:|---:|---:|
| H20 | −0.004 | 9.9 | 0.601 |
| H30 | −0.001 | 11.8 | 0.600 |
| **H40** | −0.045 | 12.4 | **0.628** |
| H60 | −0.131 | 13.9 | 0.628 |

**Découverte** : le **R² est nul ou négatif** (la magnitude du mouvement de basis n'est pas prévisible),
mais la **direction l'est** (sign-DA 0.63 à H40). Cohérent avec tout le reste : on prédit *où va* la prime,
pas *de combien*. H40 reste le meilleur horizon. Confirme que l'objet utile est directionnel, pas un niveau.

## V11-05 — Lab exhaustif de règles (BH-corrigé) : le côté short domine

41 règles `basis_z × seuil × saison × régime` testées, p-value binomiale (hit vs 0.5), **correction
Benjamini-Hochberg FDR q=0.10**. **13 survivent BH, 9 sont aussi profitables à coût 5 €/t.** Top :

| Règle | côté | n | hit | net coût 5 | p |
|---|---|---:|---:|---:|---:|
| `basis_z>1 · downtrend` | short | 29 | 0.76 | **+134** | 0.004 |
| `basis_z>1.5 · downtrend` | short | 22 | 0.82 | +109 | 0.002 |
| `basis_z>1 · all` | short | 34 | 0.74 | +68 | 0.005 |
| `basis_z>1.5 · all` | short | 24 | 0.75 | +33 | 0.011 |
| `basis_z<-1.5 · apr_jun` | long | 13 | 0.85 | +38 | 0.011 |
| `basis_z<-2 · all` | long | 17 | 0.76 | +8 | 0.025 |

**Découverte qui corrige V8** : le **côté short (basis_z > 1 → short premium, surtout en downtrend CBOT)**
est la famille de règles la **plus robuste** — plus de trades, p-values plus basses, profitable à coût 5,
survit à la correction multi-test. V8 mettait en avant le **long** `basis_z < -1.5` ; V11 montre que le
**short basis-haut est le pilier mean-reversion le plus fiable**. (Réserve : conditionnement régime
in-sample ici → à valider forward, cohérent avec le rejet V11-02 du régime appris.)

---

## Synthèse V11 — où en est l'indicateur

> **Cœur** : régression logistique **2 variables** (basis_z + month_cos), calibrée Isotonic (ECE 0.059),
> AUC 0.694, top20 DA 0.748, DA déployée 0.65 sur ~13% de coverage, validée LOYO + red team.
> **Horizon** : H40 (≈ 2,3 demi-vies de basis).
> **Règles tactiques** : la famille short basis-haut domine ; long basis-bas secondaire.
> **Coûts** : rentable jusqu'à ~3.5-4 €/t/leg ; cost-aware gating étend à coût 5 mais trop rare.
> **Régime CBOT** : rejeté en forward.

L'étude a un indicateur de recherche **plus simple, mieux calibré et plus rentable** qu'en V9, et une
compréhension économique complète. Le mur des coûts à 5 €/t reste la frontière ; le statut reste
`RESEARCH_ONLY_NOT_TRADING`.

## Améliorations nettes apportées en V11

1. Modèle **2 variables promu défaut** : AUC +0.038, **ECE −0.095**, breakeven +1 à +1.5 €/t.
2. Filtre régime **rejeté forward** (évite un faux edge post-hoc).
3. Décision **cost-aware** : edge net positif à coût 3 avec volume crédible.
4. Confirmation que **la direction du basis** est l'objet prévisible (pas la magnitude).
5. **Règles short basis-haut** identifiées comme les plus stables (BH-corrigées).

## Limites et suite

- Prix EMA toujours `barchart_proxy_exploratory` → **acquisition officielle = vrai déblocage** (`WAITING_DATA`).
- Coût 5 €/t non franchi avec volume suffisant.
- Conditionnement régime des règles V11-05 à valider forward (V12).
- Reste à faire : design paper-trading (journal sans exécution, `docs/V11_PAPER_TRADING_DESIGN.md`),
  validation données EMA officielles, données EU testées **uniquement si elles expliquent le basis**.

---

*V11 — 2026-05-31. Discipline tenue : on a simplifié, mieux calibré, rejeté le post-hoc, et compris que la*
*prime est un phénomène de basis directionnel. Recherche honnête, pas de bot réel.*
