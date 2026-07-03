# Résumé des résultats — Étape 5 (P2 : modèles avancés disciplinés)

Date : 2026-06-13. Périmètre : 10 expériences P2. Modèle principal, scripts et données
internes **non touchés**. Tout sous `external_research/experiments/external_tests/` et
`external_research/results/external_tests/`. Harnais : `_common/{ext_harness_dir, features_p2,
vol_utils, ensemble_members}.py`. Holdout 2024+ exclu partout.

> **MISE À JOUR — Étape 5 bis (2026-06-13).** Une fuite de purge a été corrigée : la date
> cible servant à exclure le holdout était approximée en **jours calendaires** (`index + h j`)
> au lieu de la vraie **ligne de marché** `index[i+h]`. Effet : 14 lignes (H40) / 28 lignes
> (H90) de fin 2023 dont la cible tombait en 2024 étaient incluses (0,4–0,7 % de
> l'échantillon). **Toutes les expériences P2 ont été re-runnées ; tous les verdicts ci-dessous
> survivent** (crop@H90 même renforcé : DA 0.658→0.669, AUC 0.713→0.724). Détail :
> `step5_correction_report.md` ; manifeste : `step5_sample_manifest_corrected.csv`. Les
> chiffres « avant » de ce résumé restent lisibles tels quels (écarts ≤ 1 pt). Le stacking
> `EXT028` a été renommé **`EXT050`** (collision : EXT028 ET EXT029 réservés au catalogue).

## 0. Question de l'étape

Les deux signaux faibles mais stables de l'étape 4 (WASDE état de bilan, Crop Condition)
peuvent-ils devenir un **indicateur robuste de direction / de risque / de score de vente à
H40-H90** ? (Pas un modèle de prix.)

**Réponse courte : OUI pour un score de DIRECTION/RISQUE, NON pour le prix.** En cadrage
**classification directionnelle**, les fondamentaux d'offre (surtout Crop Condition à H90)
améliorent nettement et de façon stable la prévision de direction ; et la **volatilité se
prévoit bien** (HAR/EGARCH), ce qui fournit un gate de risque actionnable. En revanche le
RMSE de prix reste imbattable (RW), la complexité (stacking, DL) sur-apprend, et le
trend-following échoue.

## 1. Résumé général

- **Lancées : 9 ; terminées : 8 ; bloquée : 1 (EXT012) ; reportée : 1 (EXT016 NOT_WORTH_YET).**
- **Meilleurs modèles** : EXT024 (supply-demand directionnel, crop@H90), EXT010 (HAR vol),
  EXT009 (EGARCH + filtre de vol). EXT015 valide les variables (KEEP diagnostic).
- **Modèles trop complexes / rejetés** : EXT050 (ex-EXT028) stacking (sur-apprend), EXT011
  trend-following (échoue), EXT016 NBEATSx (non justifié).

## 2. Audit préalable (`step5_pre_model_audit.md`)

Base saine : métriques étape 4 ↔ CSV conformes, verdicts cohérents, échantillons cohérents,
**EXT007 et EXT019 ont des échantillons identiques** (combinables). Holdout 2024+ exclu
partout, aucune fuite détectée. Réserve : edge faible (3-6 pts DA) → P2 disciplinée
(direction/risque, parcimonie, stabilité 2 sous-périodes obligatoire). Manifeste :
`results/external_tests/step5_sample_manifest.csv`.

## 3. Résultats par expérience

### EXT024 — supply-demand directionnel — **IMPROVE (fort)**
En classification, le marché seul a une skill directionnelle mais **instable** ; ajouter les
fondamentaux la **renforce et la stabilise**. **Crop@H90 : DA 0.599→0.658 (+5.9 pts), AUC
0.61→0.71, Brier mieux, stable sur les deux moitiés.** WASDE@H40 : +3.5 pts, stabilise la
1re moitié. Parcimonie : un seul signal par horizon (combiné ≤ meilleur seul). Fondamentaux
**complémentaires** du marché, pas autonomes (DA 0.49 sans marché à H40).

### EXT015 — sélection de variables train-only — **KEEP (diagnostic)**
Importance par permutation DANS chaque fenêtre : `s2u_z`, `s2u_pctile` (WASDE) et
`cond_gd_ex_anom`, `cond_dev5y`, `cond_poor_vp` (Crop) + saisonnalité ressortent **stables**
(importance >0, 16/16 ans). Le logit top-6 train-only (DA H90 0.656) **bat le RF
kitchen-sink** (0.577) et le marché seul. À jeter : dummies `bilan_tight/loose`, momentum
court. Le gain de l'étape 4 n'était PAS fragile.

### EXT017 — régimes de marché — **IMPROVE**
Le signal est **fort en uptrend / faible-vol / bilan extrême** (H90 uptrend balanced 0.718)
et **nul en conditions neutres/normales** (trend neutre 0.468, stocks normaux 0.58, bonne
récolte 0.49 ≈ hasard). Cohérent avec V39-E4. Les régimes expliquent QUAND ça marche ; un
filtre concentrerait l'edge mais le découpage est post-hoc → à valider en forward, ne pas
fitter de modèle par régime.

### EXT009 — GARCH/EGARCH/GJR — **KEEP (risque)**
**EGARCH = meilleur modèle de vol** (RMSE −24 % vs RW à H90 ; ≈ HAR, asymétrie en plus).
Surtout : le **filtre de vol** est actionnable — dans le décile haut de volatilité prévue,
le score directionnel **s'inverse (DA 0.38) et perd (PnL<0)** ; le filtrer fait passer la DA
de 0.658 à 0.688.

### EXT010 — HAR — **KEEP (benchmark vol principal)**
HAR **bat RW-vol et rolling-20 sur RMSE/MAE/QLIKE à tous les horizons** (H90 : −23 % RMSE).
Simple, robuste, sans tuning. Contrairement à la direction des prix, **la volatilité se
prévoit**.

### EXT011 — trend-following — **REJECT (negative control)**
Tous les signaux de tendance ont **DA < 0.5** (mom120 ~0.39), Sharpe ≤ 0.20 avec drawdowns
énormes : le maïs ne tend pas. **Negative control clé** : l'edge d'EXT024 n'est PAS du
momentum déguisé (il vient de la saisonnalité + retour à la moyenne + fondamentaux).

### EXT014 — BMA-like — **IMPROVE (stabilité seulement)**
Pondération par perf passée : **plus stable** entre sous-périodes et bat le marché seul,
mais **ne dépasse pas le meilleur modèle seul** par horizon (dilue crop@H90). Le membre
sans skill (rw_baserate) est correctement neutralisé. Utile comme filet de sécurité.

### EXT050 (ex-EXT028) — stacking ensemble — **REJECT**
Le méta-modèle **sur-apprend** (DA 1re moitié ≤ 0.5, instable : H40 0.484, H90 0.500) et fait
moins bien que la moyenne simple et le meilleur membre (crop@H90 0.665). Avec un edge faible,
**la parcimonie gagne**. *(Collision résolue à l'étape 5 bis : `EXT028` ET `EXT029` sont
réservés au catalogue `ideas_matrix.csv` (satellite, corn-crush) → stacking renommé `EXT050`,
hors plage catalogue. Lignes satellite/corn-crush intactes.)*

### EXT016 — NBEATSx — **NOT_WORTH_YET**
Non lancé : `torch`/`neuralforecast` absents ; trop peu d'observations indépendantes à H90 ;
edge faible ; la complexité a sur-appris à chaque essai (EXT028, RF). Réouverture seulement
avec données plus riches + régularisation forte.

### EXT012 — OU mean-reversion — **DATA_BLOCKED**
L'OU vise une série stationnaire (basis/spread), or EXT013 (basis) et EXT005 (courbe) sont
DATA_BLOCKED (pas d'eurusd quotidien ni de contrats par maturité). Aucune simulation
artificielle d'un basis absent.

## 4. Tableau final

| experiment_id | model_family | data_used | target | best_horizon | best_metric_gain | direction_accuracy_change | brier_change | volatility_metric_gain | stability | overfitting_risk | leakage_risk | verdict | next_action |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EXT024 | logit supply-demand | marché+WASDE+Crop (stationnaire) | dir H40/H90 | H90 | DA 0.599→0.658, AUC 0.61→0.71 | +0.059 (crop H90) | −0.024 | — | stable 2 moitiés | low | none | **IMPROVE** | crop@H90 + wasde@H40, parcimonie, cible direction |
| EXT015 | RF/logit + perm. importance | idem | dir H20/40/90 | H90 | top-6 0.656 vs RF 0.577 | +0.057 vs marché | −0.019 | — | stable (16/16 ans) | low | none | **KEEP** | garder s2u_z/pctile + cond anom/dev5y/poor_vp ; jeter dummies |
| EXT017 | régimes | idem | dir par régime | H90 | uptrend balanced 0.718 vs neutre 0.468 | hétérogène | — | — | régime-dépendant | medium (post-hoc) | none | **IMPROVE** | conditionner le score de confiance ; valider filtre en forward |
| EXT009 | GARCH/EGARCH/GJR | retours CBOT | vol H20/40/90 | H90 | filtre 0.658→0.688 | +0.030 (via filtre) | — | EGARCH RMSE −24 % vs RW | stable | low | none | **KEEP** | gate de risque du score de vente |
| EXT010 | HAR | vol réalisée | vol H20/40/90 | H90 | RMSE −23 % vs RW | — | — | meilleur QLIKE tous H | stable | low | none | **KEEP** | benchmark vol principal |
| EXT011 | trend-following | CBOT | dir + stratégie | — | DA < 0.5 partout | négatif | — | — | — | low | none | **REJECT** | negative control ; abandonner |
| EXT014 | BMA-like | membres dir. | dir H40/H90 | H90 | stabilité, bat marché seul | +0.028 vs marché (H90) | −0.020 | — | + stable que membres | low | none | **IMPROVE** | filet de sécurité ; préférer choix parcimonieux |
| EXT050 (ex-EXT028) | stacking méta-logit | membres dir. | dir H40/H90 | — | < moyenne simple & meilleur membre | instable (≤0.5 1re moitié) | — | — | instable | HIGH | none | **REJECT** | ne pas empiler |
| EXT016 | NBEATSx (DL) | variables validées | dir/retour | — | non lancé | — | — | — | — | HIGH attendu | — | **NOT_WORTH_YET** | rouvrir si données plus riches |
| EXT012 | OU mean-reversion | basis/spread | — | — | — | — | — | — | — | — | — | **DATA_BLOCKED** | eurusd quotidien + spot/contrats |

## 5. Analyse honnête

- **Les modèles avancés améliorent-ils vraiment les signaux de l'étape 4 ?** Oui, mais
  surtout par le **changement de cadrage** (direction au lieu de RMSE), pas par la
  complexité. Le simple logit parcimonieux d'EXT024 est le meilleur ; le RF, le stacking et
  (anticipé) le DL sur-apprennent.
- **WASDE + Crop Condition donnent-ils un vrai signal directionnel H40/H90 ?** Oui. Crop
  Condition à H90 (DA 0.66, AUC 0.71, stable, calibré) et WASDE à H40 (+3.5 pts, stabilisant).
  EXT015 confirme que ces variables ressortent train-only de façon stable (16/16 ans).
- **Assez stable pour un score de vente ?** Oui à un niveau **modéré** : stable sur 2
  sous-périodes, économiquement logique, mais IC bootstrap chevauchant le marché seul et DM
  non significatif → c'est un **score de confiance**, pas un signal binaire à fort edge. À
  conditionner par régime (uptrend/low-vol/bilan extrême) et par le gate de vol.
- **Les modèles de volatilité améliorent-ils le risque ?** **Oui, nettement** : HAR/EGARCH
  battent la RW de vol partout, et le filtre de vol neutralise le régime où le signal
  directionnel s'inverse. C'est le résultat le plus solide de l'étape 5.
- **Les régimes expliquent-ils quand le signal marche ?** Oui : fort en tendance/faible-vol/
  bilan extrême, nul en neutre. Précieux pour doser la confiance.
- **Les modèles complexes apportent-ils quelque chose ?** **Non.** Stacking, RF kitchen-sink
  et DL sur-apprennent ; BMA n'ajoute que de la robustesse. Parcimonie gagne.
- **Le deep learning ?** **À rejeter / reporter** (NOT_WORTH_YET) : non justifié vu l'edge
  faible et le peu d'observations indépendantes.
- **Faut-il abandonner le prix/RMSE pour un score directionnel/risque ?** **OUI, clairement.**
  Le RMSE de prix est imbattable (RW, EXT025) ; l'information exploitable est dans la
  **direction long-horizon** (fondamentaux d'offre) et le **risque** (volatilité). Le bon
  livrable est un **score de vente/direction H40-H90 conditionné par le régime et gaté par
  la volatilité**, pas une prévision de prix.

## 6. Recommandation pour l'étape 6 (synthèse finale)

**À GARDER (signaux robustes)** :
- Modèle directionnel parcimonieux **crop@H90** (logit : saison + cond_gd_ex_anom + cond_dev5y
  + cond_poor_vp) et **wasde@H40** (saison + s2u_z + s2u_pctile + s2u_slow_chg) — EXT024/EXT015.
- **HAR** (vol, EXT010) et **EGARCH** (asymétrie, EXT009) + **filtre de vol** comme gate.
- **Conditionnement par régime** (EXT017) pour le score de confiance.

**À AMÉLIORER (prometteur, à valider en forward)** :
- Filtre de régime (uptrend/low-vol/bilan extrême) — risque d'overfitting post-hoc.
- BMA comme filet de robustesse (EXT014).
- Calibration/seuils du score de vente (cible ternaire UP/WAIT/DOWN, seuils train-only).

**À REJETER** : trend-following (EXT011), stacking (EXT028), niveaux WASDE bruts, météo/COT/
éthanol (étape 4).

**DONNÉES MANQUANTES (débloquer pour aller plus loin)** : EUR/USD quotidien historique
(débloque basis EXT013, OU EXT012, tableau basis EXT025) ; contrats CBOT par maturité
(courbe EXT005, prime new-crop EXT018) ; prix éthanol/DDG (EXT004) ; archive de prévisions
météo forward (EXT033, seule voie météo prédictive).

**Signaux douteux** : le gain directionnel reste modeste (IC chevauchant le marché) → tout
repose sur une validation **forward** hors 2024+ avant toute mise en production.

**RECOMMANDATION FINALE** : **basculer l'objectif du prix vers un SCORE DE VENTE /
DIRECTION / RISQUE à H40-H90**, fondé sur (Crop Condition + WASDE stocks-to-use + saison),
conditionné par le régime et gaté par la volatilité (HAR/EGARCH). Continuer à chercher des
données (eurusd, courbe, prévisions météo) pour rouvrir les pistes bloquées. Ne pas
poursuivre la prévision de prix/RMSE ni la complexité (DL/stacking). L'étape 6 doit
formaliser ce score et définir un protocole de validation forward.

L'étape 6 n'est pas codée ici (synthèse seulement).
