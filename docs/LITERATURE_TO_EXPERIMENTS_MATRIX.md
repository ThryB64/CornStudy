# Matrice études existantes → expériences → indicateur

**Date** : 2026-05-31. Lien entre familles de littérature, réplication dans le projet, et apport potentiel à
l'indicateur de prime EMA/CBOT. Verdict mis à jour par les runs V18-LIT.

| # | Famille | Idée centrale | Réplication projet | Variable indicateur visée | Données | Verdict (post-run) |
|---|---|---|---|---|---|---|
| 1 | Théorie du stockage | courbe = stocks/portage/convenience | V18-STORE-01 : curve slope, contango/bwd, roll yield | warning « tension réelle vs surprix » | partiel (~332 obs) | voir run |
| 2 | Mean-reversion commodités | OU / retour moyenne | V18-BASIS-01 : AR1, OU half-life, threshold, régime | calibration sortie z→0/0.5/plafond | OK | voir run |
| 3 | Basis trading / convergence | convergence du basis | V13-V15 (déjà) + V18-BASIS-01 | signal short premium | OK | ADD (cœur) |
| 4 | Non-convergence grains | basis ne revient pas toujours | V18-NONCONV-01 (+ V15-02/V17-06) | warnings (crise/roll/vol/extreme) | OK | voir run |
| 5 | Price discovery contrats | volume/front dominent | V18-PD-01 : front vs liquid vs deferred | choix contrat EMA, faux roll | partiel | voir run |
| 6 | Lead-lag CBOT↔EMA | marché dominant mène | déjà V1-V8 (co-intégration, ECM) | « CBOT moteur + prime locale » | OK | KEEP (établi) |
| 7 | Event study USDA/WASDE | surprises déplacent le prix | V18-EVENT-01 : WASDE surprise → basis_change | event risk / contexte | OK | voir run |
| 8 | COT positioning | fonds extrêmes = retournement | V18-COT-01 : percentile, crowding × basis_z | warning crowding / risque short | OK (2900) | voir run |
| 9 | Météo / crop stress | stress rendement = prime physique | V18-WEATHER-01 : GDD/heat/drought × basis | warning « basis justifié » | OK (US) | voir run |
| 10 | Inter-commodités | corn lié soy/wheat/énergie | V18-COMMOD-01 : ratios × basis | contexte global | OK | voir run |
| 11 | Carry / roll yield | carry prédit rendements | V18-STORE-01 (inclus) | contexte | partiel | voir run |
| 12 | Options / IV | skew anticipe risques | V18-OPTIONS-01 | anticipation chocs | absente | DATA_BLOCKED |
| 13 | ML agricole | RF/GBM/LGBM | déjà V3-V13 | — | OK | NO_GO (ne bat pas basis_z) |
| 14 | Séries temps / régimes | ARIMA/GARCH/Markov | déjà ETUDE-11/12, V7 | régime contexte | OK | KEEP |
| 15 | Europe physique | offre/demande EU, Ukraine, TTF | V18-EU (futur) | drivers du basis | absente | WAITING_DATA |

## Pipeline d'intégration (règle stricte)

```
Étude existante
 → réplication (V18-LIT)
 → test OOF strict vs baseline basis_z (delta AUC compression / amélioration loser-avoidance)
 → ADD_TO_INDICATOR    si gain robuste (delta AUC > +0.02 et stable)
 → WATCHLIST           si gain faible (+0.005 à +0.02)
 → KEEP_AS_EXPLANATION si utile pour comprendre mais pas pour prédire
 → NO_GO               si aucun gain
 → DATA_BLOCKED        si données absentes
```

L'indicateur V17 (short basis-haut, sortie z→0/0.5, warnings) **ne change pas** tant qu'une réplication
n'a pas obtenu `ADD_TO_INDICATOR` sur test OOF.
