# Étape 6 — Synthèse des signaux robustes

Date : 2026-06-13. Question : avec toutes les sources externes (repos, études, données
gratuites) et les tests P0/P1/P2 (corrigés étape 5 bis), **a-t-on un signal robuste
exploitable** ? Réponses honnêtes, sans surpromesse.

## 1. Signal robuste pour le PRIX exact ? — **NON**
- **RMSE vs random walk** : aucune famille, aucun modèle ne bat la RW (EXT025 : 0/36 couples
  benchmark×horizon, DM p<0.10). Les fondamentaux **dégradent** le RMSE (niveaux WASDE jusqu'à
  +194 % à H90 ; météo R² OOS jusqu'à −3,4).
- **MAE / R²** : même conclusion ; R² OOS négatif dès qu'on ajoute des niveaux non-stationnaires.
- **Stabilité** : la supériorité de la RW est stable sur toutes les sous-périodes.
- **Conclusion** : **La prédiction pure du prix n'est pas validée avec les données actuelles.**

## 2. Signal robuste pour la DIRECTION ? — **OUI, partiel et modeste**
- **Meilleurs horizons** : **H90** (et secondairement H40). Court terme (H5-H20) : rien.
- **Meilleures familles** : **Crop Condition** (offre lente) > **WASDE stocks-to-use** > saison.
- **Meilleurs modèles** : **logit L2 parcimonieux** (EXT024) ; le RF, le stacking et le DL
  sur-apprennent.
- **Chiffres corrigés (EXT024, crop@H90)** : **DA 0,669** (marché seul 0,604, **+6,6 pts**),
  **AUC 0,724**, **Brier 0,218**, **balanced 0,672**, stable sur les deux moitiés (**0,632 /
  0,707**, toutes > 0,63). EXT015 : top-6 train-only 0,658 > RF 0,552 ; variables stables
  **16/16 ans**.
- **Stabilité par sous-période** : ✅ les deux moitiés > 0,63 à H90.
- **Limite de robustesse honnête** : **DM non significatif** et **IC bootstrap de la DA
  chevauchant le marché seul** → c'est un **score de confiance**, pas un signal binaire à
  fort edge. À conditionner par régime (uptrend/low-vol/bilan extrême) et gater par la vol.
- **Conclusion** : **direction H40/H90 partiellement prédictible**, utile pour un indicateur
  d'aide à la décision, **pas** pour un bot autonome.

## 3. Signal robuste pour la VOLATILITÉ ? — **OUI, le plus solide**
- **HAR** (EXT010) et **EGARCH** (EXT009) battent la RW de vol et rolling-20 sur RMSE/MAE/QLIKE
  **à tous les horizons** (−22 à −24 % RMSE à H90). EGARCH capte l'asymétrie (chocs → vol).
- **Utilité comme filtre de risque** : dans le **décile haut de vol prévue**, le score
  directionnel **s'inverse (DA 0,41, PnL<0)**. Le filtrer fait passer la DA de **0,669 à
  0,699** (et écarte le régime où l'on perd).
- **Conclusion** : la **volatilité se prévoit** (contrairement au prix) ; **gate de risque
  actionnable**. Résultat le plus robuste du programme.

## 4. Signal utile pour un SCORE DE VENTE ? — **OUI, partiel (modéré)**
- **Horizons** : **H40-H90** (décision agricole de commercialisation, pas day-trading).
- **Variables** : Crop Condition (anomalie good/excellent, déviation 5 ans, poor/very-poor),
  WASDE stocks-to-use (z, percentile, variation lente), saisonnalité ; vol HAR/EGARCH pour le
  gate ; régime (uptrend/low-vol/bilan) pour la confiance.
- **Régimes** : confiance **haute** en uptrend / low-vol / bilan extrême ; **basse** en
  neutre/normal/good-crop.
- **Comment l'utiliser sans surpromettre** : sortie **ternaire** (VENDRE / ATTENDRE /
  SURVEILLER) avec un **niveau de confiance** et un **drapeau de risque** (vol haute), pas un
  ordre automatique. Toujours afficher l'incertitude (IC chevauchant le marché).
- **Conclusion** : **oui, comme indicateur d'aide à la décision** H40-H90.

## 5. Signaux FRAGILES (gain mais instables / sur-appris / période courte)
- **Filtre de régime (EXT017)** : gain réel mais **découpage post-hoc** → à valider en forward
  avant usage en production (risque d'overfitting modéré).
- **BMA (EXT014)** : améliore la **stabilité** mais **ne dépasse pas** le meilleur membre seul
  → filet de sécurité, pas un gain de signal.
- **WASDE@H40 (EXT024)** : gain plus faible et moins net que crop@H90 ; utile surtout pour
  **stabiliser la 1re moitié**.
- **EXT002 (météo lags)** : gain DA ponctuel H40 mais R² négatif et instable → **non** un signal.

## 6. Signaux REJETÉS (à ne plus forcer avec les données actuelles)
- **Météo réalisée** (EXT001/002/020) : price-in ; dégrade le RMSE.
- **Surprise WASDE** (EXT008) : non captable en quotidien sans consensus analystes.
- **COT** (EXT003) : aucun signal de second ordre ; dossier clos.
- **Proxys éthanol/énergie** (EXT004) : sans vrai prix éthanol/DDG, inutiles.
- **Trend-following** (EXT011) : le maïs ne tend pas (negative control).
- **Stacking / DL** (EXT050/EXT016) : sur-apprentissage ; parcimonie gagne.

## 7. Signaux BLOQUÉS par manque de données
- **Futures curve / spreads / carry** (EXT005) : pas de contrats CBOT par maturité.
- **Basis / transmission spot-futures / VECM** (EXT013) : pas d'EUR/USD quotidien ni spot UE.
- **OU mean-reversion** (EXT012) : dépend du basis (bloqué).
- **Vraie surprise WASDE** (EXT008) : pas de consensus analystes pré-rapport.
- **Prime météo new-crop prédictive** (EXT018) : pas de contrats décembre + stress non ex ante.
- **Météo prévue** (EXT033) : archive de prévisions forward trop courte (seule voie météo
  prédictive cohérente avec V45).
- **Options / volatilité implicite, satellite/NDVI, prix physiques FOB** : non disponibles.

## 8. Réponse de synthèse
Avec les données **publiques gratuites**, on a trouvé : (a) **pas** de prédiction de prix
(RW imbattable) ; (b) un signal **directionnel modeste mais stable à H90** (Crop Condition +
WASDE stocks-to-use) ; (c) un signal de **volatilité/risque solide** (HAR/EGARCH). L'objet
exploitable n'est donc pas un prix, mais un **score de vente/direction/risque H40-H90**, à
valider en forward, et plusieurs familles à fort prior restent **bloquées faute de données**.
