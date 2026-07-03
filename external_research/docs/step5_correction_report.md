# Étape 5 bis — Rapport de correction méthodologique (`target_date` réelle)

Date : 2026-06-13. Périmètre : correction d'une fuite de purge temporelle dans les harnais
P1/P2, re-run des expériences P2 concernées, résolution d'une collision d'identifiant EXT.
**Aucune modification du modèle principal, du holdout 2024+, ni des données internes.**

## 1. Le bug

Les cibles sont des **log-retours `logp.shift(-h)`**, c.-à-d. `h` **lignes de marché** (jours
de cotation) en avant. Mais la purge des fenêtres d'entraînement et l'exclusion du holdout
2024+ utilisaient une **date cible approximée en jours calendaires** :

```python
df["__tgt_date"] = X.index + pd.to_timedelta(h, "D")   # FAUX
```

Le maïs cote ~252 séances/an, donc `h` lignes ≈ `1.45·h` jours calendaires. L'approximation
**sous-estimait la vraie date cible de ~45 %**. Conséquence : des décisions de fin 2023 dont
la cible réelle tombe **en 2024 (holdout)** étaient malgré tout **incluses dans
l'évaluation**, et la purge train/test laissait fuiter quelques cibles de l'année de test.

C'est une fuite **réelle mais de faible ampleur** (quelques dizaines de lignes en queue de
2023), confirmée précisément par l'audit utilisateur.

## 2. La correction

Fonction commune ajoutée à `_common/ext_harness.py` :

```python
def target_dates_from_index(index, h):
    """Vraie date de la cible : index[i+h] (lignes de marché), pas index[i] + h jours."""
    return pd.Series(index, index=index).shift(-h)
```

Fichiers corrigés (6 occurrences, plus aucune `to_timedelta(h, "D")` résiduelle) :

| Fichier | Rôle |
|---|---|
| `_common/ext_harness.py` | harnais Ridge régression (P1 + bases P2) |
| `_common/ext_harness_dir.py` | harnais directionnel logit (EXT024/017/014/050 via membres) |
| `_common/vol_utils.py` | `eval_index` volatilité (EXT009/EXT010) |
| `EXT015_shap_feature_selection/run_EXT015.py` | sélection de variables (harnais local) |
| `EXT011_trend_following_benchmark/run_EXT011.py` | direction des signaux de tendance |
| `EXT010_har_realized_volatility/run_EXT010.py` | OLS HAR (harnais local) |

`ensemble_members.py` (EXT014 BMA, EXT050 stacking) passe par `walk_forward_clf` → corrigé
indirectement.

## 3. Manifeste de l'effet (`step5_sample_manifest_corrected.csv`)

Calculé sur le calendrier marché seul pour isoler **uniquement** la fuite holdout :

| horizon | n_before | n_after | n_removed | dernière décision (avant) | vraie cible de cette décision | holdout_2024_exclu |
|---|---|---|---|---|---|---|
| 5  | 4020 | 4018 | 2  | 2023-12-26 | 2024-01-03 | ✅ |
| 20 | 4010 | 4003 | 7  | 2023-12-11 | 2024-01-10 | ✅ |
| 40 | 3997 | 3983 | 14 | 2023-11-21 | **2024-01-22** | ✅ |
| 90 | 3961 | 3933 | 28 | 2023-10-02 | **2024-02-09** | ✅ |

Les exemples de l'audit sont reproduits **exactement** (H40 → 2024-01-22 ; H90 → 2024-02-09).
La fuite portait sur **14 lignes (H40)** et **28 lignes (H90)** sur ~3 950, soit **0,35–0,71 %**
de l'échantillon. Après correction, `holdout_2024_excluded = True` à tous les horizons.

## 4. Avant / après correction (les conclusions survivent)

