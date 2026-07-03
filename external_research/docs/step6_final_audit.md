# Étape 6 — Audit final de cohérence

Date : 2026-06-13. Objet : vérifier la cohérence fichiers / verdicts / anti-fuite / méthode
**avant** toute conclusion forte. Aucune modification du modèle principal ni des résultats
passés (hors corrections documentaires). Périmètre : `external_research/` uniquement.

## 1. Cohérence des fichiers

| Vérification | Résultat |
|---|---|
| Toutes les expériences annoncées existent (run + résultats) | ✅ 26 expériences scopées dans `experiment_candidates.csv` ; 20 dossiers de résultats présents (les 6 manquants sont DATA_BLOCKED/NOT_RUN : EXT005, EXT012, EXT013, EXT016, EXT027, EXT033) |
| Métriques présentes pour chaque expérience exécutée | ✅ `metrics_*.csv` présents (P0/P1/P2) |
| Matrices à jour | ✅ `ideas_matrix.csv`, `experiment_candidates.csv` portent les verdicts P3/P4/P5/P5bis |
| Verdicts matrices ↔ rapports | ✅ cohérents (croisé step3/4/5 + correction) |
| **Collision d'identifiant EXT** | ⚠️→✅ **résolue** : `EXT028` (stacking) entrait en collision avec `EXT028_satellite_usda_report_proxy` ; **et `EXT029` aussi réservé** (`corn_crush_location_basis`). Stacking renommé **`EXT050`** (hors plage catalogue EXT001-045). Dossiers, script, `metrics_EXT050.csv`, matrices, READMEs alignés ; lignes satellite/corn-crush intactes |
| `EXT028`/`EXT029` non confondus avec `EXT050` | ✅ EXT028=satellite (not_ready), EXT029=corn-crush (not_started), EXT050=stacking (REJECT) |

## 2. Cohérence des verdicts

Chaque verdict croisé avec ses métriques réelles et les règles KEEP/IMPROVE/REJECT/
DATA_BLOCKED/LEAKAGE_RISK/NOT_WORTH_YET (`final_experiment_verdicts.csv`). Points de contrôle :

- **Aucun KEEP de prix** : conforme — aucune famille ne bat la RW en RMSE (EXT025), donc
  aucun KEEP sur la cible prix. Les KEEP existants (EXT025 benchmark, EXT026 infra, EXT009/
  EXT010 vol, EXT015 diagnostic) ne sont **pas** des KEEP de prédiction de prix. ✅
- **IMPROVE = direction, modeste, stable, DM non significatif** : EXT007, EXT019, EXT024,
  EXT014, EXT017. Tous étiquetés « direction » avec la réserve DM/IC explicite. ✅ Pas de
  sur-classement en KEEP.
- **REJECT justifiés par dégradation** : météo (EXT001/002/020), surprise WASDE (EXT008),
  COT (EXT003), éthanol (EXT004), trend (EXT011), stacking (EXT050). ✅
- **DATA_BLOCKED réellement bloqués** : EXT005, EXT012, EXT013 (données absentes, non
  simulées). ✅

## 3. Cohérence anti-fuite (`anti_leak_rules.md`)

| Règle | État | Preuve |
|---|---|---|
| 1-2. Pas de split aléatoire ; walk-forward/purged | ✅ | Harnais `ext_harness*`, refit annuel expandant, purge par date cible |
| 3. Feature disponible à la date de décision | ✅ | Familles datées à disponibilité réelle (WASDE+1BD, COT vendredi, crop lundi→mardi, météo J+1) |
| 4-5-8. Lags de publication réels | ✅ | EXT026 vintage publication-only ; COT date vendredi prouvée (3 semaines fériées) |
| 9-10. Pas de normalisation/sélection globale | ✅ | Standardisation/imputation train-only ; EXT015 sélection DANS chaque train |
| 11. Pas de tuning de seuil sur années de test | ✅ | α/C/seuils fixés ex ante |
| 12. **Holdout 2024+ jamais utilisé** | ✅ **corrigé étape 5 bis** | La date cible de purge utilisait des jours calendaires (`index+h j`) au lieu des lignes de marché `index[i+h]` → 14 (H40)/28 (H90) lignes de fin 2023 dont la cible tombait en 2024 entraient dans l'éval. **Corrigé** ; `step5_sample_manifest_corrected.csv` confirme `holdout_2024_excluded=True` partout |
| 7. Fenêtres roulantes passé-only | ✅ | z-scores/percentiles expandants `shift(1)` |
| 6. Météo prévue ≠ réalisée | ✅ | EXT033 (prévu) séparé d'EXT001/002/020 (réalisé) ; EXT033 DATA_GATED |

**Conclusion anti-fuite : la seule fuite identifiée (target_date calendaire) a été corrigée
à la racine et n'a pas changé les conclusions** (cf. `step5_correction_report.md`). Aucune
autre fuite détectée. Holdout 2024+ intact.

## 4. Cohérence méthodologique

- **Pas de surinterprétation** : le signal directionnel est qualifié de **modeste** (DM non
  significatif, IC bootstrap chevauchant le marché seul). Le rapport ne le présente jamais
  comme un edge fort ou un signal de trading autonome. ✅
- **Modèles complexes non gardés sans gain** : RF kitchen-sink, stacking (EXT050), DL
  (EXT016) → REJECT/NOT_WORTH_YET. La parcimonie est le verdict transversal. ✅
- **Signaux faibles non classés KEEP trop vite** : EXT007/EXT019/EXT024 = IMPROVE (pas KEEP),
  car DM non significatif. ✅
- **DATA_BLOCKED maintenus** : pas de simulation artificielle d'un basis/courbe absents. ✅
- **RMSE vs direction distingués** : tous les rapports séparent explicitement la cible prix
  (RMSE, perdue) de la cible direction/vol (modeste/solide). ✅

## 5. Erreurs critiques trouvées

| # | Erreur | Gravité | Traitement |
|---|---|---|---|
| 1 | Fuite holdout via `target_date` calendaire (H40/H90) | Moyenne (0,4-0,7 % des lignes) | **Corrigée** étape 5 bis (6 fichiers) ; re-run ; verdicts inchangés |
| 2 | Collision d'identifiant EXT028 (stacking vs satellite) + EXT029 aussi pris | Faible (documentaire) | **Résolue** : renommé EXT050 |
| 3 | Fuite ~8 j dans la série WASDE quotidienne **interne** (hors périmètre externe) | À traiter côté projet | Documentée (EXT026) ; ticket projet proposé ; n'affecte pas les EXT (qui utilisent le vintage) |

Aucune erreur résiduelle ne justifie de marquer un résultat externe `FRAGILE` ou
`LEAKAGE_RISK` après correction. Les conclusions de l'étape 6 peuvent s'appuyer sur les
résultats corrigés.

## 6. Verdict d'audit

**BASE SAINE.** Fichiers cohérents, verdicts justifiés par les métriques, anti-fuite
respecté (fuite unique corrigée), méthode disciplinée (parcimonie, distinction
prix/direction/vol). La synthèse finale (étape 6) est autorisée sur cette base.
