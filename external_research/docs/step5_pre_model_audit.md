# Étape 5 — Audit pré-modèle

Date : 2026-06-13. But : vérifier que l'étape 4 est une base saine avant d'empiler
des modèles P2. Aucun modèle n'est lancé tant que cet audit n'est pas conclu.

## 1. Cohérence des conclusions de l'étape 4

**Métriques README ↔ CSV : CONFORMES.** Recalcul direct des lignes `DELTA` de chaque
`metrics_EXTxxx.csv` (script de vérification) :

| EXT | H | ΔRMSE % | ΔDA | DM p | n | README cohérent ? |
|---|---|---|---|---|---|---|
| EXT007 | 20 | +10.75 | +0.061 | 0.177 | 4010 | ✅ |
| EXT007 | 40 | +24.05 | +0.031 | 0.211 | 3997 | ✅ |
| EXT019 | 40 | +1.97 | +0.018 | 0.313 | 3997 | ✅ |
| EXT019 | 90 | +0.33 | +0.044 | 0.892 | 3961 | ✅ |
| EXT001/002/020 | tous | +2 à +116 (pire) | ~0/négatif | — | — | ✅ REJECT |
| EXT008 | tous | pire | négatif | — | 691-750 | ✅ REJECT |
| EXT003 | tous | pire | négatif | — | 1696-1755 | ✅ REJECT |
| EXT004 | tous | pire | ~0/négatif | — | 2198-2257 | ✅ REJECT |

**Verdicts cohérents avec les métriques.** Les deux IMPROVE (EXT007, EXT019) portent un
gain de **direction** (jamais de RMSE), stable sur les deux sous-périodes (vérifié en
étape 4 : EXT007 ΔDA +2.6/+3.9 H5, +5.4/+6.7 H20 ; EXT019 ΔDA +4.2/+4.5 H90). Les REJECT
dégradent le RMSE et/ou la DA de façon nette — exclusion justifiée.

**Les IMPROVE sont-ils assez stables pour la P2 ?** Oui pour un test discipliné, NON pour
un KEEP : DM jamais significatif dans le bon sens, gain modeste (3-6 pts de DA), RMSE pire.
La P2 doit donc viser la **direction** (pas le RMSE) et rester parcimonieuse. Risque
principal = surinterprétation d'un edge de 3-6 pts → contrôle overfitting strict.

## 2. Cohérence des échantillons

Manifeste complet : `results/external_tests/step5_sample_manifest.csv`.

- **Fenêtre d'évaluation** : prédictions 2008→2023, refit annuel expandant, `n_train_min`
  = 750 (~3 ans). Holdout **2024+ exclu partout** (vérifié : le harnais filtre
  `date < 2024-01-01` ET `target_date < 2024-01-01`).
- **EXT007 et EXT019 ont des échantillons IDENTIQUES** (n = 4020/4010/3997/3961 pour
  H5/H20/H40/H90, même cible CBOT, même calendrier marché) → **directement combinables**
  sans biais d'alignement. C'est la base d'EXT024.
- COT (EXT003) : éval 2016+ (n≈1700) — échantillon plus court, ne pas mélanger avec
  EXT007/019 dans un même modèle.
- WASDE surprise (EXT008) : n≈700 par intersection des révisions non-NaN — déjà documenté
  comme limite ; non repris en P2 de toute façon.

## 3. Contrôle anti-fuite (re-vérifié)

| Règle | Statut étape 4 | Reconduite en P2 |
|---|---|---|
| WASDE via vintage EXT026 uniquement | ✅ `wasde_utils.load_vintage()` lit `wasde_vintage_dataset.csv` | oui |
| WASDE dispo = publication+1BD | ✅ `available_from` | oui |
| Crop condition après publication NASS | ✅ Date(dimanche)+2j = mardi | oui |
| Pas de normalisation globale | ✅ standardisation train-only par refit | oui |
| Pas de sélection de variables sur tout le dataset | ✅ (EXT015 imposera la sélection train-only par fenêtre) | oui |
| Rolling windows passées only | ✅ | oui |
| Holdout 2024+ jamais utilisé | ✅ | oui |

Aucun `LEAKAGE_RISK` détecté sur les deux familles reprises. Les encodages stationnaires
de la P2 (z/percentile expandants, classes tight/normal/loose sur seuils expandants)
devront eux aussi être strictement train-only — règle inscrite dans le plan.

## 4. Contrôle des noms d'expériences

- `EXT027` = `crop_progress_condition_surprises` dans la matrice → **réservé, non réutilisé.**
- L'ensemble de stacking s'appellera **`EXT028_model_stacking_ensemble`** (numéro libre,
  absent des matrices).
- Numéros P2 réutilisés depuis `experiment_candidates.csv` (déjà `proposed`) : EXT024,
  EXT015, EXT017, EXT009, EXT010, EXT011, EXT014, EXT016, EXT012. EXT028 = ajout propre.

## 5. Conclusion de l'audit

**Base saine. GO pour la P2 disciplinée.** Pas d'erreur bloquante, pas de fuite détectée,
échantillons cohérents et EXT007/EXT019 combinables. Réserve forte : l'edge est faible
(direction seulement, 3-6 pts de DA) → la P2 doit (1) cibler la direction/risque, pas le
RMSE ; (2) rester parcimonieuse et interprétable ; (3) contrôler l'overfitting (modèles
simples comme référence à battre, stabilité 2 sous-périodes obligatoire pour tout KEEP).