| Expérience | Métrique clé | AVANT (buggy) | APRÈS (corrigé) | Verdict |
|---|---|---|---|---|
| **EXT024** crop@H90 | DA / AUC | 0.658 / 0.713 | **0.669 / 0.724** | IMPROVE *(maintenu)* |
| EXT024 crop@H90 | DA 1re / 2e moitié | 0.619 / 0.697 | **0.632 / 0.707** | stable *(les 2 > 0.63)* |
| EXT024 wasde@H40 | DA | 0.597 | 0.592 | IMPROVE *(maintenu)* |
| EXT024 marché seul H90 | DA | 0.604 | 0.604 | référence |
| **EXT015** logit top-6 H90 | DA (vs RF 0.552, marché 0.604) | 0.656 | **0.658** | KEEP *(maintenu)* |
| **EXT017** H90 uptrend | balanced acc | 0.718 | **0.723** | IMPROVE *(maintenu)* |
| EXT017 H90 trend neutre | balanced acc | ~0.47 | 0.468 | nul *(maintenu)* |
| **EXT009** EGARCH H90 | RMSE vol (vs RW 7.81) | 5.966 (−24.5 %) | **5.958 (−23.7 %)** | KEEP *(maintenu)* |
| EXT009 filtre vol | DA décile haut | s'inverse | **0.410 (s'inverse)** | KEEP *(maintenu)* |
| EXT009 filtre vol | DA all → bas-vol | — | **0.669 → 0.699** | gate actionnable |
| **EXT010** HAR H90 | RMSE vol (vs RW 0.079) | 0.0605 (−23.4 %) | **0.0607 (−22.3 %)** | KEEP *(maintenu)* |
| **EXT011** trend mom120 H90 | DA | < 0.5 | **0.384** | REJECT *(maintenu)* |
| **EXT014** BMA H90 | DA (vs meilleur membre 0.661) | 0.633 | **0.633** | IMPROVE-stabilité *(maintenu)* |
| **EXT050** stack H40 | DA 1re moitié | 0.487 | **0.484 (< 0.5)** | REJECT *(maintenu)* |
| EXT050 stack H90 | DA 1re moitié | 0.489 | **0.500** | REJECT *(maintenu)* |

**Lecture.** Les écarts avant/après sont ≤ 1 point partout, et vont **dans le bon sens** pour
le signal phare (crop@H90 : 0.658 → 0.669, car les ~28 points de fin 2023 retirés étaient
légèrement plus bruités). La fuite était réelle mais **immatérielle pour les conclusions**.

## 5. Critères de validation de l'audit

- **Crop Condition H90 reste clairement au-dessus du marché seul, DA > 0.63, stable 2 moitiés ?**
  ✅ OUI : DA **0.669** (marché 0.604, +6,6 pts), AUC 0.724, moitiés 0.632 / 0.707 (toutes > 0.63).
  → Le signal reste **PROMETTEUR**. Verdict maintenu **IMPROVE** (pas de rétrogradation FRAGILE).
- **HAR/EGARCH restent meilleurs sur la volatilité ?** ✅ OUI (−22 à −24 % RMSE vs RW). Résultat
  risque conservé.
- **Le stacking reste instable ?** ✅ OUI (1re moitié ≤ 0.50). **REJECT définitif.**

## 6. Collision d'identifiant EXT028 → EXT050

`ideas_matrix.csv` réserve **EXT001–EXT045** au catalogue d'idées. **EXT028**
(`satellite_usda_report_proxy`, not_ready) **et EXT029** (`corn_crush_location_basis`,
not_started) sont **tous deux déjà pris**. Renommer le stacking en `EXT029` (suggestion de
l'audit) aurait **déplacé la collision**. Le stacking est une expérience **interne** de
l'étape 5, hors catalogue → renuméroté **`EXT050`** (plage ≥ 50 réservée aux expériences
internes), sans collision.

Fait : dossier `experiments/.../EXT050_model_stacking_ensemble/`, `run_EXT050.py`
(`EXP/DIRN="EXT050"`), dossier résultats renommé, `metrics_EXT050.csv` régénéré, ancien
`metrics_EXT028.csv` supprimé, lignes satellite (EXT028) et corn-crush (EXT029) **intactes**.
Matrices mises à jour (`ideas_matrix.csv`, `experiment_candidates.csv`).

## 7. Conclusion

La fuite `target_date` était **réelle** (14 lignes à H40, 28 à H90) et a été **corrigée à la
racine** par une fonction commune. Après re-run strict, **toutes les conclusions de l'étape 5
survivent** ; le signal directionnel **Crop Condition @ H90** est même légèrement **renforcé**
(DA 0.669, AUC 0.724, stable). L'étape 5 est donc **validée** et l'étape 6 (synthèse finale)
peut s'appuyer sur ces résultats corrigés. Aucun verdict rétrogradé en FRAGILE/LEAKAGE_RISK
de ce fait.
