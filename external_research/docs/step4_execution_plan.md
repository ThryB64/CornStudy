# Plan d'exécution — Étape 4 (P1 : familles fondamentales)

Date : 2026-06-12. Règles : aucun fichier interne modifié ; expériences sous `external_research/experiments/external_tests/`, résultats sous `external_research/results/external_tests/` ; holdout 2024+ exclu des évaluations.

## Statut data constaté (audit préalable)

| EXT | Famille | Données disponibles | Statut |
|---|---|---|---|
| EXT001 fenêtres agronomiques | météo | `database.parquet` : wx quotidien par 20 États (tmin/tmax/tavg/prcp/gdd/heat/cold) 2000-2025 + parts de production par État | **DATA_READY** |
| EXT002 lags/anomalies | météo | idem ; climatologie expandante à recalculer (les anomalies internes `_anom_z` ne sont pas auditées → non utilisées) | **DATA_READY** |
| EXT020 événements extrêmes | météo | idem | **DATA_READY** |
| EXT007 WASDE release | WASDE | `wasde_vintage_dataset.csv` (EXT026, 207 rapports datés publication) + calendrier USDA | **DATA_READY** |
| EXT008 surprise proxy | WASDE | idem (variations M−M-1 prêtes) — pas d'attentes analystes → terminologie `wasde_revision_proxy` | **DATA_READY** |
| EXT003 COT | positionnement | `cftc_cot.parquet` : Disaggregated MM/PM/SD hebdo **2013-2026**, daté MARDI → décalage publication vendredi+1 jour ouvré à appliquer | **DATA_READY** (éval 2016+) |
| EXT004 crush éthanol | éthanol/énergie | EIA production/stocks éthanol hebdo 2010+ ; oil/gas/rbob/brent ; **pas de prix éthanol ni DDG** | **PARTIAL_DATA** |
| EXT005 courbe futures | courbe | contrats CBOT absents ; EMA front-only 2010-2024, courbe 2025+ seulement | **DATA_BLOCKED** (audit documenté, EXT006) |
| EXT013 basis/transmission | basis | pas de spot UE (FranceAgriMer = productions annuelles) ; EMA↔CBOT faisable en descriptif sans eurusd quotidien... eurusd absent → basis €/t non constructible en externe | **DATA_BLOCKED** (audit + plan d'acquisition) |
| EXT018 prime new-crop | weather premium | contrats décembre CBOT absents → approximation série continue + saisonnalité (limite documentée) + conditionnement stocks/condition | **PARTIAL_DATA** |
| EXT019 crop condition | crop reports | `usda_nass_crop_condition` hebdo **1980-2026** (phases + G/E + P/VP + gap 5 ans) | **DATA_READY** |

## Harnais d'évaluation commun (`ext_harness.py`)

Pour rendre les 9 expériences testables comparables :

- **Cible** : log-retour CBOT t→t+h, horizons H5/H20/H40/H90.
- **Protocole** : walk-forward expandant, refit annuel (2008→2023 ; 2016→2023 pour COT), standardisation et imputation médiane **estimées sur le train uniquement**, Ridge (α=10, fixe ex ante, aucun tuning).
- **Comparaison** : modèle BASE (marché seul : ret_5d, ret_20d, vol_20, saison) vs BASE+FAMILLE — la valeur ajoutée de la famille est la SEULE question. Référence absolue : RW d'EXT025 (prédiction 0).
- **Métriques** : RMSE, MAE, R², DA, balanced accuracy, hit ratio ; deltas famille−base ; DM-test famille vs base (HAC lag h-1) ; stabilité par sous-période (2 moitiés) ; importance = |coef| standardisé moyen des refits.
- **Anti-fuite** : chaque builder applique la date de disponibilité réelle (WASDE `available_from` = publication+1BD ; COT mardi→vendredi+1BD ; crop condition lundi 16h→mardi ; météo réalisée J disponible J+1 ; climatologies expandantes ; pondérations d'État figées sur 2000-2007, hors période d'évaluation).
- Un échec du DM ou un delta DA instable entre les 2 sous-périodes → au mieux IMPROVE, jamais KEEP.

## Ordre d'exécution

1. Harnais commun. 2. Bloc météo EXT001→EXT002→EXT020 (mêmes utilitaires). 3. Bloc WASDE EXT007→EXT008. 4. EXT019. 5. EXT003. 6. EXT004. 7. EXT018. 8. Audits EXT005/EXT013 (DATA_BLOCKED). 9. Synthèse + matrices.

## Critères de verdict

- **KEEP** : ΔDA > +2 pts OU ΔRMSE < −1 % avec DM p<0.10, ET stable sur les 2 sous-périodes, ET économiquement sensé.
- **IMPROVE** : signal partiel (un horizon, une sous-période, p marginal).
- **REJECT** : aucun gain robuste vs base.
- **DATA_BLOCKED / PARTIAL_DATA / NOT_TESTABLE_YET** : selon l'audit ci-dessus.
- **LEAKAGE_RISK** : si un alignement de disponibilité ne peut être garanti.

## Sorties attendues

Par expérience : `features_EXTxxx.csv` (+ dictionnaire), `metrics_EXTxxx.csv`, `comparison_EXTxxx.csv` (périodes), `importance_EXTxxx.csv`, `README_results.md` avec verdict. Synthèse : `step4_results_summary.md` + matrices mises à jour.
